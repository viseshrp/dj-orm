from djrm.apps import AppConfig


class OrmTestHelpersConfig(AppConfig):
    name = "orm_test_helpers"

    def ready(self):
        from djrm.db.models.signals import post_migrate

        from .management import create_test_permissions

        post_migrate.connect(
            create_test_permissions,
            sender=self,
            dispatch_uid="orm_test_helpers.create_test_permissions",
        )
