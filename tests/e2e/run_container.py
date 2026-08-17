from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def run(script: str, backend: str | None = None) -> None:
    environment = dict(os.environ)
    if backend is not None:
        environment["DJRM_E2E_BACKEND"] = backend
    subprocess.run(
        [sys.executable, str(ROOT / "tests" / "e2e" / script), *([backend] if backend else [])],
        cwd=ROOT,
        env=environment,
        check=True,
    )


def run_retained_suite(backend: str) -> None:
    environment = dict(os.environ)
    environment["DJRM_E2E_BACKEND"] = backend
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "tests" / "runtests.py"),
            "--settings=e2e.full_suite_settings",
            "--verbosity=1",
            "--parallel=1",
        ],
        cwd=ROOT,
        env=environment,
        check=True,
    )
    print(f"DJRM_{backend.upper()}_RETAINED_SUITE_OK")


def main() -> int:
    run("verify_gis_exclusion.py")
    for backend in ("sqlite", "postgresql", "mysql", "oracle"):
        run("exercise_backend.py", backend)
    for backend in ("sqlite", "postgresql", "mysql"):
        run("verify_dbshell.py", backend)
    for backend in ("postgresql", "mysql", "oracle"):
        run_retained_suite(backend)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
