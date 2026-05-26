"""Tests for scripts/ai_audit/dedup.py.

Covers the three cases the task spec calls out:
    1. No prior fingerprints -> nothing is filtered, render_exclude_block
       returns empty so the LLM prompt stays clean.
    2. Some collisions -> only the colliding findings get filtered out,
       the rest pass through, and the exclude block lists the hashes.
    3. All collisions -> every new finding is filtered out so the caller
       knows to re-prompt (the pipeline turns this into a warning).

Also exercises the stability guarantees we rely on (wording drift,
trailing-slash path canonicalization, missing-field defaults).

Runnable two ways:
    * `pytest tests/test_dedup.py` if pytest is installed (it usually is
      via requirements-ai.txt).
    * `python tests/test_dedup.py` for a stdlib-only run (no pytest).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ai_audit import dedup  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _free_findings() -> list[dict]:
    """The 3 free findings as the offline pipeline would persist them."""
    return [
        {
            "category_id": "trust_gaps",
            "title": "Your /privacy link goes to a 404.",
            "what_we_saw": "The footer privacy link returns a 404 on launch.",
            "path": "/",
        },
        {
            "category_id": "dev_artifacts",
            "title": "A Dev Bypass button is visible on /auth.",
            "what_we_saw": "The /auth route still renders the Dev Bypass control to anonymous visitors.",
            "path": "/auth",
        },
        {
            "category_id": "mobile_layout",
            "title": "Sign up CTA on /pricing is below a sticky banner.",
            "what_we_saw": "On a 375px viewport the primary CTA on /pricing is overlapped by a sticky banner.",
            "path": "/pricing",
        },
    ]


def _starter_candidate_findings() -> list[dict]:
    """10 candidate Starter findings the LLM might propose post-upgrade."""
    return [
        # 1. Equivalent to free finding #1 (privacy 404) with different wording.
        {
            "category_id": "trust_gaps",
            "title": "Your privacy policy link returns a 404",
            "what_we_saw": "The footer privacy link returns a 404 on launch.",
            "path": "/",
        },
        # 2. Equivalent to free finding #2 (dev bypass on /auth).
        {
            "category_id": "dev_artifacts",
            "title": "Dev bypass still on /auth",
            "what_we_saw": "The /auth route still renders the Dev Bypass control to anonymous visitors.",
            "path": "/auth",
        },
        # 3. Genuinely new: terms 404 at /terms.
        {
            "category_id": "trust_gaps",
            "title": "Terms link returns a 404",
            "what_we_saw": "The footer terms link also returns a 404 on launch.",
            "path": "/",
        },
        # 4. Genuinely new: dev artifacts on /admin (different path).
        {
            "category_id": "dev_artifacts",
            "title": "Public /admin route loads without auth",
            "what_we_saw": "The /admin route renders the seed-data control to anonymous visitors.",
            "path": "/admin",
        },
        # 5. Equivalent to free finding #3 with slightly different wording.
        {
            "category_id": "mobile_layout",
            "title": "Pricing page CTA hidden by mobile banner",
            "what_we_saw": "On a 375px viewport the primary CTA on /pricing is overlapped by a sticky banner.",
            "path": "/pricing",
        },
        # 6. Brand new: copy_clarity issue.
        {
            "category_id": "copy_clarity",
            "title": "Hero copy still says Lorem ipsum",
            "what_we_saw": "The hero headline on / is the placeholder Lorem ipsum dolor sit amet.",
            "path": "/",
        },
        # 7-10 to round out the cap; doesn't matter for assertions.
        {"category_id": "trust_gaps", "title": "Support email is support@example.com", "what_we_saw": "fake email", "path": "/"},
        {"category_id": "mobile_layout", "title": "Hamburger nav off-screen at 320px", "what_we_saw": "off-screen nav", "path": "/"},
        {"category_id": "broken_ctas_links", "title": "Quick Book button does nothing", "what_we_saw": "dead button", "path": "/"},
        {"category_id": "broken_ctas_links", "title": "Footer GitHub link 404s", "what_we_saw": "dead link", "path": "/"},
    ]


# ---------------------------------------------------------------------------
# Case 1: no prior fingerprints -> nothing filtered
# ---------------------------------------------------------------------------


class NoPriorFingerprintsCase(unittest.TestCase):
    def test_filter_passes_everything_through(self) -> None:
        candidates = _starter_candidate_findings()
        kept = dedup.filter_out_collisions(candidates, [])
        self.assertEqual(len(kept), len(candidates))
        self.assertEqual(kept, candidates)

    def test_collisions_returns_empty(self) -> None:
        self.assertEqual(dedup.collisions(_starter_candidate_findings(), []), [])

    def test_render_exclude_block_is_empty(self) -> None:
        self.assertEqual(dedup.render_exclude_block([]), "")
        self.assertEqual(dedup.render_exclude_block(None), "")


# ---------------------------------------------------------------------------
# Case 2: some collisions -> only equivalent findings filtered, rest pass
# ---------------------------------------------------------------------------


class PartialCollisionsCase(unittest.TestCase):
    def setUp(self) -> None:
        self.free = _free_findings()
        self.candidates = _starter_candidate_findings()
        self.excluded = dedup.fingerprints(self.free)

    def test_three_excluded_hashes(self) -> None:
        # Sanity: 3 free findings produce 3 distinct fingerprints.
        self.assertEqual(len(self.excluded), 3)
        self.assertEqual(len(set(self.excluded)), 3)

    def test_collisions_identifies_the_three_overlapping(self) -> None:
        clashes = dedup.collisions(self.candidates, self.excluded)
        # Candidates #1, #2, #5 (index 0, 1, 4) should be flagged.
        titles = sorted(c["title"] for c in clashes)
        self.assertEqual(
            titles,
            sorted([
                "Your privacy policy link returns a 404",
                "Dev bypass still on /auth",
                "Pricing page CTA hidden by mobile banner",
            ]),
        )

    def test_filter_drops_only_the_overlapping(self) -> None:
        kept = dedup.filter_out_collisions(self.candidates, self.excluded)
        self.assertEqual(len(kept), len(self.candidates) - 3)
        # None of the kept findings should fingerprint into the excluded set.
        kept_fps = set(dedup.fingerprints(kept))
        self.assertTrue(kept_fps.isdisjoint(set(self.excluded)))

    def test_render_exclude_block_lists_each_hash(self) -> None:
        block = dedup.render_exclude_block(self.excluded)
        self.assertIn("EXCLUDE_FINGERPRINTS", block)
        for fp in self.excluded:
            self.assertIn(fp, block)

    def test_render_exclude_block_includes_summaries_when_provided(self) -> None:
        block = dedup.render_exclude_block(
            self.excluded,
            prior_summaries=[f["title"] for f in self.free],
        )
        self.assertIn("Plain-English summary", block)
        for f in self.free:
            self.assertIn(f["title"], block)


# ---------------------------------------------------------------------------
# Case 3: all collisions -> caller learns nothing survived
# ---------------------------------------------------------------------------


class AllCollisionsCase(unittest.TestCase):
    def test_starter_candidates_all_equal_free_returns_nothing(self) -> None:
        free = _free_findings()
        # Simulate the LLM totally ignoring the exclude block: it returns
        # paraphrased copies of every free finding and nothing else.
        echoes = [
            {
                "category_id": f["category_id"],
                "title": "Slight rewording of " + f["title"],
                "what_we_saw": f["what_we_saw"],
                "path": f["path"],
            }
            for f in free
        ]
        excluded = dedup.fingerprints(free)
        clashes = dedup.collisions(echoes, excluded)
        self.assertEqual(len(clashes), len(echoes))
        self.assertEqual(dedup.filter_out_collisions(echoes, excluded), [])


# ---------------------------------------------------------------------------
# Stability + edge cases
# ---------------------------------------------------------------------------


class StabilityCase(unittest.TestCase):
    def test_trailing_slash_canonicalization(self) -> None:
        a = {"category_id": "trust_gaps", "what_we_saw": "missing privacy page", "path": "/legal/"}
        b = {"category_id": "trust_gaps", "what_we_saw": "missing privacy page", "path": "/legal"}
        self.assertEqual(dedup.fingerprint(a), dedup.fingerprint(b))

    def test_full_url_collapses_to_path(self) -> None:
        a = {"category_id": "trust_gaps", "what_we_saw": "x", "url": "https://ex.com/pricing"}
        b = {"category_id": "trust_gaps", "what_we_saw": "x", "path": "/pricing"}
        self.assertEqual(dedup.fingerprint(a), dedup.fingerprint(b))

    def test_punctuation_and_case_drift_does_not_break_collision(self) -> None:
        a = {"category_id": "copy_clarity", "what_we_saw": "Lorem ipsum dolor sit amet.", "path": "/"}
        b = {"category_id": "copy_clarity", "what_we_saw": "lorem ipsum, dolor sit amet!", "path": "/"}
        self.assertEqual(dedup.fingerprint(a), dedup.fingerprint(b))

    def test_different_path_keeps_them_distinct(self) -> None:
        a = {"category_id": "mobile_layout", "what_we_saw": "cta hidden", "path": "/"}
        b = {"category_id": "mobile_layout", "what_we_saw": "cta hidden", "path": "/pricing"}
        self.assertNotEqual(dedup.fingerprint(a), dedup.fingerprint(b))

    def test_missing_fields_still_produces_hash(self) -> None:
        # Empty / missing fields should produce a deterministic value rather than crash.
        fp = dedup.fingerprint({})
        self.assertIsInstance(fp, str)
        self.assertEqual(len(fp), 16)

    def test_non_dict_findings_are_skipped(self) -> None:
        out = dedup.fingerprints([{"category_id": "trust_gaps", "what_we_saw": "x", "path": "/"}, None, "skip me"])
        self.assertEqual(len(out), 1)


# ---------------------------------------------------------------------------
# Stdlib-only runner
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main(verbosity=2)
