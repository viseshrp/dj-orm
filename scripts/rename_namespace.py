#!/usr/bin/env python3
"""Re-apply the django -> djo namespace rename after an upstream rebase."""

from __future__ import annotations

import argparse
import ast
import io
import re
import sys
import tokenize
from pathlib import Path
from shutil import move


PYTHON_ROOTS = ("djo", "tests")
KNOWN_MODULE_PREFIXES = (
    "django.apps",
    "django.conf",
    "django.contrib",
    "django.core",
    "django.db",
    "django.dispatch",
    "django.forms",
    "django.http",
    "django.middleware",
    "django.shortcuts",
    "django.template",
    "django.templatetags",
    "django.test",
    "django.urls",
    "django.utils",
    "django.views",
)
STRING_EXACT = {"django-admin"}
STRING_SKIP = {"DJANGO_SETTINGS_MODULE", "_django_version", "django-version"}
PYPROJECT_REPLACEMENTS = {
    'name = "Django"': 'name = "djo"',
    'django-admin = "django.core.management:execute_from_command_line"': 'djo = "djo.core.management:execute_from_command_line"',
    'known_first_party = "django"': 'known_first_party = "djo"',
    'version = {attr = "django.__version__"}': 'version = {attr = "djo.__version__"}',
    'include = ["django*"]': 'include = ["djo*"]',
}


def rename_repo_package_dir(repo_root: Path) -> bool:
    django_dir = repo_root / "django"
    djo_dir = repo_root / "djo"
    if djo_dir.exists() or not django_dir.exists():
        return False
    move(str(django_dir), str(djo_dir))
    return True


def rename_string_literal(value: str) -> str:
    if value in STRING_SKIP:
        return value
    if value in STRING_EXACT:
        return "djo"
    if value.startswith(KNOWN_MODULE_PREFIXES):
        return "djo." + value[len("django.") :]
    if "django.core.management:execute_from_command_line" in value:
        return value.replace(
            "django.core.management:execute_from_command_line",
            "djo.core.management:execute_from_command_line",
        )
    if "django-admin" in value:
        return value.replace("django-admin", "djo")
    module_pattern = "|".join(part.split(".", 1)[1] for part in KNOWN_MODULE_PREFIXES)
    value = re.sub(r"(?<![A-Z_])from django(\.[\w.]+)? import", r"from djo\1 import", value)
    value = re.sub(r"(?<![A-Z_])import django(\.[\w.]+)?", r"import djo\1", value)
    value = re.sub(rf"(?<![A-Z_])django\.({module_pattern})\b", r"djo.\1", value)
    return value


def rebuild_string_token(token_text: str, new_value: str) -> str:
    prefix_match = re.match(r"(?i)([rubf]*)", token_text)
    prefix = prefix_match.group(1)
    lowered = prefix.lower()
    if "f" in lowered:
        return token_text
    return f"{prefix}{repr(new_value)}"


