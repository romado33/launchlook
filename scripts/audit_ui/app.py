"""Flask app for the LaunchLook audit UI.

Routes:

* ``GET  /``                    — render the form (Jinja template)
* ``GET  /api/bootstrap``       — initial state: prefill, draft (if any), tier caps
* ``POST /api/draft``           — save draft JSON
* ``GET  /api/draft``           — load draft JSON for ``?slug=...``
* ``DELETE /api/draft``         — discard draft JSON for ``?slug=...``
* ``POST /api/yaml``            — generate YAML, write to ``customers/{slug}.yaml``
* ``POST /api/screenshot``      — accept an uploaded screenshot, save under
                                  ``screenshots/{slug}/finding-{n}.png``
* ``GET  /api/customers``       — list existing ``customers/*.yaml`` files
* ``GET  /api/customers/<slug>`` — load a customer YAML back into form state
* ``POST /api/deliver``         — run ``deliver_report.py`` (optionally ``--send``)
* ``GET  /api/deliver/log``     — long-poll the deliver log stream

The app is intentionally single-process / single-user: there is no auth,
no session store, and no persistence beyond the JSON drafts and the YAML
output. This matches Rob's local-only workflow.
"""

from __future__ import annotations

import io
import re
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, abort, jsonify, render_template, request, send_from_directory

from . import draft_store, deliver_runner, yaml_writer


# ---------------------------------------------------------------------------
# Tier-cap discovery — read the cap values from deliver_report.py at startup
# so future cap changes there auto-propagate without a code edit here.
# ---------------------------------------------------------------------------


_DEFAULT_TIER_CAPS = {"Starter Package": 10, "Scale Up Package": 30, "Pro Package": 40}

# Match the dict-lookup cap form used by deliver_report.py:
#   cap = {"Starter Package": 10, "Scale Up Package": 30, "Pro Package": 40}.get(tier, 30)
# Captures every "Tier Name": <int> pair so the UI auto-tracks future tier
# additions (e.g. Pro Package) without a code edit here.
_TIER_CAP_DICT_PATTERN = re.compile(
    r'cap\s*=\s*\{(?P<body>[^}]*)\}\s*\.get\(\s*tier'
)
_TIER_CAP_ENTRY_PATTERN = re.compile(
    r'["\'](?P<tier>[^"\']+)["\']\s*:\s*(?P<cap>\d+)'
)


def discover_tier_caps(deliver_report_path: Path) -> dict[str, int]:
    """Extract tier caps from the deliver_report.py source.

    Falls back to ``_DEFAULT_TIER_CAPS`` if the regex doesn't match (e.g.
    if a future refactor changes the structure of the validate function).
    """
    try:
        text = deliver_report_path.read_text(encoding="utf-8")
    except OSError:
        return dict(_DEFAULT_TIER_CAPS)
    dict_match = _TIER_CAP_DICT_PATTERN.search(text)
    if not dict_match:
        return dict(_DEFAULT_TIER_CAPS)
    parsed: dict[str, int] = {}
    for entry in _TIER_CAP_ENTRY_PATTERN.finditer(dict_match.group("body")):
        parsed[entry.group("tier")] = int(entry.group("cap"))
    return parsed or dict(_DEFAULT_TIER_CAPS)


# ---------------------------------------------------------------------------
# Deliver-log buffer (in-memory; one job at a time is fine for local use).
# ---------------------------------------------------------------------------


