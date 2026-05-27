"""Tests for ``scripts/share_report.py`` and the deliver-time
``_generate_shareable_page`` helper.

Together these tests are the q22 acceptance gate:

* Public/private toggle works (and is idempotent).
* ``is_public: false`` causes ``/r/{slug}`` to show the gentle private
  message (verified by inspecting the JSON the page reads).
* OG / Twitter meta tags are baked into the per-customer HTML at
  delivery time.
* The generated HTML and JSON contain no PII from the source YAML.
* Each example customer YAML produces a matching pair of files at
  ``landing/r/{slug}.html`` + ``landing/data/reports/{slug}.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import share_report  # noqa: E402
from scripts.deliver_report import (  # noqa: E402
    _build_share_metadata,
    _generate_shareable_page,
    load_customer_yaml,
    slugify,
    validate,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_reports_dir(tmp_path, monkeypatch):
    """Redirect SHAREABLE_REPORTS_DATA_DIR + SHAREABLE_PAGES_DIR to a tmp dir.

    Prevents tests from clobbering the committed example JSON files.
    """
    reports = tmp_path / "data" / "reports"
    pages = tmp_path / "r"
    reports.mkdir(parents=True)
    pages.mkdir(parents=True)
    monkeypatch.setattr("scripts.deliver_report.SHAREABLE_REPORTS_DATA_DIR", reports)
    monkeypatch.setattr("scripts.deliver_report.SHAREABLE_PAGES_DIR", pages)
    monkeypatch.setattr(share_report, "REPORTS_DIR", reports)
    monkeypatch.setattr(share_report, "SHAREABLE_PAGES_DIR", pages)
    return reports, pages


@pytest.fixture
def jane_yaml() -> Path:
    return REPO_ROOT / "customers" / "example-jane-sparkle.yaml"


@pytest.fixture
def webflow_yaml() -> Path:
    return REPO_ROOT / "customers" / "example-webflow.yaml"


@pytest.fixture
def pro_yaml() -> Path:
    return REPO_ROOT / "customers" / "example-pro-package.yaml"


def _gen_shareable(yaml_path: Path, slug: str | None = None, has_handoff: bool = False):
    data = load_customer_yaml(yaml_path)
    validate(data)
    c = data["customer"]
    if slug is None:
        slug = slugify(c.get("first_name", ""), c.get("app_name", ""))
    return _generate_shareable_page(
        data,
        slug=slug,
        delivered_at="2026-05-26",
        has_handoff=has_handoff,
    )


# ---------------------------------------------------------------------------
# Default-private + toggle round trip
# ---------------------------------------------------------------------------


def test_shareable_page_defaults_to_private(tmp_reports_dir, jane_yaml):
    reports, pages = tmp_reports_dir
    json_path, html_path = _gen_shareable(jane_yaml)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["is_public"] is False
    # The gentle "private" message lives on the static HTML and is
    # toggled visible by /assets/r.js. We confirm the marker text is
    # present in the HTML so OG scrapers and JS-less visitors both see
    # it.
    html = html_path.read_text(encoding="utf-8")
    assert "This report is private" in html


def test_set_public_then_private_round_trip(tmp_reports_dir, jane_yaml):
    reports, _pages = tmp_reports_dir
    json_path, _ = _gen_shareable(jane_yaml)
    slug = json_path.stem

    rc = share_report.main(["--slug", slug, "--public", "--no-commit"])
    assert rc == 0
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["is_public"] is True
    assert any(h["event"] == "set_public" for h in data["share_history"])

    rc = share_report.main(["--slug", slug, "--private", "--no-commit"])
    assert rc == 0
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["is_public"] is False
    history_events = [h["event"] for h in data["share_history"]]
    assert history_events == ["set_public", "set_private"]


def test_status_does_not_modify_state(tmp_reports_dir, jane_yaml, capsys):
    _gen_shareable(jane_yaml)
    slug = "jane-sparkle-marketplace"
    rc = share_report.main(["--slug", slug, "--status"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "Public:            no" in captured.out
    data = json.loads((tmp_reports_dir[0] / f"{slug}.json").read_text(encoding="utf-8"))
    assert data["is_public"] is False
    assert "share_history" not in data


def test_set_public_is_idempotent(tmp_reports_dir, jane_yaml):
    _gen_shareable(jane_yaml)
    slug = "jane-sparkle-marketplace"
    share_report.main(["--slug", slug, "--public", "--no-commit"])
    share_report.main(["--slug", slug, "--public", "--no-commit"])
    data = json.loads((tmp_reports_dir[0] / f"{slug}.json").read_text(encoding="utf-8"))
    n_public = sum(1 for h in data["share_history"] if h["event"] == "set_public")
    assert n_public == 1


# ---------------------------------------------------------------------------
# Handoff toggle (Pro only)
# ---------------------------------------------------------------------------


def test_handoff_share_requires_pro_eligibility(tmp_reports_dir, jane_yaml):
    _gen_shareable(jane_yaml, has_handoff=False)
    with pytest.raises(SystemExit):
        share_report.main(
            ["--slug", "jane-sparkle-marketplace", "--share-handoff", "--no-commit"]
        )


def test_handoff_share_round_trip_for_pro(tmp_reports_dir, pro_yaml):
    json_path, _ = _gen_shareable(pro_yaml, has_handoff=True)
    slug = json_path.stem
    share_report.main(["--slug", slug, "--public", "--no-commit"])
    share_report.main(["--slug", slug, "--share-handoff", "--no-commit"])
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["handoff_report"]["available"] is True
    assert data["handoff_report"]["shared"] is True

    share_report.main(["--slug", slug, "--hide-handoff", "--no-commit"])
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["handoff_report"]["shared"] is False


# ---------------------------------------------------------------------------
# Sanitization on the publish path
# ---------------------------------------------------------------------------


def test_generated_json_has_no_customer_url(tmp_reports_dir, jane_yaml):
    json_path, _ = _gen_shareable(jane_yaml)
    text = json_path.read_text(encoding="utf-8")
    assert "sparkle.lovable.app" not in text
    assert "jane@example.com" not in text


def test_generated_html_has_no_customer_url(tmp_reports_dir, jane_yaml):
    _, html_path = _gen_shareable(jane_yaml)
    text = html_path.read_text(encoding="utf-8")
    assert "sparkle.lovable.app" not in text
    assert "jane@example.com" not in text


def test_findings_use_generic_paths(tmp_reports_dir, jane_yaml):
    json_path, _ = _gen_shareable(jane_yaml)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    blob = json.dumps(data)
    # The raw YAML talks about /auth, /privacy, /terms. The public copy
    # should translate them all into generic phrases.
    assert "/auth" not in blob
    assert "/privacy" not in blob
    assert "/terms" not in blob


# ---------------------------------------------------------------------------
# OG / Twitter Card meta tags
# ---------------------------------------------------------------------------


def test_share_metadata_is_plain_english_and_punchy():
    metadata = _build_share_metadata(
        {"app_name": "Sparkle Marketplace"},
        {"label": "Needs fixes before launch"},
        n_findings=7,
        audit_date="2026-05-26",
    )
    assert metadata["title"] == "LaunchLook audit for Sparkle Marketplace"
    assert "Needs fixes before launch" in metadata["description"]
    assert "7 findings" in metadata["description"]
    assert metadata["og_image"].startswith("https://")


def test_generated_html_bakes_in_og_tags(tmp_reports_dir, jane_yaml):
    _, html_path = _gen_shareable(jane_yaml)
    html = html_path.read_text(encoding="utf-8")
    for needed in (
        '<meta property="og:title"',
        '<meta property="og:description"',
        '<meta property="og:image"',
        '<meta property="og:url"',
        '<meta name="twitter:card"',
        '<meta name="twitter:title"',
        '<meta name="twitter:description"',
        '<meta name="twitter:image"',
    ):
        assert needed in html, f"missing {needed!r} in shareable HTML"
    # And the OG URL points back at /r/{slug}
    assert (
        '<meta property="og:url" content="https://launchlook.app/r/'
        "jane-sparkle-marketplace"
        '" />'
    ) in html


def test_generated_html_does_not_load_plausible(tmp_reports_dir, jane_yaml):
    # Plausible script tag was pulled in the May 2026 simplification pass
    # (account creation deferred). The plausible-event-name=... CSS classes
    # on CTAs are intentionally preserved so re-enabling is one line.
    _, html_path = _gen_shareable(jane_yaml)
    html = html_path.read_text(encoding="utf-8")
    assert "plausible.io/js/script" not in html


# ---------------------------------------------------------------------------
# Each example customer yields a matching pair of files
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "yaml_name,expected_slug",
    [
        ("example-jane-sparkle.yaml", "jane-sparkle-marketplace"),
        ("example-webflow.yaml", "alex-bauer-studio"),
        ("example-pro-package.yaml", "mira-tessera-boards"),
    ],
)
def test_each_example_generates_matching_files(
    tmp_reports_dir, yaml_name, expected_slug
):
    yaml_path = REPO_ROOT / "customers" / yaml_name
    json_path, html_path = _gen_shareable(yaml_path)
    assert json_path.name == f"{expected_slug}.json"
    assert html_path.name == f"{expected_slug}.html"
    assert json_path.exists()
    assert html_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["customer_slug"] == expected_slug


# ---------------------------------------------------------------------------
# Re-rendering preserves public state (no quiet flips)
# ---------------------------------------------------------------------------


def test_redelivery_preserves_public_state(tmp_reports_dir, jane_yaml):
    json_path, _ = _gen_shareable(jane_yaml)
    slug = json_path.stem
    share_report.main(["--slug", slug, "--public", "--no-commit"])

    # Re-run delivery (e.g. Rob fixed a typo and re-rendered the report).
    _gen_shareable(jane_yaml)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["is_public"] is True, (
        "Re-running deliver_report.py must not silently flip a live "
        "public report back to private."
    )


# ---------------------------------------------------------------------------
# Slug not found
# ---------------------------------------------------------------------------


def test_share_report_unknown_slug_exits_cleanly(tmp_reports_dir):
    with pytest.raises(SystemExit):
        share_report.main(["--slug", "ghost-slug", "--public", "--no-commit"])


# ---------------------------------------------------------------------------
# --no-commit flag suppresses the auto-commit, default still commits
# ---------------------------------------------------------------------------


def test_no_commit_flag_suppresses_git_commit(tmp_reports_dir, jane_yaml, monkeypatch):
    """--no-commit must skip the git_commit() call entirely.

    The default behavior auto-commits after writing the JSON (production
    use case). For smoke-tests and notebook piloting we need an opt-out
    that leaves the working tree dirty without touching git.
    """
    _gen_shareable(jane_yaml)
    calls: list[tuple] = []

    def _spy_git_commit(paths, message):
        calls.append((tuple(paths), message))

    monkeypatch.setattr(share_report, "git_commit", _spy_git_commit)

    rc = share_report.main(
        ["--slug", "jane-sparkle-marketplace", "--public", "--no-commit"]
    )
    assert rc == 0
    assert (
        calls == []
    ), f"--no-commit must skip git_commit(), but it was called: {calls!r}"


def test_default_behavior_still_commits(tmp_reports_dir, jane_yaml, monkeypatch):
    """Without --no-commit, the script must still call git_commit().

    Default behavior is unchanged from production (auto-commit on toggle).
    """
    _gen_shareable(jane_yaml)
    calls: list[tuple] = []

    def _spy_git_commit(paths, message):
        calls.append((tuple(paths), message))

    monkeypatch.setattr(share_report, "git_commit", _spy_git_commit)

    rc = share_report.main(["--slug", "jane-sparkle-marketplace", "--public"])
    assert rc == 0
    assert (
        len(calls) == 1
    ), f"default behavior must call git_commit() once, got: {calls!r}"
    _, message = calls[0]
    assert "public" in message.lower()
