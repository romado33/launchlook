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

import re
import threading
import time
from collections import deque
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request, send_from_directory

from . import deliver_runner, draft_store, yaml_writer

# ---------------------------------------------------------------------------
# Tier-cap discovery — read the cap values from deliver_report.py at startup
# so future cap changes there auto-propagate without a code edit here.
# ---------------------------------------------------------------------------


_DEFAULT_TIER_CAPS = {"Starter Package": 10, "Scale Up Package": 30, "Pro Package": 40}

# Match the dict-lookup cap form used by deliver_report.py:
#   cap = {"Starter Package": 10, "Scale Up Package": 30, "Pro Package": 40}.get(tier, 30)
# Captures every "Tier Name": <int> pair so the UI auto-tracks future tier
# additions (e.g. Pro Package) without a code edit here.
_TIER_CAP_DICT_PATTERN = re.compile(r"cap\s*=\s*\{(?P<body>[^}]*)\}\s*\.get\(\s*tier")
_TIER_CAP_ENTRY_PATTERN = re.compile(r'["\'](?P<tier>[^"\']+)["\']\s*:\s*(?P<cap>\d+)')


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

    @app.route("/review/<slug>")
    def review_slug(slug: str) -> str:
        """Direct link from notification emails — opens the AI review UI for <slug>."""
        return render_template(
            "index.html",
            tier_caps=app.config["TIER_CAPS"],
            severities=yaml_writer.VALID_SEVERITIES,
            tiers=yaml_writer.VALID_TIERS,
            builders=yaml_writer.VALID_BUILDERS,
            platforms=yaml_writer.VALID_PLATFORMS,
            default_platform=yaml_writer.DEFAULT_PLATFORM,
            review_ai=True,
            review_slug=slug,
        )

    @app.route("/preview/<slug>")
    def preview_slug(slug: str) -> Any:
        """Live HTML preview of the main report — same template as the PDF."""
        import sys

        from flask import Response

        safe = draft_store.safe_slug(slug)
        yaml_path = app.config["CUSTOMERS_DIR"] / f"{safe}.yaml"
        if not yaml_path.exists():
            return Response(
                f"<pre>No customers/{safe}.yaml found. Run the audit first.</pre>",
                status=404,
                mimetype="text/html",
            )

        doc = request.args.get("doc", "report")

        try:
            sys.path.insert(0, str(app.config["REPO_ROOT"]))
            from scripts.deliver_report import (  # noqa: WPS433
                build_jinja_env,
                load_customer_yaml,
                render_main_report_html,
                render_pre_launch_checklist_html,
                render_qsg_html,
                render_user_guide_html,
            )
        except ImportError as exc:
            return Response(f"<pre>Import error: {exc}</pre>", status=500, mimetype="text/html")

        data = load_customer_yaml(yaml_path)
        env = build_jinja_env()
        now = datetime.now(UTC).strftime("%B %-d, %Y") if sys.platform != "win32" else datetime.now(UTC).strftime("%B %#d, %Y")

        tier = (data.get("customer") or {}).get("tier", "")
        has_user_guide = tier in ("Scale Up Package", "Pro Package")

        nav = (
            '<div style="position:fixed;top:0;left:0;right:0;z-index:9999;'
            'background:#1a1a2e;color:#fff;padding:8px 16px;font-family:sans-serif;'
            'font-size:13px;display:flex;gap:16px;align-items:center;flex-wrap:wrap;">'
            f'<strong>LaunchLook Preview</strong> &nbsp;|&nbsp; slug: <code>{safe}</code>'
            f' &nbsp;|&nbsp; <a href="/preview/{safe}?doc=report" style="color:#7eb8f7">Main Report</a>'
            f' &nbsp;|&nbsp; <a href="/preview/{safe}?doc=qsg" style="color:#7eb8f7">Quick Start Guide</a>'
        )
        if has_user_guide:
            nav += f' &nbsp;|&nbsp; <a href="/preview/{safe}?doc=user_guide" style="color:#7eb8f7">User Guide</a>'
        nav += (
            f' &nbsp;|&nbsp; <a href="/preview/{safe}?doc=checklist" style="color:#7eb8f7">Checklist</a>'
            f' &nbsp;|&nbsp; <a href="/review/{safe}" style="color:#a0d8a0">&#9998; Edit</a>'
            "</div>"
            '<div style="margin-top:48px;">'
        )

        if doc == "qsg":
            html = render_qsg_html(env, data, now)
            if not html:
                return Response(
                    "<pre>No Quick Start Guide in this YAML yet. Run the pipeline first.</pre>",
                    status=404,
                    mimetype="text/html",
                )
        elif doc == "user_guide":
            html = render_user_guide_html(env, data, now)
            if not html:
                msg = (
                    "<pre>No User Guide in this YAML. "
                    "User Guide is generated for Scale Up and Pro tiers only.</pre>"
                    if not has_user_guide
                    else "<pre>No User Guide in this YAML yet. Run the pipeline first.</pre>"
                )
                return Response(msg, status=404, mimetype="text/html")
        elif doc == "checklist":
            html = render_pre_launch_checklist_html(env, data, now)
        else:
            html = render_main_report_html(env, data, now, qsg_link=None)

        return Response(nav + html + "</div>", mimetype="text/html")

    @app.route("/api/bootstrap")
    def api_bootstrap() -> Any:
        prefill = app.config["PREFILL"]
        slug = (request.args.get("slug") or prefill.get("slug") or "").strip()
        # Support ?review_ai=1 so /review/<slug> links work without restarting the server.
        review_ai = app.config["REVIEW_AI"] or request.args.get("review_ai") == "1"
        existing_draft = None
        existing_customer = None
        feedback_record = None
        if slug:
            existing_draft = draft_store.load_draft(app.config["DRAFTS_DIR"], slug)
            if review_ai:
                existing_customer = _load_customer_payload(app, slug)
                feedback_record = _load_feedback(app, slug)
        return jsonify(
            {
                "slug": slug,
                "prefill": prefill,
                "draft": existing_draft,
                "review_ai": review_ai,
                "customer": existing_customer,
                "feedback": feedback_record,
                "tier_caps": app.config["TIER_CAPS"],
                "severities": list(yaml_writer.VALID_SEVERITIES),
                "tiers": list(yaml_writer.VALID_TIERS),
                "builders": list(yaml_writer.VALID_BUILDERS),
                "platforms": list(yaml_writer.VALID_PLATFORMS),
                "default_platform": yaml_writer.DEFAULT_PLATFORM,
            }
        )

    @app.route("/api/draft", methods=["POST"])
    def api_draft_save() -> Any:
        data = request.get_json(silent=True) or {}
        slug = (data.get("slug") or "").strip()
        payload = data.get("payload") or {}
        if not slug:
            return jsonify({"error": "slug is required"}), 400
        path = draft_store.save_draft(app.config["DRAFTS_DIR"], slug, payload)
        return jsonify(
            {
                "ok": True,
                "path": str(path.relative_to(app.config["REPO_ROOT"])),
                "saved_at": datetime.now(UTC).isoformat(),
            }
        )

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
            return (
                jsonify(
                    {
                        "ok": False,
                        "errors": [
                            {
                                "field": "_global",
                                "message": f"YAML serialization failed: {exc}",
                            }
                        ],
                    }
                ),
                400,
            )

        customers_dir = app.config["CUSTOMERS_DIR"]
        customers_dir.mkdir(parents=True, exist_ok=True)
        target = customers_dir / f"{draft_store.safe_slug(slug)}.yaml"
        target.write_text(yaml_text, encoding="utf-8")

        return jsonify(
            {
                "ok": True,
                "yaml": yaml_text,
                "path": str(target.relative_to(app.config["REPO_ROOT"])),
            }
        )

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
            items.append(
                {
                    "slug": path.stem,
                    "filename": path.name,
                    "modified": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
                    "size": stat.st_size,
                }
            )
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
            return (
                jsonify({"error": f"Unsupported image extension: {ext or '(none)'}"}),
                400,
            )

        clean_slug = draft_store.safe_slug(slug)
        target_dir = app.config["SCREENSHOTS_DIR"] / clean_slug
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"finding-{finding_index + 1}{ext}"
        upload.save(target)

        rel = target.relative_to(app.config["REPO_ROOT"]).as_posix()
        return jsonify(
            {
                "ok": True,
                "path": rel,
                "url": f"/screenshots/{clean_slug}/{target.name}",
                "filename": target.name,
            }
        )

    @app.route("/screenshots/<path:relpath>")
    def serve_screenshot(relpath: str) -> Any:
        return send_from_directory(app.config["SCREENSHOTS_DIR"], relpath)

    @app.route("/api/deliver", methods=["POST"])
    def api_deliver() -> Any:
        deliver_log: DeliverLog = app.config["DELIVER_LOG"]
        if deliver_log.running:
            return (
                jsonify({"ok": False, "error": "Another deliver job is already running."}),
                409,
            )

        data = request.get_json(silent=True) or {}
        slug = (data.get("slug") or "").strip()
        send = bool(data.get("send", False))
        force = request.args.get("force") == "1"
        if not slug:
            return jsonify({"error": "slug is required"}), 400

        clean = draft_store.safe_slug(slug)
        customer_yaml = app.config["CUSTOMERS_DIR"] / f"{clean}.yaml"
        if not customer_yaml.exists():
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": f"Customer YAML missing: {customer_yaml.name}. Click 'Generate YAML' first.",
                    }
                ),
                400,
            )

        # P1 #14: Block send while the pipeline is still processing this job.
        # If the Notion row Notes contain [automation:processing] without a
        # subsequent [automation:draft_ready], the pipeline is in-flight.
        # Allow override via ?force=1 so Rob can bypass a crashed-but-marked run.
        if send and not force:
            try:

                from api._lib.notion_helpers import (  # noqa: PLC0415
                    find_customer_by_email,
                    get_client,
                    get_customers_ds_id,
                )
                try:
                    import yaml as _yaml  # noqa: PLC0415
                    _cdata = _yaml.safe_load(customer_yaml.read_text(encoding="utf-8")) or {}
                    _email = (_cdata.get("customer") or {}).get("email") or ""
                except Exception:
                    _email = ""
                if _email:
                    _nc = get_client()
                    _ds = get_customers_ds_id(_nc)
                    _row = find_customer_by_email(_nc, _ds, _email)
                    if _row:
                        _notes = ""
                        _note_prop = (_row.get("properties") or {}).get("Notes") or {}
                        _rt = _note_prop.get("rich_text") or []
                        _notes = "".join(x.get("plain_text", "") for x in _rt)
                        _notes_lower = _notes.lower()
                        if (
                            "[automation:processing]" in _notes_lower
                            and "[automation:draft_ready]" not in _notes_lower
                        ):
                            return (
                                jsonify(
                                    {
                                        "ok": False,
                                        "error": (
                                            "Pipeline still processing this job — "
                                            "wait for draft_ready before sending. "
                                            "Add ?force=1 to override."
                                        ),
                                    }
                                ),
                                409,
                            )
            except Exception:  # noqa: BLE001
                pass  # Notion unavailable — allow send to proceed

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

    @app.route("/api/queue-status")
    def api_queue_status() -> Any:
        """Return live queue state from Notion for the dashboard panel.

        Gracefully returns an error key (never raises) so the UI can show
        a 'Notion unavailable' message without crashing the portal.
        """
        try:
            from api._lib.notion_helpers import (  # noqa: PLC0415
                STATUS_DELIVERED,
                get_client,
                get_customers_ds_id,
            )
            from scripts.audit_automation.discover import (  # noqa: PLC0415
                discover_all,
            )
            from scripts.stale_queue_alert import (  # noqa: PLC0415
                DEFAULT_THRESHOLD_HOURS,
                find_stale_rows,
            )

            # Pending jobs (same query the worker uses)
            pending = discover_all()

            # Stale rows
            stale = find_stale_rows(DEFAULT_THRESHOLD_HOURS)
            stale_ids = {r["page_id"] for r in stale}

            # Delivered this week
            client = get_client()
            cust_ds = get_customers_ds_id(client)
            now_utc = datetime.now(UTC)
            week_start = (now_utc - timedelta(days=now_utc.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            resp = client.data_sources.query(
                data_source_id=cust_ds,
                filter={
                    "and": [
                        {"property": "Status", "select": {"equals": STATUS_DELIVERED}},
                        {
                            "timestamp": "last_edited_time",
                            "last_edited_time": {"on_or_after": week_start.isoformat()},
                        },
                    ]
                },
                page_size=50,
            )
            delivered_this_week = len([
                r for r in resp.get("results", [])
                if not (r.get("archived") or r.get("in_trash"))
            ])

            rows = []
            for job in pending:
                rows.append({
                    "slug": job.slug,
                    "email": job.email,
                    "tier": job.tier,
                    "kind": job.kind.value,
                    "notion_db": job.notion_db,
                    "stale": job.notion_page_id in stale_ids,
                })

            # Also include stale paid rows that aren't in pending
            # (Paid/In Progress rows don't appear in discover_all)
            pending_page_ids = {j.notion_page_id for j in pending}
            for r in stale:
                if r["page_id"] not in pending_page_ids:
                    rows.append({
                        "slug": "",
                        "email": r["email"],
                        "tier": r["tier"],
                        "kind": "paid",
                        "notion_db": r["db"],
                        "stale": True,
                        "status": r["status"],
                    })

            return jsonify({
                "ok": True,
                "pending": len(rows),
                "stale": len(stale),
                "delivered_this_week": delivered_this_week,
                "threshold_hours": DEFAULT_THRESHOLD_HOURS,
                "rows": rows,
                "checked_at": datetime.now(UTC).isoformat(),
            })

        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": str(exc)}), 200

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
        errors.append(
            {
                "field": "customer.app_url",
                "message": "App URL must start with http:// or https://.",
            }
        )

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
        errors.append(
            {
                "field": "customer.platform",
                "message": f"Platform must be one of {', '.join(yaml_writer.VALID_PLATFORMS)}.",
            }
        )

    if not (verdict.get("summary") or "").strip():
        errors.append({"field": "verdict.summary", "message": "Verdict summary is required."})

    if not (verdict.get("narrative") or "").strip():
        errors.append({"field": "verdict.narrative", "message": "Verdict narrative is required."})

    if not findings:
        errors.append({"field": "findings", "message": "Add at least one finding."})

    cap = tier_caps.get(tier)
    if cap and len(findings) > cap:
        errors.append(
            {
                "field": "findings",
                "message": f"{tier} caps at {cap} findings; this audit has {len(findings)}.",
            }
        )

    for i, finding in enumerate(findings):
        for key in ("severity", "title", "what_we_saw", "why_it_matters", "fix_prompt"):
            val = (
                (finding.get(key) or "").strip()
                if isinstance(finding.get(key), str)
                else finding.get(key)
            )
            if not val:
                errors.append(
                    {
                        "field": f"findings[{i}].{key}",
                        "message": f"Finding {i + 1}: {key.replace('_', ' ')} is required.",
                    }
                )
        sev = (finding.get("severity") or "").strip().lower()
        if sev and sev not in yaml_writer.VALID_SEVERITIES:
            errors.append(
                {
                    "field": f"findings[{i}].severity",
                    "message": f"Finding {i + 1}: severity must be one of {', '.join(yaml_writer.VALID_SEVERITIES)}.",
                }
            )

    # QSG is part of every paid tier's deliverable per PRODUCT-DECISIONS.md §8,
    # but the form only hard-enforces it on Scale Up + Pro (the deeper tiers
    # where it's a marketing promise). For Starter, the QSG card is shown so
    # Rob can fill it in, but the audit can still ship without one if the
    # customer's app is too thin to write a useful guide for.
    if tier in ("Scale Up Package", "Pro Package"):
        qsg = payload.get("quick_start_guide") or {}
        if not (qsg.get("title") or "").strip():
            errors.append(
                {
                    "field": "qsg.title",
                    "message": f"Quick Start Guide title is required for {tier}.",
                }
            )
        if not (qsg.get("intro") or "").strip():
            errors.append(
                {
                    "field": "qsg.intro",
                    "message": f"Quick Start Guide intro is required for {tier}.",
                }
            )
        steps = qsg.get("steps") or []
        non_empty_steps = [
            s
            for s in steps
            if isinstance(s, dict)
            and ((s.get("title") or "").strip() or (s.get("body") or "").strip())
        ]
        if not non_empty_steps:
            errors.append(
                {
                    "field": "qsg.steps",
                    "message": "Add at least one Quick Start Guide step.",
                }
            )

    return errors
