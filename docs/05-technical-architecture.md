# LaunchLook — Technical Architecture

## Overall philosophy

Build the minimum code that lets Rob deliver more reports per hour. Avoid building anything customer-facing that doesn't already exist in the manual workflow.

The architecture is a pipeline, not a SaaS:

```
Customer pays via Stripe
    ↓
Customer fills intake form
    ↓
Rob receives email + intake data lands in Notion Customers DB
    ↓
[Manual today, automated later] Crawler runs against URL
    ↓
[Manual today, automated later] Findings populate Notion report
    ↓
[Manual today, automated later] Quick Start Guide script generates QSG
    ↓
Rob edits, finalizes, sends Notion link to customer
    ↓
[Automated] Day-3 follow-up email
    ↓
[Automated] Day-7 check-in (if Polish tier)
```

Each `[Manual today, automated later]` step is a future build item, not a day-1 requirement.

## Tech stack

- **Language**: Python 3.11+ for all scripts
- **Browser automation**: Playwright (chromium only)
- **AI**: Claude API (claude-sonnet-4-6 by default, fall back to haiku for cheap checks)
- **Notion integration**: notion-client (Python SDK)
- **Payment**: Stripe (Payment Links, no custom checkout)
- **Email**: Resend or SendGrid (whichever is easier to set up)
- **Hosting**: Vercel for landing page, Cloudflare Pages as fallback
- **Scheduling**: GitHub Actions (cron schedules) — free, simple, no infrastructure
- **Storage**: Local filesystem for screenshots and intermediate artifacts. S3 only if needed for sharing.

## Repo structure (recommended)

```
LaunchLook/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── landing/
│   ├── index.html
│   ├── checklist.html
│   ├── styles.css
│   └── images/
├── scripts/
│   ├── crawler.py           # BL-14
│   ├── qsg_generate.py      # BL-09
│   ├── qsg_render.py        # BL-10
│   ├── notion_populate.py   # BL-15
│   ├── referral_create.py   # BL-12
│   └── followup_send.py     # BL-13
├── prompts/
│   ├── quickstart_system.txt
│   ├── quickstart_user.txt
│   └── examples/
│       └── taskroom_example.md
├── templates/
│   ├── notion_report_quick_checkup.json
│   ├── notion_report_launch_pack.json
│   ├── notion_report_polish.json
│   ├── email_welcome.txt
│   ├── email_delivery.txt
│   ├── email_followup_d3.txt
│   └── email_followup_d7.txt
├── findings_library/
│   └── findings.json        # exported from Notion
├── output/                  # gitignored
│   └── scans/
└── tests/
    └── test_crawler.py
```

## Crawler architecture

The crawler is described in detail in `03-build-queue.md` (BL-14). Key principles:

- **Read-only**: never submit forms, never click destructive buttons.
- **Two-pass**: desktop (1920×1080) and mobile (375×812 viewports).
- **Captures, doesn't judges**: outputs raw JSON for human curation.
- **No persistence beyond scan**: deletes any captured credentials after each run.
- **Polite**: respects robots.txt, rate-limits requests, identifies itself in User-Agent (`LaunchLook-Crawler/0.1`).

### Crawler output schema

```json
{
  "scan_id": "scan_2026_05_20_abc123",
  "url": "https://myapp.example.com",
  "scanned_at": "2026-05-20T14:32:00Z",
  "platform_detected": "lovable",
  "pages_crawled": [
    {
      "url": "https://myapp.example.com/",
      "title": "My App - Welcome",
      "viewport": "desktop",
      "screenshot_path": "screenshots/scan_abc123/home_desktop.png",
      "console_errors": [
        {
          "type": "TypeError",
          "message": "Cannot read property 'data' of undefined",
          "source": "https://myapp.example.com/static/app.js:1234"
        }
      ],
      "network_failures": [
        {
          "url": "https://api.myapp.example.com/users",
          "status": 401,
          "method": "GET"
        }
      ],
      "links_found": ["/about", "/pricing", "/login", "/contact"],
      "broken_links": ["/contact"],
      "buttons_found": [
        {"label": "Get Started", "selector": "button.cta-primary", "click_outcome": "navigated_to_/signup"},
        {"label": "Learn More", "selector": "button.cta-secondary", "click_outcome": "no_change"}
      ],
      "placeholder_matches": [
        {"pattern": "your_company_name", "context": "Welcome to Your Company Name"}
      ],
      "trust_pages_status": {
        "/privacy": 404,
        "/terms": 200,
        "/contact": 404
      }
    }
  ],
  "auth_checks": {
    "logged_out_access": {
      "/dashboard": "loaded_with_data",
      "/admin": "redirected_to_login",
      "/settings": "loaded_with_data"
    }
  }
}
```

