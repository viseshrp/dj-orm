from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[2]


def test_default_dependencies_are_the_minimal_orm_runtime() -> None:
    with (ROOT / "pyproject.toml").open("rb") as project_file:
        project = tomllib.load(project_file)["project"]

    assert project["dependencies"] == [
        "asgiref>=3.8.1",
        "sqlparse>=0.3.1",
        "tzdata; sys_platform == 'win32'",
    ]


def test_postgresql_pooling_is_an_explicit_extra() -> None:
    with (ROOT / "pyproject.toml").open("rb") as project_file:
        extras = tomllib.load(project_file)["project"]["optional-dependencies"]

    assert extras["postgresql"] == ["psycopg>=3.1.8"]
    assert extras["postgresql-pool"] == ["psycopg[pool]>=3.1.8"]
