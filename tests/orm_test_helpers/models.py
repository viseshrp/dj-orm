from djrm.contrib.contenttypes.models import ContentType
from djrm.db import models


class UserManager(models.Manager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        return self.create(
            username=username,
            email=email or "",
            password=password or "",
            **extra_fields,
        )

    def get_by_natural_key(self, username):
        return self.get(username=username)


class User(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(blank=True)
    password = models.CharField(max_length=128, blank=True)

    objects = UserManager()

    class Meta:
        swappable = "TEST_USER_MODEL"

    def natural_key(self):
        return (self.username,)

    def __str__(self):
        return self.username


class AuthUser(models.Model):
    class Meta:
        swappable = "AUTH_USER_MODEL"


class PermissionManager(models.Manager):
    def get_by_natural_key(self, codename, app_label, model):
        return self.get(
            codename=codename,
            content_type__app_label=app_label,
            content_type__model=model,
        )


class Permission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey(ContentType, models.CASCADE)
    codename = models.CharField(max_length=100)

    objects = PermissionManager()

    class Meta:
        unique_together = (("content_type", "codename"),)

    def natural_key(self):
        return (self.codename,) + self.content_type.natural_key()

    natural_key.dependencies = ["contenttypes.contenttype"]


class Site(models.Model):
    domain = models.CharField(max_length=100)
    name = models.CharField(max_length=50)
