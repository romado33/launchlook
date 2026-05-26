"""
free-audit.py -- Vercel Python serverless function.

Receives POSTs from the free 3-finding audit form on /landing/index.html
and /landing/webflow.html. Per docs/PRODUCT-DECISIONS.md section 1 + 7
the free preview is the email-gated lead magnet at the top of the funnel.

Flow per task spec:
    1. POST with {url, email} (+ optional platform). JSON or form-urlencoded.
    2. Rate-limit:
         * <= 3 free requests per email per 30 days
         * <= 10 free requests per IP per day
       State lives in Notion in the FreeAuditRequests DB (NOTION_FREE_AUDIT_DB_ID).
    3. Validate URL (http/https only, hostname resolvable, NOT localhost or
       private RFC1918 / link-local / loopback).
    4. Validate email (simple regex).
    5. Dedupe gate: scripts/ai_audit/free_audit_lookup.recent_delivery() looks
       up the most recent prior row for the same email + same hostname inside
       the 30-day window (docs/FREE-AUDIT-WORKFLOW.md section 3). When a row
       exists we return the Starter upsell response instead of queueing a
       second free audit, and send a short founder-voice upsell email in
       place of the queue-confirmation email.
    6. Otherwise upsert to Notion as status="queued" with email, url,
       request_timestamp, ip, source page, platform, finding_fingerprints
       (empty for now; scripts/ai_audit/dedup.py + free_audit_lookup.py
       populate the fingerprints once the offline pipeline generates the
       3 findings -- see docs/FREE-AUDIT-WORKFLOW.md).
    7. Fire-and-forget confirmation email via Resend REST (urllib, no SDK)
       so api/requirements.txt stays minimal.
    8. Respond JSON {status:"queued"|"duplicate", message:"..."} to the
       browser. landing/assets/free-audit.js intercepts the form submit
       and redirects to /thanks-free-audit on either; if JS is off the
       native POST goes through and the handler returns a 303 to the
       same page.

Response shapes:
    200 {"status":"queued","message":"..."}             happy path
    200 {"status":"duplicate","message":"...","upsell":{"date":"...",
        "available_again":"...","starter_url":"..."}}  recent request for same email+host
    400 {"status":"error","message":"..."}              invalid input
    429 {"status":"error","message":"..."}              rate limited
    500 {"status":"error","message":"..."}              Notion / config failure

No customer-visible jargon: messages are plain English per
docs/SIMPLICITY-GUARDRAILS.md sections 2.1, 3.1, 5, 6. The upsell copy
avoids em-dashes per section 6 and signs the email as "-- Rob"
per section 5.2.
"""

from __future__ import annotations

import ipaddress
import json
import re
import socket
import sys
import traceback
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

# Make the api/_lib package importable when Vercel invokes this file directly.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib.env import optional_env, require_env  # noqa: E402

# Repo-root import so the serverless function can reach the shared
# Notion lookup helper that owns the dedupe contract. Vercel bundles
# the repo at /var/task; this matches what scripts/ai_audit imports
# expect when ai_audit pipeline modules are loaded.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.ai_audit.free_audit_lookup import (  # noqa: E402
    DEFAULT_RECENT_DELIVERY_DAYS,
    recent_delivery,
)

# notion_helpers does the heavy lifting for the Customers DB; for the
# free-audit DB we use the bare client directly because the schema differs.
try:
    from notion_client import Client  # noqa: E402
    from notion_client.errors import APIResponseError  # noqa: E402
except ImportError:  # pragma: no cover - exercised on cold start with missing deps
    Client = None  # type: ignore[assignment]
    APIResponseError = Exception  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

# RFC 5322 is overkill for "looks like an email"; this matches what 99 percent of
# customer-facing forms use and rejects the obvious nonsense.
_EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")

# Soft cap so an attacker can't post us a 10 MB body. Free-audit payload is
# always two short strings plus an optional platform tag.
_MAX_BODY_BYTES = 8 * 1024

# Plain-English error messages we feel comfortable showing customers.
ERR_EMAIL = "That email doesn't look right. Double-check and try again."
ERR_URL = "We couldn't reach that URL. Make sure it starts with https://, isn't localhost, and is reachable on the public internet."
ERR_RATE_EMAIL = "We've already queued a few free audits for this email recently. Try again in a few weeks, or pick up Starter ($19) to keep going."
ERR_RATE_IP = "A few free audits have already gone in from your network today. Try again tomorrow."
ERR_GENERIC = (
    "Something went wrong on our end. Email hello@launchlook.app and we'll sort it."
)

