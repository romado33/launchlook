"""Run ai_audit pipeline for one job; update Notion; email founder (never customer)."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from api._lib.env import require_env  # noqa: E402
from api._lib.notion_helpers import (  # noqa: E402
    STATUS_IN_PROGRESS,
    get_client,
    update_customer_fields,
)
from scripts.ai_audit import pipeline as ai_pipeline  # noqa: E402
from scripts.audit_automation.jobs import AuditJob, JobKind  # noqa: E402
from scripts.audit_automation.notify import send_draft_ready_email  # noqa: E402
from scripts.launchlook_constants import (  # noqa: E402
    FREE_AUDIT_DELIVER_COUNT,
    FREE_AUDIT_PIPELINE_TIER,
)

FREE_STATUS_PROCESSING = "processing"
FREE_STATUS_DRAFT_READY = "draft_ready"
FREE_STATUS_FAILED = "failed"


def _write_form_smoke_stub(job: AuditJob) -> None:
    """Optional YAML stub so Pro email round-trip can target customer inbox."""
    path = REPO_ROOT / "customers" / f"{job.slug}.yaml"
    if path.exists():
        return
    lines = [
        "form_smoke_test:",
        "  enabled: true",
        "  blocked_forms: []",
    ]
    if job.tier == "Pro Package" and job.email:
        lines.append(f"  customer_email: {job.email}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _set_free_audit_status(page_id: str, status: str) -> None:
    client = get_client()
    ds_id = require_env("NOTION_FREE_AUDIT_DB_ID")
    db = client.databases.retrieve(database_id=ds_id)
    sources = db.get("data_sources") or []
    if not sources:
        return
    client.pages.update(
        page_id=page_id,
        properties={"Status": {"select": {"name": status}}},
    )


def _mark_paid_draft_ready(job: AuditJob, *, findings_count: int) -> None:
    client = get_client()
    update_customer_fields(
        client,
        job.notion_page_id,
        {
            "status": STATUS_IN_PROGRESS,
            "notes": (
                f"[automation:draft_ready] {findings_count} findings in "
                f"customers/{job.slug}.yaml — review before send.\n"
                f"{job.intake_notes}"
            ).strip(),
        },
    )


def process_job(job: AuditJob, *, provider: str = "auto", dry_run: bool = False) -> bool:
    """Returns True on success."""
    print(f"[automation] start {job.kind.value} slug={job.slug} tier={job.tier}")

    if job.kind == JobKind.FREE and not dry_run:
        try:
            _set_free_audit_status(job.notion_page_id, FREE_STATUS_PROCESSING)
        except Exception as exc:  # noqa: BLE001
            print(f"[automation] WARN: could not set processing: {exc}")

    if not dry_run:
        _write_form_smoke_stub(job)

    parts = (job.name or "").strip().split(None, 1)
    first = parts[0] if parts else "Customer"
    last = parts[1] if len(parts) > 1 else ""

    tier = job.tier
    max_findings = None
    if job.kind == JobKind.FREE:
        tier = FREE_AUDIT_PIPELINE_TIER
        max_findings = 10

    ctx = ai_pipeline.CustomerContext(
        slug=job.slug,
        url=job.url,
        tier=tier,
        builder=job.builder,
        first_name=first,
        last_name=last,
        email=job.email,
        app_name=job.app_name or job.slug,
        intake_notes=job.intake_notes,
        platform=job.platform,
    )

    try:
        result = ai_pipeline.run(
            ctx,
            provider=provider,
            dry_run=dry_run,
            max_findings=max_findings,
        )
        form_smoke_ran = result.form_smoke_ran
        form_smoke_failed = list(result.form_smoke_failed_check_ids)
        email_roundtrip_ran = result.email_roundtrip_attempted
    except Exception as exc:  # noqa: BLE001
        err = f"{exc}\n{traceback.format_exc()}"
        print(f"[automation] FAILED: {exc}", file=sys.stderr)
        if not dry_run:
            if job.kind == JobKind.FREE:
                try:
                    _set_free_audit_status(job.notion_page_id, FREE_STATUS_FAILED)
                except Exception:
                    pass
            send_draft_ready_email(
                job,
                findings_count=0,
                yaml_rel="",
                form_smoke_ran=False,
                form_smoke_failed=[],
                email_roundtrip_ran=False,
                error=err,
            )
        return False

    yaml_rel = (
        str(result.yaml_path.relative_to(REPO_ROOT))
        if result.yaml_path
        else f"customers/{job.slug}.yaml"
    )

    if not dry_run:
        if job.kind == JobKind.FREE:
            _set_free_audit_status(job.notion_page_id, FREE_STATUS_DRAFT_READY)
        else:
            _mark_paid_draft_ready(job, findings_count=result.findings_count)

        send_draft_ready_email(
            job,
            findings_count=result.findings_count,
            yaml_rel=yaml_rel,
            form_smoke_ran=form_smoke_ran,
            form_smoke_failed=form_smoke_failed,
            email_roundtrip_ran=email_roundtrip_ran,
        )

    print(
        f"[automation] done slug={job.slug} findings={result.findings_count} "
        f"(free deliver cap={FREE_AUDIT_DELIVER_COUNT})"
    )
    return True
