"""
tally-webhook.py — Vercel Python serverless function.

Receives FORM_RESPONSE events from the LaunchLook intake form (Tally) and
upserts the corresponding row in the Notion Customers DB.

Auth model:
    Tally's free plan does NOT sign webhook payloads, so we use a
    shared-secret-in-URL pattern. Configure the Tally webhook URL as:
        https://launchlook.app/api/tally-webhook?t=<TALLY_WEBHOOK_TOKEN>
    and set the same value in env. Mismatch -> 401.

Notion mapping:
    The friendly Tally labels are mapped to Customers DB columns via
    LABEL_RULES below. Add/adjust rules when the form changes.

Return shape:
    200 {"status": "created"|"updated", "page_id": "..."}    on success
    200 {"status": "ignored", "reason": "..."}               for non-form events
    401 {"error": "..."}                                     on token mismatch
    400 {"error": "..."}                                     on malformed payload
    500 {"error": "..."}                                     on Notion / unknown failure
"""

from __future__ import annotations

import json
import re
import sys
import traceback
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

# Make the api/_lib package importable when Vercel invokes this file directly.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib.env import optional_env, require_env  # noqa: E402
from _lib.notion_helpers import (  # noqa: E402
    STATUS_INTAKE,
    get_client,
    get_customers_ds_id,
    upsert_customer,
)

# ---------------------------------------------------------------------------
# Label routing
# ---------------------------------------------------------------------------
# Each rule: (regex applied to lower-cased label, friendly key, optional transform).
# First match wins. Anything unmatched is dropped into the Notes field.

LABEL_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"name", re.I), "name"),
    (re.compile(r"email", re.I), "email"),
    (re.compile(r"app\s*url|live\s*url|website", re.I), "app_url"),
    (re.compile(r"app\s*name", re.I), "app_name"),
    (re.compile(r"platform|which platform", re.I), "platform"),
    (re.compile(r"tier|which tier|package", re.I), "tier"),
    (
        re.compile(r"what does your app do|one\s*line|description", re.I),
        "app_description",
    ),
]


# Tally option strings -> Customers DB Tier select values.
# Includes legacy ($9 / $29) keys so old form responses still map cleanly.
# Also includes the hidden-field slug values forwarded from the Stripe success
# URL (?tier=starter / scale_up / pro), which replace the explicit Q8 question.
TIER_MAP = {
    # Hidden-field slugs (from ?tier= in Stripe success URL — new path, no Q8)
    "starter": "Starter Package",
    "scale_up": "Scale Up Package",
    "pro": "Pro Package",
    # Q8 display text (old path — keep until Q8 is deleted in Tally)
    "starter package ($19)": "Starter Package",
    "starter package ($9)": "Starter Package",
    "scale up package ($49)": "Scale Up Package",
    "scale up": "Scale Up Package",
    "full package ($49)": "Scale Up Package",
    "full package ($29)": "Scale Up Package",
    "full": "Scale Up Package",
    "launch package": "Scale Up Package",
    "pro package ($99)": "Pro Package",
}


PLATFORMS = {"lovable", "bolt", "base44", "replit", "v0", "other"}


# ---------------------------------------------------------------------------
# Payload parsing
# ---------------------------------------------------------------------------


def _value_from_field(field: dict[str, Any]) -> Any:
    """Tally encodes selects as option ids; resolve them to the option text."""
    val = field.get("value")
    options = field.get("options") or []
    if val is None:
        return None
    if isinstance(val, list):
        labels: list[str] = []
        for entry in val:
            if isinstance(entry, str):
                match = next((o for o in options if o.get("id") == entry), None)
                labels.append(match["text"] if match else entry)
            else:
                labels.append(str(entry))
        return ", ".join(label for label in labels if label)
    if isinstance(val, str):
        match = next((o for o in options if o.get("id") == val), None)
        return match["text"] if match else val
    return val


def parse_tally_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Flatten a Tally FORM_RESPONSE into a friendly dict."""
    data = payload.get("data") or {}
    fields = data.get("fields") or []
    flat: dict[str, Any] = {"_extras": {}}
    test_account_q_value: str | None = None
    tier_value: str | None = None
    for field in fields:
        label_raw = field.get("label") or ""
        label = label_raw.strip()
        value = _value_from_field(field)
        if value in (None, "", []):
            continue
        # Track tier separately so we can normalise it before storing.
        if re.search(r"tier|which tier", label, re.I):
            tier_value = str(value)
        if re.search(r"test\s+accounts?", label, re.I) and "?" in label:
            test_account_q_value = str(value)

        # Route to friendly key if a rule matches.
        for pattern, friendly in LABEL_RULES:
            if pattern.search(label):
                flat[friendly] = value
                break
        else:
            flat["_extras"][label] = value

    if tier_value:
        normalized = TIER_MAP.get(tier_value.strip().lower())
        if normalized:
            flat["tier"] = normalized

    # Platform: normalise to title case for known values.
    plat = flat.get("platform")
    if isinstance(plat, str):
        low = plat.strip().lower()
        flat["platform"] = plat.strip().title() if low in PLATFORMS else plat.strip()

    flat["_test_accounts_q"] = test_account_q_value
    flat["_submission_id"] = data.get("submissionId") or data.get("responseId")
    flat["_form_id"] = data.get("formId")
    return flat


def _notes_from_extras(flat: dict[str, Any]) -> str:
    """Roll unmatched Q/A pairs into a Notes blurb for Rob's review."""
    extras = flat.get("_extras") or {}
    parts: list[str] = []
    for label, value in extras.items():
        parts.append(f"{label}: {value}")
    if flat.get("_test_accounts_q"):
        parts.append(f"Test accounts question: {flat['_test_accounts_q']}")
    if flat.get("_submission_id"):
        parts.append(f"Tally submission: {flat['_submission_id']}")
    return "\n".join(parts)


