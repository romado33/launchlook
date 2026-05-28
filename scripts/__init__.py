"""LaunchLook scripts package.

Marks ``scripts/`` as a real Python package so Vercel's Python runtime
bundles top-level modules (e.g. ``scripts/launchlook_constants.py``)
when ``api/*.py`` functions import from them. Sub-packages already have
their own ``__init__.py``; this file is required so that direct imports
like ``from scripts.launchlook_constants import FREE_AUDIT_DELIVER_COUNT``
also work at function cold-start.
"""
