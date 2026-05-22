# Findings Library

The findings seed library (38 entries as of v2) that powers LaunchLook audits. Source of truth for both manual work today and (eventually) the BL-15 scanner that auto-populates Notion reports.

## Files

| File | Purpose |
|------|---------|
| `findings.json` | Machine-readable, the source of truth. Used by future scripts. |
| `findings.csv` | Notion-importable. Drag into a Notion database to seed it. |

## How to import into Notion (BL-03)

1. Open the `LaunchLook Ops` Notion workspace (create it if you haven't yet).
2. New page → choose **Database — Full page** → name it `Findings Library`.
3. Top-right `...` menu → **Merge with CSV** → upload `findings.csv`.
4. Adjust column types after import:
   - `ID` → Text (or Title — make this the row title)
   - `Finding Name` → Text
   - `Category` → Select (categories listed below)
   - `Severity` → Select (Critical / High / Medium / Low — colour Critical red, High orange, Medium yellow, Low gray)
   - All other fields → Text (multiline)
5. Add a `Variables Used` rollup field later if you want it.

### Severity colours (Notion select options)

| Severity | Notion colour |
|----------|---------------|
| Critical | red |
| High | orange |
| Medium | yellow |
| Low | gray |

### Categories (Notion select options)

- Placeholders & forgotten content
- Trust pages & legal
- Broken functionality
- Mobile & responsive
- Authentication & permissions
- Sharing & meta
- User experience
- Performance & polish

## How to add new findings (during real audits)

After every manual audit, ask: "Is there a finding here that isn't in the library yet?" If yes:

1. **Add in Notion first** (the working copy) — new row, ID auto-generates as FL-036, FL-037, etc.
2. **Tag it** with `added: YYYY-MM-DD` and `first_seen_customer: <first name>`.
3. **Sync back to this repo** monthly: re-export the Notion DB as CSV, run `scripts/findings_sync.py` (TODO: build when needed), commit.

Goal: 1–3 new findings per real audit during the first 30 customers.

## Variables used in fix prompts

The `findings.json` file has a `variables` block listing every `{VARIABLE}` placeholder used across the library. When delivering a report manually, substitute them with values from the customer's intake form.

The most common substitutions:

| Variable | Source |
|---|---|
| `{ACTUAL_NAME}` | Intake form field 4 ("What does your app do?") → product name from URL |
| `{ACTUAL_EMAIL}` | Intake form field 11 (support email, Launch Pack+) |
| `{ONE_LINE_DESCRIPTION}` | Intake form field 4 |
| `{PAGE}` | Per-finding — the page where the issue appears |

## False-positive risks documented in `notes`

Each finding's `notes` field flags known false positives. The scanner (when built) should treat these as soft signals, not auto-include — Rob makes the final call.

Known false positives:

- **FL-005 (TODO)** — false positive in real to-do apps
- **FL-007 (Acme)** — could be a legitimate brand
- **FL-027 (Coming soon)** — could be an intentional feature gate

## When the scanner ships (BL-15)

`scripts/notion_populate.py` will read `findings.json`, run regex/HTTP detections from the crawler output, and write findings into a customer's Notion report page using the matching fix prompt. The Notion DB stays the working copy for Rob's edits; the JSON stays the source for the scanner.
