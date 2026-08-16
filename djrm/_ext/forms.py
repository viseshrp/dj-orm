"""Lazy access to the forms package removed from djrm."""

from importlib import import_module


class _MissingForms:
    def __getattr__(self, name):
        raise ImportError("djrm.forms is not available in this fork.")


try:
    forms = import_module("djrm.forms")
except ModuleNotFoundError:
    forms = _MissingForms()
