"""Lazy access to the forms package removed from djrm."""

from importlib import import_module

FORMS_UNAVAILABLE_MESSAGE = "djrm.forms is not available in this fork."


def forms_unavailable():
    raise ImportError(FORMS_UNAVAILABLE_MESSAGE)


class _MissingForms:
    def __getattr__(self, name):
        forms_unavailable()


try:
    forms = import_module("djrm.forms")
except ModuleNotFoundError:
    forms = _MissingForms()
