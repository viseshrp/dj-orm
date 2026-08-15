from djorm.apps import AppConfig
from djorm.utils.translation import gettext_lazy as _


class SiteMapsConfig(AppConfig):
    default_auto_field = 'djorm.db.models.AutoField'
    name = 'djorm.contrib.sitemaps'
    verbose_name = _("Site Maps")
