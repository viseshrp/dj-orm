import unittest

from djrm.db import connection
from djrm.test import SimpleTestCase, TestCase, modify_settings
from djrm.utils.functional import cached_property


@unittest.skipUnless(connection.vendor == "postgresql", "PostgreSQL specific tests")
# Register PostgreSQL type handlers.
@modify_settings(INSTALLED_APPS={"append": "djrm.contrib.postgres"})
class PostgreSQLSimpleTestCase(SimpleTestCase):
    pass


@unittest.skipUnless(connection.vendor == "postgresql", "PostgreSQL specific tests")
# Register PostgreSQL type handlers.
@modify_settings(INSTALLED_APPS={"append": "djrm.contrib.postgres"})
class PostgreSQLTestCase(TestCase):
    @cached_property
    def default_text_search_config(self):
        with connection.cursor() as cursor:
            cursor.execute("SHOW default_text_search_config")
            row = cursor.fetchone()
            return row[0] if row else None

    def check_default_text_search_config(self):
        if self.default_text_search_config != "pg_catalog.english":
            self.skipTest("The default text search config is not 'english'.")
