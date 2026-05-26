"""Form-submit smoke test runner (q15).

Reuses the Playwright capture pattern (q14 + q16) to:

1. Detect ``<form>`` elements on the customer's homepage.
2. Skip anything that looks like checkout / payment / destructive
   actions (so we never accidentally place a real order or delete
   real data).
3. Fill each remaining form with safe synthetic values (the
   LaunchLook smoke-test fixtures, so the customer can spot the rows
   in their inbox or database).
4. Submit and observe the response: redirect, thank-you text, error
   toast, or silent no-op.
5. Flag forms that silently fail, error on valid input, lose state,
   or never confirm. Plain-English findings only (per
   ``docs/SIMPLICITY-GUARDRAILS.md`` section 6 the buyer-facing name
   for the category is "form & signup flows"; the strings
   "form-submit smoke test", "synthetic values", and "round-trip"
   never cross to the customer).
6. Optional Pro-tier email round-trip via
   ``scripts/ai_audit/disposable_mailbox.py``: poll for a
   confirmation email for up to 60 seconds, flag silently broken
   signup flows where nothing ever arrives.

Tier cap (same shape as q14 + q16):

* Starter Package -- 1 finding (worst form).
* Scale Up Package -- up to 3.
* Pro Package -- all detected forms.

Per ``docs/SIMPLICITY-GUARDRAILS.md`` section 6 the runner never
emits internal taxonomy ("smoke test", "synthetic values") onto a
customer surface; the YAML's ``display_name_buyer`` ("form & signup
flows") and the persona tag ("Caught by The Stranger Who Tried to
Sign Up") are the only labels visitors see.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Callable

CATEGORY_ID = "form_submit_smoke"

# ---------------------------------------------------------------------------
# Synthetic values: safe, identifiable, NEVER real PII
# ---------------------------------------------------------------------------
#
# Every value should be obvious to a customer looking at their inbox or
# database -- it identifies itself as a LaunchLook smoke test row. The
# 555 phone area code is reserved for fiction; the launchlook.app email
# domain is ours; the company name spells "LaunchLook Smoke Test" out.

SYNTHETIC_VALUES: dict[str, str] = {
    "email": "stranger+launchlook-smoke-test@launchlook.app",
    "name": "LaunchLook Smoke Test (First-Time Visitor)",
    "first_name": "LaunchLook",
    "last_name": "Smoke-Test",
    "phone": "+15555550100",
    "company": "LaunchLook Smoke Test",
    "url": "https://launchlook.app/smoke-test",
    "website": "https://launchlook.app/smoke-test",
    "message": "LaunchLook smoke test: just trying the form to see what happens.",
    "comment": "LaunchLook smoke test: just trying the form to see what happens.",
    "subject": "LaunchLook smoke test",
    "password": "LaunchLook-SmokeTest-Do-Not-Login-2026!",
    "address": "1 LaunchLook Smoke Test Lane",
    "city": "Smoke Test",
    "zip": "00000",
    "postal_code": "00000",
    "default_text": "LaunchLook smoke test",
}


# Field-name keyword -> SYNTHETIC_VALUES key. The first match wins.
# Order matters: ``email`` must come before the ``name`` family.
_FIELD_TYPE_HINTS: list[tuple[str, str]] = [
    ("email", "email"),
    ("phone", "phone"),
    ("tel", "phone"),
    ("mobile", "phone"),
    ("company", "company"),
    ("organization", "company"),
    ("organisation", "company"),
    ("first", "first_name"),
    ("last", "last_name"),
    ("surname", "last_name"),
    ("fullname", "name"),
    ("full_name", "name"),
    ("name", "name"),
    ("website", "url"),
    ("url", "url"),
    ("address", "address"),
    ("street", "address"),
    ("city", "city"),
    ("zip", "zip"),
    ("postal", "postal_code"),
    ("subject", "subject"),
    ("message", "message"),
    ("comment", "comment"),
    ("note", "comment"),
    ("password", "password"),
    ("pwd", "password"),
    ("passwd", "password"),
]


# ---------------------------------------------------------------------------
# Safety guardrails (cite SIMPLICITY-GUARDRAILS section 6 in commit msg)
# ---------------------------------------------------------------------------
#
# Never submit anything that looks like a real-money or destructive
# action. The runner skips matches and surfaces a "we skipped this
# form on purpose" finding instead, so the customer knows the form
# was seen but not exercised.

# Tokens we treat as "looks like checkout/payment" in selectors, ids,
# field names, parent class lists, or form action URLs.
_PAYMENT_TOKENS: tuple[str, ...] = (
    "checkout",
    "payment",
    "pay-",
    "/pay",
    "stripe",
    "paypal",
    "card-number",
    "card_number",
    "cardnumber",
    "cc-number",
    "cc_number",
    "cvv",
    "cvc",
    "credit-card",
    "credit_card",
    "expiry",
    "exp-month",
    "exp_month",
    "card-cvc",
    "order-",
    "order_",
    "billing",
)

# Destructive labels we skip even if the form is otherwise harmless.
_DESTRUCTIVE_LABELS: tuple[str, ...] = (
    "delete",
    "remove",
    "destroy",
    "cancel subscription",
    "cancel my subscription",
    "unsubscribe",
    "unsubscribe me",
    "close my account",
    "deactivate",
    "wipe",
)

# Hard cap on forms submitted per audit (limits blast radius even if a
# customer happens to have many low-risk forms on a single page).
_MAX_FORMS_PER_AUDIT = 3


# ---------------------------------------------------------------------------
# Plain-English finding text (no jargon ever crosses to the customer)
# ---------------------------------------------------------------------------
#
# Per ``docs/SIMPLICITY-GUARDRAILS.md`` section 6 the strings
# "form-submit smoke test", "synthetic values", "round-trip" never
# appear here. The buyer-facing display name is "form & signup flows"
# and the finding voice is The Stranger's: bemused, patient, honest.

PLAIN_ENGLISH: dict[str, str] = {
    "no_response": (
        "I clicked Submit on your {form_name}. Nothing visibly happened: no "
        "confirmation message, no redirect, no error. I wasn't sure if it worked, "
        "and most first-time visitors won't try a second time."
    ),
    "missing_thank_you": (
        "After I submitted your {form_name}, the page didn't show a thank-you "
        "message or confirmation. I had no way to tell if my information went "
        "through, so I'd reasonably assume it didn't."
    ),
    "submit_button_inert": (
        "The submit button on your {form_name} didn't seem to fire when I clicked "
        "it. The button changed state briefly, then went back to normal. Real "
        "visitors will give up after one try."
    ),
    "validation_error": (
        "Your {form_name} rejected an input that looked valid ('{value}' for "
        "{field_name}). Strangers won't troubleshoot a form error; they'll just "
        "leave."
    ),
    "no_required_validation": (
        "Your {form_name} let me submit with all the fields empty. Either junk is "
        "going to your inbox, or strangers are getting confused when nothing "
        "happens after they click Submit on a blank form."
    ),
    "form_action_404": (
        "Your {form_name} sends submissions to {action_url}, which returns a 404. "
        "Anything visitors typed is being lost in mid-air."
    ),
    "checkout_skipped": (
        "I saw your {form_name} but didn't submit it on purpose: it looks like a "
        "checkout or payment form, and I don't want to place a real order. Worth "
        "running through it yourself with a Stripe test card to confirm it works."
    ),
    "destructive_skipped": (
        "I saw your {form_name} but didn't submit it on purpose: the button text "
        "('{label}') looked destructive (delete / cancel / unsubscribe). Worth "
        "confirming it works on a test account when you get a moment."
    ),
    "no_confirmation_email": (
        "I submitted your {form_name} with a real test email address and waited "
        "60 seconds. No confirmation email arrived. If your flow is supposed to "
        "send a welcome or verification email, it's silently broken right now."
    ),
}


# ---------------------------------------------------------------------------
# Builder-specific fix prompts (same shape as q14 + q16, deterministic)
# ---------------------------------------------------------------------------
#
# Keyed by (failure type, platform). Platforms beyond "generic" fall
# through to the generic prompt when a specific one is missing.

_FIX_PROMPT_LIBRARY: dict[tuple[str, str], str] = {
    ("no_response", "lovable"): (
        "Open Lovable and ask it: \"Find the submit handler for {form_name}. Add a "
        "visible success state: either swap the button to a checkmark, show a "
        "confirmation message above the form, or redirect to /thank-you. Wrap the "
        "submit call in try/catch so server errors surface as a clear toast.\""
    ),
    ("no_response", "bolt"): (
        "Open your project in Bolt. Ask Bolt: \"Audit the submit handler on "
        "{form_name}. Add a visible success path (confirmation message, toast, or "
        "redirect to /thank-you) and a visible error path (clear error toast) so "
        "the user is never left guessing.\""
    ),
    ("no_response", "v0"): (
        "Open the form component in v0. Ask v0: \"Add a useState success flag to "
        "the submit handler. Render a confirmation message when success is true, "
        "render an error message when an exception is thrown, and disable the "
        "submit button while pending.\""
    ),
    ("no_response", "cursor"): (
        "In Cursor, open the submit handler for {form_name}. Add a useState success "
        "flag and render a visible confirmation block on success. Wrap the submit "
        "call in try/catch and show an error toast on failure."
    ),
    ("no_response", "webflow"): (
        "Open Webflow Designer. Select the form element for {form_name} and open "
        "Settings. Configure the 'Success state' (the Form Success element) with a "
        "visible 'Thanks, we got it!' message. Test by submitting once."
    ),
    ("no_response", "generic"): (
        "After submitting {form_name}, the page needs to confirm the action: a "
        "thank-you message, a redirect, or a clear inline confirmation. Add one "
        "visible success path and one visible error path so visitors are never left "
        "guessing whether the submit worked."
    ),
    ("missing_thank_you", "lovable"): (
        "Open Lovable and ask it: \"After the {form_name} submit succeeds, show a "
        "thank-you message above the form (or redirect to /thank-you). Real "
        "visitors need a visible confirmation, not just a quiet network 200.\""
    ),
    ("missing_thank_you", "bolt"): (
        "Open your project in Bolt. Ask Bolt: \"Add a post-submit thank-you state "
        "to {form_name}: either render a 'Thanks, we got it!' div in place of the "
        "form, or route to a /thank-you page.\""
    ),
    ("missing_thank_you", "v0"): (
        "Open the form component in v0. Ask v0: \"After a successful submit, "
        "replace the form with a small 'Thanks, we got it!' card. Keep the same "
        "visual width so the page doesn't reflow.\""
    ),
    ("missing_thank_you", "cursor"): (
        "In Cursor, open the form component for {form_name}. After a successful "
        "submit, conditionally render a 'Thanks, we got it!' block in place of "
        "the form (or push to /thank-you)."
    ),
    ("missing_thank_you", "webflow"): (
        "Open Webflow Designer. Add an Interaction on the {form_name} form "
        "element: 'After form submit, show element' and point it at a "
        "'Thanks, we got it!' div placed near the form. Test in Preview."
    ),
    ("missing_thank_you", "generic"): (
        "After a successful submit on {form_name}, show a clear thank-you message "
        "in place of the form (or redirect to a /thank-you page). The visitor "
        "should never have to guess whether the submission landed."
    ),
    ("submit_button_inert", "lovable"): (
        "Open Lovable and ask it: \"Check the onClick / onSubmit handler for "
        "{form_name}. Make sure the form actually calls the submit endpoint, and "
        "that the click handler isn't being swallowed by a wrapping element.\""
    ),
    ("submit_button_inert", "generic"): (
        "The submit button on {form_name} appears to do nothing. Confirm the "
        "button is wired to the form's submit handler, that the handler actually "
        "calls your backend endpoint, and that nothing else on the page is "
        "swallowing the click."
    ),
    ("no_required_validation", "lovable"): (
        "Open Lovable and ask it: \"Add a required attribute to every essential "
        "input on {form_name} and show a clear validation message if the user "
        "submits with an empty required field.\""
    ),
    ("no_required_validation", "generic"): (
        "Add HTML5 `required` (or framework-level required validation) to every "
        "essential input on {form_name}, and show a clear inline message when a "
        "visitor tries to submit an empty form."
    ),
    ("form_action_404", "lovable"): (
        "Open Lovable and ask it: \"The {form_name} form posts to {action_url}, "
        "which returns 404. Wire the form to a real backend route or service "
        "(Lovable Functions, your own API, a form-handler like Formspree).\""
    ),
    ("form_action_404", "generic"): (
        "{form_name} is posting to {action_url}, which 404s. Wire the form to a "
        "real endpoint (your backend, a serverless function, or a form-handler "
        "like Formspree) and verify a test submission lands somewhere you can "
        "read."
    ),
    ("validation_error", "lovable"): (
        "Open Lovable and ask it: \"Loosen the validation on '{field_name}' in "
        "{form_name}. Right now valid-looking input is being rejected, which "
        "means real visitors can't submit. Show what input is expected if you "
        "have a specific format requirement.\""
    ),
    ("validation_error", "generic"): (
        "The {field_name} field on {form_name} rejects valid-looking input. Loosen "
        "the validation rule, or surface a clear hint about the exact format you "
        "expect (e.g. 'must include country code') before the visitor types."
    ),
    ("checkout_skipped", "generic"): (
        "We skipped this form on purpose so we wouldn't place a real order. Run "
        "your full checkout with a Stripe test card (4242 4242 4242 4242) on a "
        "staging URL, and confirm the order shows up in your dashboard with the "
        "correct line items and amount."
    ),
    ("destructive_skipped", "generic"): (
        "We skipped this form on purpose so we wouldn't delete real data. Run the "
        "flow yourself on a test account and confirm it does the right thing "
        "(and ideally surfaces a 'are you sure?' confirmation step)."
    ),
    ("no_confirmation_email", "lovable"): (
        "Open Lovable and ask it: \"After {form_name} submits successfully, send "
        "a confirmation email via Resend (or your configured email service). "
        "Verify the sending domain so emails don't land in spam.\""
    ),
    ("no_confirmation_email", "generic"): (
        "After {form_name} succeeds, send a confirmation email (welcome, "
        "verification, or a simple 'we got your message'). Verify your sending "
        "domain (SPF / DKIM / DMARC) so the email actually lands in real inboxes."
    ),
}


def _fix_prompt_for(failure: str, platform: str, *, form_name: str, **fmt: Any) -> str:
    key = (failure, (platform or "generic").lower())
    template = _FIX_PROMPT_LIBRARY.get(key) or _FIX_PROMPT_LIBRARY[(failure, "generic")]
    fmt.setdefault("form_name", form_name)
    fmt.setdefault("action_url", fmt.get("action_url") or "(unknown)")
    fmt.setdefault("field_name", fmt.get("field_name") or "the field")
    try:
        return template.format(**fmt)
    except KeyError:
        return template


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _looks_like_payment(blob: str) -> bool:
    """Return True if *blob* (a lowercased haystack) looks payment-related."""
    if not blob:
        return False
    needle = blob.lower()
    return any(token in needle for token in _PAYMENT_TOKENS)


def _looks_destructive(label: str) -> bool:
    if not label:
        return False
    needle = label.lower()
    return any(token in needle for token in _DESTRUCTIVE_LABELS)


def _synthetic_value_for(field: dict[str, Any]) -> tuple[str, str]:
    """Return (synthetic_value, hint_key) for one detected field.

    Match order: input type=email / tel / password win first, then we
    fall back to keyword hints in the name / id / placeholder / label.
    """

    type_ = (field.get("type") or "").strip().lower()
    if type_ == "email":
        return SYNTHETIC_VALUES["email"], "email"
    if type_ in {"tel", "phone"}:
        return SYNTHETIC_VALUES["phone"], "phone"
    if type_ == "password":
        return SYNTHETIC_VALUES["password"], "password"
    if type_ == "url":
        return SYNTHETIC_VALUES["url"], "url"
    if type_ == "number":
        return "1", "default_text"

    haystack_parts = [
        field.get("name") or "",
        field.get("id") or "",
        field.get("placeholder") or "",
        field.get("label") or "",
        field.get("autocomplete") or "",
    ]
    haystack = " ".join(haystack_parts).lower()
    for keyword, key in _FIELD_TYPE_HINTS:
        if keyword in haystack:
            return SYNTHETIC_VALUES[key], key

    return SYNTHETIC_VALUES["default_text"], "default_text"


def _form_display_name(form_info: dict[str, Any]) -> str:
    """Pick the friendliest label for the form in finding copy."""
    name = (
        form_info.get("name")
        or form_info.get("label")
        or form_info.get("submit_label")
        or form_info.get("id")
        or "signup form"
    )
    return str(name).strip() or "signup form"


def _is_blocked_selector(selector: str, blocked: list[str]) -> bool:
    if not selector:
        return False
    return any(b.strip() and b.strip() in selector for b in (blocked or []))


def _tier_cap(tier: str) -> int:
    t = (tier or "").strip().lower()
    if t in {"pro", "pro package"}:
        return 99
    if t in {"scale up", "scale up package", "scaleup", "scale-up"}:
        return 3
    return 1


def _captures_email(form_info: dict[str, Any]) -> bool:
    for f in form_info.get("fields") or []:
        if (f.get("type") or "").lower() == "email":
            return True
        for hay in (f.get("name"), f.get("id"), f.get("placeholder"), f.get("autocomplete")):
            if hay and "email" in str(hay).lower():
                return True
    return False


def _severity_for(failure: str, captures_email: bool) -> str:
    if failure in {"form_action_404", "no_response", "submit_button_inert"}:
        return "high"
    if failure == "no_confirmation_email":
        return "high" if captures_email else "medium"
    if failure in {"missing_thank_you", "validation_error", "no_required_validation"}:
        return "medium"
    return "medium"


def _why_it_matters(captures_email: bool) -> str:
    if captures_email:
        return (
            "If a form on your homepage doesn't confirm what just happened, the "
            "visitor assumes it didn't work, leaves, and never comes back. Forms "
            "that capture email are typically the top of your funnel; one quiet "
            "failure here propagates downstream into everything else."
        )
    return (
        "Forms are where first-time visitors decide whether your site does what "
        "it says. A silent failure on the homepage form is the single fastest way "
        "to lose an otherwise interested visitor."
    )


# ---------------------------------------------------------------------------
# Detection (the only async part needs Playwright)
# ---------------------------------------------------------------------------

_DETECT_FORMS_JS = r"""
() => {
    const forms = [];
    const seen = new WeakSet();
    document.querySelectorAll('form').forEach((form, idx) => {
        if (seen.has(form)) return;
        seen.add(form);
        const fields = [];
        form.querySelectorAll('input, textarea, select').forEach((el) => {
            const type = (el.getAttribute('type') || el.tagName).toLowerCase();
            if (type === 'hidden' || type === 'submit' || type === 'button' || type === 'reset' || type === 'image') return;
            const id = el.id || '';
            let labelText = '';
            if (id) {
                const lab = document.querySelector(`label[for="${CSS.escape(id)}"]`);
                if (lab) labelText = (lab.textContent || '').trim();
            }
            if (!labelText) {
                const parentLabel = el.closest('label');
                if (parentLabel) labelText = (parentLabel.textContent || '').trim();
            }
            fields.push({
                tag: el.tagName.toLowerCase(),
                type,
                name: el.getAttribute('name') || '',
                id,
                placeholder: el.getAttribute('placeholder') || '',
                autocomplete: el.getAttribute('autocomplete') || '',
                required: el.hasAttribute('required') || el.required === true,
                label: labelText.slice(0, 120),
            });
        });
        const submit = form.querySelector('button[type=submit], input[type=submit], button:not([type])');
        const submitLabel = submit ? (submit.value || submit.textContent || '').trim() : '';
        const ariaLabel = form.getAttribute('aria-label') || '';
        const name = form.getAttribute('name') || ariaLabel || '';
        let parentClasses = '';
        let p = form.parentElement;
        while (p && parentClasses.length < 300) {
            parentClasses += ' ' + (p.className || '') + ' ' + (p.id || '');
            p = p.parentElement;
        }
        forms.push({
            index: idx,
            selector: form.id ? `#${form.id}` : `form:nth-of-type(${idx + 1})`,
            id: form.id || '',
            name: name.trim(),
            action: form.getAttribute('action') || '',
            method: (form.getAttribute('method') || 'get').toLowerCase(),
            submit_label: submitLabel.slice(0, 120),
            field_count: fields.length,
            fields,
            parent_haystack: parentClasses.trim(),
        });
    });
    return forms;
};
"""


async def detect_forms(page: Any) -> list[dict[str, Any]]:
    """Return a list of form-info dicts for every ``<form>`` on the page."""
    return await page.evaluate(_DETECT_FORMS_JS)


# ---------------------------------------------------------------------------
# Skip-decision: payment / destructive forms get a finding but never a fill
# ---------------------------------------------------------------------------


def _skip_reason(form_info: dict[str, Any]) -> str | None:
    """Return a skip key (matching PLAIN_ENGLISH) or None to proceed."""
    blob_parts = [
        form_info.get("selector") or "",
        form_info.get("id") or "",
        form_info.get("name") or "",
        form_info.get("action") or "",
        form_info.get("submit_label") or "",
        form_info.get("parent_haystack") or "",
    ]
    for f in form_info.get("fields") or []:
        blob_parts.append(f.get("name") or "")
        blob_parts.append(f.get("id") or "")
        blob_parts.append(f.get("autocomplete") or "")
        blob_parts.append(f.get("type") or "")
    blob = " ".join(blob_parts)
    if _looks_like_payment(blob):
        return "checkout_skipped"
    label = form_info.get("submit_label") or ""
    if _looks_destructive(label):
        return "destructive_skipped"
    return None


# ---------------------------------------------------------------------------
# Fill / submit / observe (Playwright)
# ---------------------------------------------------------------------------


async def fill_form(page: Any, form_info: dict[str, Any]) -> dict[str, str]:
    """Fill detected text-like fields with synthetic values.

    Returns a ``{name_or_id: synthetic_value}`` map so the observer can
    quote the field back in any validation-error finding without
    leaking PII.
    """
    filled: dict[str, str] = {}
    selector = form_info.get("selector") or "form"
    for field in form_info.get("fields") or []:
        tag = (field.get("tag") or "").lower()
        ftype = (field.get("type") or "").lower()
        if ftype in {"hidden", "submit", "button", "reset", "image", "file"}:
            continue
        if tag == "select":
            continue
        if ftype in {"checkbox", "radio"}:
            continue
        value, _ = _synthetic_value_for(field)
        ident = field.get("id") or field.get("name") or ""
        if not ident:
            continue
        target_selector = (
            f'{selector} [id="{ident}"]'
            if field.get("id")
            else f'{selector} [name="{ident}"]'
        )
        try:
            await page.fill(target_selector, value, timeout=2_000)
            filled[ident] = value
        except Exception:  # noqa: BLE001
            continue
    return filled


async def submit_and_observe(
    page: Any,
    form_info: dict[str, Any],
    *,
    timeout_ms: int = 8_000,
) -> dict[str, Any]:
    """Submit the form and watch for a success / error signal."""
    selector = form_info.get("selector") or "form"
    submit_selector = (
        f"{selector} button[type=submit], "
        f"{selector} input[type=submit], "
        f"{selector} button:not([type])"
    )
    start_url = page.url

    action_url = form_info.get("action") or ""
    captured_status: dict[str, int] = {}

    async def _on_response(resp: Any) -> None:
        try:
            if action_url and action_url in resp.url:
                captured_status[resp.url] = resp.status
        except Exception:  # noqa: BLE001
            pass

    page.on("response", _on_response)
    try:
        try:
            await page.click(submit_selector, timeout=2_500)
        except Exception:  # noqa: BLE001
            return {
                "outcome": "submit_button_inert",
                "detail": "submit button could not be clicked",
            }

        await page.wait_for_timeout(timeout_ms)

        for url, status in captured_status.items():
            if status == 404:
                return {
                    "outcome": "form_action_404",
                    "detail": f"action {url} returned 404",
                    "action_url": url,
                }

        body_text = ""
        try:
            body_text = (await page.inner_text("body")) or ""
        except Exception:  # noqa: BLE001
            body_text = ""

        lower = body_text.lower()

        if page.url != start_url and "thank" in lower:
            return {"outcome": "ok", "detail": f"redirected to {page.url}"}
        if page.url != start_url:
            return {"outcome": "ok", "detail": f"redirected to {page.url}"}

        positive_markers = (
            "thank you",
            "thanks!",
            "we got it",
            "check your email",
            "we'll be in touch",
            "subscribed",
            "submission received",
            "we received",
            "success",
            "confirmed",
        )
        if any(m in lower for m in positive_markers):
            return {"outcome": "ok", "detail": "thank-you marker on page"}

        validation_markers = (
            "is required",
            "is invalid",
            "please enter a valid",
            "must be a valid",
            "invalid email",
            "error",
        )
        if any(m in lower for m in validation_markers):
            return {
                "outcome": "validation_error",
                "detail": "validation-style text on page after submit",
                "field_name": "the email or required field",
                "value": SYNTHETIC_VALUES["email"],
            }

        try:
            still_visible = await page.is_visible(selector)
        except Exception:  # noqa: BLE001
            still_visible = True

        if still_visible:
            return {
                "outcome": "no_response",
                "detail": "form still on page with no visible confirmation",
            }
        return {
            "outcome": "missing_thank_you",
            "detail": "form disappeared but no confirmation rendered",
        }
    finally:
        try:
            page.remove_listener("response", _on_response)
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------


_DEFAULT_CACHE_TTL_SECONDS = 24 * 60 * 60
_CACHE_DIR = Path("data/form_smoke_cache")


def _cache_key(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def _cache_path(key: str) -> Path:
    return _CACHE_DIR / f"{key}.json"


def _cache_ttl_seconds() -> int:
    raw = os.environ.get("FORM_SMOKE_CACHE_TTL_SECONDS")
    if not raw:
        return _DEFAULT_CACHE_TTL_SECONDS
    try:
        return max(0, int(raw))
    except ValueError:
        return _DEFAULT_CACHE_TTL_SECONDS


def _read_cache(key: str) -> list[dict[str, Any]] | None:
    path = _cache_path(key)
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if age > _cache_ttl_seconds():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_cache(key: str, payload: list[dict[str, Any]]) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(key).write_text(json.dumps(payload), encoding="utf-8")


async def _run_smoke_test_async(
    url: str,
    *,
    blocked_selectors: list[str],
) -> list[dict[str, Any]]:
    """Drive Playwright through detect -> fill -> submit -> observe."""
    from playwright.async_api import async_playwright  # local import: optional dep

    results: list[dict[str, Any]] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle", timeout=45_000)
            forms = await detect_forms(page)

            considered = 0
            for form_info in forms:
                selector = form_info.get("selector") or ""
                if _is_blocked_selector(selector, blocked_selectors):
                    continue

                skip = _skip_reason(form_info)
                if skip:
                    results.append(
                        {
                            "form": form_info,
                            "outcome": skip,
                            "detail": "skipped intentionally",
                            "label": form_info.get("submit_label") or "",
                        }
                    )
                    continue

                if considered >= _MAX_FORMS_PER_AUDIT:
                    break
                considered += 1

                if considered > 1:
                    await page.goto(url, wait_until="networkidle", timeout=45_000)
                    forms_fresh = await detect_forms(page)
                    if len(forms_fresh) > form_info["index"]:
                        form_info = forms_fresh[form_info["index"]]

                filled = await fill_form(page, form_info)
                observation = await submit_and_observe(page, form_info)

                if observation.get("outcome") == "ok":
                    results.append(
                        {
                            "form": form_info,
                            "outcome": "ok",
                            "detail": observation.get("detail", ""),
                            "filled": filled,
                        }
                    )
                    continue

                results.append(
                    {
                        "form": form_info,
                        "outcome": observation["outcome"],
                        "detail": observation.get("detail", ""),
                        "filled": filled,
                        "action_url": observation.get("action_url"),
                        "field_name": observation.get("field_name"),
                        "value": observation.get("value"),
                    }
                )
        finally:
            await browser.close()
    return results


def run_form_smoke_test_raw(
    url: str,
    *,
    blocked_selectors: list[str] | None = None,
    use_cache: bool = True,
) -> list[dict[str, Any]] | None:
    """Run Playwright; return raw per-form observations or None on failure."""
    blocked = list(blocked_selectors or [])
    key = _cache_key(url + "|" + ",".join(sorted(blocked)))
    if use_cache:
        cached = _read_cache(key)
        if cached is not None:
            return cached
    try:
        results = asyncio.run(_run_smoke_test_async(url, blocked_selectors=blocked))
    except Exception:  # noqa: BLE001
        return None
    if use_cache and results is not None:
        _write_cache(key, results)
    return results


# ---------------------------------------------------------------------------
# Translation to finding dicts
# ---------------------------------------------------------------------------


def _check_id(form_info: dict[str, Any], outcome: str) -> str:
    raw_id = (form_info.get("id") or form_info.get("name") or form_info.get("selector") or "form")
    safe = re.sub(r"[^a-z0-9]+", "-", raw_id.lower()).strip("-") or "form"
    return f"form_submit_smoke.{safe}.{outcome}"


_OUTCOME_TITLES: dict[str, str] = {
    "no_response": "Your {form_name} doesn't confirm anything after submit",
    "missing_thank_you": "Your {form_name} doesn't show a thank-you message after submit",
    "submit_button_inert": "Your {form_name} submit button doesn't seem to fire",
    "validation_error": "Your {form_name} rejects valid-looking input on {field_name}",
    "no_required_validation": "Your {form_name} accepts a fully empty submit",
    "form_action_404": "Your {form_name} sends submissions to a URL that 404s",
    "checkout_skipped": "We saw your {form_name} but didn't submit it",
    "destructive_skipped": "We saw your {form_name} but didn't submit it",
    "no_confirmation_email": "Your {form_name} didn't send a confirmation email",
}


def to_findings(
    raw_results: list[dict[str, Any]],
    *,
    tier: str,
    platform: str,
    email_roundtrip: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Translate raw runner output to the standard finding-dict shape.

    Tier-cap is applied after skipped-form findings (which always
    surface so the customer knows we saw the form on purpose).
    """
    passed_ids: list[str] = []
    failed_ids: list[str] = []

    sev_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}

    actionable: list[dict[str, Any]] = []
    skipped_findings: list[dict[str, Any]] = []

    for r in raw_results or []:
        form_info = r.get("form") or {}
        form_name = _form_display_name(form_info)
        outcome = r.get("outcome") or "no_response"
        captures_email = _captures_email(form_info)

        if outcome == "ok":
            passed_ids.append(_check_id(form_info, "ok"))
            continue

        title_template = _OUTCOME_TITLES.get(outcome, _OUTCOME_TITLES["no_response"])
        title = title_template.format(
            form_name=form_name,
            field_name=r.get("field_name") or "the field",
        )

        if outcome in {"checkout_skipped", "destructive_skipped"}:
            description = PLAIN_ENGLISH[outcome].format(
                form_name=form_name,
                label=r.get("label") or "",
            )
            why = (
                "We surface skipped forms on purpose so you know we saw them. "
                "The point is to avoid placing a real order or deleting real "
                "data during the audit; you should run the flow yourself on a "
                "test account or with a test card to confirm it works."
            )
            severity = "low"
            fix_prompt = _fix_prompt_for(outcome, platform, form_name=form_name)
            check_id = _check_id(form_info, outcome)
            skipped_findings.append(
                {
                    "id": check_id,
                    "category": CATEGORY_ID,
                    "title": title,
                    "severity": severity,
                    "what_we_saw": description,
                    "why_it_matters": why,
                    "fix_prompt": fix_prompt,
                    "tester": "The Stranger Who Tried to Sign Up",
                    "tag": "Caught by The Stranger Who Tried to Sign Up",
                    "source": "external",
                    "external_origin": "form_smoke_test",
                    "skipped": True,
                }
            )
            failed_ids.append(check_id)
            continue

        description = PLAIN_ENGLISH[outcome].format(
            form_name=form_name,
            field_name=r.get("field_name") or "the field",
            value=r.get("value") or SYNTHETIC_VALUES["email"],
            action_url=r.get("action_url") or "(unknown)",
        )
        severity = _severity_for(outcome, captures_email)
        fix_prompt = _fix_prompt_for(
            outcome,
            platform,
            form_name=form_name,
            field_name=r.get("field_name") or "the field",
            action_url=r.get("action_url") or "(unknown)",
        )
        check_id = _check_id(form_info, outcome)
        actionable.append(
            {
                "id": check_id,
                "category": CATEGORY_ID,
                "title": title,
                "severity": severity,
                "what_we_saw": description,
                "why_it_matters": _why_it_matters(captures_email),
                "fix_prompt": fix_prompt,
                "tester": "The Stranger Who Tried to Sign Up",
                "tag": "Caught by The Stranger Who Tried to Sign Up",
                "source": "external",
                "external_origin": "form_smoke_test",
            }
        )
        failed_ids.append(check_id)

    for entry in email_roundtrip or []:
        if entry.get("arrived"):
            passed_ids.append(_check_id(entry.get("form") or {}, "email_arrived"))
            continue
        form_info = entry.get("form") or {}
        form_name = _form_display_name(form_info)
        description = PLAIN_ENGLISH["no_confirmation_email"].format(form_name=form_name)
        fix_prompt = _fix_prompt_for("no_confirmation_email", platform, form_name=form_name)
        check_id = _check_id(form_info, "no_confirmation_email")
        actionable.append(
            {
                "id": check_id,
                "category": CATEGORY_ID,
                "title": _OUTCOME_TITLES["no_confirmation_email"].format(form_name=form_name),
                "severity": "high",
                "what_we_saw": description,
                "why_it_matters": _why_it_matters(True),
                "fix_prompt": fix_prompt,
                "tester": "The Stranger Who Tried to Sign Up",
                "tag": "Caught by The Stranger Who Tried to Sign Up",
                "source": "external",
                "external_origin": "form_smoke_test",
            }
        )
        failed_ids.append(check_id)

    actionable.sort(key=lambda f: -sev_rank.get((f.get("severity") or "").lower(), 0))
    cap = _tier_cap(tier)
    capped = actionable[:cap]

    findings = capped + skipped_findings

    return {
        "findings": findings,
        "passed_check_ids": passed_ids,
        "failed_check_ids": failed_ids,
    }


