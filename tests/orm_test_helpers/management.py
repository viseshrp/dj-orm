from djrm.contrib.contenttypes.models import ContentType

from .models import Permission, User


def create_test_permissions(app_config, verbosity, using, **kwargs):
    content_type = ContentType.objects.db_manager(using).get_for_model(User)
    permissions = (
        ("add_user", "Can add user"),
        ("change_user", "Can change user"),
        ("delete_user", "Can delete user"),
    )
    for codename, name in permissions:
        Permission.objects.using(using).update_or_create(
            content_type=content_type,
            codename=codename,
            defaults={"name": name},
        )
