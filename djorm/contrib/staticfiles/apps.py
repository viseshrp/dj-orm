from djorm.apps import AppConfig
from djorm.contrib.staticfiles.checks import check_finders, check_storages
from djorm.core import checks
from djorm.utils.translation import gettext_lazy as _


class StaticFilesConfig(AppConfig):
    name = 'djorm.contrib.staticfiles'
    verbose_name = _("Static Files")
    ignore_patterns = ["CVS", ".*", "*~"]

    def ready(self):
        checks.register(check_finders, checks.Tags.staticfiles)
        checks.register(check_storages, checks.Tags.staticfiles)
