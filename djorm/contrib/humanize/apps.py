from djorm.apps import AppConfig
from djorm.utils.translation import gettext_lazy as _


class HumanizeConfig(AppConfig):
    name = 'djorm.contrib.humanize'
    verbose_name = _("Humanize")
