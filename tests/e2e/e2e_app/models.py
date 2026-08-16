from djrm.db import models


class Publisher(models.Model):
    name = models.CharField(max_length=80, unique=True)
    region = models.CharField(max_length=20)


class Book(models.Model):
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, related_name="books")
    title = models.CharField(max_length=120, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    rating = models.IntegerField()
    metadata = models.JSONField(default=dict)

    class Meta:
        indexes = [models.Index(fields=["publisher", "rating"], name="book_pub_rating_idx")]


class Sale(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="sales")
    channel = models.CharField(max_length=20)
    units = models.PositiveIntegerField()
    sold_on = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["book", "channel", "sold_on"],
                name="sale_book_chan_date_uq",
            )
        ]
