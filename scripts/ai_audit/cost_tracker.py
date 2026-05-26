"""Per-customer AI cost tracking for LaunchLook audits.

Logs token usage + cost per LLM call, aggregates per customer, writes a
daily JSONL summary at ``data/ai_costs/<YYYY-MM-DD>.jsonl``.

Internal-only tooling per docs/SIMPLICITY-GUARDRAILS.md §6. Cost data is
NEVER surfaced on customer-facing pages, reports, QSGs, or email
templates. The on-disk log records ``customer_id`` (slug) only - no
emails, no URLs, no findings content.

Design:

* ``calculate_cost(model, input_tokens, output_tokens) -> float`` does the
  $/MTok math from a small pricing table.
* ``log_call(...)`` appends one JSON line to today's file.
* ``aggregate_customer(customer_id)`` scans every daily file and rolls up
  totals for one customer.
* ``daily_summary(date)`` returns totals + p50/p95 latency for one day.
* ``set_context(customer_id, tier)`` / ``current_context()`` form a tiny
  context-var pair that the LLM client wraps each call with. The pipeline
  sets the context once per audit; the LLM client tags every API call.
* ``track_call(call_type)`` is the context-manager wrapper around an
  individual API call - measures wall-clock latency and writes the row.

Pricing dict is the canonical table. Confirm against Anthropic /
OpenAI's public pricing pages and update the dict + source comment if
they move. Cited sources are in the docstring on PRICING below.
"""

from __future__ import annotations

import contextlib
import contextvars
import json
import os
import statistics
import time
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COSTS_DIR = REPO_ROOT / "data" / "ai_costs"


# ---------------------------------------------------------------------------
# Pricing table (USD per million tokens)
# ---------------------------------------------------------------------------

# Canonical sources confirmed May 26, 2026:
#   Anthropic - https://platform.claude.com/docs/en/about-claude/pricing
#   OpenAI    - https://developers.openai.com/api/docs/pricing
# Update both the entry AND the comment date if either provider shifts.
# Standard list price only; we deliberately do NOT special-case the
# cache-read / cache-write tiers or the >200k long-context premium because
# our finding-generation and verdict prompts both sit comfortably under
# 200k tokens and we are not using prompt caching today.
PRICING: dict[str, dict[str, float]] = {
    # Anthropic Claude Sonnet 4.5 (current default per docs/PRODUCT-DECISIONS.md
    # and scripts/ai_audit/llm_client.DEFAULT_CLAUDE_MODEL).
    "claude-sonnet-4-5-20250929": {
        "input_per_million": 3.00,
        "output_per_million": 15.00,
    },
    "claude-sonnet-4-5": {"input_per_million": 3.00, "output_per_million": 15.00},
    # Sibling Sonnets - same per-token pricing.
    "claude-sonnet-4-6": {"input_per_million": 3.00, "output_per_million": 15.00},
    "claude-sonnet-4-0": {"input_per_million": 3.00, "output_per_million": 15.00},
    # Claude 3.5 Sonnet - kept in the fallback chain in llm_client.py.
    "claude-3-5-sonnet-20241022": {
        "input_per_million": 3.00,
        "output_per_million": 15.00,
    },
    "claude-3-5-sonnet-latest": {
        "input_per_million": 3.00,
        "output_per_million": 15.00,
    },
    # Other tiers - included so the cost calc still works if Rob ever
    # overrides LAUNCHLOOK_CLAUDE_MODEL to a different model.
    "claude-opus-4-5-20250929": {
        "input_per_million": 5.00,
        "output_per_million": 25.00,
    },
    "claude-opus-4-5": {"input_per_million": 5.00, "output_per_million": 25.00},
    "claude-haiku-4-5": {"input_per_million": 1.00, "output_per_million": 5.00},
    # OpenAI - GPT-4o family + a couple of likely successors.
    "gpt-4o": {"input_per_million": 2.50, "output_per_million": 10.00},
    "gpt-4o-mini": {"input_per_million": 0.15, "output_per_million": 0.60},
    "gpt-4.1": {"input_per_million": 2.00, "output_per_million": 8.00},
    "gpt-4.1-mini": {"input_per_million": 0.40, "output_per_million": 1.60},
    # GPT-5 family pricing (best-effort estimate; update from openai.com
    # when finalized for our deployment).
    "gpt-5-mini": {"input_per_million": 0.25, "output_per_million": 2.00},
    # Stub provider - always free in our test runs.
    "stub-deterministic": {"input_per_million": 0.00, "output_per_million": 0.00},
}

