"""
e2e-auth.py — gate for the internal /e2e checklist page.

POST JSON {"password": "..."} and compare to E2E_CHECKLIST_PASSWORD.
Returns 200 {"ok": true} or 401. The checklist page stores unlock in
sessionStorage after a successful POST (no cookie needed).

Set E2E_CHECKLIST_PASSWORD in Vercel + local .env. Generate with:
  python -c "import secrets; print(secrets.token_urlsafe(24))"
"""

from __future__ import annotations

import hashlib
import hmac
import json
import sys
import traceback
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib.env import optional_env  # noqa: E402


def _password_ok(provided: str, expected: str) -> bool:
    a = hashlib.sha256(provided.encode("utf-8")).digest()
    b = hashlib.sha256(expected.encode("utf-8")).digest()
    return hmac.compare_digest(a, b)


class handler(BaseHTTPRequestHandler):  # noqa: N801
    def do_POST(self) -> None:  # noqa: N802
        try:
            expected = optional_env("E2E_CHECKLIST_PASSWORD")
            if not expected:
                self._respond(
                    503,
                    {"ok": False, "error": "E2E_CHECKLIST_PASSWORD not configured"},
                )
                return

            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            try:
                payload = json.loads(raw.decode("utf-8")) if raw else {}
            except json.JSONDecodeError as exc:
                self._respond(400, {"ok": False, "error": f"invalid JSON: {exc}"})
                return

            provided = str(payload.get("password") or "")
            if not provided or not _password_ok(provided, expected):
                self._respond(401, {"ok": False, "error": "invalid password"})
                return

            self._respond(200, {"ok": True})
        except Exception as exc:  # noqa: BLE001
            print(f"[e2e-auth] ERROR: {exc}\n{traceback.format_exc()}", file=sys.stderr)
            self._respond(500, {"ok": False, "error": "server error"})

    def do_GET(self) -> None:  # noqa: N802
        self._respond(
            200,
            {"status": "ok", "hint": "POST JSON {password} to unlock /e2e checklist."},
        )

    def _respond(self, status: int, body: dict[str, Any]) -> None:
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        sys.stderr.write(f"[e2e-auth] {format % args}\n")
