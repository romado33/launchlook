#!/usr/bin/env python3
"""Regenerate the public sample Main Report PDF from example-jane-sparkle.yaml.

Writes landing/samples/sparkle-marketplace-main-report.pdf (served at /sample).
Does not regenerate shareable /r/ pages or email customers.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
YAML = REPO_ROOT / "customers" / "example-jane-sparkle.yaml"
OUT_PDF = REPO_ROOT / "output" / "reports" / "jane-sparkle-marketplace" / "main-report.pdf"
PUBLIC_PDF = REPO_ROOT / "landing" / "samples" / "sparkle-marketplace-main-report.pdf"


def main() -> int:
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "deliver_report.py"),
        "--customer",
        str(YAML),
        "--no-open",
    ]
    print("→", " ".join(cmd))
    rc = subprocess.call(cmd)
    if rc != 0:
        return rc
    if not OUT_PDF.is_file():
        print(f"ERROR: expected {OUT_PDF}", file=sys.stderr)
        return 1
    PUBLIC_PDF.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(OUT_PDF, PUBLIC_PDF)
    print(f"✓ copied to {PUBLIC_PDF.relative_to(REPO_ROOT)}")
    print("  Deployed URL: https://launchlook.app/sample (redirects to PDF)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