### Platform detection

Detect the platform by looking for known artifacts in HTML/headers:
- Lovable: `lovable.dev` in script src, specific meta tags
- Bolt: `bolt.new` references, `stackblitz` in console errors
- Base44: `base44` references in HTML or JS
- Replit: `repl.co` in URLs or assets
- v0: `v0.dev` references, Vercel hosting headers

If none match, mark as `unknown`. Don't fail the scan.

### Code skeleton

```python
"""
LaunchLook crawler — collects raw observations for manual curation.
Does NOT make judgments. Output JSON gets reviewed in Notion.
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

PLACEHOLDER_PATTERNS = [
    (r"your\s+(company|business|brand|app|product)\s+name", "generic_company_name"),
    (r"lorem\s+ipsum|consectetur\s+adipiscing", "lorem_ipsum"),
    (r"\[insert\s+\w+|\[your\s+\w+|\[add\s+\w+", "bracket_placeholder"),
    (r"\bTODO\b|\bFIXME\b", "todo_comment"),
    (r"(support|hello|info|contact)@(example|yourdomain|domain|test)\.com", "placeholder_email"),
    (r"\bacme\b|example\s+(corp|inc|company|llc)", "acme_placeholder"),
    (r"coming\s+soon", "coming_soon"),
    (r"placeholder", "literal_placeholder_word"),
]

TRUST_PAGES = ["/privacy", "/privacy-policy", "/terms", "/terms-of-service", "/contact", "/about"]
PROTECTED_ROUTES = ["/dashboard", "/admin", "/settings", "/profile", "/account"]


async def scan_app(url, output_dir, test_creds=None):
    scan_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_path = Path(output_dir) / scan_id
    output_path.mkdir(parents=True, exist_ok=True)
    screenshot_dir = output_path / "screenshots"
    screenshot_dir.mkdir(exist_ok=True)

    result = {
        "scan_id": scan_id,
        "url": url,
        "scanned_at": datetime.utcnow().isoformat() + "Z",
        "pages_crawled": [],
        "auth_checks": {"logged_out_access": {}},
        "trust_pages_status": {},
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        desktop_context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        await scan_page(desktop_context, url, "desktop", screenshot_dir, result)
        await desktop_context.close()

        mobile_context = await browser.new_context(
            viewport={"width": 375, "height": 812},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"
        )
        await scan_page(mobile_context, url, "mobile", screenshot_dir, result)
        await mobile_context.close()

        check_context = await browser.new_context()
        for path in TRUST_PAGES:
            page = await check_context.new_page()
            try:
                response = await page.goto(url.rstrip("/") + path, timeout=10000)
                result["trust_pages_status"][path] = response.status if response else 0
            except Exception:
                result["trust_pages_status"][path] = "error"
            await page.close()

        for route in PROTECTED_ROUTES:
            page = await check_context.new_page()
            try:
                response = await page.goto(url.rstrip("/") + route, timeout=10000)
                final_url = page.url
                if "login" in final_url or "signin" in final_url:
                    outcome = "redirected_to_login"
                elif response and response.status >= 400:
                    outcome = f"error_{response.status}"
                else:
                    outcome = "loaded"
                result["auth_checks"]["logged_out_access"][route] = outcome
            except Exception as e:
                result["auth_checks"]["logged_out_access"][route] = f"error: {str(e)[:50]}"
            await page.close()

        await check_context.close()
        await browser.close()

    output_file = output_path / "scan.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Scan complete: {output_file}")
    return result


async def scan_page(context, url, viewport_name, screenshot_dir, result):
    page = await context.new_page()
    page_result = {
        "url": url,
        "viewport": viewport_name,
        "console_errors": [],
        "network_failures": [],
        "links_found": [],
        "buttons_found": [],
        "placeholder_matches": [],
    }

    page.on("console", lambda msg:
        page_result["console_errors"].append({
            "type": msg.type,
            "message": msg.text[:200]
        }) if msg.type == "error" else None
    )

    page.on("response", lambda response:
        page_result["network_failures"].append({
            "url": response.url,
            "status": response.status,
            "method": response.request.method
        }) if response.status >= 400 else None
    )

    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
    except Exception as e:
        page_result["load_error"] = str(e)[:200]
        await page.close()
        result["pages_crawled"].append(page_result)
        return

    screenshot_path = screenshot_dir / f"home_{viewport_name}.png"
    await page.screenshot(path=str(screenshot_path), full_page=True)
    page_result["screenshot_path"] = str(screenshot_path.relative_to(screenshot_dir.parent))
    page_result["title"] = await page.title()

    visible_text = await page.evaluate("() => document.body.innerText")
    for pattern, name in PLACEHOLDER_PATTERNS:
        matches = re.finditer(pattern, visible_text, re.IGNORECASE)
        for m in matches:
            context_start = max(0, m.start() - 40)
            context_end = min(len(visible_text), m.end() + 40)
            page_result["placeholder_matches"].append({
                "pattern": name,
                "matched_text": m.group(0),
                "context": visible_text[context_start:context_end]
            })

    links = await page.evaluate("""
        () => Array.from(document.querySelectorAll('a[href]'))
            .map(a => a.getAttribute('href'))
            .filter(h => h && !h.startsWith('#'))
    """)
    page_result["links_found"] = list(set(links))

    buttons = await page.evaluate("""
        () => Array.from(document.querySelectorAll('button, [role="button"]'))
            .filter(b => b.offsetParent !== null)
            .map(b => ({
                label: b.innerText.trim().slice(0, 50),
                selector: b.tagName.toLowerCase() + (b.className ? '.' + b.className.split(' ')[0] : '')
            }))
    """)
    page_result["buttons_found"] = buttons[:30]

    if viewport_name == "mobile":
        overflow = await page.evaluate("""
            () => ({
                bodyWidth: document.body.scrollWidth,
                viewportWidth: window.innerWidth,
                overflows: document.body.scrollWidth > window.innerWidth
            })
        """)
        page_result["horizontal_overflow"] = overflow["overflows"]
        page_result["body_width"] = overflow["bodyWidth"]
        page_result["viewport_width"] = overflow["viewportWidth"]

    await page.close()
    result["pages_crawled"].append(page_result)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python crawler.py <url> [output_dir]")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./scans"
    asyncio.run(scan_app(url, output_dir))
```

