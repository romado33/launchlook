"""LaunchLook audit UI package.

Tiny local web form that captures findings during a manual app review and
auto-generates the customer YAML file consumed by ``scripts/deliver_report.py``.

The Flask app lives at ``scripts.audit_ui.app`` and the CLI entry point is
``scripts/audit_ui.py``.
"""
