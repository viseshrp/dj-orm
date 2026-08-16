#!/usr/bin/env python3
"""Run djrm end-to-end tests against disposable Docker databases."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COMPOSE_FILE = ROOT / "tests" / "e2e" / "compose.yaml"
PROJECT = f"djrm-e2e-{os.getpid()}"


def compose(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "docker",
            "compose",
            "--project-name",
            PROJECT,
            "--file",
            str(COMPOSE_FILE),
            *args,
        ],
        cwd=ROOT,
        check=check,
        text=True,
    )


def verify_oracle_dbshell() -> None:
    environment = dict(os.environ)
    environment.update(
        {
            "DJRM_E2E_BACKEND": "oracle",
            "DJRM_E2E_PROJECT": PROJECT,
            "DJRM_ORACLE_NAME": "oracle:1521/FREEPDB1",
            "PATH": f"{ROOT / 'tests' / 'e2e' / 'bin'}{os.pathsep}{environment['PATH']}",
            "PYTHONPATH": os.pathsep.join(
                path
                for path in (str(ROOT / "tests"), str(ROOT), environment.get("PYTHONPATH"))
                if path
            ),
        }
    )
    subprocess.run(
        [
            "uv",
            "run",
            "--isolated",
            "--extra",
            "oracle",
            "python",
            "tests/e2e/verify_dbshell.py",
            "oracle",
        ],
        cwd=ROOT,
        env=environment,
        check=True,
    )


def main() -> int:
    try:
        compose("up", "--detach", "--build", "--wait", "postgres", "mysql", "oracle")
        compose("run", "--rm", "--build", "runner")
        verify_oracle_dbshell()
    finally:
        compose(
            "down",
            "--volumes",
            "--remove-orphans",
            "--rmi",
            "local",
            check=False,
        )
    print("All external database end-to-end tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
