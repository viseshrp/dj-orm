"""Lazy access to the forms package removed from Djorm."""

from importlib import import_module


class _MissingForms:
    def __getattr__(self, name):
        raise ImportError("djorm.forms is not available in this fork.")


try:
    forms = import_module("djorm.forms")
except ModuleNotFoundError:
    forms = _MissingForms()
