from djrm.db.models import JSONField as BuiltinJSONField

__all__ = ["JSONField"]


class JSONField(BuiltinJSONField):
    system_check_removed_details = {
        "msg": (
            "djrm.contrib.postgres.fields.JSONField is removed except for "
            "support in historical migrations."
        ),
        "hint": "Use djrm.db.models.JSONField instead.",
        "id": "fields.E904",
    }
