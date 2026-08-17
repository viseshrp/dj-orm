import unittest
from io import StringIO

from djrm.db import connection
from djrm.test import TestCase
from djrm.test.runner import DiscoverRunner
from djrm.utils.version import PY311

from .models import Person


@unittest.skipUnless(
    connection.vendor == "sqlite", "Only run on sqlite so we can check output SQL."
)
class TestDebugSQL(unittest.TestCase):
    class PassingTest(TestCase):
        def runTest(self):
            Person.objects.filter(first_name="pass").count()

    class FailingTest(TestCase):
        def runTest(self):
            Person.objects.filter(first_name="fail").count()
            self.fail()

    class ErrorTest(TestCase):
        def runTest(self):
            Person.objects.filter(first_name="error").count()
            raise Exception

    class ErrorSetUpTestDataTest(TestCase):
        @classmethod
        def setUpTestData(cls):
            raise Exception

        def runTest(self):
            pass

    class PassingSubTest(TestCase):
        def runTest(self):
            with self.subTest():
                Person.objects.filter(first_name="subtest-pass").count()

    class FailingSubTest(TestCase):
        def runTest(self):
            with self.subTest():
                Person.objects.filter(first_name="subtest-fail").count()
                self.fail()

    class ErrorSubTest(TestCase):
        def runTest(self):
            with self.subTest():
                Person.objects.filter(first_name="subtest-error").count()
                raise Exception

    def _test_output(self, verbosity):
        runner = DiscoverRunner(debug_sql=True, verbosity=0)
        suite = runner.test_suite()
        suite.addTest(self.FailingTest())
        suite.addTest(self.ErrorTest())
        suite.addTest(self.PassingTest())
        suite.addTest(self.PassingSubTest())
        suite.addTest(self.FailingSubTest())
        suite.addTest(self.ErrorSubTest())
        stream = StringIO()
        resultclass = runner.get_resultclass()
        old_force_debug_cursor = connection.force_debug_cursor
        connection.force_debug_cursor = True
        try:
            runner.test_runner(
                verbosity=verbosity,
                stream=stream,
                resultclass=resultclass,
            ).run(suite)
        finally:
            connection.force_debug_cursor = old_force_debug_cursor
        return stream.getvalue()

    def test_output_normal(self):
        full_output = self._test_output(1)
        for output in self.expected_outputs:
            self.assertIn(output, full_output)
        for output in self.verbose_expected_outputs:
            self.assertNotIn(output, full_output)

    def test_output_verbose(self):
        full_output = self._test_output(2)
        for output in self.expected_outputs:
            self.assertIn(output, full_output)
        for output in self.verbose_expected_outputs:
            self.assertIn(output, full_output)

    expected_outputs = [
        (
            """SELECT COUNT(*) AS "__count"\n"""
            """FROM "test_runner_person"\n"""
            """WHERE "test_runner_person"."first_name" = 'error';"""
        ),
        (
            """SELECT COUNT(*) AS "__count"\n"""
            """FROM "test_runner_person"\n"""
            """WHERE "test_runner_person"."first_name" = 'fail';"""
        ),
        (
            """SELECT COUNT(*) AS "__count"\n"""
            """FROM "test_runner_person"\n"""
            """WHERE "test_runner_person"."first_name" = 'subtest-error';"""
        ),
        (
            """SELECT COUNT(*) AS "__count"\n"""
            """FROM "test_runner_person"\n"""
            """WHERE "test_runner_person"."first_name" = 'subtest-fail';"""
        ),
    ]

    # Python 3.11 uses fully qualified test name in the output.
    method_name = ".runTest" if PY311 else ""
    test_class_path = "test_runner.test_debug_sql.TestDebugSQL"
    verbose_expected_outputs = [
        f"runTest ({test_class_path}.FailingTest{method_name}) ... FAIL",
        f"runTest ({test_class_path}.ErrorTest{method_name}) ... ERROR",
        f"runTest ({test_class_path}.PassingTest{method_name}) ... ok",
        # If there are errors/failures in subtests but not in test itself,
        # the status is not written. That behavior comes from Python.
        f"runTest ({test_class_path}.FailingSubTest{method_name}) ...",
        f"runTest ({test_class_path}.ErrorSubTest{method_name}) ...",
        (
            """SELECT COUNT(*) AS "__count" """
            """FROM "test_runner_person" WHERE """
            """"test_runner_person"."first_name" = 'pass';"""
        ),
        (
            """SELECT COUNT(*) AS "__count" """
            """FROM "test_runner_person" WHERE """
            """"test_runner_person"."first_name" = 'subtest-pass';"""
        ),
    ]

    def test_setupclass_exception(self):
        runner = DiscoverRunner(debug_sql=True, verbosity=0)
        suite = runner.test_suite()
        suite.addTest(self.ErrorSetUpTestDataTest())
        stream = StringIO()
        runner.test_runner(
            verbosity=0,
            stream=stream,
            resultclass=runner.get_resultclass(),
        ).run(suite)
        output = stream.getvalue()
        self.assertIn(
            "ERROR: setUpClass "
            "(test_runner.test_debug_sql.TestDebugSQL.ErrorSetUpTestDataTest)",
            output,
        )
