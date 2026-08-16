#!/usr/bin/env python3
"""Inspect and install djrm distribution artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import zipfile


class InspectionError(RuntimeError):
    """A distribution artifact failed structural inspection."""


def one_match(dist_dir: Path, pattern: str) -> Path:
    matches = sorted(dist_dir.glob(pattern))
    if len(matches) != 1:
        raise InspectionError(f"Expected one {pattern} artifact, found {len(matches)}.")
    return matches[0]


def inspect_wheel(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    required = {
        "djrm/__init__.py",
        "djrm/_version.py",
        "djrm/db/models/__init__.py",
        "djrm/core/management/__init__.py",
    }
    missing = sorted(required - names)
    if missing:
        raise InspectionError(f"Wheel is missing required paths: {', '.join(missing)}")
    if any(name.startswith("django/") for name in names):
        raise InspectionError("Wheel contains a forbidden django package.")
    if any(name.startswith("djrm/contrib/gis/") for name in names):
        raise InspectionError("Wheel contains the excluded GIS package.")
    if any(name.endswith(".po") for name in names):
        raise InspectionError("Wheel contains gettext source catalogs.")
    if not any(name.endswith("/LC_MESSAGES/django.mo") for name in names):
        raise InspectionError("Wheel does not contain compiled translation catalogs.")
    if not any("djrm-" in name and name.endswith(".dist-info/METADATA") for name in names):
        raise InspectionError("Wheel metadata directory is not normalized from djrm.")


def inspect_sdist(sdist: Path) -> None:
    with tarfile.open(sdist, "r:gz") as archive:
        names = archive.getnames()
    if any("/djrm/contrib/gis/" in f"/{name}" for name in names):
        raise InspectionError("Source archive contains the excluded GIS package.")
    if any(name.endswith(".po") for name in names):
        raise InspectionError("Source archive contains gettext source catalogs.")
    if not any(name.endswith("/LC_MESSAGES/django.mo") for name in names):
        raise InspectionError("Source archive does not contain compiled translation catalogs.")
    suffixes = {
        "README.md",
        "MAINTENANCE.md",
        "scripts/apply_django_lts.py",
        "tests/djrm_smoke/test_distribution.py",
    }
    for suffix in suffixes:
        if not any(name.endswith(f"/{suffix}") for name in names):
            raise InspectionError(f"Source archive is missing {suffix}.")


def isolated_install(wheel: Path) -> None:
    uv = shutil.which("uv")
    if uv is None:
        raise InspectionError("uv is required for the isolated wheel check.")
    with tempfile.TemporaryDirectory(prefix="djrm-wheel-") as temp_dir:
        environment = Path(temp_dir) / ".venv"
        subprocess.run([uv, "venv", str(environment)], check=True)
        python = environment / (
            "Scripts/python.exe" if environment.name == "Scripts" else "bin/python"
        )
        if not python.exists():
            python = environment / "Scripts" / "python.exe"
        subprocess.run([uv, "pip", "install", "--python", str(python), str(wheel)], check=True)
        script = """
from importlib.metadata import version
import djrm
from djrm.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "djrm.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[],
)
djrm.setup()
from djrm.db import models
from djrm.utils.translation import activate, gettext
assert models.Model is not None
activate("fr")
assert gettext("January") == "janvier"
print(version("djrm"))
"""
        subprocess.run([str(python), "-c", script], check=True)
        djrm_command = python.parent / ("djrm.exe" if python.suffix == ".exe" else "djrm")
        subprocess.run([str(djrm_command), "--help"], check=True, stdout=subprocess.DEVNULL)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dist_dir", type=Path)
    parser.add_argument("--skip-install", action="store_true")
    args = parser.parse_args()
    try:
        wheel = one_match(args.dist_dir, "*.whl")
        sdist = one_match(args.dist_dir, "*.tar.gz")
        inspect_wheel(wheel)
        inspect_sdist(sdist)
        if not args.skip_install:
            isolated_install(wheel)
    except (InspectionError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}")
        return 1
    print(f"Distribution artifacts passed inspection: {wheel.name}, {sdist.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