# ---------------------------------------------------------------------------
# Public entry point (matches the q14 + q16 contract)
# ---------------------------------------------------------------------------


def run_form_smoke_test(
    *,
    base_url: str,
    tier: str,
    platform: str = "generic",
    customer_email: str | None = None,
    blocked_selectors: list[str] | None = None,
    use_cache: bool = True,
    email_roundtrip: Callable[..., list[dict[str, Any]]] | None = None,
    enabled: bool = True,
) -> dict[str, Any]:
    """Run the form-smoke-test against ``base_url`` and translate the result.

    Returns the standard external-runner contract dict::

        {
          "findings": list[dict],
          "passed_check_ids": list[str],
          "failed_check_ids": list[str],
          "ran": bool,
        }

    When Playwright is unavailable, the customer opted out, or the page
    can't be loaded, ``ran`` is False, findings is empty, and
    passed_check_ids is empty (we don't claim "forms work" if we never
    submitted any).
    """
    if not enabled:
        return {
            "findings": [],
            "passed_check_ids": [],
            "failed_check_ids": [],
            "ran": False,
            "skipped_reason": "opt_out",
        }

    raw = run_form_smoke_test_raw(
        base_url,
        blocked_selectors=blocked_selectors,
        use_cache=use_cache,
    )
    if raw is None:
        return {
            "findings": [],
            "passed_check_ids": [],
            "failed_check_ids": [],
            "ran": False,
        }

    email_results: list[dict[str, Any]] = []
    if (tier or "").strip().lower() in {"pro", "pro package"} and email_roundtrip is not None:
        try:
            email_results = email_roundtrip(raw_results=raw, customer_email=customer_email) or []
        except Exception:  # noqa: BLE001
            email_results = []

    translated = to_findings(
        raw,
        tier=tier,
        platform=platform,
        email_roundtrip=email_results,
    )
    translated["ran"] = True
    return translated


# ---------------------------------------------------------------------------
# Default email round-trip wiring (Pro tier only)
# ---------------------------------------------------------------------------


def default_email_roundtrip(
    *,
    raw_results: list[dict[str, Any]],
    customer_email: str | None = None,
    poll_seconds: int = 60,
) -> list[dict[str, Any]]:
    """Poll a disposable mailbox for any form that captured an email.

    Falls back silently (empty list) when the disposable mailbox API
    is unreachable or the optional dependency is missing -- per the
    task spec, we never block on email-roundtrip checks.
    """
    try:
        from . import disposable_mailbox  # local import: optional dep
    except Exception:  # noqa: BLE001
        return []

    out: list[dict[str, Any]] = []
    for r in raw_results or []:
        form_info = r.get("form") or {}
        if not _captures_email(form_info):
            continue
        if r.get("outcome") in {"checkout_skipped", "destructive_skipped"}:
            continue
        try:
            arrived = disposable_mailbox.wait_for_message(
                address=SYNTHETIC_VALUES["email"],
                poll_seconds=poll_seconds,
            )
        except Exception:  # noqa: BLE001
            arrived = False
        out.append({"form": form_info, "arrived": bool(arrived)})
    return out
