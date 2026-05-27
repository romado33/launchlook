"""
audit_checklist.py — print the 20-minute manual audit workflow.

Usage:
    python scripts/audit_checklist.py
    python scripts/audit_checklist.py --tier launch
"""

from __future__ import annotations

import argparse

STEPS_QUICK = """
LaunchLook — 20-minute Starter workflow
==========================================

0. Prep (2 min)
   - Duplicate templates/notion/report-quick-checkup.md in Notion
   - Open findings_library/findings.json or: python scripts/findings_lookup.py <keyword>
   - Open the app in Chrome (not Lovable preview)

1. Desktop pass (5 min)
   - Screenshot homepage
   - Click every visible button — note dead ends
   - Visit /privacy, /terms, /contact — note 404s
   - DevTools → Console — note errors
   - Visible text scan: lorem, TODO, "Your Company Name", "Local Host", dev tools

2. Mobile pass (5 min)
   - DevTools → iPhone SE (375px), reload, screenshot
   - Horizontal scroll? Text under 16px? Tiny tap targets?

3. Signup pass (5 min) — skip if no auth
   - Sign up with test email
   - Confirmation email arrives?
   - Dashboard empty state? Nav works?

4. Logged-out probe (2 min)
   - Incognito → /dashboard, /admin, /settings — should redirect, not show data

5. Write-up (5–7 min)
   - 5–7 findings, severity order
   - Substitute {ACTUAL_NAME}, {PAGE}, {BUTTON_NAME} in fix prompts
   - Verdict: Ready / Needs fixes / Don't ship

After audit:
   - New pattern? Add row to Findings Library + findings.json
   - Note crawler ideas in templates/notion/crawler-wishlist.md
"""

STEPS_LAUNCH = (
    STEPS_QUICK
    + """
Launch Pack additions (+15 min):
   - Two test accounts: User A vs User B cross-data check
   - python scripts/qsg_compose_prompt.py ... > output/<customer>/qsg_prompt.txt
   - Paste into ChatGPT, edit, paste into report Part 2
   - python scripts/qsg_render.py --input ... --output ...html
"""
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tier",
        choices=["starter", "launch", "quick"],
        default="starter",
        help="'quick' is an alias for starter",
    )
    args = parser.parse_args()
    tier = "starter" if args.tier == "quick" else args.tier

    if tier == "starter":
        print(STEPS_QUICK.strip())
    else:
        print(STEPS_LAUNCH.strip())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
