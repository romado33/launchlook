"""Tests for the free-audit 30-day fingerprint dedupe gate.

Covers the five cases the task spec calls out:

1. Fresh submission (no prior row) -> queues a fresh free audit normally
   and sends the confirmation email.
2. Repeat within 30 days same URL + same email -> returns the Starter
   upsell response, does NOT write a second row, sends the upsell email
   (not the queue confirmation).
3. Repeat after 30 days -> falls back to fresh-submission behaviour
   (uses a frozen ``now`` so the cutoff is deterministic).
4. Same URL with a different email = different person -> delivers the
   fresh free audit; dedup is per email+host, not per host alone.
5. Storage round-trip: a row written by ``process_request`` is visible
   to ``recent_delivery`` on the next call against the same stub client.

The tests speak directly to ``process_request`` via its
``notion_client_factory`` + ``email_sender`` + ``upsell_sender``
dependency-injection seams so they do not touch the network. The fake
Notion client implements just enough of the ``Client.databases`` /
``Client.data_sources`` / ``Client.pages`` surface to drive the dedupe
code paths.

Runs two ways (mirrors tests/test_dedup.py + tests/test_verified_badge.py):

* ``pytest tests/test_free_audit_dedup.py``
* ``python tests/test_free_audit_dedup.py`` (stdlib-only)
"""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# The serverless handler reads NOTION_FREE_AUDIT_DB_ID via the
# api/_lib/env.require_env() helper to fetch the data-source id.
# Set test placeholders BEFORE importing the module so cold-start
# behaviour matches what Vercel does (env present, real client stubbed).
os.environ.setdefault("NOTION_TOKEN", "test-token")
os.environ.setdefault("NOTION_FREE_AUDIT_DB_ID", "test-free-audit-db-id")

# api/free-audit.py is not a regular module (hyphenated filename + no
# package __init__.py); load it through importlib the same way
# tests/test_verified_badge.py loads api/verify.py.
_FREE_AUDIT_PATH = REPO_ROOT / "api" / "free-audit.py"
_spec = importlib.util.spec_from_file_location("free_audit_api", _FREE_AUDIT_PATH)
free_audit = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(free_audit)

from scripts.ai_audit import free_audit_lookup  # noqa: E402

# ---------------------------------------------------------------------------
# Fake Notion client
# ---------------------------------------------------------------------------


class _Databases:
    def retrieve(self, *, database_id: str) -> dict[str, Any]:  # noqa: ARG002
        return {"data_sources": [{"id": "ds-test"}]}


