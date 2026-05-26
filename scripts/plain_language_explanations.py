"""One-off helper: refresh customer explanations in findings.json for non-technical readers."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "findings_library" / "findings.json"

PLAIN: dict[str, str] = {
    "FL-015": (
        "When the page loads, something in the background is failing "
        "(the browser reports {N} hidden errors). Features may not work reliably."
    ),
    "FL-016": (
        "When the page loads, some pieces of the app fail to load in the background: "
        "{REQUEST_LIST}. Anything that depends on those pieces may be broken."
    ),
    "FL-020": (
        "People who are not signed in can still open pages that should be private, "
        "such as {PROTECTED_ROUTES}. They may see information they should not."
    ),
    "FL-021": (
        "Someone signed in as one user could see another person's information — "
        "for example: {EXAMPLE}. New signups might see other people's data."
    ),
    "FL-022": (
        "New users sign up but never get the confirmation email, "
        "so they cannot finish creating an account."
    ),
    "FL-023": (
        "When you paste your link into Slack, Twitter, or iMessage, the preview still "
        "shows generic builder text — not a real description of your app."
    ),
    "FL-024": (
        "The small icon in the browser tab is still the default. "
        "Your app should have its own so people recognize the tab."
    ),
    "FL-025": ("Browser tabs show a generic title instead of your app name."),
    "FL-030": (
        "The first time someone signs in, the main screen is empty "
        "with no hint about what to do next."
    ),
    "FL-031": (
        "While content is loading, the screen stays blank — people may think the app froze."
    ),
    "FL-032": (
        "If someone types a wrong web address, they get a generic error "
        'instead of a friendly "page not found" screen with a way home.'
    ),
    "FL-033": (
        "The app calls the same type of person different names "
        "(e.g. customer, client, user). That feels confusing."
    ),
    "FL-008": (
        "There is no privacy policy page. People expect one before they sign up or pay."
    ),
    "FL-009": (
        "There is no Terms of Service page. Users have nothing clear to agree to."
    ),
    "FL-017": (
        "On a phone, the page scrolls sideways — something is wider than the screen."
    ),
    "FL-018": (
        "Text on mobile is hard to read (about {SIZE}px). "
        "Most apps use at least 16px on phones."
    ),
    "FL-019": ("Some buttons on mobile are too small to tap comfortably."),
}


def main() -> None:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    n = 0
    for f in data["findings"]:
        if f["id"] in PLAIN:
            f["explanation"] = PLAIN[f["id"]]
            n += 1
    PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Updated {n} explanations in {PATH}")


if __name__ == "__main__":
    main()
