#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import io
import re
import sys
import tokenize
from pathlib import Path


PYTHON_ROOTS = ("djo", "tests")
STRING_PREFIXES = ("django.",)
STRING_EXACT = {"django", "django-admin"}
STRING_SKIP = {"DJANGO_SETTINGS_MODULE", "_django_version", "django-version"}
PYPROJECT_REPLACEMENTS = {
    'name = "Django"': 'name = "djo"',
    'django-admin = "django.core.management:execute_from_command_line"': 'djo = "djo.core.management:execute_from_command_line"',
    'known_first_party = "django"': 'known_first_party = "djo"',
    'version = {attr = "django.__version__"}': 'version = {attr = "djo.__version__"}',
    'include = ["django*"]': 'include = ["djo*"]',
}
def rename_string_literal(value: str) -> str:
    if value in STRING_SKIP:
        return value
    if value in STRING_EXACT:
        return "djo" if value == "django" else "djo"
    if value.startswith(STRING_PREFIXES):
        return "djo." + value[len("django.") :]
    if "django.core.management:execute_from_command_line" in value:
        return value.replace(
            "django.core.management:execute_from_command_line",
            "djo.core.management:execute_from_command_line",
        )
    if "django-admin" in value:
        return value.replace("django-admin", "djo")
    value = re.sub(r"(?<![A-Z_])from django(\.[\w.]+)? import", r"from djo\1 import", value)
    value = re.sub(r"(?<![A-Z_])import django(\.[\w.]+)?", r"import djo\1", value)
    value = re.sub(r"(?<![A-Z_])django\.(apps|conf|contrib|core|db|dispatch|forms|http|middleware|shortcuts|template|templatetags|test|urls|utils|views)\b", r"djo.\1", value)
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
    updated: list[tuple[int, str]] = []
    changed = False
    current_stmt: list[tokenize.TokenInfo] = []

    for idx, token in enumerate(tokens):
        token_str = token.string
        tok_type = token.type
        if tok_type == tokenize.STRING:
            try:
                value = ast.literal_eval(token_str)
            except Exception:
                updated.append((tok_type, token_str))
                current_stmt.append(token)
                continue
            if isinstance(value, str):
                new_value = rename_string_literal(value)
                if new_value != value:
                    token_str = rebuild_string_token(token_str, new_value)
                    changed = True
            updated.append((tok_type, token_str))
            current_stmt.append(token._replace(string=token_str))
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
                changed = True

        updated.append((tok_type, token_str))
        current_stmt.append(token._replace(string=token_str))
        if tok_type in {tokenize.NEWLINE, tokenize.ENDMARKER}:
            current_stmt.clear()

    if not changed:
        return False

    rewritten = tokenize.untokenize(updated)
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
            elif token.type == tokenize.NAME and token.string == "django":
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
                    stmt_tok.type == tokenize.NAME
                    and stmt_tok.string in {"import", "from"}
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]

    changed_files = 0
    if not args.check:
        for path in iter_python_files(repo_root):
            if rewrite_python(path):
                changed_files += 1
        if rewrite_pyproject(repo_root / "pyproject.toml"):
            changed_files += 1

    residuals = verify_no_residuals(repo_root)
    if residuals:
        print("Residual django references found in Python files:", file=sys.stderr)
        for rel in residuals[:200]:
            print(rel, file=sys.stderr)
        return 1

    if not args.check:
        print(f"Updated {changed_files} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
