from __future__ import annotations

from datetime import date
from decimal import Decimal
import os

import djrm
from djrm.core.management import call_command
from djrm.db import IntegrityError, connection, transaction
from djrm.db.models import (
    Count,
    DecimalField,
    Exists,
    ExpressionWrapper,
    F,
    Max,
    OuterRef,
    Subquery,
    Sum,
    Window,
)
from djrm.db.models.functions import Coalesce, DenseRank

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "e2e.settings")
djrm.setup()

from e2e.e2e_app.models import Book, Publisher, Sale  # noqa: E402


def reset_schema() -> None:
    call_command("migrate", interactive=False, verbosity=0)
    call_command("makemigrations", "e2e_app", check=True, dry_run=True, verbosity=0)
    Sale.objects.all().delete()
    Book.objects.all().delete()
    Publisher.objects.all().delete()


def seed() -> None:
    with transaction.atomic():
        north = Publisher.objects.create(name="North Press", region="NA")
        south = Publisher.objects.create(name="South Press", region="EU")
        query_engines = Book.objects.create(
            publisher=north,
            title="Query Engines",
            price=Decimal("30.00"),
            rating=5,
            metadata={"level": "advanced", "topics": ["queries", "indexes"]},
        )
        data_layers = Book.objects.create(
            publisher=north,
            title="Data Layers",
            price=Decimal("20.00"),
            rating=4,
            metadata={"level": "intro", "topics": ["models"]},
        )
        orm_internals = Book.objects.create(
            publisher=south,
            title="ORM Internals",
            price=Decimal("25.00"),
            rating=5,
            metadata={"level": "advanced", "topics": ["transactions"]},
        )
        Sale.objects.bulk_create(
            [
                Sale(
                    book=query_engines,
                    channel="web",
                    units=3,
                    sold_on=date(2026, 1, 2),
                ),
                Sale(
                    book=query_engines,
                    channel="store",
                    units=2,
                    sold_on=date(2026, 1, 3),
                ),
                Sale(
                    book=data_layers,
                    channel="web",
                    units=4,
                    sold_on=date(2026, 1, 4),
                ),
                Sale(
                    book=orm_internals,
                    channel="partner",
                    units=2,
                    sold_on=date(2026, 1, 5),
                ),
            ]
        )


def verify_relational_queries() -> None:
    revenue = ExpressionWrapper(
        F("books__price") * F("books__sales__units"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    publishers = list(
        Publisher.objects.annotate(
            book_count=Count("books", distinct=True),
            total_units=Coalesce(Sum("books__sales__units"), 0),
            revenue=Sum(revenue),
            top_rating=Max("books__rating"),
        )
        .order_by("name")
        .values_list("name", "book_count", "total_units", "revenue", "top_rating")
    )
    assert publishers == [
        ("North Press", 2, 9, Decimal("230.00"), 5),
        ("South Press", 1, 2, Decimal("50.00"), 5),
    ]

    latest_sale = Sale.objects.filter(book=OuterRef("pk")).order_by("-sold_on", "-pk")
    books = list(
        Book.objects.annotate(
            latest_channel=Subquery(latest_sale.values("channel")[:1]),
            has_bulk_sale=Exists(Sale.objects.filter(book=OuterRef("pk"), units__gte=4)),
        )
        .order_by("title")
        .values_list("title", "latest_channel", "has_bulk_sale")
    )
    assert books == [
        ("Data Layers", "web", True),
        ("ORM Internals", "partner", False),
        ("Query Engines", "store", False),
    ]

    ranked = list(
        Book.objects.annotate(
            publisher_rank=Window(
                expression=DenseRank(),
                partition_by=[F("publisher_id")],
                order_by=F("rating").desc(),
            )
        )
        .order_by("publisher__name", "publisher_rank", "title")
        .values_list("title", "publisher_rank")
    )
    assert ranked == [("Query Engines", 1), ("Data Layers", 2), ("ORM Internals", 1)]
    assert set(Book.objects.filter(metadata__level="advanced").values_list("title", flat=True)) == {
        "ORM Internals",
        "Query Engines",
    }


def verify_updates_and_transactions() -> None:
    Book.objects.filter(title="Data Layers").update(price=F("price") + Decimal("5.00"))
    assert Book.objects.get(title="Data Layers").price == Decimal("25.00")

    publisher_count = Publisher.objects.count()
    try:
        with transaction.atomic():
            Publisher.objects.create(name="North Press", region="APAC")
    except IntegrityError:
        pass
    else:  # pragma: no cover - an enforced unique constraint must reject this.
        raise AssertionError("The publisher unique constraint was not enforced.")
    assert Publisher.objects.count() == publisher_count

    with transaction.atomic():
        locked = Publisher.objects.select_for_update().get(name="North Press")
        assert locked.region == "NA"


def verify_management_and_introspection() -> None:
    assert {
        "e2e_app_book",
        "e2e_app_publisher",
        "e2e_app_sale",
    }.issubset(set(connection.introspection.table_names()))
    call_command("showmigrations", "e2e_app", verbosity=0)


def main() -> int:
    reset_schema()
    seed()
    verify_relational_queries()
    verify_updates_and_transactions()
    verify_management_and_introspection()
    print(f"DJRM_{connection.vendor.upper()}_ORM_OK server={connection.get_database_version()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