# Where the upsell email + JSON response point. Mirrors the existing
# free-audit confirmation email so the Plausible StarterCheckout goal
# still fires from the same /#pricing button (which carries the
# data-launchlook-stripe="starter" attribute landing/assets/apply-config.js
# wires up to the real Stripe URL).
STARTER_URL = "https://launchlook.app/#pricing"


def validate_email(value: str) -> str | None:
    """Return canonicalized lowercase email, or None if invalid."""
    if not value:
        return None
    cleaned = value.strip().lower()
    if len(cleaned) > 254 or not _EMAIL_REGEX.match(cleaned):
        return None
    return cleaned


def validate_url(value: str) -> str | None:
    """Return canonicalized URL, or None if not safe.

    Rejects non-http/https schemes, localhost, RFC1918 private ranges,
    link-local, multicast, and unresolvable hosts. A reachability check
    is deliberately NOT done here -- the offline audit pipeline will hit
    the site at audit time. This keeps the form latency low and avoids
    handing attackers a way to use us as a side-channel scanner.
    """
    if not value:
        return None
    cleaned = value.strip()
    if len(cleaned) > 2048:
        return None
    try:
        parsed = urlparse(cleaned)
    except Exception:
        return None
    if parsed.scheme not in ("http", "https"):
        return None
    host = (parsed.hostname or "").strip().lower()
    if not host:
        return None
    if host in {"localhost", "0.0.0.0"} or host.endswith(".localhost"):
        return None

    # Resolve and reject private / loopback / link-local / multicast targets.
    try:
        # getaddrinfo returns IPv4 + IPv6 records; reject if ANY is unsafe.
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return None
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return None
    return cleaned


# ---------------------------------------------------------------------------
# Date helper
# ---------------------------------------------------------------------------


def _format_date(value: datetime) -> str:
    """Plain-English date string ("May 26, 2026").

    ``strftime("%-d")`` is POSIX-only and ``"%#d"`` is Windows-only; build
    the day manually so the customer-facing copy stays portable between
    Vercel (Linux) and Rob's local dev machine.
    """
    return f"{value.strftime('%B')} {value.day}, {value.year}"


# ---------------------------------------------------------------------------
# Notion: free-audit DB helpers
# ---------------------------------------------------------------------------

# DB schema (created manually by Rob; see docs/FREE-AUDIT-WORKFLOW.md):
#   Title       "Request"   title       (e.g. "you@email.com -- example.com")
#   Email       "Email"     email
#   URL         "URL"       url
#   IP          "IP"        rich_text
#   Status      "Status"    select       (queued / processed / delivered /
#                                         skipped / abuse)
#   Source      "Source"    select       (index / webflow / api)
#   Platform    "Platform"  select       (vibe-coder / webflow)
#   Fingerprints "Finding Fingerprints"  rich_text  (semicolon-separated hashes,
#                                                    populated by the offline
#                                                    pipeline after delivery)


def _get_free_audit_ds_id(client: Client) -> str:
    db_id = require_env("NOTION_FREE_AUDIT_DB_ID")
    db = client.databases.retrieve(database_id=db_id)
    sources = db.get("data_sources") or []
    if not sources:
        raise RuntimeError(
            f"Free-audit DB {db_id[:8]}... has no data_sources. Re-share it with the integration."
        )
    return sources[0]["id"]


def _build_props(
    *, email: str, url: str, ip: str, source: str, platform: str
) -> dict[str, Any]:
    title = f"{email} -- {urlparse(url).hostname or 'unknown'}"
    return {
        "Request": {"title": [{"text": {"content": title[:2000]}}]},
        "Email": {"email": email},
        "URL": {"url": url},
        "IP": {"rich_text": [{"text": {"content": ip[:200]}}]},
        "Status": {"select": {"name": "queued"}},
        "Source": {"select": {"name": source}},
        "Platform": {"select": {"name": platform}},
    }


def _count_recent_requests_by_email(
    client: Client, ds_id: str, email: str, since: datetime
) -> int:
    """Count free-audit rows for this email created at or after `since`."""
    try:
        resp = client.data_sources.query(
            data_source_id=ds_id,
            filter={
                "and": [
                    {"property": "Email", "email": {"equals": email}},
                    {
                        "timestamp": "created_time",
                        "created_time": {"on_or_after": since.isoformat()},
                    },
                ]
            },
            page_size=10,
        )
    except APIResponseError as exc:
        raise RuntimeError(f"Notion query failed: {exc}") from exc
    return sum(
        1
        for r in resp.get("results", [])
        if not r.get("archived") and not r.get("in_trash")
    )


