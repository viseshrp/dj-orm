"""Lazy access to the forms package removed from Djo."""

from importlib import import_module


class _MissingForms:
    def __getattr__(self, name):
        raise ImportError("djo.forms is not available in this fork.")


try:
    forms = import_module("djo.forms")
except ModuleNotFoundError:
    forms = _MissingForms()
