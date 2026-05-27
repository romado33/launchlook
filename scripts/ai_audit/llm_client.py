"""Provider-agnostic LLM client for the AI audit pipeline.

Supports three backends, all returning the same Python-shaped responses:

* ``ClaudeClient`` (Anthropic) — default when ``ANTHROPIC_API_KEY`` is set.
  Uses tool-use with a JSON schema to coerce structured output.
* ``GPTClient`` (OpenAI) — fallback when ``OPENAI_API_KEY`` is set. Uses
  ``response_format={"type":"json_schema",...}`` (vision-capable model
  required: gpt-4o, gpt-4o-mini, or gpt-5-mini).
* ``StubClient`` — offline mode. Generates deterministic placeholder
  findings from the prescreener hits so the rest of the pipeline can be
  exercised without an API key. Used by tests and for smoke checks.

Vision: each finding-generation call receives ``screenshots`` as a list of
``(label, path_to_png)`` tuples. Both real providers send the PNGs as
multimodal input. The stub ignores them.

Structured output: we declare a single ``Audit`` schema that wraps the
findings list, plus a separate ``Verdict`` schema and ``QSG`` schema. The
schemas are deliberately small so they slot into either Anthropic's
``input_schema`` or OpenAI's ``json_schema`` without translation.

The client returns plain Python dicts. The pipeline owns YAML emission.
"""

from __future__ import annotations

import base64
import json
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from . import cost_tracker

# ---------------------------------------------------------------------------
# Default model names (override via env var)
# ---------------------------------------------------------------------------

DEFAULT_CLAUDE_MODEL = os.getenv("LAUNCHLOOK_CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
DEFAULT_CLAUDE_FALLBACKS = [
    "claude-sonnet-4-5-20250929",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-latest",
]
DEFAULT_GPT_MODEL = os.getenv("LAUNCHLOOK_GPT_MODEL", "gpt-4o")
DEFAULT_GPT_FALLBACKS = ["gpt-4o", "gpt-4o-mini", "gpt-5-mini"]


# ---------------------------------------------------------------------------
# Structured-output schemas (provider-agnostic)
# ---------------------------------------------------------------------------


FINDING_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    # OpenAI strict mode requires every property key to be in required.
    # screenshot_caption is optional in meaning but must be listed here;
    # pass "" when the model has nothing to say about it.
    "required": [
        "severity",
        "title",
        "what_we_saw",
        "why_it_matters",
        "screenshot_caption",
        "fix_prompt",
        "category",
        "tag",
    ],
    "properties": {
        "severity": {
            "type": "string",
            "enum": ["critical", "high", "medium", "low"],
            "description": "Severity bucket per the LaunchLook definitions.",
        },
        "title": {
            "type": "string",
            "description": "Short, scannable title that names the visible problem.",
        },
        "what_we_saw": {
            "type": "string",
            "description": (
                "1-3 sentences. Quote the exact visible label, route, "
                "or element. Reference desktop/mobile when relevant."
            ),
        },
        "why_it_matters": {
            "type": "string",
            "description": (
                "1-2 sentences. What it costs the founder: trust, "
                "conversions, launch readiness, exposure."
            ),
        },
        "screenshot_caption": {
            "type": "string",
            "description": "Optional. 1 sentence describing what to look at.",
        },
        "fix_prompt": {
            "type": "string",
            "description": (
                "Paste-ready directive for the customer's builder chat. "
                "Imperative voice. Names specific routes/copy."
            ),
        },
        "category": {
            "type": "string",
            "description": (
                "The ``id`` of the finding category from the data-driven "
                "list in scripts/ai_audit/finding_categories.yaml. "
                "Lowercase snake_case (e.g. 'trust_gaps', 'mobile_layout')."
            ),
        },
        "tag": {
            "type": "string",
            "description": (
                "Persona tag in the form 'Caught by The {Persona}'. Must "
                "match the ``tester:`` field on the chosen category. See "
                "docs/TESTERS-CAST.md for the 7 canonical personas."
            ),
        },
    },
}

AUDIT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["findings"],
    "properties": {
        "findings": {
            "type": "array",
            "items": FINDING_SCHEMA,
        },
    },
}

