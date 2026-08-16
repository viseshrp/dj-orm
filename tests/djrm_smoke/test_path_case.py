from pathlib import Path

from scripts.check_path_case import case_mismatches, physical_paths


def test_path_case_match() -> None:
    assert (
        case_mismatches(
            {".github/pull_request_template.md"},
            {".github/pull_request_template.md"},
        )
        == []
    )


def test_path_case_mismatch() -> None:
    assert case_mismatches(
        {".github/pull_request_template.md"},
        {".github/PULL_REQUEST_TEMPLATE.md"},
    ) == [
        (
            ".github/pull_request_template.md",
            (".github/PULL_REQUEST_TEMPLATE.md",),
        )
    ]


def test_physical_paths_preserve_spelling(tmp_path: Path) -> None:
    github = tmp_path / ".github"
    github.mkdir()
    (github / "PULL_REQUEST_TEMPLATE.md").write_text("template\n", encoding="utf-8")
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "ignored").write_text("ignored\n", encoding="utf-8")

    assert physical_paths(tmp_path, {".github/pull_request_template.md"}) == {
        ".github/PULL_REQUEST_TEMPLATE.md"
    }
