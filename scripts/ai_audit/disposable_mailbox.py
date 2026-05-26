"""Disposable mailbox helper for the form-smoke-test email round-trip (q15).

Used only at Pro tier from ``scripts/ai_audit/form_smoke_test.py``. After
the smoke test submits a form that captures an email, this helper polls
a free disposable-email API (mail.tm by default) for up to
``poll_seconds`` seconds. If a confirmation email arrives, the form
"passed" its round-trip; if not, the runner surfaces a finding in The
Stranger's voice.

The module is intentionally small + defensive:

* Network failures, JSON parse errors, missing API responses -> we
  return ``False`` (no finding, no crash, just a logged warning).
* The disposable-mailbox APIs are externally hosted and can disappear
  without notice; the caller must tolerate that.
* We never use a customer-controlled email address. The poll target is
  always the LaunchLook synthetic mailbox advertised in
  ``form_smoke_test.SYNTHETIC_VALUES['email']``.

Per ``docs/SIMPLICITY-GUARDRAILS.md`` section 6 nothing here may leak
onto a customer surface: the buyer never sees "round-trip", "mailbox
API", or the disposable provider name.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

_CACHE_DIR = Path("data/form_smoke_cache/mailbox")
_DEFAULT_PROVIDER = "mail.tm"
_USER_AGENT = "LaunchLook/1.0 (form-smoke-test email round-trip)"


def _log_warn(msg: str) -> None:
    print(f"[mailbox] WARN: {msg}", file=sys.stderr)


def _cache_path(address: str) -> Path:
    key = hashlib.sha1(address.lower().encode("utf-8")).hexdigest()
    return _CACHE_DIR / f"{key}.json"


def _load_session(address: str) -> dict[str, Any] | None:
    path = _cache_path(address)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _save_session(address: str, session: dict[str, Any]) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(address).write_text(json.dumps(session), encoding="utf-8")


def _request(
    url: str,
    *,
    method: str = "GET",
    data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 10,
) -> dict[str, Any] | None:
    """Tiny HTTP helper that returns parsed JSON or None on any failure."""
    payload = None
    base_headers = {"User-Agent": _USER_AGENT, "Accept": "application/json"}
    if data is not None:
        payload = json.dumps(data).encode("utf-8")
        base_headers["Content-Type"] = "application/json"
    if headers:
        base_headers.update(headers)
    req = urllib.request.Request(url, data=payload, headers=base_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return {}
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        if exc.code in {404, 401}:
            return None
        _log_warn(f"HTTP {exc.code} on {url}")
        return None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        _log_warn(f"failed to call {url}: {exc}")
        return None


# ---------------------------------------------------------------------------
# mail.tm provider
# ---------------------------------------------------------------------------


_MAIL_TM_BASE = "https://api.mail.tm"


def _ensure_mail_tm_session(address: str) -> dict[str, Any] | None:
    """Return (or create) a cached mail.tm account + token for ``address``."""
    cached = _load_session(address)
    if cached and cached.get("token"):
        return cached

    domains = _request(f"{_MAIL_TM_BASE}/domains")
    if not domains:
        return None
    members = domains.get("hydra:member") if isinstance(domains, dict) else None
    if not members:
        return None
    domain = members[0].get("domain")
    if not domain:
        return None

    local = hashlib.sha1(address.encode("utf-8")).hexdigest()[:16]
    provider_address = f"{local}@{domain}"
    password = (
        os.environ.get("LAUNCHLOOK_MAIL_TM_PASSWORD") or "LaunchLookSmokeTest!2026"
    )

    created = _request(
        f"{_MAIL_TM_BASE}/accounts",
        method="POST",
        data={"address": provider_address, "password": password},
    )
    if created is None:
        return None
    token_resp = _request(
        f"{_MAIL_TM_BASE}/token",
        method="POST",
        data={"address": provider_address, "password": password},
    )
    if not token_resp or "token" not in token_resp:
        return None

    session = {
        "provider": "mail.tm",
        "address": provider_address,
        "token": token_resp["token"],
        "created_at": time.time(),
    }
    _save_session(address, session)
    return session


def _check_mail_tm(session: dict[str, Any]) -> bool:
    """Return True if the mailbox has at least one message."""
    headers = {"Authorization": f"Bearer {session['token']}"}
    payload = _request(f"{_MAIL_TM_BASE}/messages", headers=headers)
    if not payload:
        return False
    members = payload.get("hydra:member") if isinstance(payload, dict) else None
    if not members:
        return False
    return len(members) > 0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def wait_for_message(
    *,
    address: str,
    poll_seconds: int = 60,
    interval_seconds: int = 5,
) -> bool:
    """Poll a disposable mailbox for up to ``poll_seconds`` seconds.

    ``address`` is treated as an opaque key for caching the provider-side
    mailbox (the provider may not actually accept the customer-facing
    address; mail.tm rotates its own domain). Returns True on first
    arrival, False on timeout or any error.
    """
    if not address:
        return False
    provider = os.environ.get("LAUNCHLOOK_MAILBOX_PROVIDER") or _DEFAULT_PROVIDER
    if provider != "mail.tm":
        _log_warn(f"unknown provider {provider!r}; only mail.tm is wired")
        return False

    session = _ensure_mail_tm_session(address)
    if not session:
        return False

    deadline = time.time() + max(0, poll_seconds)
    interval = max(1, interval_seconds)
    while time.time() < deadline:
        if _check_mail_tm(session):
            return True
        time.sleep(interval)
    return False


def cached_provider_address(address: str) -> str | None:
    """Inspect the cached provider mailbox tied to ``address`` (debug aid)."""
    session = _load_session(address)
    if not session:
        return None
    return session.get("address")
