from djorm.apps import AppConfig
from djorm.utils.translation import gettext_lazy as _


class RedirectsConfig(AppConfig):
    default_auto_field = 'djorm.db.models.AutoField'
    name = 'djorm.contrib.redirects'
    verbose_name = _("Redirects")