## Quick Start Guide pipeline

The QSG generation is the most novel piece. Detailed below.

### System prompt

```
You are a senior technical writer with 15 years of experience writing user documentation for software products. You specialize in writing Quick Start Guides for non-technical end users.

Your job is to write a one-page Quick Start Guide for the end users of a web application. You will be given:
- The app's name
- A one-line description
- Who the target user is
- The main workflow users do
- Crawled copy from the homepage and post-signup pages
- Visible navigation labels and CTAs

WRITING PRINCIPLES (non-negotiable):
- Plain language. No jargon. No "leverage," "seamless," "robust," "innovative," "powerful," "cutting-edge," "streamline," or any other marketing words.
- Active voice and second person ("you"). Not "users can..." but "you can..."
- Short sentences (under 20 words when possible).
- Concrete verbs over abstract ones. "Click Save" not "Initiate the save process."
- Describe what the user sees. Use actual UI labels from the crawled content (in quotes when referring to specific buttons or sections).
- Never invent features. If the crawled content doesn't show evidence of a feature, don't claim it exists.
- Acknowledge uncertainty honestly. If you can't tell how something works from the crawled content, write a placeholder section the human reviewer can fill in: [REVIEWER: confirm — does {X} work this way?]

STRUCTURE (must follow exactly):
Output a Markdown document with these sections in this order:

1. # {App Name}
2. ## What it is
   - 2-3 sentences explaining what the app does and what problem it solves.
3. ## Who it's for
   - 1-2 sentences naming the target user.
4. ## Get started
   - Numbered list of 3-5 steps to go from "just signed up" to "ready to use." Each step is one sentence. Reference actual UI elements.
5. ## What you can do
   - 3-5 bullets, each describing one core workflow in plain language. Each bullet is one sentence. Lead with the verb.
6. ## Common questions
   - 4-6 Q&A pairs. Questions should be ones a real user would ask ("How do I change my password?", "Can I cancel anytime?", "Where do I see my history?"). Answers should be 1-3 sentences each, concrete, and reference actual UI elements when possible.
7. ## Get help
   - 1-2 sentences pointing to the support email or contact method.

FORMATTING RULES:
- Use Markdown headings as shown above (# for title, ## for sections).
- Bold only for emphasis, never for whole sentences.
- Use bullets for lists, numbered lists only for sequential steps.
- No tables, no images, no code blocks (this is user-facing doc).
- Total length: 250-450 words.

OUTPUT FORMAT:
Markdown only. No preamble, no "Here is your guide," no closing remarks. Start directly with the # title and end with the last sentence of Get help.

If any required input is missing or empty, do your best with what you have and flag gaps with [REVIEWER: needs {X}] markers in the relevant section.
```

