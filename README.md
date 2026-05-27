# LaunchLook

A friendly pre-launch checkup for vibe-coded apps. **Site:** [launchlook.app](https://launchlook.app). Founders building with Lovable, Bolt, Base44, and Replit send their URL and get back a plain-English fix list plus an AI-generated Quick Start Guide for their users. AI drafts the audit, a founder personally reviews and curates every finding before delivery. $9 to start.

> **Status**: pre-launch. Zero paying customers yet. AI-first delivery shipped (`scripts/ai_audit.py`), with founder spot-check via `scripts/audit_ui.py --review-ai` before each report goes out. See `docs/AI-AUDIT-PIPELINE.md`.

**Rob — everything left for you:** [`docs/ROB-REMAINING-TODO.md`](docs/ROB-REMAINING-TODO.md)  
**Build Tally intake (manual):** [`docs/TALLY-INTAKE-PASTE.txt`](docs/TALLY-INTAKE-PASTE.txt)  
**All docs index:** [`docs/README.md`](docs/README.md)

## Read this first

If you (human or AI assistant) are about to touch any code in this repo, read the handoff docs in `docs/` **in order** before writing anything:

1. `docs/00-START-HERE.md`
2. `docs/ROB-REMAINING-TODO.md` — owner checklist (what's still manual)
3. `docs/01-product-spec.md`
4. `docs/02-strategy-and-context.md` — read before challenging any decision
5. `docs/03-build-queue.md` — BL-XX tickets
6. `docs/04-content-and-copy.md`
7. `docs/05-technical-architecture.md`
8. `docs/06-findings-library.md`
9. `docs/07-launchlook-go-live.md` — Stripe, Tally, E2E
10. `docs/TALLY-AI-ONE-SHOT.txt` — when building the intake form in Tally

The biggest risk to this project is over-building. The manual-first strategy is deliberate, not a placeholder for "real" engineering.

## Repo layout

```
launchlook/
├── landing/             # Static site: home, checklist, privacy, terms, thanks (BL-05, BL-06)
│   └── images/
├── scripts/             # audit_checklist, findings_lookup, email_render, QSG, referral, follow-up
├── prompts/             # AI prompt files (Quick Start Guide etc.)
│   └── examples/        # Worked input/output pairs for prompt tuning
├── templates/
│   ├── notion/          # Notion report templates (Quick / Launch / Polish)
│   ├── email/           # Email templates (welcome, delivery, follow-ups)
│   ├── qsg/             # HTML template for qsg_render.py (BL-10)
│   └── examples/        # Sample reports (e.g. LiLo practice audit)
├── findings_library/    # 38-finding seed library (JSON + CSV) + placeholder patterns
├── output/              # Generated artifacts — gitignored
│   └── scans/
├── tests/               # Smoke tests
└── docs/                # The handoff package — source of truth
```

## Setup

Requires Python 3.11+. Most MVP work does **not** need any of the optional dependencies.

```powershell
# Windows
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Then fill in `.env` as accounts get created (Stripe → Notion → Resend → optional AI keys). Do not commit `.env`.

### Optional extras

| Extra      | When to install                              | Command                          |
|------------|----------------------------------------------|----------------------------------|
| `crawler`  | After customer 10 — when starting BL-14      | `pip install -e ".[crawler]"`    |
| `ai`       | Only if QSG generation is API-automated      | `pip install -e ".[ai]"`         |

After installing `crawler`, also run `playwright install chromium`.

## Build queue

Work is tracked in `docs/03-build-queue.md`. Tickets are referenced as **BL-XX** throughout this repo (in code comments, commit messages, file names).

**Do not start BL-14 (Playwright crawler) or BL-15 (Notion auto-population) until customer 10 is reached.** This is a hard gate, not a guideline.

## Operator quick reference

```bash
python scripts/customers_track.py init         # once — creates data/customers.json
python scripts/customers_track.py stats        # paying count / milestone to 10
python scripts/audit_checklist.py              # 20-min audit steps
python scripts/findings_lookup.py placeholder  # search findings library
python scripts/email_render.py delivery --name X --app-name Y --report-link URL --platform Lovable
python scripts/qsg_compose_prompt.py ...       # paste output into ChatGPT
python scripts/qsg_render.py --input ...md --output ...html
python scripts/notion_test.py --list-customers # after Notion is wired
```

Landing deploy: push to `main` (Vercel builds from repo root). Config: `landing/assets/config.js`; overrides: `config.local.js` (gitignored). After Tally publish, set `intakeFormUrl` — see [`docs/TALLY-COPY-PASTE.md`](docs/TALLY-COPY-PASTE.md).

## License

Internal project. Not for redistribution.
