from unittest import mock

from djrm.db import connection
from djrm.test import TransactionTestCase

from .models import Car


class AssertNumQueriesUponConnectionTests(TransactionTestCase):
    available_apps = []

    def test_ignores_connection_configuration_queries(self):
        real_ensure_connection = connection.ensure_connection
        connection.close()

        def make_configuration_query():
            is_opening_connection = connection.connection is None
            real_ensure_connection()
            if is_opening_connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1" + connection.features.bare_select_suffix)

        ensure_connection = "djrm.db.backends.base.base.BaseDatabaseWrapper.ensure_connection"
        with mock.patch(ensure_connection, side_effect=make_configuration_query):
            with self.assertNumQueries(1):
                list(Car.objects.all())