def _count_recent_requests_by_ip(
    client: Client, ds_id: str, ip: str, since: datetime
) -> int:
    if not ip:
        return 0
    try:
        resp = client.data_sources.query(
            data_source_id=ds_id,
            filter={
                "and": [
                    {"property": "IP", "rich_text": {"equals": ip}},
                    {
                        "timestamp": "created_time",
                        "created_time": {"on_or_after": since.isoformat()},
                    },
                ]
            },
            page_size=20,
        )
    except APIResponseError as exc:
        raise RuntimeError(f"Notion query failed: {exc}") from exc
    return sum(
        1
        for r in resp.get("results", [])
        if not r.get("archived") and not r.get("in_trash")
    )


# ---------------------------------------------------------------------------
# Confirmation + upsell emails (Resend REST)
# ---------------------------------------------------------------------------


def _post_resend_email(*, payload: dict[str, Any], context: str) -> None:
    """POST an email payload to Resend; log + swallow failures."""
    api_key = optional_env("RESEND_API_KEY")
    if not api_key:
        print(
            f"[free-audit] WARN: RESEND_API_KEY missing; skipping {context} email",
            file=sys.stderr,
        )
        return

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            req, timeout=8
        ) as resp:  # noqa: S310 - explicit trusted host
            resp.read()
    except urllib.error.HTTPError as exc:
        print(
            f"[free-audit] WARN: Resend HTTP {exc.code} on {context}: {exc.read()[:200]!r}",
            file=sys.stderr,
        )
    except urllib.error.URLError as exc:
        print(
            f"[free-audit] WARN: Resend network error on {context}: {exc}",
            file=sys.stderr,
        )


# Plain-English founder voice per SIMPLICITY-GUARDRAILS section 5.1 and 6.
# Single short paragraph, no "AI-powered" framing, no platform branding,
# signs as "-- Rob" per section 5.2.
def _send_confirmation_email(*, to: str, audit_url: str) -> None:
    from_email = optional_env("FROM_EMAIL", "hello@launchlook.app")
    admin_email = optional_env("ADMIN_EMAIL")

    host = urlparse(audit_url).hostname or audit_url
    subject = f"Got it -- your 3 findings for {host} are queued"
    text_body = (
        f"Hi,\n\n"
        f"Got your request for a free 3-finding audit on {audit_url}. "
        f"I'll walk through it on desktop and phone like a first-time visitor and email you the three highest-impact things to fix within 24 hours. "
        f"No login, no portal -- just one email back.\n\n"
        f"If you want all 10 findings sooner, Starter ($19) covers the full pass: {STARTER_URL}\n\n"
        f"-- LaunchLook\n"
        f"hello@launchlook.app\n"
    )

    payload: dict[str, Any] = {
        "from": f"LaunchLook <{from_email}>",
        "to": [to],
        "subject": subject,
        "text": text_body,
        "reply_to": from_email,
    }
    if admin_email and admin_email.lower() != to.lower():
        payload["bcc"] = [admin_email]

    _post_resend_email(payload=payload, context="confirmation")


# Upsell email used when ``recent_delivery`` returns a prior row -- replaces
# the queue-confirmation so the customer sees the actual next step instead
# of silent "already queued" copy. Plain English, founder voice, no
# em-dashes (SIMPLICITY-GUARDRAILS section 6), signs as "-- Rob"
# (section 5.2). Body stays well under the 150-word delivery cap (section 5.3).
def _send_upsell_email(
    *,
    to: str,
    audit_url: str,
    prior_submitted_at: datetime,
    available_again_at: datetime,
) -> None:
    from_email = optional_env("FROM_EMAIL", "hello@launchlook.app")
    admin_email = optional_env("ADMIN_EMAIL")

    host = urlparse(audit_url).hostname or audit_url
    submitted_str = _format_date(prior_submitted_at)
    available_str = _format_date(available_again_at)

    subject = f"You already ran the free check for {host}"
    text_body = (
        f"Hi,\n\n"
        f"Thanks for coming back. You ran the free check for {audit_url} on {submitted_str}. "
        f"I keep the findings consistent for 30 days so you can re-check after fixing.\n\n"
        f"If you've already worked through those three, Starter ($19) picks up where the free audit left off "
        f"(same plain-English style, 10 findings instead of 3, no rehash): {STARTER_URL}\n\n"
        f"Or wait until {available_str} to run the free check again.\n\n"
        f"-- LaunchLook\n"
        f"hello@launchlook.app\n"
    )

    payload: dict[str, Any] = {
        "from": f"LaunchLook <{from_email}>",
        "to": [to],
        "subject": subject,
        "text": text_body,
        "reply_to": from_email,
    }
    if admin_email and admin_email.lower() != to.lower():
        payload["bcc"] = [admin_email]

    _post_resend_email(payload=payload, context="upsell")


