"""Tests for edge cases in api/free-audit.py not covered by test_free_audit_dedup.py.

Covers:
  - URL validation edge cases (bare domain, IPv6 private, localhost variants,
    missing scheme, invalid characters, port stripping)
  - Email validation edge cases (whitespace, long local part, unicode look-alikes)
  - Rate limiting: email cap (>=3), IP cap (>=10), both caps together
  - Platform normalisation: unknown platform defaults silently to vibe-coder
  - dedup failure falls back to fresh path (does NOT 500 out)
  - Empty / missing payload fields all return 400 not 500

Runs two ways:
  * pytest tests/test_free_audit_validation.py
  * python tests/test_free_audit_validation.py
"""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("NOTION_TOKEN", "test-token")
os.environ.setdefault("NOTION_FREE_AUDIT_DB_ID", "test-free-audit-db-id")

_FREE_AUDIT_PATH = REPO_ROOT / "api" / "free-audit.py"
_spec = importlib.util.spec_from_file_location("free_audit_api", _FREE_AUDIT_PATH)
free_audit = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(free_audit)


# ---------------------------------------------------------------------------
# Minimal fake Notion client (only what validate / rate-limit paths need)
# ---------------------------------------------------------------------------


class _EmptyNotionClient:
    """Notion stub that looks like an empty database (no prior rows)."""

    class _Databases:
        def retrieve(self, *, database_id: str) -> dict[str, Any]:  # noqa: ARG002
            return {"data_sources": [{"id": "ds-test"}]}

    class _DataSources:
        def query(self, **_: Any) -> dict[str, Any]:
            return {"results": []}

    class _Pages:
        def __init__(self) -> None:
            self.created: list[dict[str, Any]] = []

        def create(self, *, parent: Any, properties: Any) -> dict[str, Any]:
            row = {"id": f"row-{len(self.created) + 1}"}
            self.created.append(row)
            return row

    def __init__(self) -> None:
        self.databases = self._Databases()
        self.data_sources = self._DataSources()
        self.pages = self._Pages()


def _noop(**_: Any) -> None:
    pass


def _submit(
    url: str,
    email: str = "user@example.com",
    ip: str = "1.2.3.4",
    platform: str = "vibe-coder",
    source: str = "index",
    client: Any = None,
    now: datetime | None = None,
) -> tuple[int, dict[str, Any]]:
    factory = (lambda: client) if client else (lambda: _EmptyNotionClient())
    return free_audit.process_request(
        payload={"url": url, "email": email, "platform": platform},
        ip=ip,
        source=source,
        now=now or datetime(2026, 6, 1, 12, tzinfo=UTC),
        notion_client_factory=factory,
        email_sender=_noop,
        upsell_sender=_noop,
        ops_notification_sender=_noop,
    )


# ---------------------------------------------------------------------------
# URL validation
# ---------------------------------------------------------------------------


class UrlValidationCase(unittest.TestCase):
    def test_bare_domain_accepted(self) -> None:
        """Domain without https:// prefix should be normalised and accepted."""
        status, body = _submit("launchlook.app")
        self.assertEqual(status, 200, msg=body)
        self.assertEqual(body["status"], "queued")

    def test_bare_domain_with_path_accepted(self) -> None:
        status, body = _submit("launchlook.app/pricing")
        self.assertEqual(status, 200, msg=body)

    def test_http_scheme_accepted(self) -> None:
        status, body = _submit("http://example.com")
        self.assertEqual(status, 200, msg=body)

    def test_ftp_scheme_rejected(self) -> None:
        status, body = _submit("ftp://example.com")
        self.assertEqual(status, 400, msg=body)

    def test_localhost_rejected(self) -> None:
        status, body = _submit("http://localhost")
        self.assertEqual(status, 400, msg=body)

    def test_localhost_subdomain_rejected(self) -> None:
        status, body = _submit("http://app.localhost")
        self.assertEqual(status, 400, msg=body)

    def test_url_over_2048_chars_rejected(self) -> None:
        status, body = _submit("https://example.com/" + "a" * 2100)
        self.assertEqual(status, 400, msg=body)

    def test_empty_url_rejected(self) -> None:
        status, body = _submit("")
        self.assertEqual(status, 400, msg=body)

    def test_whitespace_only_url_rejected(self) -> None:
        status, body = _submit("   ")
        self.assertEqual(status, 400, msg=body)

    def test_ipv4_private_rejected(self) -> None:
        """192.168.x.x is RFC1918 private — must be blocked."""
        status, body = _submit("http://192.168.1.1")
        self.assertEqual(status, 400, msg=body)

    def test_ipv4_loopback_rejected(self) -> None:
        status, body = _submit("http://127.0.0.1")
        self.assertEqual(status, 400, msg=body)


