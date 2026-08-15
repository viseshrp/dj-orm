from djorm.apps import AppConfig
from djorm.utils.translation import gettext_lazy as _


class SessionsConfig(AppConfig):
    name = 'djorm.contrib.sessions'
    verbose_name = _("Sessions")
