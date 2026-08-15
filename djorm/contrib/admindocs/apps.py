from djorm.apps import AppConfig
from djorm.utils.translation import gettext_lazy as _


class AdminDocsConfig(AppConfig):
    name = 'djorm.contrib.admindocs'
    verbose_name = _("Administrative Documentation")