VERDICT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    # ``label`` is the canonical 4-value vocabulary documented in
    # scripts/ai_audit/prompts/verdict_generation.txt. Pipeline normalizes
    # any drift back to one of these four before the YAML is written.
    "required": ["label", "emoji", "summary", "narrative"],
    "properties": {
        "label": {
            "type": "string",
            "enum": [
                "Ready to share",
                "Safe for friends/family testing",
                "Needs fixes before launch",
                "Do not invite real users yet",
            ],
        },
        "emoji": {"type": "string", "enum": ["🟢", "🟡", "🔴"]},
        "summary": {"type": "string"},
        "narrative": {"type": "string"},
    },
}

QSG_STEP_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["title", "body"],
    "properties": {
        "title": {"type": "string"},
        "body": {"type": "string"},
    },
}

QSG_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["title", "intro", "steps", "footer_note"],
    "properties": {
        "title": {"type": "string"},
        "intro": {"type": "string"},
        "steps": {"type": "array", "items": QSG_STEP_SCHEMA, "minItems": 1},
        "footer_note": {"type": "string"},
    },
}

# Handoff Report narrative sections (q18). One free-text field per call so
# context_paragraph / recommended_order / code_review_notes can iterate
# their prompts independently. See scripts/ai_audit/prompts/handoff_*.txt.
HANDOFF_TEXT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["text"],
    "properties": {
        "text": {"type": "string", "minLength": 1},
    },
}


# ---------------------------------------------------------------------------
# Base client
# ---------------------------------------------------------------------------


class LLMClient(ABC):
    """Abstract LLM client used by the audit pipeline.

    Each method returns a ``dict`` already shaped like the equivalent slice
    of the customer YAML. The pipeline owns sorting, capping, and YAML
    emission.
    """

    name: str = "abstract"
    model: str = ""

    @abstractmethod
    def generate_findings(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        screenshots: list[tuple[str, Path]],
        max_findings: int,
    ) -> list[dict[str, Any]]:
        """Return a list of finding dicts matching ``FINDING_SCHEMA``."""

    @abstractmethod
    def generate_verdict(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        """Return ``{label, emoji, summary, narrative}``.

        ``label`` is one of the four canonical values declared in
        ``VERDICT_SCHEMA``; the pipeline normalizes any drift before
        the YAML is written.
        """

    @abstractmethod
    def generate_qsg(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        screenshots: list[tuple[str, Path]],
    ) -> dict[str, Any]:
        """Return ``{title, intro, steps:[{title, body}...], footer_note}``."""

    @abstractmethod
    def generate_handoff_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        section: str,
    ) -> str:
        """Return one free-text paragraph for a Handoff Report section.

        ``section`` is a short slug like ``"context_paragraph"``,
        ``"recommended_order"`` or ``"code_review_notes"``. The pipeline
        uses it for the cost-tracker call type and for the stub fallback
        text. Screenshots are intentionally not passed: the handoff
        narrative is grounded in the already-generated findings, not in
        re-inspecting the site.
        """

    def regenerate_finding(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        screenshots: list[tuple[str, Path]],
    ) -> dict[str, Any]:
        """Generate a single replacement finding.

        Default implementation reuses ``generate_findings(max=1)`` and
        returns the first item. Providers can override for efficiency.
        """
        findings = self.generate_findings(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            screenshots=screenshots,
            max_findings=1,
        )
        if not findings:
            raise RuntimeError("Regeneration returned no finding")
        return findings[0]


# ---------------------------------------------------------------------------
# Helpers shared by both real providers
# ---------------------------------------------------------------------------


def _read_png_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def _coerce_findings_payload(payload: Any) -> list[dict[str, Any]]:
    """Accept either ``{"findings":[...]}`` or a bare list. Drop garbage."""
    if isinstance(payload, dict):
        findings = payload.get("findings", [])
    elif isinstance(payload, list):
        findings = payload
    else:
        findings = []
    cleaned: list[dict[str, Any]] = []
    for entry in findings:
        if not isinstance(entry, dict):
            continue
        sev = (entry.get("severity") or "").strip().lower()
        if sev not in {"critical", "high", "medium", "low"}:
            continue
        if not (entry.get("title") or "").strip():
            continue
        cleaned.append(
            {
                "severity": sev,
                "title": entry.get("title", "").strip(),
                "what_we_saw": (entry.get("what_we_saw") or "").strip(),
                "why_it_matters": (entry.get("why_it_matters") or "").strip(),
                "screenshot_caption": (entry.get("screenshot_caption") or "").strip(),
                "fix_prompt": (entry.get("fix_prompt") or "").strip(),
            }
        )
    return cleaned


# ---------------------------------------------------------------------------
# Claude (Anthropic)
# ---------------------------------------------------------------------------


