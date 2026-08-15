from djorm.apps import AppConfig
from djorm.contrib.sites.checks import check_site_id
from djorm.core import checks
from djorm.db.models.signals import post_migrate
from djorm.utils.translation import gettext_lazy as _

from .management import create_default_site


class SitesConfig(AppConfig):
    default_auto_field = 'djorm.db.models.AutoField'
    name = 'djorm.contrib.sites'
    verbose_name = _("Sites")

    def ready(self):
        post_migrate.connect(create_default_site, sender=self)
        checks.register(check_site_id, checks.Tags.sites)