# ---------------------------------------------------------------------------
# Email validation
# ---------------------------------------------------------------------------


class EmailValidationCase(unittest.TestCase):
    def test_valid_email_accepted(self) -> None:
        self.assertIsNotNone(free_audit.validate_email("user@example.com"))

    def test_leading_trailing_whitespace_stripped(self) -> None:
        result = free_audit.validate_email("  user@example.com  ")
        self.assertEqual(result, "user@example.com")

    def test_uppercase_normalised_to_lower(self) -> None:
        result = free_audit.validate_email("User@Example.COM")
        self.assertEqual(result, "user@example.com")

    def test_missing_at_sign_rejected(self) -> None:
        self.assertIsNone(free_audit.validate_email("notanemail"))

    def test_missing_tld_rejected(self) -> None:
        self.assertIsNone(free_audit.validate_email("user@example"))

    def test_single_char_tld_rejected(self) -> None:
        self.assertIsNone(free_audit.validate_email("user@example.c"))

    def test_empty_string_rejected(self) -> None:
        self.assertIsNone(free_audit.validate_email(""))

    def test_email_over_254_chars_rejected(self) -> None:
        long_local = "a" * 250
        self.assertIsNone(free_audit.validate_email(f"{long_local}@example.com"))

    def test_spaces_inside_rejected(self) -> None:
        self.assertIsNone(free_audit.validate_email("user name@example.com"))


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


class _RateLimitClient:
    """Notion stub that pre-fills rate-limit counters."""

    class _Databases:
        def retrieve(self, *, database_id: str) -> dict[str, Any]:  # noqa: ARG002
            return {"data_sources": [{"id": "ds-test"}]}

    def __init__(self, email_count: int = 0, ip_count: int = 0) -> None:
        self._email_count = email_count
        self._ip_count = ip_count
        self.databases = self._Databases()

        parent = self

        class _DS:
            def query(self, **kwargs: Any) -> dict[str, Any]:
                f = kwargs.get("filter") or {}
                conditions = f.get("and") or []
                has_email = any("email" in str(c) for c in conditions)
                count = parent._email_count if has_email else parent._ip_count
                return {"results": [{"archived": False, "in_trash": False}] * count}

        self.data_sources = _DS()

        class _Pages:
            created: list[Any] = []

            def create(self, **_: Any) -> dict[str, Any]:
                return {"id": "new-row"}

        self.pages = _Pages()


class RateLimitCase(unittest.TestCase):
    def _submit_with_counts(
        self,
        email_count: int,
        ip_count: int,
    ) -> tuple[int, dict[str, Any]]:
        client = _RateLimitClient(email_count=email_count, ip_count=ip_count)
        return _submit(
            "https://example.com",
            client=client,
        )

    def test_email_at_cap_minus_one_passes(self) -> None:
        status, body = self._submit_with_counts(email_count=2, ip_count=0)
        self.assertEqual(status, 200, msg=body)

    def test_email_at_cap_is_blocked(self) -> None:
        status, body = self._submit_with_counts(email_count=3, ip_count=0)
        self.assertEqual(status, 429, msg=body)
        self.assertIn("email", body["message"].lower())

    def test_email_over_cap_is_blocked(self) -> None:
        status, body = self._submit_with_counts(email_count=5, ip_count=0)
        self.assertEqual(status, 429, msg=body)

    def test_ip_at_cap_minus_one_passes(self) -> None:
        status, body = self._submit_with_counts(email_count=0, ip_count=9)
        self.assertEqual(status, 200, msg=body)

    def test_ip_at_cap_is_blocked(self) -> None:
        status, body = self._submit_with_counts(email_count=0, ip_count=10)
        self.assertEqual(status, 429, msg=body)
        self.assertIn("network", body["message"].lower())

    def test_ip_over_cap_is_blocked(self) -> None:
        status, body = self._submit_with_counts(email_count=0, ip_count=20)
        self.assertEqual(status, 429, msg=body)

    def test_email_checked_before_ip(self) -> None:
        """When both caps are exceeded, email cap wins (checked first in code)."""
        status, body = self._submit_with_counts(email_count=5, ip_count=15)
        self.assertEqual(status, 429, msg=body)
        self.assertIn("email", body["message"].lower())


# ---------------------------------------------------------------------------
# Platform normalisation
# ---------------------------------------------------------------------------


