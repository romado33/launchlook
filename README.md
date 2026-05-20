# Onceover

A friendly pre-launch checkup for vibe-coded apps. Founders building with Lovable, Bolt, Base44, and Replit send their URL and get back a plain-English fix list plus an AI-generated Quick Start Guide for their users. $7 to start.

> **Status**: pre-launch. Zero paying customers yet. Manual delivery is intentional — automation is gated on customer milestones (see `docs/03-build-queue.md`).

## Read this first

If you (human or AI assistant) are about to touch any code in this repo, read the handoff docs in `docs/` **in order** before writing anything:

1. `docs/00-START-HERE.md`
2. `docs/01-product-spec.md`
3. `docs/02-strategy-and-context.md` — read before challenging any decision
4. `docs/03-build-queue.md` — start work here
5. `docs/04-content-and-copy.md`
6. `docs/05-technical-architecture.md`
7. `docs/06-findings-library.md`

The biggest risk to this project is over-building. The manual-first strategy is deliberate, not a placeholder for "real" engineering.

## Repo layout

```
onceover/
├── landing/             # Static landing page + /checklist (BL-05, BL-06)
│   └── images/
├── scripts/             # Operational scripts (QSG, referral, follow-up, crawler)
├── prompts/             # AI prompt files (Quick Start Guide etc.)
│   └── examples/        # Worked input/output pairs for prompt tuning
├── templates/
│   ├── notion/          # Notion report templates (Quick / Launch / Polish)
│   └── email/           # Email templates (welcome, delivery, follow-ups)
├── findings_library/    # The 35-finding seed library + future additions
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

## License

Internal project. Not for redistribution.
