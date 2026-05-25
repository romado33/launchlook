"""
customer_loader.py - shared loader for prep scripts (screenshots + prescreener).

Both prep scripts accept --customer-id (a Notion page id, prefix of a page id,
or a slug derived from name/app name) and need the same data: name, email,
app url. This module centralises that lookup so the two scripts stay in sync.

A --url override is supported so Rob can smoke-test the scripts against any
public site without touching Notion.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ROOT = REPO_ROOT / "output" / "customers"


@dataclass
class Customer:
    """Minimal data the prep scripts need."""

    page_id: str | None
    slug: str
    name: str
    email: str
    app_url: str

    @property
    def output_dir(self) -> Path:
        return OUTPUT_ROOT / self.slug


# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------

_SLUG_BAD = re.compile(r"[^a-z0-9-]+")


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", "-", text)
    text = _SLUG_BAD.sub("-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or f"customer-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"


def slug_from_url(url: str) -> str:
    host = urlparse(url).hostname or url
    return slugify(host)


# ---------------------------------------------------------------------------
# Notion lookup
# ---------------------------------------------------------------------------


def _matches_id(row: dict, customer_id: str) -> bool:
    """Match by full id, hyphen-stripped id, or prefix on either form."""
    raw = (row.get("id") or "").lower()
    norm = raw.replace("-", "")
    needle = customer_id.lower().replace("-", "")
    return raw.startswith(customer_id.lower()) or norm.startswith(needle)


def _get_title(prop: dict | None) -> str:
    if not prop or not prop.get("title"):
        return ""
    return prop["title"][0].get("plain_text", "")


def _get_text(prop: dict | None) -> str:
    if not prop:
        return ""
    if prop.get("title"):
        return prop["title"][0].get("plain_text", "")
    if prop.get("rich_text"):
        return prop["rich_text"][0].get("plain_text", "")
    return ""


def _get_email(prop: dict | None) -> str:
    if not prop:
        return ""
    return prop.get("email") or ""


def _get_url(prop: dict | None) -> str:
    if not prop:
        return ""
    return prop.get("url") or ""


def load_customer_from_notion(customer_id: str) -> Customer:
    """Look up a customer row by Notion page id (or a unique prefix)."""
    token = os.getenv("NOTION_TOKEN")
    db_id = os.getenv("NOTION_CUSTOMERS_DB_ID")
    if not token or not db_id:
        sys.exit(
            "ERROR: NOTION_TOKEN and NOTION_CUSTOMERS_DB_ID must be set "
            "(or pass --url for a smoke test)."
        )
    try:
        from notion_client import Client
    except ImportError:
        sys.exit("ERROR: pip install notion-client (see requirements-automation.txt)")

    client = Client(auth=token)
    db = client.databases.retrieve(database_id=db_id)
    ds_id = db["data_sources"][0]["id"]

    # Try a direct retrieve first; falls back to a scan if it isn't a full id.
    try:
        page = client.pages.retrieve(page_id=customer_id)
        return _row_to_customer(page)
    except Exception:
        pass

    cursor = None
    while True:
        resp = client.data_sources.query(
            data_source_id=ds_id, page_size=100, start_cursor=cursor
        )
        for row in resp.get("results", []):
            if row.get("archived") or row.get("in_trash"):
                continue
            if _matches_id(row, customer_id):
                return _row_to_customer(row)
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")

    sys.exit(f"ERROR: no Customers DB row matches id/prefix {customer_id!r}")


def _row_to_customer(row: dict) -> Customer:
    props = row.get("properties", {})
    name = _get_title(props.get("Name")) or "(untitled)"
    email = _get_email(props.get("Email"))
    app_url = _get_url(props.get("App URL"))
    app_name = _get_text(props.get("App Name"))
    slug = slugify(app_name or name) if (app_name or name) else slug_from_url(app_url)
    return Customer(
        page_id=row.get("id"),
        slug=slug,
        name=name,
        email=email,
        app_url=app_url,
    )


# ---------------------------------------------------------------------------
# Public entry point (used by both prep scripts)
# ---------------------------------------------------------------------------


def load_customer(customer_id: str | None, url_override: str | None) -> Customer:
    """Resolve a Customer from either Notion id or a raw URL override."""
    if url_override:
        slug = slug_from_url(url_override)
        return Customer(
            page_id=None,
            slug=slug,
            name=f"smoke-test ({slug})",
            email="",
            app_url=url_override,
        )
    if not customer_id:
        sys.exit("ERROR: pass --customer-id <notion-page-id> or --url <url>.")
    customer = load_customer_from_notion(customer_id)
    if not customer.app_url:
        sys.exit(
            f"ERROR: customer {customer.name!r} has no App URL in Notion. "
            "Fill it in (or pass --url for a one-off run)."
        )
    return customer
