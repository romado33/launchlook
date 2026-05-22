# Publishing the checklist as a public GitHub repo (BL-16)

This folder contains the files for the standalone public checklist repo. It's intentionally separate from the main `LaunchLook` repo so the public-facing artifact stays clean (no internal docs, no scripts, no fix prompts).

## One-time setup

```bash
# From the LaunchLook repo root:
cd external/launchlook-prelaunch-checklist

# Initialize a fresh repo here (it's not a submodule)
git init -b main
git add .
git commit -m "Initial checklist v1"

# Create the public repo on GitHub
gh repo create launchlook-prelaunch-checklist \
  --public \
  --description "A free pre-launch checklist for vibe-coded apps (Lovable / Bolt / Base44 / Replit)." \
  --source . \
  --push
```

The repo URL becomes `https://github.com/{your-handle}/launchlook-prelaunch-checklist`.

## Updating

When the in-app `/checklist` page changes:

1. Update `external/launchlook-prelaunch-checklist/README.md` to match (verbatim — no marketing words sneaking in)
2. From inside that folder:
   ```bash
   git add README.md
   git commit -m "Update checklist: <one-line change description>"
   git push
   ```
3. Update the landing/checklist.html in the main repo to match
4. Deploy landing page (`cd ../../landing && vercel --prod`)

## Update both at once

The checklist content lives in three places that must stay in sync:

| Location | File |
|----------|------|
| Public GitHub repo | `external/launchlook-prelaunch-checklist/README.md` |
| LaunchLook website /checklist page | `landing/checklist.html` |
| Original handoff doc (historical) | `docs/04-content-and-copy.md` (section 5) |

When you change one, change the others. Otherwise the public version drifts from the website version.

## Why a separate repo?

- The free checklist is the top-of-funnel content. It should be discoverable on GitHub independently of the product.
- Keeping it separate means anyone can star/fork/contribute without touching internal LaunchLook stuff.
- It also lets you point to a stable URL: `github.com/{your-handle}/launchlook-prelaunch-checklist`.

## What NOT to publish

The main `LaunchLook` repo contains:
- Findings library JSON (your competitive moat — keep private)
- Customer report templates with referral/upsell mechanics
- Email templates with sales copy
- Internal Notion DB schemas
- Strategy docs and customer pipeline scripts

None of those belong in the public checklist repo. Only this folder gets published.