def rewrite_python(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    tokens = list(tokenize.generate_tokens(io.StringIO(original).readline))
    line_offsets: list[int] = []
    offset = 0
    for line in original.splitlines(keepends=True):
        line_offsets.append(offset)
        offset += len(line)
    replacements: list[tuple[int, int, str]] = []
    current_stmt: list[tokenize.TokenInfo] = []

    def replace_token(token: tokenize.TokenInfo, replacement: str) -> None:
        start = line_offsets[token.start[0] - 1] + token.start[1]
        end = line_offsets[token.end[0] - 1] + token.end[1]
        replacements.append((start, end, replacement))

    for idx, token in enumerate(tokens):
        token_str = token.string
        tok_type = token.type
        if tok_type == tokenize.STRING:
            try:
                value = ast.literal_eval(token_str)
            except Exception:
                current_stmt.append(token)
                continue
            if isinstance(value, str):
                new_value = rename_string_literal(value)
                if new_value != value:
                    token_str = rebuild_string_token(token_str, new_value)
                    if token_str != token.string:
                        replace_token(token, token_str)
            current_stmt.append(token)
            continue

        if tok_type == tokenize.NAME and token_str == "django":
            next_nontrivia = None
            for later in tokens[idx + 1 :]:
                if later.type not in {
                    tokenize.NL,
                    tokenize.NEWLINE,
                    tokenize.INDENT,
                    tokenize.DEDENT,
                    tokenize.COMMENT,
                }:
                    next_nontrivia = later
                    break
            prev_nontrivia = None
            for earlier in reversed(current_stmt):
                if earlier.type not in {
                    tokenize.NL,
                    tokenize.NEWLINE,
                    tokenize.INDENT,
                    tokenize.DEDENT,
                    tokenize.COMMENT,
                }:
                    prev_nontrivia = earlier
                    break
            in_import = any(
                stmt_tok.type == tokenize.NAME and stmt_tok.string in {"import", "from"}
                for stmt_tok in current_stmt
            )
            dotted_access = (
                next_nontrivia is not None
                and next_nontrivia.string == "."
                and (prev_nontrivia is None or prev_nontrivia.string != ".")
            )
            import_head = in_import and (
                prev_nontrivia is None
                or prev_nontrivia.string in {"import", "from", ","}
            )
            if import_head or dotted_access:
                token_str = "djo"
                replace_token(token, token_str)

        current_stmt.append(token)
        if tok_type in {tokenize.NEWLINE, tokenize.ENDMARKER}:
            current_stmt.clear()

    if not replacements:
        return False
    rewritten = original
    for start, end, replacement in reversed(replacements):
        rewritten = rewritten[:start] + replacement + rewritten[end:]
    path.write_text(rewritten, encoding="utf-8")
    return True


def rewrite_pyproject(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    rewritten = original
    for src, dst in PYPROJECT_REPLACEMENTS.items():
        rewritten = rewritten.replace(src, dst)
    if rewritten == original:
        return False
    path.write_text(rewritten, encoding="utf-8")
    return True


def iter_python_files(repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    for root in PYTHON_ROOTS:
        base = repo_root / root
        if base.exists():
            paths.extend(sorted(base.rglob("*.py")))
    return paths


def token_has_rewritable_django_name(
    token: tokenize.TokenInfo, tokens: list[tokenize.TokenInfo], idx: int, current_stmt: list[tokenize.TokenInfo]
) -> bool:
    if token.type != tokenize.NAME or token.string != "django":
        return False
    next_nontrivia = None
    for later in tokens[idx + 1 :]:
        if later.type not in {
            tokenize.NL,
            tokenize.NEWLINE,
            tokenize.INDENT,
            tokenize.DEDENT,
            tokenize.COMMENT,
        }:
            next_nontrivia = later
            break
    prev_nontrivia = None
    for earlier in reversed(current_stmt):
        if earlier.type not in {
            tokenize.NL,
            tokenize.NEWLINE,
            tokenize.INDENT,
            tokenize.DEDENT,
            tokenize.COMMENT,
        }:
            prev_nontrivia = earlier
            break
    in_import = any(
        stmt_tok.type == tokenize.NAME and stmt_tok.string in {"import", "from"}
        for stmt_tok in current_stmt
    )
    dotted_access = (
        next_nontrivia is not None
        and next_nontrivia.string == "."
        and (prev_nontrivia is None or prev_nontrivia.string != ".")
    )
    import_head = in_import and (
        prev_nontrivia is None or prev_nontrivia.string in {"import", "from", ","}
    )
    return import_head or dotted_access


def verify_no_residuals(repo_root: Path) -> list[str]:
    failures: list[str] = []
    for path in iter_python_files(repo_root):
        original = path.read_text(encoding="utf-8")
        tokens = list(tokenize.generate_tokens(io.StringIO(original).readline))
        current_stmt: list[tokenize.TokenInfo] = []
        failed = False
        for idx, token in enumerate(tokens):
            if token.type == tokenize.STRING:
                try:
                    value = ast.literal_eval(token.string)
                except Exception:
                    value = None
                if isinstance(value, str) and rename_string_literal(value) != value:
                    failures.append(str(path.relative_to(repo_root)))
                    failed = True
                    break
            elif token_has_rewritable_django_name(token, tokens, idx, current_stmt):
                failures.append(str(path.relative_to(repo_root)))
                failed = True
                break
            current_stmt.append(token)
            if token.type in {tokenize.NEWLINE, tokenize.ENDMARKER}:
                current_stmt.clear()
        if failed:
            continue
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Re-apply the django -> djo namespace rename after an upstream rebase."
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Repository to transform. Defaults to the parent of this script.",
    )
    args = parser.parse_args()
    repo_root = (
        args.repo_root.resolve()
        if args.repo_root is not None
        else Path(__file__).resolve().parents[1]
    )

    changed_files = 0
    if not args.check:
        if rename_repo_package_dir(repo_root):
            changed_files += 1
        for path in iter_python_files(repo_root):
            if rewrite_python(path):
                changed_files += 1
        if rewrite_pyproject(repo_root / "pyproject.toml"):
            changed_files += 1

    residuals = verify_no_residuals(repo_root)
    if residuals:
        print("Residual django namespace references found in Python files:", file=sys.stderr)
        for rel in residuals[:200]:
            print(rel, file=sys.stderr)
        return 1

    if not args.check:
        print(f"Updated {changed_files} paths.")
    else:
        print("No residual django namespace references found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
