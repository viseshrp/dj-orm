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


def main() -> int:
    run("verify_gis_exclusion.py")
    for backend in ("sqlite", "postgresql", "mysql", "oracle"):
        run("exercise_backend.py", backend)
    for backend in ("sqlite", "postgresql", "mysql"):
        run("verify_dbshell.py", backend)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