# ---------------------------------------------------------------------------
# Customer-facing copy for the JSON response.
# ---------------------------------------------------------------------------


def _build_upsell_message(
    *, audit_url: str, prior_submitted_at: datetime, available_again_at: datetime
) -> str:
    """Plain-English upsell copy for the JSON response message field.

    No em-dashes (SIMPLICITY-GUARDRAILS section 6). Single short
    paragraph the frontend can surface as-is when JS is disabled.
    """
    submitted_str = _format_date(prior_submitted_at)
    available_str = _format_date(available_again_at)
    return (
        f"You ran the free check for {audit_url} on {submitted_str}. "
        f"The findings stay consistent for 30 days so you can re-check after fixing. "
        f"If you've already worked through those three, Starter ($19) picks up where "
        f"the free audit left off (10 findings instead of 3, no rehash): "
        f"{STARTER_URL}. Otherwise the free check opens back up on {available_str}."
    )


# ---------------------------------------------------------------------------
# Core handler (pure-ish; isolated from HTTP wiring for unit-testability)
# ---------------------------------------------------------------------------


def process_request(
    *,
    payload: dict[str, Any],
    ip: str,
    source: str,
    now: datetime | None = None,
    notion_client_factory=None,
    email_sender=_send_confirmation_email,
    upsell_sender=_send_upsell_email,
) -> tuple[int, dict[str, Any]]:
    """Validate + rate-limit + persist + notify. Returns (status_code, body)."""
    now = now or datetime.now(UTC)

    email = validate_email(str(payload.get("email") or ""))
    if not email:
        return 400, {"status": "error", "message": ERR_EMAIL}

    url = validate_url(str(payload.get("url") or ""))
    if not url:
        return 400, {"status": "error", "message": ERR_URL}

    platform = (str(payload.get("platform") or "vibe-coder")).strip().lower()
    if platform not in {"vibe-coder", "webflow"}:
        platform = "vibe-coder"

    factory = notion_client_factory or (
        lambda: Client(auth=require_env("NOTION_TOKEN"))
    )
    try:
        client = factory()
        ds_id = _get_free_audit_ds_id(client)
    except Exception as exc:  # noqa: BLE001
        print(f"[free-audit] ERROR: Notion setup failed: {exc}", file=sys.stderr)
        return 500, {"status": "error", "message": ERR_GENERIC}

    # ---- Rate limits ----
    since_email = now - timedelta(days=30)
    since_ip = now - timedelta(days=1)
    try:
        email_count = _count_recent_requests_by_email(client, ds_id, email, since_email)
    except Exception as exc:  # noqa: BLE001
        print(f"[free-audit] ERROR: email rate query failed: {exc}", file=sys.stderr)
        return 500, {"status": "error", "message": ERR_GENERIC}
    if email_count >= 3:
        return 429, {"status": "error", "message": ERR_RATE_EMAIL}

    try:
        ip_count = _count_recent_requests_by_ip(client, ds_id, ip, since_ip)
    except Exception as exc:  # noqa: BLE001
        print(f"[free-audit] ERROR: ip rate query failed: {exc}", file=sys.stderr)
        return 500, {"status": "error", "message": ERR_GENERIC}
    if ip_count >= 10:
        return 429, {"status": "error", "message": ERR_RATE_IP}

    # ---- 30-day dedupe gate (recent_delivery) ----
    # Same email + same hostname inside the 30-day window returns the
    # Starter upsell response instead of generating a second free audit.
    # Same URL with a different email = different person -> falls through.
    # See docs/FREE-AUDIT-WORKFLOW.md section 3.
    try:
        prior = recent_delivery(
            url=url,
            email=email,
            days=DEFAULT_RECENT_DELIVERY_DAYS,
            client=client,
            ds_id=ds_id,
            now=now,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[free-audit] WARN: recent_delivery failed: {exc}", file=sys.stderr)
        prior = None

    if prior is not None:
        prior_submitted_at = prior.get("created_at") or now
        available_again_at = prior.get("expires_at") or (
            prior_submitted_at + timedelta(days=DEFAULT_RECENT_DELIVERY_DAYS)
        )
        prior_url = prior.get("url") or url
        message = _build_upsell_message(
            audit_url=prior_url,
            prior_submitted_at=prior_submitted_at,
            available_again_at=available_again_at,
        )
        # Mirror the queued path: send the customer the actual next step
        # (best-effort; we still return 200 either way).
        try:
            upsell_sender(
                to=email,
                audit_url=prior_url,
                prior_submitted_at=prior_submitted_at,
                available_again_at=available_again_at,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[free-audit] WARN: upsell email failed: {exc}", file=sys.stderr)
        return 200, {
            "status": "duplicate",
            "message": message,
            "upsell": {
                "date": _format_date(prior_submitted_at),
                "available_again": _format_date(available_again_at),
                "starter_url": STARTER_URL,
            },
        }

    # ---- Persist ----
    props = _build_props(email=email, url=url, ip=ip, source=source, platform=platform)
    try:
        client.pages.create(parent={"data_source_id": ds_id}, properties=props)
    except Exception as exc:  # noqa: BLE001
        print(f"[free-audit] ERROR: Notion create failed: {exc}", file=sys.stderr)
        return 500, {"status": "error", "message": ERR_GENERIC}

    # ---- Confirmation email (best-effort) ----
    try:
        email_sender(to=email, audit_url=url)
    except Exception as exc:  # noqa: BLE001
        print(f"[free-audit] WARN: confirmation email failed: {exc}", file=sys.stderr)

    return 200, {
        "status": "queued",
        "message": "Got it. Check your inbox for a confirmation. Your 3 findings will arrive within 24 hours.",
    }


# ---------------------------------------------------------------------------
# HTTP wiring
# ---------------------------------------------------------------------------


def _parse_body(content_type: str, raw: bytes) -> dict[str, Any]:
    """Accept either JSON or form-urlencoded so the form keeps working with JS off."""
    if not raw:
        return {}
    ctype = (content_type or "").lower()
    if "application/json" in ctype:
        try:
            data = json.loads(raw.decode("utf-8", errors="replace"))
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}
    if "application/x-www-form-urlencoded" in ctype or "multipart/form-data" in ctype:
        parsed = parse_qs(raw.decode("utf-8", errors="replace"))
        flat: dict[str, Any] = {}
        for key, values in parsed.items():
            if values:
                flat[key] = values[0]
        return flat
    # Last-ditch: try JSON anyway in case Content-Type was dropped.
    try:
        data = json.loads(raw.decode("utf-8", errors="replace"))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _client_ip(headers) -> str:
    # Vercel sets x-forwarded-for; first hop is the real client.
    xff = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For") or ""
    if xff:
        return xff.split(",")[0].strip()
    real = headers.get("x-real-ip") or headers.get("X-Real-IP") or ""
    return real.strip()


def _source_from_referer(headers) -> str:
    ref = (headers.get("referer") or headers.get("Referer") or "").lower()
    if "/webflow" in ref:
        return "webflow"
    if ref:
        return "index"
    return "api"


def _wants_html(headers) -> bool:
    accept = (headers.get("accept") or headers.get("Accept") or "").lower()
    # JS POST sets Accept: application/json; native form POST doesn't.
    return "application/json" not in accept and "text/html" in accept


class handler(BaseHTTPRequestHandler):  # noqa: N801 (Vercel convention)
    def do_POST(self) -> None:  # noqa: N802
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length > _MAX_BODY_BYTES:
                self._respond_json(400, {"status": "error", "message": ERR_GENERIC})
                return
            raw = self.rfile.read(length) if length > 0 else b""
            payload = _parse_body(self.headers.get("Content-Type", ""), raw)
            ip = _client_ip(self.headers)
            source = _source_from_referer(self.headers)
            wants_html = _wants_html(self.headers)

            try:
                require_env("NOTION_TOKEN")
                require_env("NOTION_FREE_AUDIT_DB_ID")
            except Exception as exc:
                print(f"[free-audit] ERROR: missing env: {exc}", file=sys.stderr)
                self._respond_json(500, {"status": "error", "message": ERR_GENERIC})
                return

            status, body = process_request(payload=payload, ip=ip, source=source)

            if wants_html and status in (200,):
                # No-JS native form POST: redirect to the thanks page.
                self.send_response(303)
                self.send_header("Location", "/thanks-free-audit")
                self.end_headers()
                return

            self._respond_json(status, body)
        except Exception as exc:  # noqa: BLE001
            print(
                f"[free-audit] ERROR: {exc}\n{traceback.format_exc()}", file=sys.stderr
            )
            self._respond_json(500, {"status": "error", "message": ERR_GENERIC})

    def do_GET(self) -> None:  # noqa: N802
        # Tiny health-check so we can verify the route is alive in a browser.
        self._respond_json(
            200,
            {
                "status": "ok",
                "hint": "POST {url, email} as JSON to queue a free 3-finding audit.",
            },
        )

    def _respond_json(self, status: int, body: dict[str, Any]) -> None:
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        sys.stderr.write(f"[free-audit] {format % args}\n")