### User message template

```
Write a Quick Start Guide for the following web app:

APP NAME: {app_name}
ONE-LINE DESCRIPTION: {one_line_description}
TARGET USER: {target_user_description}
MAIN WORKFLOW: {main_workflow_description}
PLATFORM BUILT WITH: {platform}

CRAWLED HOMEPAGE COPY:
"""
{homepage_text}
"""

CRAWLED POST-SIGNUP COPY:
"""
{post_signup_text}
"""

VISIBLE NAVIGATION LABELS: {nav_labels_comma_separated}
VISIBLE CTAs: {cta_labels_comma_separated}
SUPPORT EMAIL: {support_contact}
FOUNDER NOTES: {founder_notes}
```

### Post-process check

After Claude returns the Markdown, run a check for forbidden words. If any appear, log a warning and flag for human review.

```python
FORBIDDEN_WORDS = [
    "leverage", "seamless", "robust", "cutting-edge", "innovative",
    "streamline", "powerful", "elevate", "empower", "unlock",
    "supercharge", "revolutionize", "best-in-class", "world-class"
]

def check_forbidden(markdown_text):
    flagged = []
    for word in FORBIDDEN_WORDS:
        if word.lower() in markdown_text.lower():
            flagged.append(word)
    return flagged
```

### API call structure

```python
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_qsg(context):
    system_prompt = open("prompts/quickstart_system.txt").read()
    user_template = open("prompts/quickstart_user.txt").read()
    user_message = user_template.format(**context)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        temperature=0.5,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )

    return response.content[0].text
```

## Notion integration

### Authentication

Use a Notion integration token. Store in `.env` as `NOTION_TOKEN=secret_xxx`. Share each database with the integration manually in Notion's UI.

### Reading customer data

```python
from notion_client import Client

notion = Client(auth=os.getenv("NOTION_TOKEN"))

def get_pending_customers():
    response = notion.databases.query(
        database_id=os.getenv("NOTION_CUSTOMERS_DB_ID"),
        filter={
            "and": [
                {"property": "Delivered", "checkbox": {"equals": False}},
                {"property": "Intake Received", "checkbox": {"equals": True}}
            ]
        }
    )
    return response["results"]
```