class DeliverLog:
    """Thread-safe append-and-poll log buffer for the deliver subprocess."""

    def __init__(self, max_lines: int = 2000) -> None:
        self._lines: deque[str] = deque(maxlen=max_lines)
        self._all_lines: list[str] = []
        self._lock = threading.Lock()
        self.running = False
        self.exit_code: int | None = None
        self.started_at: float | None = None
        self.finished_at: float | None = None

    def begin(self) -> None:
        with self._lock:
            self._lines.clear()
            self._all_lines.clear()
            self.running = True
            self.exit_code = None
            self.started_at = time.time()
            self.finished_at = None

    def append(self, line: str) -> None:
        with self._lock:
            self._lines.append(line)
            self._all_lines.append(line)

    def finish(self, exit_code: int) -> None:
        with self._lock:
            self.running = False
            self.exit_code = exit_code
            self.finished_at = time.time()

    def snapshot(self, since: int = 0) -> dict[str, Any]:
        with self._lock:
            total = len(self._all_lines)
            new_lines = self._all_lines[since:]
            return {
                "running": self.running,
                "exit_code": self.exit_code,
                "lines": new_lines,
                "next_offset": total,
                "total": total,
            }


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app(
    *,
    repo_root: Path,
    prefill: dict[str, Any] | None = None,
    auto_open: bool = True,
    review_ai: bool = False,
) -> Flask:
    pkg_root = Path(__file__).resolve().parent
    app = Flask(
        __name__,
        template_folder=str(pkg_root / "templates"),
        static_folder=str(pkg_root / "static"),
        static_url_path="/static",
    )
    app.config["JSON_SORT_KEYS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB screenshot ceiling

    app.config["REPO_ROOT"] = repo_root
    app.config["DRAFTS_DIR"] = repo_root / "drafts"
    app.config["CUSTOMERS_DIR"] = repo_root / "customers"
    app.config["SCREENSHOTS_DIR"] = repo_root / "screenshots"
    app.config["DELIVER_REPORT_PATH"] = repo_root / "scripts" / "deliver_report.py"
    app.config["TIER_CAPS"] = discover_tier_caps(app.config["DELIVER_REPORT_PATH"])
    app.config["PREFILL"] = prefill or {}
    app.config["AUTO_OPEN"] = auto_open
    app.config["REVIEW_AI"] = bool(review_ai)
    app.config["FEEDBACK_DIR"] = repo_root / "data" / "ai_feedback"

    deliver_log = DeliverLog()
    app.config["DELIVER_LOG"] = deliver_log

    _register_routes(app)
    return app


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


def _register_routes(app: Flask) -> None:
    @app.route("/")
    def index() -> str:
        return render_template(
            "index.html",
            tier_caps=app.config["TIER_CAPS"],
            severities=yaml_writer.VALID_SEVERITIES,
            tiers=yaml_writer.VALID_TIERS,
            builders=yaml_writer.VALID_BUILDERS,
            platforms=yaml_writer.VALID_PLATFORMS,
            default_platform=yaml_writer.DEFAULT_PLATFORM,
            review_ai=app.config["REVIEW_AI"],
        )

    @app.route("/api/bootstrap")
    def api_bootstrap() -> Any:
        prefill = app.config["PREFILL"]
        slug = (request.args.get("slug") or prefill.get("slug") or "").strip()
        existing_draft = None
        existing_customer = None
        feedback_record = None
        if slug:
            existing_draft = draft_store.load_draft(app.config["DRAFTS_DIR"], slug)
            if app.config["REVIEW_AI"]:
                existing_customer = _load_customer_payload(app, slug)
                feedback_record = _load_feedback(app, slug)
        return jsonify({
            "slug": slug,
            "prefill": prefill,
            "draft": existing_draft,
            "review_ai": app.config["REVIEW_AI"],
            "customer": existing_customer,
            "feedback": feedback_record,
            "tier_caps": app.config["TIER_CAPS"],
            "severities": list(yaml_writer.VALID_SEVERITIES),
            "tiers": list(yaml_writer.VALID_TIERS),
            "builders": list(yaml_writer.VALID_BUILDERS),
            "platforms": list(yaml_writer.VALID_PLATFORMS),
            "default_platform": yaml_writer.DEFAULT_PLATFORM,
        })

    @app.route("/api/draft", methods=["POST"])
    def api_draft_save() -> Any:
        data = request.get_json(silent=True) or {}
        slug = (data.get("slug") or "").strip()
        payload = data.get("payload") or {}
        if not slug:
            return jsonify({"error": "slug is required"}), 400
        path = draft_store.save_draft(app.config["DRAFTS_DIR"], slug, payload)
        return jsonify({
            "ok": True,
            "path": str(path.relative_to(app.config["REPO_ROOT"])),
            "saved_at": datetime.now(timezone.utc).isoformat(),
        })

    @app.route("/api/draft", methods=["GET"])
    def api_draft_load() -> Any:
        slug = (request.args.get("slug") or "").strip()
        if not slug:
            return jsonify({"error": "slug is required"}), 400
        record = draft_store.load_draft(app.config["DRAFTS_DIR"], slug)
        if not record:
            return jsonify({"draft": None})
        return jsonify({"draft": record})

    @app.route("/api/draft", methods=["DELETE"])
    def api_draft_delete() -> Any:
        slug = (request.args.get("slug") or "").strip()
        if not slug:
            return jsonify({"error": "slug is required"}), 400
        deleted = draft_store.delete_draft(app.config["DRAFTS_DIR"], slug)
        return jsonify({"ok": True, "deleted": deleted})

    @app.route("/api/yaml", methods=["POST"])
    def api_yaml_generate() -> Any:
        data = request.get_json(silent=True) or {}
        slug = (data.get("slug") or "").strip()
        payload = data.get("payload") or {}
        if not slug:
            return jsonify({"error": "slug is required"}), 400

        errors = _validate_payload(payload, app.config["TIER_CAPS"])
        if errors:
            return jsonify({"ok": False, "errors": errors}), 400

        try:
            yaml_text = yaml_writer.form_to_yaml(payload)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "errors": [{"field": "_global", "message": f"YAML serialization failed: {exc}"}]}), 400

        customers_dir = app.config["CUSTOMERS_DIR"]
        customers_dir.mkdir(parents=True, exist_ok=True)
        target = customers_dir / f"{draft_store.safe_slug(slug)}.yaml"
        target.write_text(yaml_text, encoding="utf-8")

        return jsonify({
            "ok": True,
            "yaml": yaml_text,
            "path": str(target.relative_to(app.config["REPO_ROOT"])),
        })

    @app.route("/api/customers")
    def api_customers_list() -> Any:
        customers_dir = app.config["CUSTOMERS_DIR"]
        if not customers_dir.exists():
            return jsonify({"customers": []})
        items = []
        for path in sorted(customers_dir.glob("*.yaml")):
            try:
                stat = path.stat()
            except OSError:
                continue
            items.append({
                "slug": path.stem,
                "filename": path.name,
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "size": stat.st_size,
            })
        return jsonify({"customers": items})

    @app.route("/api/customers/<slug>")
    def api_customers_load(slug: str) -> Any:
        clean = draft_store.safe_slug(slug)
        target = app.config["CUSTOMERS_DIR"] / f"{clean}.yaml"
        if not target.exists():
            return jsonify({"error": f"Customer YAML not found: {target.name}"}), 404
        try:
            text = target.read_text(encoding="utf-8")
            payload = yaml_writer.yaml_to_form(text)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": f"Failed to parse {target.name}: {exc}"}), 500
        return jsonify({"slug": clean, "payload": payload, "yaml": text})

    @app.route("/api/screenshot", methods=["POST"])
    def api_screenshot_upload() -> Any:
        slug = (request.form.get("slug") or "").strip()
        index_str = (request.form.get("index") or "").strip()
        if not slug:
            return jsonify({"error": "slug is required"}), 400
        try:
            finding_index = int(index_str)
        except ValueError:
            return jsonify({"error": "index must be an integer"}), 400
        if finding_index < 0:
            return jsonify({"error": "index must be non-negative"}), 400

        upload = request.files.get("file")
        if upload is None or not upload.filename:
            return jsonify({"error": "file is required"}), 400

        ext = Path(upload.filename).suffix.lower()
        if ext not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
            return jsonify({"error": f"Unsupported image extension: {ext or '(none)'}"}), 400

        clean_slug = draft_store.safe_slug(slug)
        target_dir = app.config["SCREENSHOTS_DIR"] / clean_slug
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"finding-{finding_index + 1}{ext}"
        upload.save(target)

        rel = target.relative_to(app.config["REPO_ROOT"]).as_posix()
        return jsonify({
            "ok": True,
            "path": rel,
            "url": f"/screenshots/{clean_slug}/{target.name}",
            "filename": target.name,
        })

    @app.route("/screenshots/<path:relpath>")
    def serve_screenshot(relpath: str) -> Any:
        return send_from_directory(app.config["SCREENSHOTS_DIR"], relpath)

    @app.route("/api/deliver", methods=["POST"])
    def api_deliver() -> Any:
        deliver_log: DeliverLog = app.config["DELIVER_LOG"]
        if deliver_log.running:
            return jsonify({"ok": False, "error": "Another deliver job is already running."}), 409

        data = request.get_json(silent=True) or {}
        slug = (data.get("slug") or "").strip()
        send = bool(data.get("send", False))
        if not slug:
            return jsonify({"error": "slug is required"}), 400

        clean = draft_store.safe_slug(slug)
        customer_yaml = app.config["CUSTOMERS_DIR"] / f"{clean}.yaml"
        if not customer_yaml.exists():
            return jsonify({
                "ok": False,
                "error": f"Customer YAML missing: {customer_yaml.name}. Click 'Generate YAML' first.",
            }), 400

        deliver_log.begin()
        deliver_runner.run_deliver_in_thread(
            app.config["REPO_ROOT"],
            customer_yaml,
            send=send,
            on_line=deliver_log.append,
            on_exit=deliver_log.finish,
        )
        return jsonify({"ok": True})

    @app.route("/api/deliver/log")
    def api_deliver_log() -> Any:
        deliver_log: DeliverLog = app.config["DELIVER_LOG"]
        try:
            since = int(request.args.get("since", "0"))
        except ValueError:
            since = 0
        return jsonify(deliver_log.snapshot(since=since))

    # ---- AI review-mode endpoints -------------------------------------

    @app.route("/api/feedback", methods=["POST"])
    def api_feedback_record() -> Any:
        """Record a single Rob action against the AI draft for a finding."""
        data = request.get_json(silent=True) or {}
        slug = (data.get("slug") or "").strip()
        action = (data.get("action") or "").strip().lower()
        try:
            finding_idx = int(data.get("finding_idx", -1))
        except (TypeError, ValueError):
            finding_idx = -1
        if not slug or finding_idx < 0:
            return jsonify({"error": "slug and finding_idx are required"}), 400
        if action not in {"approved", "edited", "rejected", "regenerated", "draft"}:
            return jsonify({"error": f"unknown action {action!r}"}), 400

        try:
            from scripts.ai_audit import feedback as feedback_log  # noqa: WPS433
        except ImportError as exc:
            return jsonify({"error": f"ai_audit package missing: {exc}"}), 500

        feedback_log.record_action(
            app.config["REPO_ROOT"],
            draft_store.safe_slug(slug),
            finding_idx,
            action,
            ai_title=data.get("ai_title"),
            ai_severity=data.get("ai_severity"),
            final_title=data.get("final_title"),
            final_severity=data.get("final_severity"),
        )
        return jsonify({"ok": True})

    @app.route("/api/feedback/finalize", methods=["POST"])
    def api_feedback_finalize() -> Any:
        """Mark all un-reviewed findings as approved and stamp reviewed_at."""
        data = request.get_json(silent=True) or {}
        slug = (data.get("slug") or "").strip()
        if not slug:
            return jsonify({"error": "slug is required"}), 400
        final_findings = data.get("final_findings") or []
        try:
            from scripts.ai_audit import feedback as feedback_log  # noqa: WPS433
        except ImportError as exc:
            return jsonify({"error": f"ai_audit package missing: {exc}"}), 500
        feedback_log.finalize(
            app.config["REPO_ROOT"],
            draft_store.safe_slug(slug),
            final_findings=final_findings,
        )
        return jsonify({"ok": True})

    @app.route("/api/regenerate-finding", methods=["POST"])
    def api_regenerate_finding() -> Any:
        """Ask the LLM to redraft a single finding for the current customer.

        Body::
          {
            "slug":     "jane-smith",
            "finding":  { ...current dict... },
            "customer": { ...current customer dict... },
            "provider": "auto"
          }
        Returns the replacement finding dict.
        """
        data = request.get_json(silent=True) or {}
        slug = (data.get("slug") or "").strip()
        finding = data.get("finding") or {}
        customer = data.get("customer") or {}
        provider = (data.get("provider") or "auto").strip().lower()
        if not slug:
            return jsonify({"error": "slug is required"}), 400

        try:
            from scripts.ai_audit import pipeline as ai_pipeline  # noqa: WPS433
        except ImportError as exc:
            return jsonify({"error": f"ai_audit package missing: {exc}"}), 500

        try:
            ctx = ai_pipeline.context_from_kwargs(
                slug=draft_store.safe_slug(slug),
                url=customer.get("app_url") or "https://example.com",
                tier=customer.get("tier") or "Starter Package",
                builder=customer.get("builder") or "Lovable",
                first_name=customer.get("first_name") or "",
                last_name=customer.get("last_name") or "",
                email=customer.get("email") or "",
                app_name=customer.get("app_name") or "",
                platform=customer.get("platform") or yaml_writer.DEFAULT_PLATFORM,
            )
        except SystemExit as exc:
            return jsonify({"error": str(exc) or "invalid customer fields"}), 400

        try:
            new_finding = ai_pipeline.regenerate_finding(
                ctx,
                existing_finding=finding,
                provider=provider,
            )
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": f"regeneration failed: {exc}"}), 500

        return jsonify({"ok": True, "finding": new_finding})