class ClaudeClient(LLMClient):
    name = "claude"

    def __init__(self, *, api_key: str | None = None, model: str | None = None) -> None:
        try:
            import anthropic
        except ImportError:
            sys.exit(
                "ERROR: anthropic package not installed.\nRun: pip install -r requirements-ai.txt"
            )
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self._anthropic = anthropic
        self._client = anthropic.Anthropic(api_key=key)
        self.model = model or DEFAULT_CLAUDE_MODEL

    # ----------- internal helpers -----------

    def _build_content_blocks(
        self, user_prompt: str, screenshots: list[tuple[str, Path]]
    ) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        for label, path in screenshots:
            if not path.exists():
                continue
            blocks.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": _read_png_b64(path),
                    },
                }
            )
            blocks.append({"type": "text", "text": f"[{label}]"})
        blocks.append({"type": "text", "text": user_prompt})
        return blocks

    def _call_with_tool(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        screenshots: list[tuple[str, Path]],
        tool_name: str,
        tool_description: str,
        input_schema: dict[str, Any],
        call_type: str = "other",
    ) -> dict[str, Any]:
        tool = {
            "name": tool_name,
            "description": tool_description,
            "input_schema": input_schema,
        }
        content_blocks = self._build_content_blocks(user_prompt, screenshots)

        last_err: Exception | None = None
        candidates = [self.model] + [m for m in DEFAULT_CLAUDE_FALLBACKS if m != self.model]
        for candidate in candidates:
            try:
                with cost_tracker.track_call(call_type) as _tracker:
                    resp = self._client.messages.create(  # type: ignore[call-overload]  # anthropic SDK model arg is a Literal union; ours is a runtime str
                        model=candidate,
                        max_tokens=8000,
                        system=system_prompt,
                        messages=[{"role": "user", "content": content_blocks}],
                        tools=[tool],
                        tool_choice={"type": "tool", "name": tool_name},
                    )
                    _usage = getattr(resp, "usage", None)
                    if _usage is not None:
                        _tracker.set_usage(
                            candidate,
                            int(getattr(_usage, "input_tokens", 0) or 0),
                            int(getattr(_usage, "output_tokens", 0) or 0),
                        )
                self.model = candidate
                for block in resp.content:
                    if (
                        getattr(block, "type", None) == "tool_use"
                        and getattr(block, "name", None) == tool_name
                    ):
                        return dict(block.input or {})
                raise RuntimeError(f"Claude returned no tool_use block for {tool_name!r}")
            except self._anthropic.NotFoundError as exc:
                last_err = exc
                continue
            except self._anthropic.APIError as exc:
                raise RuntimeError(f"Anthropic API error: {exc}") from exc
        raise RuntimeError(
            f"None of the Claude model candidates worked ({', '.join(candidates)}): {last_err}"
        )

    # ----------- public surface -----------

    def generate_findings(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        screenshots: list[tuple[str, Path]],
        max_findings: int,
    ) -> list[dict[str, Any]]:
        payload = self._call_with_tool(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            screenshots=screenshots,
            tool_name="record_audit_findings",
            call_type="finding_generation",
            tool_description=(
                "Record the draft audit findings as a structured list. "
                f"At most {max_findings} findings, sorted critical→low."
            ),
            input_schema=AUDIT_SCHEMA,
        )
        return _coerce_findings_payload(payload)[:max_findings]

    def generate_verdict(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        payload = self._call_with_tool(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            screenshots=[],
            tool_name="record_audit_verdict",
            call_type="verdict_generation",
            tool_description="Record the verdict label, emoji, summary, and narrative.",
            input_schema=VERDICT_SCHEMA,
        )
        return {
            "label": (payload.get("label") or "").strip(),
            "emoji": payload.get("emoji", "🟡"),
            "summary": (payload.get("summary") or "").strip(),
            "narrative": (payload.get("narrative") or "").strip(),
        }

    def generate_qsg(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        screenshots: list[tuple[str, Path]],
    ) -> dict[str, Any]:
        payload = self._call_with_tool(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            screenshots=screenshots,
            tool_name="record_quick_start_guide",
            call_type="qsg_generation",
            tool_description="Record the one-page Quick Start Guide for end users.",
            input_schema=QSG_SCHEMA,
        )
        return _normalize_qsg(payload)

    def generate_handoff_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        section: str,
    ) -> str:
        payload = self._call_with_tool(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            screenshots=[],
            tool_name="record_handoff_text",
            call_type=f"handoff_{section}",
            tool_description=(
                "Record a single paragraph or short numbered list for the "
                "Handoff Report. Plain English, no corporate jargon."
            ),
            input_schema=HANDOFF_TEXT_SCHEMA,
        )
        return (payload.get("text") or "").strip()