### Writing a report page

```python
def create_report_page(customer_data, findings, parent_page_id):
    new_page = notion.pages.create(
        parent={"page_id": parent_page_id},
        properties={
            "title": [{"text": {"content": f"{customer_data['name']} — {customer_data['app_url']}"}}]
        },
        children=build_report_blocks(customer_data, findings)
    )
    return new_page["url"]
```

## Email infrastructure

### Provider

Use Resend (resend.com) for transactional email. Reasons:
- Simple API
- Generous free tier (3000 emails/month)
- Great deliverability for transactional
- Easy custom domain setup

### Sending pattern

```python
import resend

resend.api_key = os.getenv("RESEND_API_KEY")

def send_email(to, subject, body, from_email="hello@launchlook.app"):
    return resend.Emails.send({
        "from": f"Rob at LaunchLook <{from_email}>",
        "to": to,
        "subject": subject,
        "text": body
    })
```

## Stripe integration

### Payment Links (no custom checkout)

Use Stripe's hosted Payment Links. Three per tier, all configured in Stripe dashboard:
- Starter: $7 USD one-time
- Launch: $29 USD one-time
- follow-up: $59 USD one-time

Each Payment Link has:
- Success URL: `https://launchlook.app/intake?tier=quick&session_id={CHECKOUT_SESSION_ID}`
- Cancel URL: `https://launchlook.app`

### Webhooks

Configure a webhook endpoint at `https://launchlook.app/webhook/stripe`. Listen for:
- `checkout.session.completed` — write to Notion Customers DB, send welcome email

For MVP, can also poll Stripe API on a cron schedule instead of webhooks. Simpler.

## Scheduling

Use GitHub Actions for scheduled jobs:

```yaml
name: Daily Follow-up Sender

on:
  schedule:
    - cron: '0 14 * * *'  # 14:00 UTC daily

jobs:
  send-followups:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python scripts/followup_send.py
        env:
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          RESEND_API_KEY: ${{ secrets.RESEND_API_KEY }}
          NOTION_CUSTOMERS_DB_ID: ${{ secrets.NOTION_CUSTOMERS_DB_ID }}
```

## Environment variables

Create `.env.example`:

```
# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Notion
NOTION_TOKEN=secret_...
NOTION_CUSTOMERS_DB_ID=...
NOTION_FINDINGS_DB_ID=...
NOTION_OUTREACH_DB_ID=...
NOTION_REPORTS_PARENT_PAGE_ID=...

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email
RESEND_API_KEY=re_...
FROM_EMAIL=hello@launchlook.app
ADMIN_EMAIL=rob@launchlook.app

# Playwright
HEADLESS=true
```

Never commit `.env`. Add to `.gitignore`.

## Cost projections

Per 10 customers (Starter tier):
- Claude API for QSG (only Launch and Polish, so ~5 of 10): ~$0.50 total
- Playwright runs (when scanner is live): negligible
- Notion: free tier sufficient
- Resend: free tier sufficient
- Vercel: free tier sufficient
- Stripe fees: ~$0.50 per $7 transaction = $5.00 across 10
- Domain renewal: $12/year

Total cost per 10 customers: ~$6. Revenue per 10 customers at $7 base: $70 minimum, likely $150+ with tier mix.

## Security and privacy considerations

- Don't store customer app data beyond what's in screenshots/reports
- Delete screenshots and crawl artifacts after 30 days
- Never log customer test credentials — pass to Playwright in memory only
- Use HTTPS everywhere
- API keys in `.env`, never committed
- Add a basic privacy policy at `/privacy`

## What to defer

- Test coverage above smoke tests
- Type checking (mypy / pyright)
- CI/CD beyond GitHub Actions
- Containerization (Docker)
- Observability (Sentry, etc.)
- Database migrations (no DB yet — Notion is the DB)
- Authentication system (no logins yet)
- Multi-tenancy (single-operator product)
