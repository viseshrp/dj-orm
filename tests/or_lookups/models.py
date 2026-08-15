'\nOR lookups\n\nTo perform an OR lookup, or a lookup that combines ANDs and ORs, combine\n``QuerySet`` objects using ``&`` and ``|`` operators.\n\nAlternatively, use positional arguments, and pass one or more expressions of\nclauses using the variable ``djorm.db.models.Q``.\n'

from djorm.db import models


class Article(models.Model):
    headline = models.CharField(max_length=50)
    pub_date = models.DateTimeField()

    class Meta:
        ordering = ("pub_date",)

    def __str__(self):
        return self.headline