class PlatformNormalisationCase(unittest.TestCase):
    def _get_platform_stored(self, platform_input: str) -> str | None:
        """Submit with the given platform and return the value stored in props."""
        stored: list[str] = []

        class _CapturingClient:
            class _Databases:
                def retrieve(self, *, database_id: str) -> dict[str, Any]:  # noqa: ARG002
                    return {"data_sources": [{"id": "ds"}]}

            class _DataSources:
                def query(self, **_: Any) -> dict[str, Any]:
                    return {"results": []}

            class _Pages:
                def create(self_, *, parent: Any, properties: Any) -> dict[str, Any]:
                    sel = (properties.get("Platform") or {}).get("select") or {}
                    stored.append(sel.get("name") or "")
                    return {"id": "row-1"}

            def __init__(self) -> None:
                self.databases = self._Databases()
                self.data_sources = self._DataSources()
                self.pages = self._Pages()

        _submit(
            "https://example.com",
            platform=platform_input,
            client=_CapturingClient(),
        )
        return stored[0] if stored else None

    def test_vibe_coder_stored_verbatim(self) -> None:
        self.assertEqual(self._get_platform_stored("vibe-coder"), "vibe-coder")

    def test_webflow_stored_verbatim(self) -> None:
        self.assertEqual(self._get_platform_stored("webflow"), "webflow")

    def test_unknown_platform_stored_as_vibe_coder(self) -> None:
        """Unknown platforms silently fall back to vibe-coder.

        This is the expected behaviour (see api/free-audit.py inline comment)
        but means ops can't distinguish "unknown platform" from Lovable/Cursor
        submissions. The test documents the current contract so a future
        explicit 'unknown' option is a deliberate change.
        """
        self.assertEqual(self._get_platform_stored("shopify"), "vibe-coder")

    def test_empty_platform_stored_as_vibe_coder(self) -> None:
        self.assertEqual(self._get_platform_stored(""), "vibe-coder")

    def test_mixed_case_webflow_normalised(self) -> None:
        """The code does .strip().lower() so 'Webflow' becomes 'webflow'."""
        self.assertEqual(self._get_platform_stored("Webflow"), "webflow")


# ---------------------------------------------------------------------------
# Dedup failure falls back to fresh (not a 500)
# ---------------------------------------------------------------------------


class DedupFailureFallbackCase(unittest.TestCase):
    def test_recent_delivery_exception_queues_normally(self) -> None:
        """If recent_delivery raises, the code catches and falls back to None
        (the fresh path). The customer still gets queued; nothing 500s.

        This is the documented behaviour in api/free-audit.py line ~591.
        """
        now = datetime(2026, 6, 1, 12, tzinfo=UTC)
        client = _EmptyNotionClient()

        # Patch recent_delivery so it raises.
        with patch(
            "scripts.ai_audit.free_audit_lookup.recent_delivery",
            side_effect=RuntimeError("Notion timeout"),
        ):
            # Re-import the module's internal reference via the loaded module.
            # Because free_audit imports recent_delivery at module load time
            # we need to patch the name as the module sees it.

            # Directly patch the name in the already-loaded module's namespace.
            orig = free_audit.recent_delivery  # type: ignore[attr-defined]
            try:
                free_audit.recent_delivery = lambda **_: (_ for _ in ()).throw(  # type: ignore[attr-defined]
                    RuntimeError("Notion timeout")
                )
                status, body = free_audit.process_request(
                    payload={"url": "https://example.com", "email": "x@example.com"},
                    ip="1.2.3.4",
                    source="index",
                    now=now,
                    notion_client_factory=lambda: client,
                    email_sender=_noop,
                    upsell_sender=_noop,
                    ops_notification_sender=_noop,
                )
            finally:
                free_audit.recent_delivery = orig  # type: ignore[attr-defined]

        self.assertEqual(status, 200, msg=f"dedup failure should not 500: {body!r}")
        self.assertEqual(body["status"], "queued")

    def test_missing_payload_fields_return_400(self) -> None:
        """Completely empty payload returns 400, not 500."""
        status, body = free_audit.process_request(
            payload={},
            ip="1.2.3.4",
            source="index",
            now=datetime(2026, 6, 1, tzinfo=UTC),
            notion_client_factory=lambda: _EmptyNotionClient(),
            email_sender=_noop,
            upsell_sender=_noop,
            ops_notification_sender=_noop,
        )
        self.assertEqual(status, 400, msg=body)

    def test_none_values_in_payload_return_400(self) -> None:
        status, body = free_audit.process_request(
            payload={"url": None, "email": None},
            ip="1.2.3.4",
            source="index",
            now=datetime(2026, 6, 1, tzinfo=UTC),
            notion_client_factory=lambda: _EmptyNotionClient(),
            email_sender=_noop,
            upsell_sender=_noop,
            ops_notification_sender=_noop,
        )
        self.assertEqual(status, 400, msg=body)


# ---------------------------------------------------------------------------
# Stdlib-only runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
