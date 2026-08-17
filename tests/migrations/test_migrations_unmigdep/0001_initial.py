from djrm.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "__first__"),
    ]

    operations = [
        migrations.CreateModel(
            "Book",
            [
                ("id", models.AutoField(primary_key=True)),
                (
                    "content_type",
                    models.ForeignKey(
                        "contenttypes.ContentType", models.SET_NULL, null=True
                    ),
                ),
            ],
        )
    ]
