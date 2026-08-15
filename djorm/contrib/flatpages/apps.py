from djorm.apps import AppConfig
from djorm.utils.translation import gettext_lazy as _


class FlatPagesConfig(AppConfig):
    default_auto_field = 'djorm.db.models.AutoField'
    name = 'djorm.contrib.flatpages'
    verbose_name = _("Flat Pages")
