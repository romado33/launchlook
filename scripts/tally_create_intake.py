"""
tally_create_intake.py — create the LaunchLook post-purchase intake form via Tally API.

Reads TALLY_API_KEY from .env (gitignored). Builds the full form structure
declared in INTAKE_FORM below and POSTs it to Tally. Returns the new form's
public URL.

Usage:
    python scripts/tally_create_intake.py                       # creates as DRAFT (safe, must publish in Tally UI)
    python scripts/tally_create_intake.py --publish             # creates as PUBLISHED immediately
    python scripts/tally_create_intake.py --dry-run             # prints the JSON payload without calling the API
    python scripts/tally_create_intake.py --replace <FORM_ID>   # DELETE the given form, then create a fresh one (DRAFT by default)

Question structure:
    Each question is rendered as ONE title block plus the input (or option) blocks.
    The optional ``description`` is inlined into the TITLE HTML as a smaller
    second line — Tally's logic dropdown surfaces the TITLE text as the
    question identifier, so this keeps logic readable instead of showing
    a separate LABEL block's helper text.

Notes:
    * The Tally API does not currently expose conditional logic via API.
      Set the three visibility rules (Q9 only when Q8 = Scale Up Package or
      Pro Package; Q10/Q11 only when Q9 = "Yes — I'll provide two test
      accounts") manually in the Tally editor after creation.
    * Notification email (hello@launchlook.app) and the "after submit"
      redirect to https://tally.so/r/Y5xO5J also need to be set in the
      Tally UI (Settings → Notifications and Settings → After submit).

See: https://developers.tally.so/api-reference/endpoint/forms/post
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent
RESPONSE_DIR = REPO_ROOT / "output" / "tally"
RESPONSE_PATH = RESPONSE_DIR / "intake-create-response.json"

TALLY_API_URL = "https://api.tally.so/forms"


# ---------------------------------------------------------------------------
# Form structure — edit this dict to change the intake form.
# ---------------------------------------------------------------------------

INTAKE_FORM = {
    "title": "LaunchLook — Post-purchase intake",
    "intro": (
        "Please read before submitting.\n\n"
        "• Only submit temporary test accounts. Do not submit personal "
        "passwords, admin credentials, API keys, database credentials, real "
        "customer data, health data, children's data, or payment information.\n\n"
        "• For Scale Up ($49) and Pro ($99) only: create temporary test accounts (not "
        "real users). Submit credentials here only — not by email.\n\n"
        "• We delete test credentials within 24 hours of delivery. Rotate or "
        "delete test accounts after your report arrives."
    ),
    "questions": [
        # Q1 — name
        {
            "key": "name",
            "title": "What's your name?",
            "description": "First name is fine.",
            "type": "INPUT_TEXT",
            "required": True,
            "placeholder": "Alex",
        },
        # Q2 — email
        {
            "key": "email",
            "title": "Email",
            "description": "Match the email you used at checkout if you can — makes things easier.",
            "type": "INPUT_EMAIL",
            "required": True,
            "placeholder": "you@example.com",
        },
        # Q3 — app URL
        {
            "key": "app_url",
            "title": "App URL",
            "description": "The live URL. Staging URLs work too if they're publicly reachable.",
            "type": "INPUT_LINK",
            "required": True,
            "placeholder": "https://your-app.example.com",
        },
        # Q4 — what does your app do
        {
            "key": "app_description",
            "title": "What does your app do?",
            "description": "One sentence. Plain language. Example: A shared to-do list for small teams.",
            "type": "INPUT_TEXT",
            "required": True,
            "placeholder": "A shared to-do list for small teams.",
        },
        # Q5 — main user
        {
            "key": "main_user",
            "title": "Who's your main user?",
            "description": "1–2 sentences. Who's going to use this? What do they do?",
            "type": "TEXTAREA",
            "required": True,
            "placeholder": "Small business owners and team leads.",
        },
        # Q6 — main workflow
        {
            "key": "main_workflow",
            "title": "What's the main thing they do in your app?",
            "description": "The one thing your app is for. The main workflow.",
            "type": "TEXTAREA",
            "required": True,
            "placeholder": "Create a task, assign it, mark it done.",
        },
        # Q7 — platform
        {
            "key": "platform",
            "title": "Which platform built it?",
            "description": None,
            "type": "MULTIPLE_CHOICE",
            "required": True,
            "options": ["Lovable", "Bolt", "Base44", "Replit", "v0", "Cursor", "Other"],
        },
        # Q8 — tier
        {
            "key": "tier",
            "title": "Which tier did you purchase?",
            "description": "We'll match against Stripe — this confirms what you expect.",
            "type": "MULTIPLE_CHOICE",
            "required": True,
            "options": [
                "Starter Package ($19)",
                "Scale Up Package ($49)",
                "Pro Package ($99)",
            ],
        },
        # Q9 — test accounts? (Scale Up + Pro only — set conditional in Tally UI)
        {
            "key": "test_accounts_choice",
            "title": "Can we use test accounts?",
            "description": (
                "Scale Up and Pro only. The user-data isolation check needs two "
                "signed-in sessions. We can sign up fresh test accounts ourselves "
                "if you prefer — we delete them after the audit."
            ),
            "type": "MULTIPLE_CHOICE",
            "required": False,
            "options": [
                "Yes — I'll provide two test accounts",
                "I'll create test accounts using my own signup flow — you provision them",
                "No — skip the cross-user check",
            ],
        },
        # Q10 — test account 1 (conditional on Q9 = "Yes")
        {
            "key": "test_account_1",
            "title": "Test account 1 — email and password",
            "description": (
                "Only fill this in if you chose 'Yes' above. We'll only use these "
                "for the audit. Credentials are deleted within 24 hours of delivery."
            ),
            "type": "TEXTAREA",
            "required": False,
            "placeholder": "Email: test1@example.com\nPassword: ...",
        },
        # Q11 — test account 2 (conditional on Q9 = "Yes")
        {
            "key": "test_account_2",
            "title": "Test account 2 — email and password",
            "description": (
                "Only fill this in if you chose 'Yes' above. We'll only use these "
                "for the audit. Credentials are deleted within 24 hours of delivery."
            ),
            "type": "TEXTAREA",
            "required": False,
            "placeholder": "Email: test2@example.com\nPassword: ...",
        },
        # Q12 — support email (for QSG)
        {
            "key": "support_email_for_qsg",
            "title": "Your support email (for the Quick Start Guide)",
            "description": (
                "We'll put this in your one-page user guide so people know how to "
                "reach you."
            ),
            "type": "INPUT_EMAIL",
            "required": True,
            "placeholder": "hello@your-app.example.com",
        },
        # Q13 — anything specific
        {
            "key": "specific_concerns",
            "title": "Anything specific you want us to check?",
            "description": "Anything broken you're worried about? Optional.",
            "type": "TEXTAREA",
            "required": False,
            "placeholder": "I'm not sure the booking page works on mobile...",
        },
        # Q14 — anxiety
        {
            "key": "anxiety_level",
            "title": "How anxious are you about launching?",
            "description": "Optional. Helps me match the tone of your report.",
            "type": "MULTIPLE_CHOICE",
            "required": False,
            "options": ["Calm, just curious", "A bit nervous", "Not sleeping"],
        },
        # Q15 — consent checkbox
        {
            "key": "consent",
            "title": (
                "I confirm I am submitting only temporary test credentials (if "
                "any) and no sensitive production data — no personal passwords, "
                "admin credentials, API keys, database credentials, real customer "
                "data, health data, children's data, or payment information."
            ),
            "description": None,
            "type": "CHECKBOXES",
            "required": True,
            "options": ["I confirm"],
        },
    ],
}


# ---------------------------------------------------------------------------
# Block builders
# ---------------------------------------------------------------------------


def new_uuid() -> str:
    return str(uuid.uuid4())


def block(
    *,
    block_type: str,
    group_type: str,
    payload: dict,
    group_uuid: str | None = None,
) -> dict:
    """Build a single Tally API block."""
    return {
        "uuid": new_uuid(),
        "type": block_type,
        "groupUuid": group_uuid or new_uuid(),
        "groupType": group_type,
        "payload": payload,
    }


def title_block(html: str) -> dict:
    return block(
        block_type="FORM_TITLE",
        group_type="TEXT",
        payload={"title": html, "html": html},
    )


def intro_text_block(text: str) -> dict:
    html = text.replace("\n\n", "<br><br>").replace("\n", "<br>")
    return block(
        block_type="TEXT",
        group_type="TEXT",
        payload={"html": html},
    )


def question_title_block(group_uuid: str, html: str) -> dict:
    return block(
        block_type="TITLE",
        group_type="QUESTION",
        payload={"html": html},
        group_uuid=group_uuid,
    )


def build_title_html(title: str, description: str | None) -> str:
    """Inline the description as a smaller second line of the title.

    Tally's conditional-logic dropdown surfaces TITLE text as the question
    identifier. Keeping description inside the TITLE block (instead of a
    separate LABEL block) makes the logic editor list real question names,
    not helper text.
    """
    if not description:
        return title
    return (
        f"{title}<br>"
        f'<span style="font-weight:400;opacity:0.7;font-size:0.9em">'
        f"{description}</span>"
    )


# Kept for reference (unused). Tally's logic editor lists LABEL text as the
# question identifier in dropdowns, which is confusing. We now inline the
# description into the TITLE block via ``build_title_html`` instead.
def question_label_block(group_uuid: str, text: str) -> dict:  # pragma: no cover
    return block(
        block_type="LABEL",
        group_type="LABEL",
        payload={"html": text},
        group_uuid=group_uuid,
    )


def input_block(
    *,
    input_type: str,
    group_uuid: str,
    placeholder: str | None,
    required: bool,
) -> dict:
    """Tally requires groupType to match the input type (not 'QUESTION')."""
    payload: dict = {"isRequired": required}
    if placeholder:
        payload["placeholder"] = placeholder
    return block(
        block_type=input_type,
        group_type=input_type,
        payload=payload,
        group_uuid=group_uuid,
    )


def _boundary_flags(i: int, total: int) -> dict:
    """Tally needs explicit isFirst/isLast booleans on every option block."""
    return {"isFirst": i == 0, "isLast": i == total - 1}


def multiple_choice_option_blocks(
    *,
    group_uuid: str,
    options: list[str],
    required: bool,
) -> list[dict]:
    blocks: list[dict] = []
    total = len(options)
    for i, text in enumerate(options):
        payload: dict = {"index": i, "text": text, **_boundary_flags(i, total)}
        if i == 0 and required:
            payload["isRequired"] = True
        blocks.append(
            block(
                block_type="MULTIPLE_CHOICE_OPTION",
                group_type="MULTIPLE_CHOICE",
                payload=payload,
                group_uuid=group_uuid,
            )
        )
    return blocks


def checkbox_option_blocks(
    *,
    group_uuid: str,
    options: list[str],
    required: bool,
) -> list[dict]:
    blocks: list[dict] = []
    total = len(options)
    for i, text in enumerate(options):
        payload: dict = {"index": i, "text": text, **_boundary_flags(i, total)}
        if i == 0 and required:
            payload["isRequired"] = True
        blocks.append(
            block(
                block_type="CHECKBOX",
                group_type="CHECKBOXES",
                payload=payload,
                group_uuid=group_uuid,
            )
        )
    return blocks


def build_question_blocks(q: dict) -> list[dict]:
    """Convert one declarative question into the matching Tally blocks.

    Grouping rules (from Tally API docs):
      * INPUT_TEXT / INPUT_EMAIL / INPUT_LINK / TEXTAREA: a single TITLE block
        plus the INPUT block, both sharing one groupUuid (groupType=QUESTION
        on TITLE, matching input type on the INPUT block).
      * MULTIPLE_CHOICE / CHECKBOXES / DROPDOWN: TITLE on its own groupUuid
        (QUESTION); OPTION blocks share a separate groupUuid keyed to that
        choice type.
      * Description text is inlined into the TITLE HTML — no separate LABEL
        block, so Tally's logic dropdown shows the real question title.
    """
    qtype = q["type"]
    title_group = new_uuid()

    title_html = build_title_html(q["title"], q.get("description"))
    blocks: list[dict] = [question_title_block(title_group, title_html)]

    if qtype in ("INPUT_TEXT", "INPUT_EMAIL", "INPUT_LINK", "INPUT_NUMBER", "TEXTAREA"):
        blocks.append(
            input_block(
                input_type=qtype,
                group_uuid=title_group,
                placeholder=q.get("placeholder"),
                required=q.get("required", False),
            )
        )
    elif qtype == "MULTIPLE_CHOICE":
        blocks.extend(
            multiple_choice_option_blocks(
                group_uuid=new_uuid(),
                options=q["options"],
                required=q.get("required", False),
            )
        )
    elif qtype == "CHECKBOXES":
        blocks.extend(
            checkbox_option_blocks(
                group_uuid=new_uuid(),
                options=q["options"],
                required=q.get("required", False),
            )
        )
    else:
        sys.exit(f"ERROR: unsupported question type {qtype!r} for {q.get('key')}")
    return blocks


def build_form_payload(form_def: dict, status: str) -> dict:
    blocks: list[dict] = [title_block(form_def["title"])]
    if form_def.get("intro"):
        blocks.append(intro_text_block(form_def["intro"]))
    for q in form_def["questions"]:
        blocks.extend(build_question_blocks(q))
    return {"status": status, "blocks": blocks}


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------


def _auth_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def create_form(payload: dict, api_key: str) -> dict:
    resp = requests.post(
        TALLY_API_URL, headers=_auth_headers(api_key), json=payload, timeout=30
    )
    if resp.status_code >= 400:
        body = resp.text[:2000]
        sys.exit(
            f"ERROR: Tally API returned {resp.status_code}\n"
            f"Response body (first 2 KB):\n{body}"
        )
    return resp.json()


def delete_form(form_id: str, api_key: str) -> None:
    url = f"{TALLY_API_URL}/{form_id}"
    resp = requests.delete(url, headers=_auth_headers(api_key), timeout=30)
    if resp.status_code in (200, 202, 204):
        print(
            f"Deleted Tally form {form_id} (HTTP {resp.status_code}).", file=sys.stderr
        )
        return
    if resp.status_code == 404:
        print(
            f"WARN: form {form_id} not found (HTTP 404). Proceeding to create.",
            file=sys.stderr,
        )
        return
    body = resp.text[:2000]
    sys.exit(
        f"ERROR: DELETE {url} returned {resp.status_code}\n"
        f"Response body (first 2 KB):\n{body}"
    )


def get_form(form_id: str, api_key: str) -> dict:
    url = f"{TALLY_API_URL}/{form_id}"
    resp = requests.get(url, headers=_auth_headers(api_key), timeout=30)
    if resp.status_code >= 400:
        body = resp.text[:2000]
        sys.exit(
            f"ERROR: GET {url} returned {resp.status_code}\n"
            f"Response body (first 2 KB):\n{body}"
        )
    return resp.json()


def summarize_local_payload(payload: dict) -> dict:
    """Count blocks by groupType from the locally built payload (sanity check)."""
    counts: dict[str, int] = {}
    for b in payload["blocks"]:
        counts[b["groupType"]] = counts.get(b["groupType"], 0) + 1
    question_groups = sum(
        1
        for b in payload["blocks"]
        if b["type"] == "TITLE" and b["groupType"] == "QUESTION"
    )
    return {"counts": counts, "question_groups": question_groups}


def save_response(data: dict) -> None:
    RESPONSE_DIR.mkdir(parents=True, exist_ok=True)
    RESPONSE_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def print_next_steps(form: dict, summary: dict) -> None:
    form_id = form.get("id", "?")
    public_url = f"https://tally.so/r/{form_id}"
    lines = [
        "",
        f"  Form created: {form.get('name', 'Untitled')}",
        f"  ID:           {form_id}",
        f"  Status:       {form.get('status', '?')}",
        f"  Public URL:   {public_url}",
        f"  Edit in app:  https://tally.so/forms/{form_id}/edit",
        f"  Response:     {RESPONSE_PATH}",
        "",
        "  Local payload sanity check:",
        f"    Question groups (TITLE/QUESTION blocks): {summary['question_groups']}",
        f"    Block counts by groupType: {summary['counts']}",
        "",
        "  Still TODO in the Tally UI (API doesn't cover these):",
        "    1. Settings -> Notifications -> email submissions to hello@launchlook.app",
        "    2. Settings -> After submit -> Redirect to https://tally.so/r/Y5xO5J",
        "    3. On Q10 + Q11: click block menu (the 6-dot handle) -> Hide  (makes them hidden by default)",
        "    4. Add /logic block: IF Q8 = 'Scale Up Package ($49)' OR 'Pro Package ($99)' THEN Show blocks: Q9",
        "    5. Add /logic block: IF Q9 = 'Yes - I will provide two test accounts' THEN Show blocks: Q10, Q11",
        f"    6. If happy, Publish -> update intakeFormUrl in landing/assets/config.js to '{public_url}'",
    ]
    sys.stdout.buffer.write(("\n".join(lines) + "\n").encode("utf-8", errors="replace"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--publish", action="store_true", help="Create as PUBLISHED (default: DRAFT)"
    )
    group.add_argument(
        "--dry-run", action="store_true", help="Print JSON payload only, don't call API"
    )
    parser.add_argument(
        "--replace",
        metavar="FORM_ID",
        default=None,
        help="DELETE the given Tally form, then create a new one. Use with care.",
    )
    args = parser.parse_args()

    status = "PUBLISHED" if args.publish else "DRAFT"
    payload = build_form_payload(INTAKE_FORM, status)
    summary = summarize_local_payload(payload)

    if args.dry_run:
        print(json.dumps(payload, indent=2))
        print(
            f"\n[dry-run] {len(payload['blocks'])} blocks, "
            f"{summary['question_groups']} question groups. Status would be {status}.",
            file=sys.stderr,
        )
        return 0

    api_key = os.getenv("TALLY_API_KEY")
    if not api_key:
        sys.exit(
            "ERROR: TALLY_API_KEY not set.\n"
            "Add it to .env (gitignored) at the repo root. Example:\n"
            "  TALLY_API_KEY=tly-xxxx..."
        )

    if args.replace:
        print(f"Deleting Tally form {args.replace}…", file=sys.stderr)
        delete_form(args.replace, api_key)

    print(
        f"Creating Tally form ({len(payload['blocks'])} blocks, "
        f"{summary['question_groups']} question groups, status={status})…",
        file=sys.stderr,
    )
    form = create_form(payload, api_key)
    save_response(form)

    new_id = form.get("id")
    if new_id:
        verified = get_form(new_id, api_key)
        print(
            f"GET /forms/{new_id} -> status={verified.get('status')}, "
            f"name={verified.get('name')!r}",
            file=sys.stderr,
        )

    print_next_steps(form, summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
