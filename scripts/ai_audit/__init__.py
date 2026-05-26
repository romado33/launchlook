"""scripts.ai_audit: AI-powered audit pipeline for LaunchLook.

This package generates draft customer YAMLs by sending screenshots, prescreener
hits, and cleaned HTML to a vision-capable LLM (Claude or GPT) and parsing the
structured response into the same schema ``deliver_report.py`` consumes.

The public entry points are:

* ``scripts.ai_audit.pipeline.run`` — full end-to-end pipeline (capture →
  prescreen → HTML extract → LLM → YAML write).
* ``scripts.ai_audit.pipeline.regenerate_finding`` — refresh a single finding
  in an existing YAML, used by the audit UI's review mode.
* ``scripts.ai_audit.llm_client.build_client`` — provider-agnostic LLM factory
  (Anthropic or OpenAI, with an offline stub for tests).

The companion CLI lives at ``scripts/ai_audit.py``.
"""

from __future__ import annotations

__all__ = ["pipeline", "llm_client", "html_extract", "feedback"]
