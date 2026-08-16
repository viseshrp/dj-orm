from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

SQL_BY_BACKEND = {
    "sqlite": "SELECT 'DJRM_SQLITE_DBSHELL_OK';\n.quit\n",
    "postgresql": ("\\pset tuples_only on\nSELECT 'DJRM_POSTGRESQL_DBSHELL_OK';\n\\q\n"),
    "mysql": "SELECT 'DJRM_MYSQL_DBSHELL_OK';\nquit\n",
    "oracle": (
        "SET HEADING OFF FEEDBACK OFF PAGESIZE 0\n"
        "SELECT 'DJRM_ORACLE_DBSHELL_OK' FROM dual;\n"
        "EXIT\n"
    ),
}


def main() -> int:
    backend = sys.argv[1]
    marker = f"DJRM_{backend.upper()}_DBSHELL_OK"
    environment = dict(os.environ)
    environment["DJRM_E2E_BACKEND"] = backend
    tests_path = str(Path(__file__).resolve().parents[1])
    environment["PYTHONPATH"] = os.pathsep.join(
        path for path in (tests_path, environment.get("PYTHONPATH")) if path
    )
    result = subprocess.run(
        [sys.executable, "-m", "djrm", "dbshell", "--settings=e2e.settings"],
        cwd=Path(__file__).resolve().parents[2],
        env=environment,
        input=SQL_BY_BACKEND[backend],
        text=True,
        capture_output=True,
        timeout=60,
    )
    output = result.stdout + result.stderr
    if result.returncode != 0:
        raise RuntimeError(f"{backend} dbshell failed ({result.returncode}):\n{output}")
    if marker not in output:
        raise AssertionError(f"{backend} dbshell did not return {marker}:\n{output}")
    print(marker)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