# ---------------------------------------------------------------------------
# GPT (OpenAI)
# ---------------------------------------------------------------------------


class GPTClient(LLMClient):
    name = "gpt"

    def __init__(self, *, api_key: str | None = None, model: str | None = None) -> None:
        try:
            import openai
        except ImportError:
            sys.exit(
                "ERROR: openai package not installed.\nRun: pip install -r requirements-ai.txt"
            )
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self._openai = openai
        self._client = openai.OpenAI(api_key=key)
        self.model = model or DEFAULT_GPT_MODEL

    def _build_user_content(
        self, user_prompt: str, screenshots: list[tuple[str, Path]]
    ) -> list[dict[str, Any]]:
        parts: list[dict[str, Any]] = []
        for label, path in screenshots:
            if not path.exists():
                continue
            b64 = _read_png_b64(path)
            parts.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                }
            )
            parts.append({"type": "text", "text": f"[{label}]"})
        parts.append({"type": "text", "text": user_prompt})
        return parts

    def _call_with_schema(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        screenshots: list[tuple[str, Path]],
        schema_name: str,
        schema: dict[str, Any],
        call_type: str = "other",
    ) -> dict[str, Any]:
        user_content = self._build_user_content(user_prompt, screenshots)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        last_err: Exception | None = None
        candidates = [self.model] + [m for m in DEFAULT_GPT_FALLBACKS if m != self.model]
        for candidate in candidates:
            try:
                with cost_tracker.track_call(call_type) as _tracker:
                    resp = self._client.chat.completions.create(  # type: ignore[call-overload]  # openai SDK model arg is a Literal union; ours is a runtime str
                        model=candidate,
                        messages=messages,
                        response_format={
                            "type": "json_schema",
                            "json_schema": {
                                "name": schema_name,
                                "schema": schema,
                                "strict": True,
                            },
                        },
                        max_completion_tokens=8000,
                    )
                    _usage = getattr(resp, "usage", None)
                    if _usage is not None:
                        _tracker.set_usage(
                            candidate,
                            int(getattr(_usage, "prompt_tokens", 0) or 0),
                            int(getattr(_usage, "completion_tokens", 0) or 0),
                        )
                self.model = candidate
                raw = resp.choices[0].message.content or "{}"
                return json.loads(raw)
            except self._openai.NotFoundError as exc:
                last_err = exc
                continue
            except self._openai.BadRequestError as exc:
                if "json_schema" in str(exc).lower():
                    # Fall back to plain json_object on older models.
                    try:
                        resp = self._client.chat.completions.create(  # type: ignore[call-overload]  # openai SDK model arg is a Literal union; ours is a runtime str
                            model=candidate,
                            messages=messages,
                            response_format={"type": "json_object"},
                            max_completion_tokens=8000,
                        )
                        self.model = candidate
                        raw = resp.choices[0].message.content or "{}"
                        return json.loads(raw)
                    except Exception as exc2:  # noqa: BLE001
                        last_err = exc2
                        continue
                raise RuntimeError(f"OpenAI API error: {exc}") from exc
            except self._openai.APIError as exc:
                raise RuntimeError(f"OpenAI API error: {exc}") from exc
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"OpenAI returned non-JSON content: {exc}") from exc
        raise RuntimeError(
            f"None of the GPT model candidates worked ({', '.join(candidates)}): {last_err}"
        )

    def generate_findings(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        screenshots: list[tuple[str, Path]],
        max_findings: int,
    ) -> list[dict[str, Any]]:
        payload = self._call_with_schema(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            screenshots=screenshots,
            schema_name="audit_findings",
            call_type="finding_generation",
            schema=AUDIT_SCHEMA,
        )
        return _coerce_findings_payload(payload)[:max_findings]

    def generate_verdict(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        payload = self._call_with_schema(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            screenshots=[],
            schema_name="audit_verdict",
            call_type="verdict_generation",
            schema=VERDICT_SCHEMA,
        )
        return {
            "label": (payload.get("label") or "").strip(),
            "emoji": payload.get("emoji", "🟡"),
            "summary": (payload.get("summary") or "").strip(),
            "narrative": (payload.get("narrative") or "").strip(),
        }

    def generate_qsg(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        screenshots: list[tuple[str, Path]],
    ) -> dict[str, Any]:
        payload = self._call_with_schema(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            screenshots=screenshots,
            schema_name="quick_start_guide",
            call_type="qsg_generation",
            schema=QSG_SCHEMA,
        )
        return _normalize_qsg(payload)

    def generate_handoff_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        section: str,
    ) -> str:
        payload = self._call_with_schema(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            screenshots=[],
            schema_name="handoff_text",
            call_type=f"handoff_{section}",
            schema=HANDOFF_TEXT_SCHEMA,
        )
        return (payload.get("text") or "").strip()


