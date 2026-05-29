# Tally Intake Form Setup

This doc describes how to configure the Tally intake form fields, including
the 3 optional tone/audience fields for Scale Up and Pro customers.

**Canonical safety copy** (Block 0 at top of form, Q9–Q11 help text, `/thanks` page):
use **dedicated test accounts with dummy data**; **not** admin, billing, or real
customers; credentials **only in this form** (never email); **deleted within 24 hours**
of delivery. Paste-ready text lives in `TALLY-INTAKE-PASTE.txt` (Block 0, Q9–Q11, Thank you page).

---

## Standard fields (all paid tiers)

These are already wired into the pipeline via the hidden `tier` parameter
in the Tally success URL. No changes needed.

| Tally field label | Mapped to | Notes |
|---|---|---|
| First name | `customer.first_name` | Required |
| Last name | `customer.last_name` | Optional |
| Email | `customer.email` | Required |
| App name | `customer.app_name` | Required |
| App URL | `customer.app_url` | Required |
| Builder / platform | `customer.builder` | Dropdown |
| Anything you want the auditor to know | `customer.intake_notes` | Optional freetext |
| Tier (hidden) | `customer.tier` | Set via `?tier=` in the success URL |

---

## New optional fields (Scale Up and Pro only)

These 3 fields feed both the Quick Start Guide and the User Guide prompts.
They should be shown **conditionally** in Tally — only when the hidden `tier`
field equals `Scale Up Package` or `Pro Package`.

### How to add conditional logic in Tally

1. In your Tally form, go to the field you want to show conditionally.
2. Click **Conditional logic** (or the logic icon on that field block).
3. Set: **Show this field when → Tier → is → Scale Up Package** (add an
   OR condition for **Pro Package** as well).
4. Add the field to the form, then apply the condition.

### The 3 fields to add

**Field 1 — Primary user**
- Label: `Who are your users?`
- Type: Short text or paragraph
- Placeholder: e.g. `Small business owners, 35-55, non-technical`
- Mapped to: `customer_ctx.user_audience` in the pipeline
- Conditional: Show for Scale Up and Pro only

**Field 2 — Tone**
- Label: `What tone fits your brand?`
- Type: Short text (or a 3-option multiple choice: Friendly / Formal / Casual)
- Placeholder: e.g. `Friendly and approachable, informal`
- Mapped to: `customer_ctx.user_tone` in the pipeline
- Conditional: Show for Scale Up and Pro only

**Field 3 — Content notes**
- Label: `Anything the guide must or must not mention?`
- Type: Short text or paragraph
- Placeholder: e.g. `We never use the word "dashboard" — we call it "your workspace"`
- Mapped to: `customer_ctx.user_content_constraints` in the pipeline
- Conditional: Show for Scale Up and Pro only
- Mark as optional so it does not block form submission

---

## Wall of Launches opt-in

**Q_WALL_OPT_IN** (Checkbox, optional)
Label: "I'm happy for LaunchLook to list my app on the Wall of Launches after I ship."
Tally field type: Checkbox (single, optional)
Purpose: Grants permission to add the app to launchlook.app/wall
Note: Add this as the last question in the form, clearly optional. No field ID yet — update this doc once added in Tally.

---

## How these fields reach the pipeline

When the Tally webhook (or Tally email) delivers responses to your intake
processing script, map these three field answers onto the `CustomerContext`
dataclass fields:

```python
CustomerContext(
    # ... other fields ...
    user_audience=intake.get("who_are_your_users", ""),
    user_tone=intake.get("tone", ""),
    user_content_constraints=intake.get("content_notes", ""),
)
```

The `build_user_guide_prompt()` function in `scripts/ai_audit/pipeline.py`
picks them up automatically. If the fields are blank (Starter customers, or
Scale Up/Pro customers who skipped them), the prompt defaults to neutral
plain-English tone and a general adult audience.

---

## Tally field IDs

After adding these fields in Tally, note their field IDs here so the intake
processing script can map them by ID (more reliable than matching by label):

| Field | Tally field ID |
|---|---|
| Who are your users? | *(fill in after adding to form)* |
| What tone fits your brand? | *(fill in after adding to form)* |
| Anything the guide must or must not mention? | *(fill in after adding to form)* |
