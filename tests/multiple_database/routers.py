from djrm.db import DEFAULT_DB_ALIAS


class TestRouter:
    """
    Vaguely behave like primary/replica, but the databases aren't assumed to
    propagate changes.
    """

    def db_for_read(self, model, instance=None, **hints):
        if instance:
            return instance._state.db or "other"
        return "other"

    def db_for_write(self, model, **hints):
        return DEFAULT_DB_ALIAS

    def allow_relation(self, obj1, obj2, **hints):
        return obj1._state.db in ("default", "other") and obj2._state.db in (
            "default",
            "other",
        )

    def allow_migrate(self, db, app_label, **hints):
        return True


class UserRouter:
    """
    Control all database operations on the ORM-only user helper model.
    """

    def db_for_read(self, model, **hints):
        "Point all read operations on helper models to 'default'."
        if model._meta.app_label == "orm_test_helpers":
            # We use default here to ensure we can tell the difference
            # between a read request and a write request for helper objects.
            return "default"
        return None

    def db_for_write(self, model, **hints):
        "Point all write operations on helper models to 'other'."
        if model._meta.app_label == "orm_test_helpers":
            return "other"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        "Allow any relation if an ORM helper model is involved."
        return (
            obj1._meta.app_label == "orm_test_helpers"
            or obj2._meta.app_label == "orm_test_helpers"
            or None
        )

    def allow_migrate(self, db, app_label, **hints):
        "Make sure the helper app only appears on the 'other' database."
        if app_label == "orm_test_helpers":
            return db == "other"
        return None


class WriteRouter:
    # A router that only expresses an opinion on writes
    def db_for_write(self, model, **hints):
        return "writer"
