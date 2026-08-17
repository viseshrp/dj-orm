import os
from pathlib import Path
import subprocess
import sys
import unittest

from djrm.core.management import get_commands

EXPECTED_ORM_COMMANDS = {"check", "shell", "test"}


class ManagementCommandDiscoveryTests(unittest.TestCase):
    def test_orm_workflow_commands_are_discoverable(self) -> None:
        self.assertLessEqual(EXPECTED_ORM_COMMANDS, get_commands().keys())


def run_djrm(*arguments: str) -> subprocess.CompletedProcess[str]:
    root = Path(__file__).resolve().parents[2]
    environment = dict(os.environ)
    environment["DJANGO_SETTINGS_MODULE"] = "tests.test_sqlite"
    return subprocess.run(
        [sys.executable, "-m", "djrm", *arguments],
        cwd=root,
        env=environment,
        text=True,
        capture_output=True,
    )


def test_check_command_runs_database_and_model_checks() -> None:
    result = run_djrm("check", "--database", "default")

    assert result.returncode == 0, result.stderr
    assert "System check identified no issues" in result.stdout


def test_shell_command_executes_with_orm_imports() -> None:
    result = run_djrm(
        "shell",
        "--no-imports",
        "-c",
        "from djrm.db import models; assert models.QuerySet is not None; print('shell-ok')",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "shell-ok"


def test_test_command_runs_discovered_unittest_case() -> None:
    result = run_djrm(
        "test",
        "tests/djrm_smoke",
        "--pattern=test_management_commands.py",
        "--noinput",
        "-v0",
    )

    assert result.returncode == 0, result.stderr
    assert "Ran 1 test" in result.stderr
    assert "OK" in result.stderr
