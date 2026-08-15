from djorm.apps import AppConfig
from djorm.utils.translation import gettext_lazy as _


class SyndicationConfig(AppConfig):
    name = 'djorm.contrib.syndication'
    verbose_name = _("Syndication")
