"""Stable customer slug from email + hostname."""

from __future__ import annotations

import re
from urllib.parse import urlparse


def slug_from_email_url(email: str, url: str) -> str:
    host = (urlparse(url).hostname or "site").lower()
    host = re.sub(r"^www\.", "", host)
    host_slug = re.sub(r"[^a-z0-9]+", "-", host).strip("-")[:40]
    local = (email or "user").split("@")[0].lower()
    local_slug = re.sub(r"[^a-z0-9]+", "-", local).strip("-")[:24]
    base = f"{local_slug}-{host_slug}".strip("-")
    return base or "audit-customer"
