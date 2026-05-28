"""Stable customer slug from email + hostname."""

from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse


def slug_from_email_url(email: str, url: str) -> str:
    host = (urlparse(url).hostname or "site").lower()
    host = re.sub(r"^www\.", "", host)
    host_slug = re.sub(r"[^a-z0-9]+", "-", host).strip("-")[:40]
    local = (email or "user").split("@")[0].lower()
    local_slug = re.sub(r"[^a-z0-9]+", "-", local).strip("-")[:24]
    # Append a 6-char hex suffix derived from the email so two different
    # accounts sharing the same hostname (e.g. john@myapp vs jane@myapp)
    # produce distinct slugs and never collide on disk.
    # NOTE: existing customers/{slug}.yaml files created before this change
    # use the old format (no suffix). Do NOT rename/migrate them.
    email_suffix = hashlib.sha256(email.lower().encode()).hexdigest()[:6]
    base = f"{local_slug}-{host_slug}-{email_suffix}".strip("-")
    return base or "audit-customer"
