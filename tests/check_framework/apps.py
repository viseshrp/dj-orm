from djrm.apps import AppConfig


class CheckDefaultPKConfig(AppConfig):
    name = "check_framework"


class CheckPKConfig(AppConfig):
    name = "check_framework"
    default_auto_field = "djrm.db.models.BigAutoField"
