from djorm.apps import AppConfig
from djorm.contrib.messages.storage import base
from djorm.contrib.messages.utils import get_level_tags
from djorm.core.signals import setting_changed
from djorm.utils.functional import SimpleLazyObject
from djorm.utils.translation import gettext_lazy as _


def update_level_tags(setting, **kwargs):
    if setting == "MESSAGE_TAGS":
        base.LEVEL_TAGS = SimpleLazyObject(get_level_tags)


class MessagesConfig(AppConfig):
    name = 'djorm.contrib.messages'
    verbose_name = _("Messages")

    def ready(self):
        setting_changed.connect(update_level_tags)