class _DataSources:
    """Minimal data-sources surface that supports the filters the code uses.

    The real Notion ``data_sources.query`` accepts arbitrary
    ``filter``/``sorts``/``page_size``; we only implement what
    ``api/free-audit.py`` + ``free_audit_lookup.recent_delivery`` send:

    * ``{"and": [...]}`` compounds
    * ``{"property": "Email", "email": {"equals": ...}}``
    * ``{"property": "IP", "rich_text": {"equals": ...}}``
    * ``{"timestamp": "created_time", "created_time": {"on_or_after": iso}}``
    * ``sorts=[{"timestamp": "created_time", "direction": "descending"}]``
    """

    def __init__(self, parent: FakeNotionClient) -> None:
        self._parent = parent

    def query(
        self,
        *,
        data_source_id: str,  # noqa: ARG002
        filter: dict[str, Any] | None = None,  # noqa: A002
        sorts: list[dict[str, Any]] | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        rows = [r for r in self._parent.rows if self._match(r, filter)]
        if sorts:
            direction = sorts[0].get("direction", "ascending")
            rows.sort(
                key=lambda r: r.get("created_time", ""),
                reverse=(direction == "descending"),
            )
        if page_size:
            rows = rows[:page_size]
        return {"results": rows}

    def _match(self, row: dict[str, Any], spec: dict[str, Any] | None) -> bool:
        if not spec:
            return True
        if "and" in spec:
            return all(self._match(row, c) for c in spec["and"])
        if "or" in spec:
            return any(self._match(row, c) for c in spec["or"])
        if "timestamp" in spec and spec["timestamp"] == "created_time":
            cutoff = spec["created_time"]["on_or_after"]
            return (row.get("created_time") or "") >= cutoff
        if "property" in spec:
            prop_name = spec["property"]
            prop = row.get("properties", {}).get(prop_name, {})
            if "email" in spec:
                return (prop.get("email") or "").lower() == (
                    spec["email"]["equals"] or ""
                ).lower()
            if "rich_text" in spec:
                parts = prop.get("rich_text") or []
                value = "".join(p.get("plain_text") or "" for p in parts)
                return value == spec["rich_text"]["equals"]
        return False


class _Pages:
    def __init__(self, parent: FakeNotionClient) -> None:
        self._parent = parent

    def create(
        self, *, parent: dict[str, Any], properties: dict[str, Any]  # noqa: ARG002
    ) -> dict[str, Any]:
        # Mimic Notion-shaped row so subsequent queries via the same
        # stub return it (storage round-trip).
        now = self._parent.now or datetime.now(UTC)
        # The Status select stores the plain text under name; normalize
        # the IP rich_text so the same shape recent_delivery + the rate
        # limiters consume comes out of pages.create as well.
        normalized = dict(properties)
        ip_prop = normalized.get("IP") or {}
        rich = ip_prop.get("rich_text") or []
        if rich and "text" in rich[0]:
            rich = [{"plain_text": rich[0]["text"]["content"]}]
        normalized["IP"] = {"rich_text": rich}
        url_prop = normalized.get("URL") or {}
        normalized["URL"] = {"url": url_prop.get("url")}
        email_prop = normalized.get("Email") or {}
        normalized["Email"] = {"email": email_prop.get("email")}
        status_prop = normalized.get("Status") or {}
        normalized["Status"] = status_prop
        row = {
            "id": f"row-{len(self._parent.rows) + 1}",
            "created_time": now.isoformat().replace("+00:00", "Z"),
            "properties": normalized,
            "archived": False,
            "in_trash": False,
        }
        self._parent.rows.append(row)
        self._parent.created.append(row)
        return row


class FakeNotionClient:
    """Stub Notion client driven by the unit tests."""

    def __init__(
        self,
        *,
        rows: list[dict[str, Any]] | None = None,
        now: datetime | None = None,
    ) -> None:
        self.rows = list(rows or [])
        self.created: list[dict[str, Any]] = []
        self.now = now
        self.databases = _Databases()
        self.data_sources = _DataSources(self)
        self.pages = _Pages(self)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_row(
    *,
    row_id: str,
    email: str,
    url: str,
    created_at: datetime,
    ip: str = "203.0.113.10",
    status: str = "queued",
    fingerprints: list[str] | None = None,
    summaries: list[str] | None = None,
) -> dict[str, Any]:
    """Build a Notion-shaped row matching docs/FREE-AUDIT-WORKFLOW.md schema."""
    props: dict[str, Any] = {
        "Request": {"title": [{"text": {"content": f"{email} -- {url}"}}]},
        "Email": {"email": email},
        "URL": {"url": url},
        "IP": {"rich_text": [{"plain_text": ip}]},
        "Status": {"select": {"name": status}},
        "Source": {"select": {"name": "index"}},
        "Platform": {"select": {"name": "vibe-coder"}},
    }
    if fingerprints:
        props["Finding Fingerprints"] = {
            "rich_text": [{"plain_text": ";".join(fingerprints)}]
        }
    if summaries:
        props["Finding Summaries"] = {
            "rich_text": [{"plain_text": "\n".join(summaries)}]
        }
    return {
        "id": row_id,
        "created_time": created_at.isoformat().replace("+00:00", "Z"),
        "properties": props,
        "archived": False,
        "in_trash": False,
    }


class _SenderRecorder:
    """Capture calls to email_sender / upsell_sender."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)


# Reachable resolvable host that satisfies validate_url's RFC1918 gate.
TEST_URL = "https://example.com"
TEST_EMAIL = "sarah@example.com"
OTHER_EMAIL = "alice@example.com"


# ---------------------------------------------------------------------------
# Case 1: fresh submission -> queues normally
# ---------------------------------------------------------------------------


class FreshSubmissionCase(unittest.TestCase):
    def test_no_prior_row_queues_and_sends_confirmation(self) -> None:
        now = datetime(2026, 5, 26, 14, 0, tzinfo=UTC)
        client = FakeNotionClient(rows=[], now=now)
        confirm = _SenderRecorder()
        upsell = _SenderRecorder()

        status, body = free_audit.process_request(
            payload={"url": TEST_URL, "email": TEST_EMAIL},
            ip="203.0.113.10",
            source="index",
            now=now,
            notion_client_factory=lambda: client,
            email_sender=confirm,
            upsell_sender=upsell,
        )

        self.assertEqual(status, 200, msg=f"unexpected body: {body!r}")
        self.assertEqual(body["status"], "queued")
        self.assertEqual(len(client.created), 1, "fresh submission should write 1 row")
        self.assertEqual(len(confirm.calls), 1, "confirmation email must fire")
        self.assertEqual(confirm.calls[0]["to"], TEST_EMAIL)
        self.assertEqual(len(upsell.calls), 0, "upsell email must NOT fire on fresh")


# ---------------------------------------------------------------------------
# Case 2: repeat within 30 days -> upsell, no new row
# ---------------------------------------------------------------------------


class RepeatWithin30DaysCase(unittest.TestCase):
    def test_same_email_same_host_within_window_returns_upsell(self) -> None:
        now = datetime(2026, 5, 26, 14, 0, tzinfo=UTC)
        prior = _make_row(
            row_id="row-prior",
            email=TEST_EMAIL,
            url=TEST_URL,
            created_at=now - timedelta(days=10),
            status="delivered",
            fingerprints=["abc123", "def456", "ghi789"],
            summaries=["Privacy 404", "Dev bypass", "CTA hidden"],
        )
        client = FakeNotionClient(rows=[prior], now=now)
        confirm = _SenderRecorder()
        upsell = _SenderRecorder()

        status, body = free_audit.process_request(
            payload={"url": TEST_URL, "email": TEST_EMAIL},
            ip="203.0.113.10",
            source="index",
            now=now,
            notion_client_factory=lambda: client,
            email_sender=confirm,
            upsell_sender=upsell,
        )

        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "duplicate")
        self.assertEqual(len(client.created), 0, "must NOT write a second row")
        self.assertEqual(len(confirm.calls), 0, "confirmation must NOT fire on repeat")
        self.assertEqual(len(upsell.calls), 1, "upsell email must fire on repeat")

        upsell_kwargs = upsell.calls[0]
        self.assertEqual(upsell_kwargs["to"], TEST_EMAIL)
        # The available_again date is the prior submission + 30 days.
        self.assertEqual(
            upsell_kwargs["available_again_at"].date(),
            (now - timedelta(days=10) + timedelta(days=30)).date(),
        )

        # Customer-visible JSON copy carries the upsell paragraph.
        self.assertIn("Starter ($19)", body["message"])
        self.assertIn(free_audit.STARTER_URL, body["message"])
        self.assertIn("30 days", body["message"])
        # SIMPLICITY-GUARDRAILS section 6: no em-dashes anywhere
        # in the customer-facing copy.
        self.assertNotIn("\u2014", body["message"])
        self.assertIn("upsell", body)
        self.assertEqual(body["upsell"]["starter_url"], free_audit.STARTER_URL)


# ---------------------------------------------------------------------------
# Case 3: repeat AFTER 30 days -> delivers normally (mocked datetime)
# ---------------------------------------------------------------------------


class RepeatAfter30DaysCase(unittest.TestCase):
    def test_same_email_same_host_after_window_delivers_fresh(self) -> None:
        now = datetime(2026, 5, 26, 14, 0, tzinfo=UTC)
        prior = _make_row(
            row_id="row-prior",
            email=TEST_EMAIL,
            url=TEST_URL,
            created_at=now - timedelta(days=45),  # well past the 30-day window
            status="delivered",
        )
        client = FakeNotionClient(rows=[prior], now=now)
        confirm = _SenderRecorder()
        upsell = _SenderRecorder()

        status, body = free_audit.process_request(
            payload={"url": TEST_URL, "email": TEST_EMAIL},
            ip="203.0.113.99",
            source="index",
            now=now,
            notion_client_factory=lambda: client,
            email_sender=confirm,
            upsell_sender=upsell,
        )

        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "queued")
        self.assertEqual(len(client.created), 1, "expired prior -> new row written")
        self.assertEqual(len(confirm.calls), 1, "confirmation fires for fresh path")
        self.assertEqual(len(upsell.calls), 0)


# ---------------------------------------------------------------------------
# Case 4: same URL, different email -> different person, fresh delivery
# ---------------------------------------------------------------------------


class DifferentEmailSameUrlCase(unittest.TestCase):
    def test_different_email_same_host_delivers_fresh(self) -> None:
        now = datetime(2026, 5, 26, 14, 0, tzinfo=UTC)
        prior = _make_row(
            row_id="row-prior",
            email=OTHER_EMAIL,
            url=TEST_URL,
            created_at=now - timedelta(days=5),
            status="queued",
        )
        client = FakeNotionClient(rows=[prior], now=now)
        confirm = _SenderRecorder()
        upsell = _SenderRecorder()

        status, body = free_audit.process_request(
            payload={"url": TEST_URL, "email": TEST_EMAIL},
            ip="203.0.113.42",
            source="index",
            now=now,
            notion_client_factory=lambda: client,
            email_sender=confirm,
            upsell_sender=upsell,
        )

        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "queued")
        self.assertEqual(
            len(client.created), 1, "different person -> writes its own row"
        )
        self.assertEqual(len(confirm.calls), 1)
        self.assertEqual(len(upsell.calls), 0)


# ---------------------------------------------------------------------------
# Case 5: storage round-trip
# ---------------------------------------------------------------------------


class StorageRoundTripCase(unittest.TestCase):
    def test_write_then_recent_delivery_finds_it(self) -> None:
        now = datetime(2026, 5, 26, 14, 0, tzinfo=UTC)
        client = FakeNotionClient(rows=[], now=now)
        confirm = _SenderRecorder()
        upsell = _SenderRecorder()

        # 1. First submission writes the row.
        status, body = free_audit.process_request(
            payload={"url": TEST_URL, "email": TEST_EMAIL},
            ip="203.0.113.10",
            source="index",
            now=now,
            notion_client_factory=lambda: client,
            email_sender=confirm,
            upsell_sender=upsell,
        )
        self.assertEqual(body["status"], "queued")
        self.assertEqual(len(client.rows), 1)

        # 2. ``recent_delivery`` against the same stub client now reports
        #    the prior row, in the same shape api/free-audit.py expects.
        record = free_audit_lookup.recent_delivery(
            url=TEST_URL,
            email=TEST_EMAIL,
            days=30,
            client=client,
            ds_id="ds-test",
            now=now + timedelta(minutes=1),
        )
        self.assertIsNotNone(record)
        assert record is not None  # narrowing for type-checker
        self.assertEqual(record["url"], TEST_URL)
        self.assertEqual(record["status"], "queued")
        self.assertIsNotNone(record["created_at"])
        self.assertIsNotNone(record["expires_at"])
        self.assertEqual(
            record["expires_at"] - record["created_at"], timedelta(days=30)
        )

        # 3. A second submission within the window now flips to upsell.
        status2, body2 = free_audit.process_request(
            payload={"url": TEST_URL, "email": TEST_EMAIL},
            ip="203.0.113.10",
            source="index",
            now=now + timedelta(days=1),
            notion_client_factory=lambda: client,
            email_sender=confirm,
            upsell_sender=upsell,
        )
        self.assertEqual(status2, 200)
        self.assertEqual(body2["status"], "duplicate")
        self.assertEqual(len(client.created), 1, "still only one row written")
        self.assertEqual(len(upsell.calls), 1, "upsell fires on the second visit")


# ---------------------------------------------------------------------------
# Stdlib-only runner
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main(verbosity=2)
