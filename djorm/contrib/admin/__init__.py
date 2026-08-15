from djorm.contrib.admin.decorators import action, display, register
from djorm.contrib.admin.filters import (
    AllValuesFieldListFilter,
    BooleanFieldListFilter,
    ChoicesFieldListFilter,
    DateFieldListFilter,
    EmptyFieldListFilter,
    FieldListFilter,
    ListFilter,
    RelatedFieldListFilter,
    RelatedOnlyFieldListFilter,
    SimpleListFilter,
)
from djorm.contrib.admin.options import (
    HORIZONTAL,
    VERTICAL,
    ModelAdmin,
    ShowFacets,
    StackedInline,
    TabularInline,
)
from djorm.contrib.admin.sites import AdminSite, site
from djorm.utils.module_loading import autodiscover_modules

__all__ = [
    "action",
    "display",
    "register",
    "ModelAdmin",
    "HORIZONTAL",
    "VERTICAL",
    "StackedInline",
    "TabularInline",
    "AdminSite",
    "site",
    "ListFilter",
    "SimpleListFilter",
    "FieldListFilter",
    "BooleanFieldListFilter",
    "RelatedFieldListFilter",
    "ChoicesFieldListFilter",
    "DateFieldListFilter",
    "AllValuesFieldListFilter",
    "EmptyFieldListFilter",
    "RelatedOnlyFieldListFilter",
    "ShowFacets",
    "autodiscover",
]


def autodiscover():
    autodiscover_modules("admin", register_to=site)
