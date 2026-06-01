"""Print Confidence Checks Notion DB property names and types."""

from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(REPO_ROOT, ".env")


def main() -> int:
    if not os.path.isfile(ENV_PATH):
        sys.exit(f"Missing {ENV_PATH}")
    with open(ENV_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

    db_id = (os.getenv("NOTION_CONFIDENCE_CHECK_DB_ID") or "").strip()
    token = (os.getenv("NOTION_TOKEN") or "").strip()
    if not db_id or not token:
        sys.exit("NOTION_CONFIDENCE_CHECK_DB_ID and NOTION_TOKEN required")

    from notion_client import Client

    client = Client(auth=token)
    db = client.databases.retrieve(database_id=db_id)
    props = db.get("properties") or {}
    for name in sorted(props):
        spec = props[name]
        t = spec.get("type", "?")
        extra = ""
        if t == "select":
            opts = [o["name"] for o in (spec.get("select", {}).get("options") or [])]
            extra = f"  options={opts}"
        print(f"{name}: {t}{extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
