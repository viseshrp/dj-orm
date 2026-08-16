"""Helpers for fallbacks around deliberately removed modules."""


def is_expected_missing_module(
    error: ModuleNotFoundError,
    *expected_modules: str,
) -> bool:
    """Return whether the error names an expected module or one of its parents."""
    missing = error.name
    if missing is None:
        return False
    return any(module == missing or module.startswith(f"{missing}.") for module in expected_modules)
