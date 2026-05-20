# Prompts — Quick Start Guide pipeline

The QSG is the centerpiece of the Launch Pack ($29) and Polish ($59) tiers. The pipeline goes:

```
Intake form
    ↓
Manual crawl of customer's app (homepage + post-signup if creds provided)
    ↓
Run scripts/qsg_compose_prompt.py to fill in the user-message template
    ↓
Paste system prompt + composed user message into chatgpt.com (or Anthropic Workbench)
    ↓
Get Markdown draft
    ↓
Rob's editing pass (~10 min): tone, accuracy, UI labels, forbidden-words sweep
    ↓
Run scripts/qsg_render.py to produce styled HTML (BL-10)
    ↓
Paste Markdown into the Notion Launch Pack report + send HTML link
```

## Files

| File | Purpose |
|------|---------|
| `quickstart_system.txt` | System prompt — paste once at top of ChatGPT session |
| `quickstart_user.txt` | User-message template with `{placeholders}` |
| `examples/taskroom_input.txt` | A worked input example (TaskRoom) |
| `examples/taskroom_output.md` | The expected output from the TaskRoom input — your quality benchmark |

## How to use (manual workflow — current default)

1. Audit a real customer's app. Capture:
   - Homepage visible text (copy-paste from the page)
   - Post-signup visible text (after you sign up with their provided test creds)
   - Navigation labels (the menu/nav bar)
   - Button labels (visible CTAs)
2. Open intake form responses for the customer. Note: app name, description, target user, main workflow, platform, support email.
3. From the repo root:

   ```bash
   python scripts/qsg_compose_prompt.py \
       --app-name "TaskRoom" \
       --description "A simple shared to-do list for small teams." \
       --target-user "Small business owners or team leads..." \
       --workflow "Create a task, assign it..." \
       --platform Lovable \
       --homepage-file ./output/scans/{customer}/homepage.txt \
       --postsignup-file ./output/scans/{customer}/postsignup.txt \
       --nav "Tasks, Team, Settings, Help" \
       --ctas "Add Task, Assign, Mark Done" \
       --support hello@taskroom.app \
       --notes "Most users invite 2–5 teammates." \
       > ./output/scans/{customer}/qsg_prompt.txt
   ```

4. Open ChatGPT (chatgpt.com) → start a new chat.
5. **Paste the contents of `quickstart_system.txt` first** as the opening message: "Use this as your system prompt: [paste]"
6. **Then paste the composed prompt from step 3.**
7. ChatGPT returns a Markdown draft.
8. **Spot-edit the draft.** Look for:
   - Any forbidden words → strike them. The composer script flags them when you run it; if any get through, fix manually.
   - `[REVIEWER: ...]` markers → these are honest gaps. Resolve from the actual app or replace with a generic fallback.
   - UI labels that don't match what's actually in the app → fix.
   - Sentences over 20 words → shorten.
9. Paste the edited Markdown into the Notion Launch Pack report (Part 2).
10. (BL-10, future) Render to HTML for embedding.

## How to use (API-automated workflow — future)

When you decide to wire up OpenAI's or Anthropic's API:

```bash
export OPENAI_API_KEY=sk-...  # or ANTHROPIC_API_KEY
python scripts/qsg_generate.py --input ./output/scans/{customer}/intake.json \
    --output ./output/scans/{customer}/quickstart.md
```

Currently `qsg_generate.py` is a skeleton that will error with a clear message if no key is set.

## Iterating the prompt

The system prompt will need tuning across the first 5–10 customers. Track changes:

- Keep a `prompts/CHANGELOG.md` (TODO when first change is made)
- Run new prompt against `examples/taskroom_input.txt` and diff against `examples/taskroom_output.md` to catch regressions
- If a customer pushes back on the QSG, capture their exact complaint and either tighten the prompt OR add a constraint

## Quality bar

Before pasting a draft into a customer report, every QSG must pass:

- [ ] No forbidden words anywhere
- [ ] No `[REVIEWER: ...]` markers remain (either resolved or replaced)
- [ ] Every UI label matches what's actually visible in the app
- [ ] 250–450 words total
- [ ] Reads aloud naturally (read it out loud — if any sentence feels stiff, rewrite)
- [ ] A non-technical user (friend, family) can read it cold and explain back what the app does
