from djrm.db import migrations, models
import djrm.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Publisher",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=80, unique=True)),
                ("region", models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name="Book",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=120, unique=True)),
                ("price", models.DecimalField(decimal_places=2, max_digits=8)),
                ("rating", models.IntegerField()),
                ("metadata", models.JSONField(default=dict)),
                (
                    "publisher",
                    models.ForeignKey(
                        on_delete=djrm.db.models.deletion.CASCADE,
                        related_name="books",
                        to="e2e_app.publisher",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["publisher", "rating"],
                        name="book_pub_rating_idx",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="Sale",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("channel", models.CharField(max_length=20)),
                ("units", models.PositiveIntegerField()),
                ("sold_on", models.DateField()),
                (
                    "book",
                    models.ForeignKey(
                        on_delete=djrm.db.models.deletion.CASCADE,
                        related_name="sales",
                        to="e2e_app.book",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("book", "channel", "sold_on"),
                        name="sale_book_chan_date_uq",
                    )
                ],
            },
        ),
    ]
