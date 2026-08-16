from djrm.apps import AppConfig


class E2EAppConfig(AppConfig):
    default_auto_field = "djrm.db.models.AutoField"
    name = "e2e.e2e_app"