def _normalize_qsg(payload: dict[str, Any]) -> dict[str, Any]:
    steps_raw = payload.get("steps") or []
    steps: list[dict[str, str]] = []
    for entry in steps_raw:
        if not isinstance(entry, dict):
            continue
        title = (entry.get("title") or "").strip()
        body = (entry.get("body") or "").strip()
        if title or body:
            steps.append({"title": title, "body": body})
    return {
        "title": (payload.get("title") or "").strip(),
        "intro": (payload.get("intro") or "").strip(),
        "steps": steps,
        "footer_note": (payload.get("footer_note") or "").strip(),
    }


# ---------------------------------------------------------------------------
# Stub client (offline)
# ---------------------------------------------------------------------------


def _stub_token_estimate(system_prompt: str, user_prompt: str) -> int:
    """Rough char/4 estimate for the stub provider's cost log row."""
    return max(1, (len(system_prompt) + len(user_prompt)) // 4)


def _stub_output_estimate(approx_chars: int) -> int:
    return max(1, approx_chars // 4)


class StubClient(LLMClient):
    """Offline LLM substitute. Emits canned findings from prescreener hits.

    Used by:
    * the smoke test (no API key)
    * future unit tests for the pipeline / yaml writer
    * Rob when he wants to dry-run the wiring without burning tokens

    Severity mapping mirrors findings.csv's labels.
    """

    name = "stub"
    model = "stub-deterministic"

    def __init__(
        self,
        *,
        prescreener_hits: list[dict[str, Any]] | None = None,
        builder: str = "Lovable",
        app_name: str = "your app",
    ) -> None:
        self._hits = prescreener_hits or []
        self._builder = builder or "Lovable"
        self._app_name = app_name or "your app"

    def generate_findings(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        screenshots: list[tuple[str, Path]],
        max_findings: int,
    ) -> list[dict[str, Any]]:
        with cost_tracker.track_call("finding_generation") as _t:
            _t.set_usage(
                self.model,
                _stub_token_estimate(system_prompt, user_prompt),
                _stub_output_estimate(max_findings * 180),
            )
        sev_map = {
            "Critical": "critical",
            "High": "high",
            "Medium": "medium",
            "Low": "low",
        }
        out: list[dict[str, Any]] = []
        seen: set[str] = set()
        for hit in self._hits:
            finding = hit.get("finding", {})
            page = hit.get("page", {})
            fid = finding.get("id", "")
            if fid in seen:
                continue
            seen.add(fid)
            sev_raw = finding.get("severity", "").strip().capitalize()
            sev = sev_map.get(sev_raw, "medium")
            matches = hit.get("matches") or [{}]
            sample = matches[0].get("text") or finding.get("name", "issue")
            out.append(
                {
                    "severity": sev,
                    "title": finding.get("name", fid) or "Issue detected by prescreener",
                    "what_we_saw": (
                        f"On {page.get('url', 'the live URL')}, the prescreener matched "
                        f"the pattern '{sample[:60]}' from {fid}."
                    ),
                    "why_it_matters": (
                        finding.get("explanation")
                        or "A first-time visitor would likely notice this."
                    ),
                    "screenshot_caption": "",
                    "fix_prompt": (
                        f"(STUB CLIENT) Apply the {self._builder} fix for {fid}. "
                        "Replace this text with a real LLM response by setting "
                        "ANTHROPIC_API_KEY or OPENAI_API_KEY in .env."
                    ),
                }
            )
        # If we have no prescreener hits, emit a single placeholder finding.
        if not out:
            out.append(
                {
                    "severity": "medium",
                    "title": "Stub finding (no API key set)",
                    "what_we_saw": (
                        f"This is a placeholder generated by the offline stub client for "
                        f"{self._app_name}. The pipeline ran end-to-end with no real LLM."
                    ),
                    "why_it_matters": (
                        "Real findings need ANTHROPIC_API_KEY or OPENAI_API_KEY in .env."
                    ),
                    "screenshot_caption": "",
                    "fix_prompt": (
                        f"Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env and re-run "
                        f"scripts/ai_audit.py to generate a real {self._builder} audit."
                    ),
                }
            )
        return out[:max_findings]

    def generate_verdict(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        with cost_tracker.track_call("verdict_generation") as _t:
            _t.set_usage(
                self.model,
                _stub_token_estimate(system_prompt, user_prompt),
                _stub_output_estimate(200),
            )
        return {
            "label": "Safe for friends/family testing",
            "emoji": "🟡",
            "summary": "Stub verdict; rerun with a real LLM key to get a curated narrative.",
            "narrative": (
                f"This is a placeholder verdict for {self._app_name}. The AI pipeline "
                "ran end-to-end without an LLM key set, so findings and narrative are "
                "stubbed. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env to generate "
                "a real draft."
            ),
        }

    def generate_qsg(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        screenshots: list[tuple[str, Path]],
    ) -> dict[str, Any]:
        with cost_tracker.track_call("qsg_generation") as _t:
            _t.set_usage(
                self.model,
                _stub_token_estimate(system_prompt, user_prompt),
                _stub_output_estimate(600),
            )
        return {
            "title": f"{self._app_name}, Getting Started",
            "intro": (
                "Stub Quick Start Guide. Set ANTHROPIC_API_KEY or OPENAI_API_KEY "
                "to get a real guide written from the audit evidence."
            ),
            "steps": [
                {
                    "title": "Open the app",
                    "body": "Stub step. Real steps are generated by the LLM from screenshots.",
                },
                {
                    "title": "Try the main action",
                    "body": "Stub step. Replace by setting an LLM API key.",
                },
            ],
            "footer_note": "Stub footer. Replace by setting an LLM API key.",
        }

    def generate_handoff_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        section: str,
    ) -> str:
        with cost_tracker.track_call(f"handoff_{section}") as _t:
            _t.set_usage(
                self.model,
                _stub_token_estimate(system_prompt, user_prompt),
                _stub_output_estimate(280),
            )
        if section == "recommended_order":
            return (
                "1. Stub recommended order. Set ANTHROPIC_API_KEY or "
                "OPENAI_API_KEY to get a real prioritization."
            )
        if section == "code_review_notes":
            return (
                "Stub code-review notes. A real LLM run lists 3 to 5 "
                "architecture or integration concerns the developer "
                "should look at first."
            )
        # context_paragraph (default)
        return (
            f"Stub context paragraph for {self._app_name}. Set an LLM "
            "API key to get a real one written from the audit evidence."
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def build_client(
    *,
    provider: str = "auto",
    stub_context: dict[str, Any] | None = None,
) -> LLMClient:
    """Pick a provider based on availability and user preference.

    ``provider`` is one of: ``"auto"``, ``"claude"``, ``"gpt"``, ``"stub"``.
    With ``"auto"`` we prefer Claude (better at structured output + vision
    in our benchmarks), then GPT, then exit with a clear error message
    listing what env vars are missing.

    ``stub_context`` is forwarded to ``StubClient`` to make stub responses
    a little more realistic for smoke tests.
    """
    provider = (provider or "auto").lower()

    if provider == "stub":
        return StubClient(**(stub_context or {}))

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if provider == "claude":
        if not anthropic_key:
            sys.exit("ERROR: --provider claude but ANTHROPIC_API_KEY is not set in .env")
        return ClaudeClient(api_key=anthropic_key)

    if provider == "gpt":
        if not openai_key:
            sys.exit("ERROR: --provider gpt but OPENAI_API_KEY is not set in .env")
        return GPTClient(api_key=openai_key)

    if provider == "auto":
        if anthropic_key:
            return ClaudeClient(api_key=anthropic_key)
        if openai_key:
            return GPTClient(api_key=openai_key)
        sys.exit(
            "ERROR: no LLM API key found.\n"
            "Set ANTHROPIC_API_KEY (preferred) or OPENAI_API_KEY in .env.\n"
            "Or pass --provider stub to run the pipeline without an LLM "
            "(generates placeholder findings; useful for smoke tests)."
        )

    sys.exit(f"ERROR: unknown --provider {provider!r}. Choose from: auto, claude, gpt, stub.")