# ---------------------------------------------------------------------------
# Helpers for review-mode bootstrap
# ---------------------------------------------------------------------------


def _load_customer_payload(app: Flask, slug: str) -> dict[str, Any] | None:
    """Load customers/<slug>.yaml into the form-payload shape (if present)."""
    target = app.config["CUSTOMERS_DIR"] / f"{draft_store.safe_slug(slug)}.yaml"
    if not target.exists():
        return None
    try:
        text = target.read_text(encoding="utf-8")
        payload = yaml_writer.yaml_to_form(text)
        return {"payload": payload, "yaml": text, "path": target.name}
    except Exception:
        return None


def _load_feedback(app: Flask, slug: str) -> dict[str, Any] | None:
    try:
        from scripts.ai_audit import feedback as feedback_log  # noqa: WPS433
    except ImportError:
        return None
    data = feedback_log.load(app.config["REPO_ROOT"], draft_store.safe_slug(slug))
    return data or None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def _validate_payload(payload: dict[str, Any], tier_caps: dict[str, int]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []

    customer = payload.get("customer") or {}
    verdict = payload.get("verdict") or {}
    findings = payload.get("findings") or []

    email = (customer.get("email") or "").strip()
    if not email:
        errors.append({"field": "customer.email", "message": "Email is required."})
    elif not _EMAIL_RE.match(email):
        errors.append({"field": "customer.email", "message": "Email format looks invalid."})

    app_url = (customer.get("app_url") or "").strip()
    if not app_url:
        errors.append({"field": "customer.app_url", "message": "App URL is required."})
    elif not _URL_RE.match(app_url):
        errors.append({"field": "customer.app_url", "message": "App URL must start with http:// or https://."})

    tier = (customer.get("tier") or "").strip()
    if tier not in yaml_writer.VALID_TIERS:
        errors.append({"field": "customer.tier", "message": "Choose a valid tier."})

    if not (customer.get("first_name") or "").strip():
        errors.append({"field": "customer.first_name", "message": "First name is required."})

    if not (customer.get("app_name") or "").strip():
        errors.append({"field": "customer.app_name", "message": "App name is required."})

    if not (customer.get("builder") or "").strip():
        errors.append({"field": "customer.builder", "message": "Pick a builder."})

    platform = (customer.get("platform") or yaml_writer.DEFAULT_PLATFORM).strip().lower()
    if platform and platform not in yaml_writer.VALID_PLATFORMS:
        errors.append({
            "field": "customer.platform",
            "message": f"Platform must be one of {', '.join(yaml_writer.VALID_PLATFORMS)}.",
        })

    if not (verdict.get("summary") or "").strip():
        errors.append({"field": "verdict.summary", "message": "Verdict summary is required."})

    if not (verdict.get("narrative") or "").strip():
        errors.append({"field": "verdict.narrative", "message": "Verdict narrative is required."})

    if not findings:
        errors.append({"field": "findings", "message": "Add at least one finding."})

    cap = tier_caps.get(tier)
    if cap and len(findings) > cap:
        errors.append({
            "field": "findings",
            "message": f"{tier} caps at {cap} findings; this audit has {len(findings)}.",
        })

    for i, finding in enumerate(findings):
        for key in ("severity", "title", "what_we_saw", "why_it_matters", "fix_prompt"):
            val = (finding.get(key) or "").strip() if isinstance(finding.get(key), str) else finding.get(key)
            if not val:
                errors.append({"field": f"findings[{i}].{key}", "message": f"Finding {i + 1}: {key.replace('_', ' ')} is required."})
        sev = (finding.get("severity") or "").strip().lower()
        if sev and sev not in yaml_writer.VALID_SEVERITIES:
            errors.append({"field": f"findings[{i}].severity", "message": f"Finding {i + 1}: severity must be one of {', '.join(yaml_writer.VALID_SEVERITIES)}."})

    # QSG is part of every paid tier's deliverable per PRODUCT-DECISIONS.md §8,
    # but the form only hard-enforces it on Scale Up + Pro (the deeper tiers
    # where it's a marketing promise). For Starter, the QSG card is shown so
    # Rob can fill it in, but the audit can still ship without one if the
    # customer's app is too thin to write a useful guide for.
    if tier in ("Scale Up Package", "Pro Package"):
        qsg = payload.get("quick_start_guide") or {}
        if not (qsg.get("title") or "").strip():
            errors.append({"field": "qsg.title", "message": f"Quick Start Guide title is required for {tier}."})
        if not (qsg.get("intro") or "").strip():
            errors.append({"field": "qsg.intro", "message": f"Quick Start Guide intro is required for {tier}."})
        steps = qsg.get("steps") or []
        non_empty_steps = [s for s in steps if isinstance(s, dict) and ((s.get("title") or "").strip() or (s.get("body") or "").strip())]
        if not non_empty_steps:
            errors.append({"field": "qsg.steps", "message": "Add at least one Quick Start Guide step."})

    return errors
