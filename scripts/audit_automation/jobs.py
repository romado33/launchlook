"""Job model for the audit automation queue."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class JobKind(str, Enum):
    FREE = "free"
    PAID = "paid"


@dataclass
class AuditJob:
    kind: JobKind
    slug: str
    url: str
    email: str
    tier: str
    builder: str
    platform: str
    app_name: str
    name: str
    intake_notes: str
    notion_page_id: str
    notion_db: str  # "free_audit" | "customers"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditJob:
        return cls(
            kind=JobKind(data["kind"]),
            slug=str(data["slug"]),
            url=str(data["url"]),
            email=str(data["email"]),
            tier=str(data["tier"]),
            builder=str(data.get("builder") or "Lovable"),
            platform=str(data.get("platform") or "vibe-coder"),
            app_name=str(data.get("app_name") or ""),
            name=str(data.get("name") or ""),
            intake_notes=str(data.get("intake_notes") or ""),
            notion_page_id=str(data["notion_page_id"]),
            notion_db=str(data["notion_db"]),
        )
