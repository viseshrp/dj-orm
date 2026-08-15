from djorm.views.generic.base import RedirectView, TemplateView, View
from djorm.views.generic.dates import (
    ArchiveIndexView,
    DateDetailView,
    DayArchiveView,
    MonthArchiveView,
    TodayArchiveView,
    WeekArchiveView,
    YearArchiveView,
)
from djorm.views.generic.detail import DetailView
from djorm.views.generic.edit import CreateView, DeleteView, FormView, UpdateView
from djorm.views.generic.list import ListView

__all__ = [
    "View",
    "TemplateView",
    "RedirectView",
    "ArchiveIndexView",
    "YearArchiveView",
    "MonthArchiveView",
    "WeekArchiveView",
    "DayArchiveView",
    "TodayArchiveView",
    "DateDetailView",
    "DetailView",
    "FormView",
    "CreateView",
    "UpdateView",
    "DeleteView",
    "ListView",
    "GenericViewError",
]


class GenericViewError(Exception):
    """A problem in a generic view."""

    pass
