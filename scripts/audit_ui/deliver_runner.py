"""Shell out to ``scripts/deliver_report.py`` and stream its output.

The audit UI's "Save + send PDFs" button calls this module's
``run_deliver`` helper. We spawn a subprocess with line-buffered output and
stream stdout+stderr lines back to the caller via a callback. The caller
in ``audit_ui.app`` accumulates the lines into an in-memory log buffer
that the browser polls via long-poll/SSE.

We pass ``--yes`` to skip the interactive ``Send now?`` prompt because
there is no TTY when we shell out.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from collections.abc import Callable
from pathlib import Path


def run_deliver(
    repo_root: Path,
    customer_yaml: Path,
    *,
    send: bool,
    qsg_link: str | None = None,
    on_line: Callable[[str], None] | None = None,
    extra_env: dict[str, str] | None = None,
) -> int:
    """Run ``deliver_report.py`` and return its exit code.

    Lines from stdout/stderr are forwarded to ``on_line`` as they arrive.
    Stderr is merged into stdout so log ordering matches what Rob would
    see if he'd run the script himself.
    """
    script = repo_root / "scripts" / "deliver_report.py"
    if not script.exists():
        raise FileNotFoundError(f"deliver_report.py not found at {script}")

    cmd: list[str] = [
        sys.executable,
        "-u",
        str(script),
        "--customer",
        str(customer_yaml),
        "--no-open",
    ]
    if send:
        cmd.append("--send")
        cmd.append("--yes")
    if qsg_link:
        cmd.extend(["--qsg-link", qsg_link])

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    if extra_env:
        env.update(extra_env)

    if on_line:
        on_line(f"$ {' '.join(_shell_quote(c) for c in cmd)}")

    proc = subprocess.Popen(
        cmd,
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    if proc.stdout is None:
        proc.wait()
        return proc.returncode

    for line in iter(proc.stdout.readline, ""):
        if on_line:
            on_line(line.rstrip("\r\n"))
    proc.stdout.close()
    proc.wait()

    if on_line:
        on_line(f"[deliver_report.py exited with code {proc.returncode}]")

    return proc.returncode


def run_deliver_in_thread(
    repo_root: Path,
    customer_yaml: Path,
    *,
    send: bool,
    qsg_link: str | None = None,
    on_line: Callable[[str], None] | None = None,
    on_exit: Callable[[int], None] | None = None,
) -> threading.Thread:
    """Launch ``run_deliver`` on a background thread; return the Thread."""

    def _target() -> None:
        try:
            rc = run_deliver(
                repo_root,
                customer_yaml,
                send=send,
                qsg_link=qsg_link,
                on_line=on_line,
            )
        except Exception as exc:  # noqa: BLE001 — surface failure to UI
            if on_line:
                on_line(f"[error] {exc}")
            rc = 1
        if on_exit:
            on_exit(rc)

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()
    return thread


def _shell_quote(value: str) -> str:
    if not value or any(ch in value for ch in ' "\t\n'):
        return '"' + value.replace('"', r"\"") + '"'
    return value