# Severity thresholds for `--alert` mode. Calibrated against the
# Starter / Scale Up / Pro tier prices ($19 / $49 / $99). 20% of the
# tier price is the "this audit is eating margin" line.
TIER_PRICE_USD: dict[str, float] = {
    "Starter Package": 19.00,
    "Scale Up Package": 49.00,
    "Pro Package": 99.00,
}
PER_CUSTOMER_COST_ALERT_RATIO = 0.20  # alert when cost > 20% of tier price
PER_CUSTOMER_HIGH_COST_RATIO = 0.10  # flag as outlier above 10% of tier price
DAILY_COST_ALERT_USD = 50.00  # rough sanity check; tune as volume grows
PER_CUSTOMER_CALL_COUNT_ALERT = 15  # likely loop/retry storm above this

CALL_TYPES = {
    "finding_generation",
    "qsg_generation",
    "verdict_generation",
    "dedup_check",
    "prescreen",
    "other",
}


# ---------------------------------------------------------------------------
# Calculation
# ---------------------------------------------------------------------------


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return the USD cost of one LLM call.

    Falls back to the Sonnet 4.5 rate when the model is unknown so the
    log still has a useful number rather than 0. Unknown models are
    surfaced via stderr exactly once (so smoke tests stay quiet).
    """
    pricing = PRICING.get(model)
    if pricing is None:
        pricing = PRICING["claude-sonnet-4-5-20250929"]
        _warn_unknown_model_once(model)
    in_cost = (max(0, int(input_tokens)) / 1_000_000.0) * pricing["input_per_million"]
    out_cost = (max(0, int(output_tokens)) / 1_000_000.0) * pricing[
        "output_per_million"
    ]
    return round(in_cost + out_cost, 6)


_warned_models: set[str] = set()


def _warn_unknown_model_once(model: str) -> None:
    if model in _warned_models:
        return
    _warned_models.add(model)
    import sys

    print(
        f"[cost_tracker] WARN: unknown model {model!r}, using Sonnet 4.5 rates as fallback. "
        "Add a pricing row in scripts/ai_audit/cost_tracker.PRICING.",
        file=sys.stderr,
    )


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------


def _utc_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _today_path() -> Path:
    return COSTS_DIR / f"{datetime.now(UTC).strftime('%Y-%m-%d')}.jsonl"


def log_call(
    customer_id: str,
    tier: str,
    model: str,
    call_type: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: int,
) -> dict[str, Any]:
    """Append a row to ``data/ai_costs/<YYYY-MM-DD>.jsonl``.

    The row is kept deliberately small. Per SIMPLICITY-GUARDRAILS §6
    no PII (emails, URLs, names, findings content) is written here -
    the slug-style customer_id is the only identifier.
    """
    if call_type not in CALL_TYPES:
        call_type = "other"
    cost = calculate_cost(model, input_tokens, output_tokens)
    row = {
        "timestamp": _utc_iso(),
        "customer_id": (customer_id or "unknown").strip() or "unknown",
        "tier": (tier or "unknown").strip() or "unknown",
        "model": (model or "unknown").strip() or "unknown",
        "call_type": call_type,
        "input_tokens": int(max(0, input_tokens)),
        "output_tokens": int(max(0, output_tokens)),
        "cost_usd": cost,
        "latency_ms": int(max(0, latency_ms)),
    }
    _append_row(_today_path(), row)
    return row


def _append_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(row, ensure_ascii=False, sort_keys=False)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------


def iter_rows(date: str | None = None) -> Iterator[dict[str, Any]]:
    """Yield every cost row, optionally filtered to a YYYY-MM-DD date.

    Tolerates missing files and skips malformed lines without raising.
    """
    if date:
        files = [COSTS_DIR / f"{date}.jsonl"]
    else:
        files = sorted(COSTS_DIR.glob("*.jsonl")) if COSTS_DIR.exists() else []
    for path in files:
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        yield json.loads(raw)
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue


def iter_rows_since(days: int) -> Iterator[dict[str, Any]]:
    """Yield rows from the last ``days`` calendar days (UTC).

    Each daily file is named ``YYYY-MM-DD.jsonl``. We compare strings to
    avoid timezone gymnastics.
    """
    from datetime import timedelta

    cutoff = (datetime.now(UTC) - timedelta(days=max(0, days - 1))).date()
    if not COSTS_DIR.exists():
        return
    for path in sorted(COSTS_DIR.glob("*.jsonl")):
        try:
            file_date = datetime.strptime(path.stem, "%Y-%m-%d").date()
        except ValueError:
            continue
        if file_date < cutoff:
            continue
        yield from iter_rows(path.stem)


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def aggregate_customer(customer_id: str) -> dict[str, Any]:
    """Roll up total cost, call count, and token totals for a customer.

    Scans every daily file. Returns zeros for an unknown customer.
    """
    total_cost = 0.0
    call_count = 0
    input_total = 0
    output_total = 0
    tier: str | None = None
    call_type_counts: dict[str, int] = {}
    first_seen: str | None = None
    last_seen: str | None = None
    for row in iter_rows():
        if row.get("customer_id") != customer_id:
            continue
        call_count += 1
        total_cost += float(row.get("cost_usd", 0.0))
        input_total += int(row.get("input_tokens", 0))
        output_total += int(row.get("output_tokens", 0))
        if not tier and row.get("tier"):
            tier = row.get("tier")
        ct = row.get("call_type", "other")
        call_type_counts[ct] = call_type_counts.get(ct, 0) + 1
        ts = row.get("timestamp")
        if ts:
            if first_seen is None or ts < first_seen:
                first_seen = ts
            if last_seen is None or ts > last_seen:
                last_seen = ts
    return {
        "customer_id": customer_id,
        "tier": tier or "unknown",
        "call_count": call_count,
        "input_tokens": input_total,
        "output_tokens": output_total,
        "cost_usd": round(total_cost, 6),
        "call_type_counts": call_type_counts,
        "first_seen": first_seen,
        "last_seen": last_seen,
    }


def daily_summary(date: str | None = None) -> dict[str, Any]:
    """Return total cost, unique customer count, p50/p95 latency for a day.

    ``date`` defaults to today (UTC), formatted YYYY-MM-DD.
    """
    date = date or datetime.now(UTC).strftime("%Y-%m-%d")
    rows = list(iter_rows(date))
    if not rows:
        return {
            "date": date,
            "call_count": 0,
            "customer_count": 0,
            "total_cost_usd": 0.0,
            "input_tokens": 0,
            "output_tokens": 0,
            "p50_latency_ms": 0,
            "p95_latency_ms": 0,
            "models": {},
            "call_types": {},
        }
    customers: set[str] = set()
    total_cost = 0.0
    in_tok = 0
    out_tok = 0
    latencies: list[int] = []
    models: dict[str, int] = {}
    call_types: dict[str, int] = {}
    for row in rows:
        customers.add(row.get("customer_id", "unknown"))
        total_cost += float(row.get("cost_usd", 0.0))
        in_tok += int(row.get("input_tokens", 0))
        out_tok += int(row.get("output_tokens", 0))
        latencies.append(int(row.get("latency_ms", 0)))
        m = row.get("model", "unknown")
        models[m] = models.get(m, 0) + 1
        ct = row.get("call_type", "other")
        call_types[ct] = call_types.get(ct, 0) + 1
    return {
        "date": date,
        "call_count": len(rows),
        "customer_count": len(customers),
        "total_cost_usd": round(total_cost, 6),
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "p50_latency_ms": int(statistics.median(latencies)) if latencies else 0,
        "p95_latency_ms": _percentile(latencies, 95),
        "models": models,
        "call_types": call_types,
    }


def _percentile(values: list[int], pct: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, int(round((pct / 100.0) * (len(ordered) - 1)))))
    return int(ordered[k])


# ---------------------------------------------------------------------------
# Context variables (so the LLM client doesn't need to thread args)
# ---------------------------------------------------------------------------


_customer_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "launchlook_cost_customer_id", default="unknown"
)
_tier_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "launchlook_cost_tier", default="unknown"
)


def set_context(
    customer_id: str, tier: str
) -> tuple[contextvars.Token, contextvars.Token]:
    """Set the customer_id + tier visible to every LLM call until reset.

    Returns the ``contextvars.Token`` pair so the caller can ``reset`` them
    later (typically via ``customer_context(...)`` below).
    """
    cid_token = _customer_id_var.set((customer_id or "unknown").strip() or "unknown")
    tier_token = _tier_var.set((tier or "unknown").strip() or "unknown")
    return cid_token, tier_token


def reset_context(tokens: tuple[contextvars.Token, contextvars.Token]) -> None:
    cid_token, tier_token = tokens
    try:
        _customer_id_var.reset(cid_token)
    except ValueError:
        pass
    try:
        _tier_var.reset(tier_token)
    except ValueError:
        pass


def current_context() -> tuple[str, str]:
    return _customer_id_var.get(), _tier_var.get()


@contextlib.contextmanager
def customer_context(customer_id: str, tier: str) -> Iterator[None]:
    """``with`` wrapper around set_context / reset_context."""
    tokens = set_context(customer_id, tier)
    try:
        yield
    finally:
        reset_context(tokens)


# ---------------------------------------------------------------------------
# Per-call tracker (used by llm_client.py around every API call)
# ---------------------------------------------------------------------------


class CallTracker:
    """Records latency, then takes token counts to write a cost row.

    Used as a context manager by the real provider clients::

        with track_call("finding_generation") as tracker:
            resp = self._client.messages.create(...)
            tracker.set_usage(model, resp.usage.input_tokens, resp.usage.output_tokens)

    If ``set_usage`` is not called (e.g. the API errored before a usage
    block came back), nothing is written.
    """

    def __init__(self, call_type: str) -> None:
        self.call_type = call_type if call_type in CALL_TYPES else "other"
        self._t0: float = 0.0
        self._recorded = False
        self.row: dict[str, Any] | None = None

    def __enter__(self) -> CallTracker:
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None  # never suppress exceptions

    def set_usage(self, model: str, input_tokens: int, output_tokens: int) -> None:
        if self._recorded:
            return
        latency_ms = int((time.perf_counter() - self._t0) * 1000)
        customer_id, tier = current_context()
        if os.getenv("LAUNCHLOOK_DISABLE_COST_LOG") == "1":
            self._recorded = True
            return
        try:
            self.row = log_call(
                customer_id=customer_id,
                tier=tier,
                model=model,
                call_type=self.call_type,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
            )
        except Exception as exc:  # noqa: BLE001
            import sys

            print(f"[cost_tracker] WARN: failed to log call: {exc}", file=sys.stderr)
        finally:
            self._recorded = True


def track_call(call_type: str) -> CallTracker:
    return CallTracker(call_type)
