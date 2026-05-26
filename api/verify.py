"""
verify.py - Vercel Python serverless function for badge verification.

GET /api/verify?slug=jane-sparkle

Behaviour:

* 200 + JSON ``{valid: true, tier, verified_at, expires_at, customer_url, ...}``
  when the slug has a current badge.
* 200 + JSON ``{valid: false, reason: "expired", expired_on: ...}`` when the
  slug has a badge but the validity window has passed.
* 404 + JSON ``{valid: false, reason: "unknown_slug", ...}`` when there is
  no badge for that slug.
* 400 + JSON ``{error: "missing_slug"}`` when ``slug=`` is missing or empty.
* 429 + JSON ``{error: "rate_limited", retry_after_seconds}`` when an IP has
  made more than ``RATE_LIMIT_PER_MINUTE`` requests in the last 60 seconds.

The badge record lives at ``landing/data/verified/{slug}.json``, committed to
the repo so the verification surface is reproducible across deploys. A
future iteration may move this to Notion / D1 / KV; the file-shape contract
stays the same.

Local invocation pattern (for smoke testing without Vercel):

    python api/verify.py --slug jane-sparkle

This bypasses the HTTP layer and prints the same JSON body the serverless
function would return. Useful for verification step 3 in the q17 spec.

Rate limit notes:
    The per-IP counter lives in module-level state, which means each
    Vercel function instance has its own bucket. That is acceptable for
    a low-volume public verification endpoint: the worst case is N * 10
    requests per minute where N is the number of warm instances. If real
    traffic ever justifies it, swap the in-memory dict for a Vercel KV or
    Upstash Redis-backed counter; the call site does not need to change.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
from collections import deque
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from threading import Lock
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
VERIFY_DATA_ROOT = REPO_ROOT / "landing" / "data" / "verified"

RATE_LIMIT_PER_MINUTE = 10
RATE_LIMIT_WINDOW_SECONDS = 60

# Module-level rate-limit state: ip -> deque[float timestamps].
_rate_state: dict[str, deque[float]] = {}
_rate_lock = Lock()


# ---------------------------------------------------------------------------
# Rate limit
# ---------------------------------------------------------------------------


def is_rate_limited(
    ip: str,
    *,
    now: float | None = None,
    limit: int = RATE_LIMIT_PER_MINUTE,
    window_seconds: float = RATE_LIMIT_WINDOW_SECONDS,
) -> tuple[bool, int]:
    """Token-bucket-ish sliding window counter.

    Returns ``(rate_limited, retry_after_seconds)``.

    Thread-safe via a module-level lock; an empty ``ip`` is treated as a
    single shared bucket (i.e. blocked aggressively) so a misconfigured
    proxy that strips the IP header cannot accidentally amplify load.
    """
    now = now if now is not None else time.monotonic()
    key = ip or "_unknown_"
    with _rate_lock:
        bucket = _rate_state.setdefault(key, deque())
        cutoff = now - window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            retry_after = max(1, int(window_seconds - (now - bucket[0])))
            return True, retry_after
        bucket.append(now)
        return False, 0


def _reset_rate_state_for_tests() -> None:
    """Tests call this between cases to clear the sliding window."""
    with _rate_lock:
        _rate_state.clear()


# ---------------------------------------------------------------------------
# Slug validation + lookup
# ---------------------------------------------------------------------------


SLUG_PATTERN = "abcdefghijklmnopqrstuvwxyz0123456789-"


def normalize_slug(raw: str) -> str | None:
    """Lowercase + reject anything that is not ``[a-z0-9-]``.

    Returns ``None`` for invalid slugs so the handler can 400 cleanly.
    """
    if not raw:
        return None
    candidate = raw.strip().lower()
    if not candidate or len(candidate) > 80:
        return None
    if any(ch not in SLUG_PATTERN for ch in candidate):
        return None
    return candidate


def load_verify_record(
    slug: str,
    verify_root: Path = VERIFY_DATA_ROOT,
) -> dict[str, Any] | None:
    path = verify_root / f"{slug}.json"
    if not path.exists() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(
            f"[verify] ERROR: could not parse verify.json for slug={slug!r}: {exc}",
            file=sys.stderr,
        )
        return None


# ---------------------------------------------------------------------------
# Core "is the badge still valid?" logic
# ---------------------------------------------------------------------------


def evaluate_badge(
    record: dict[str, Any],
    *,
    today: date | None = None,
) -> dict[str, Any]:
    """Return the JSON body for a found record.

    ``today`` is overrideable for tests so we do not need to freeze time.
    """
    today = today or date.today()

    try:
        expires_at = datetime.strptime(record["expires_at"], "%Y-%m-%d").date()
    except (KeyError, ValueError):
        return {
            "valid": False,
            "reason": "malformed_record",
            "hint": "verify.json missing or malformed expires_at field",
        }

    is_current = today <= expires_at
    body: dict[str, Any] = {
        "valid": bool(is_current),
        "customer_slug": record.get("customer_slug"),
        "tier": record.get("tier"),
        "verified_at": record.get("verified_at"),
        "expires_at": record.get("expires_at"),
        "issued_by": record.get("issued_by", "LaunchLook"),
    }

    customer_url = record.get("customer_url") or ""
    if customer_url:
        body["customer_url"] = customer_url

    if not is_current:
        body["reason"] = "expired"
        body["expired_on"] = record.get("expires_at")
        body["reverify_cta"] = (
            "Need a re-verification? A $9 re-check refreshes the badge for "
            "the same validity window."
        )

    if record.get("previous_verified_at"):
        body["previous_verified_at"] = record["previous_verified_at"]

    return body


def handle_verify(
    slug_raw: str | None,
    ip: str = "",
    *,
    verify_root: Path = VERIFY_DATA_ROOT,
    today: date | None = None,
    enforce_rate_limit: bool = True,
) -> tuple[int, dict[str, Any]]:
    """Full request handler: returns ``(status_code, json_body)``.

    Exposed as a plain function so tests can drive it without an HTTP server.
    """
    if enforce_rate_limit:
        limited, retry_after = is_rate_limited(ip)
        if limited:
            return 429, {
                "error": "rate_limited",
                "retry_after_seconds": retry_after,
                "hint": (
                    "Verification is capped at 10 requests per minute per IP. "
                    "Retry after a short wait."
                ),
            }

    slug = normalize_slug(slug_raw or "")
    if not slug:
        return 400, {
            "error": "missing_slug",
            "hint": "Provide ?slug=<customer-slug>. Slugs are lowercase a-z, 0-9, and dashes.",
        }

    record = load_verify_record(slug, verify_root=verify_root)
    if record is None:
        return 404, {
            "valid": False,
            "reason": "unknown_slug",
            "customer_slug": slug,
            "hint": (
                "We do not have a record of that badge. If you bought a "
                "LaunchLook verification, email hello@launchlook.app."
            ),
        }

    return 200, evaluate_badge(record, today=today)


# ---------------------------------------------------------------------------
# HTTP handler (Vercel)
# ---------------------------------------------------------------------------


class handler(BaseHTTPRequestHandler):  # noqa: N801
    """Vercel Python runtime expects a `handler` class with do_* methods."""

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        slug_raw = (query.get("slug") or [""])[0]
        ip = _client_ip(self.headers)

        status, body = handle_verify(slug_raw, ip=ip)
        self._respond(status, body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def _respond(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "public, max-age=60")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        sys.stderr.write(f"[verify] {format % args}\n")


def _client_ip(headers: Any) -> str:
    """Best-effort client IP for rate limiting.

    Vercel sets ``x-forwarded-for`` with the public IP at index 0. Fall back
    to ``x-real-ip``, then to the remote address (which is the platform
    proxy and would lump every caller into one bucket -- acceptable as a
    last resort).
    """
    raw = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For")
    if raw:
        first = raw.split(",")[0].strip()
        if first:
            return first
    return (
        headers.get("x-real-ip")
        or headers.get("X-Real-IP")
        or ""
    )


# ---------------------------------------------------------------------------
# Local invocation (for `python api/verify.py --slug jane-sparkle`)
# ---------------------------------------------------------------------------


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local smoke test for /api/verify.")
    parser.add_argument("--slug", required=True, help="Customer slug to look up.")
    parser.add_argument(
        "--no-rate-limit",
        action="store_true",
        help="Skip the rate limiter (useful for CI loops).",
    )
    args = parser.parse_args(argv)
    status, body = handle_verify(
        args.slug,
        ip="cli",
        enforce_rate_limit=not args.no_rate_limit,
    )
    print(f"status: {status}")
    print(json.dumps(body, indent=2))
    return 0 if status < 400 else 1


if __name__ == "__main__":
    sys.exit(_cli())
