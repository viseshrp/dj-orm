from djorm.conf.urls.i18n import i18n_patterns
from djorm.urls import include, re_path
from djorm.utils.translation import gettext_lazy as _

urlpatterns = i18n_patterns(
    re_path(
        _(r"^account/"),
        include("i18n.patterns.urls.wrong_namespace", namespace="account"),
    ),
)