def _test_accounts_checkbox(flat: dict[str, Any]) -> bool:
    """True iff Scale Up / Pro tier + Q9 answered "Yes -- I'll provide ...".

    Accepts both the normalised Notion values ("Scale Up Package", "Pro Package")
    and the raw hidden-field slugs ("scale_up", "pro") so the check works
    regardless of whether Q8 still exists or has been replaced by a hidden field.
    Tally lower-cases option text inconsistently, so we just look for "yes".
    """
    tier = flat.get("tier") or ""
    tier_lower = tier.strip().lower()
    is_scale_up_or_pro = tier in ("Scale Up Package", "Pro Package") or tier_lower in (
        "scale_up",
        "pro",
    )
    if not is_scale_up_or_pro:
        return False
    answer = (flat.get("_test_accounts_q") or "").strip().lower()
    return answer.startswith("yes")


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------


def process_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Pure function for unit testing — no HTTP, no env checks beyond Notion."""
    if (payload.get("eventType") or "").upper() != "FORM_RESPONSE":
        return {"status": "ignored", "reason": f"event {payload.get('eventType')!r}"}

    flat = parse_tally_payload(payload)
    email = (flat.get("email") or "").strip().lower()
    if not email:
        return {"status": "error", "reason": "no email in submission"}

    fields: dict[str, Any] = {
        "name": flat.get("name") or "",
        "email": email,
        "app_url": flat.get("app_url") or "",
        "platform": flat.get("platform") or "",
        "tier": flat.get("tier") or "",
        "status": STATUS_INTAKE,
        "intake_received": True,
        "intake_received_at": datetime.now(UTC).isoformat(),
        "notes": _notes_from_extras(flat),
    }
    if flat.get("app_description"):
        # No dedicated column for description; prefix into Notes so Rob still sees it.
        fields["notes"] = f"App: {flat['app_description']}\n\n{fields['notes']}".strip()
    # The schema currently has no "Test accounts provided" checkbox; signal via Notes.
    if _test_accounts_checkbox(flat):
        fields["notes"] = (
            f"[{flat.get('tier', 'Scale Up/Pro')} — test accounts provided]\n{fields['notes']}"
        ).strip()

    client = get_client()
    ds_id = get_customers_ds_id(client)
    page_id, action = upsert_customer(client, ds_id, fields, email_for_match=email)
    return {"status": action, "page_id": page_id, "email": email}


class handler(BaseHTTPRequestHandler):  # noqa: N801 (Vercel convention)
    def do_POST(self) -> None:  # noqa: N802
        try:
            expected_token = optional_env("TALLY_WEBHOOK_TOKEN")
            if not expected_token:
                self._respond(500, {"error": "TALLY_WEBHOOK_TOKEN not configured"})
                return
            parsed = urlparse(self.path or "")
            query = parse_qs(parsed.query)
            provided = (query.get("t") or [""])[0]
            if provided != expected_token:
                self._respond(401, {"error": "invalid or missing ?t=<token>"})
                return

            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            try:
                payload = json.loads(raw.decode("utf-8")) if raw else {}
            except json.JSONDecodeError as exc:
                self._respond(400, {"error": f"invalid JSON: {exc}"})
                return

            # require_env is called inside process_payload via get_client(); catch separately.
            try:
                require_env("NOTION_TOKEN")
                require_env("NOTION_CUSTOMERS_DB_ID")
            except Exception as exc:
                self._respond(500, {"error": str(exc)})
                return

            result = process_payload(payload)
            self._respond(200, result)
        except Exception as exc:  # noqa: BLE001
            print(
                f"[tally-webhook] ERROR: {exc}\n{traceback.format_exc()}",
                file=sys.stderr,
            )
            self._respond(500, {"error": str(exc)})

    def do_GET(self) -> None:  # noqa: N802
        # Useful for sanity-checking the route in a browser.
        self._respond(
            200,
            {
                "status": "ok",
                "hint": "POST a Tally FORM_RESPONSE here with ?t=<token>.",
            },
        )

    def _respond(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        sys.stderr.write(f"[tally-webhook] {format % args}\n")
