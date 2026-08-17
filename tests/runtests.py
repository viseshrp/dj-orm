#!/usr/bin/env python
import argparse
import atexit
import copy
import gc
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import warnings

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import djrm
except ImportError as e:
    raise RuntimeError(
        "djrm is not installed. Follow the setup instructions in CONTRIBUTING.md."
    ) from e
else:
    from djrm.apps import apps
    from djrm.conf import settings
    from djrm.db import connection, connections
    from djrm.test import TestCase, TransactionTestCase
    from djrm.test.runner import get_max_test_processes, parallel_type
    from djrm.test.utils import NullTimeKeeper, TimeKeeper, get_runner
    from djrm.utils.deprecation import (
        RemovedInDjango60Warning,
        RemovedInDjango61Warning,
    )
    from djrm.utils.functional import classproperty
    from djrm.utils.log import DEFAULT_LOGGING
    from djrm.utils.version import PY312, PYPY

try:
    import MySQLdb
except ImportError:
    pass
else:
    # Ignore informational warnings from QuerySet.explain().
    warnings.filterwarnings("ignore", r"\(1003, *", category=MySQLdb.Warning)

    # Make deprecation warnings errors to ensure no usage of deprecated features.
warnings.simplefilter("error", RemovedInDjango60Warning)
warnings.simplefilter("error", RemovedInDjango61Warning)
# Make resource and runtime warning errors to ensure no usage of error prone
# patterns.
warnings.simplefilter("error", ResourceWarning)
warnings.simplefilter("error", RuntimeWarning)

# Reduce garbage collection frequency to improve performance. Since CPython
# uses refcounting, garbage collection only collects objects with cyclic
# references, which are a minority, so the garbage collection threshold can be
# larger than the default threshold of 700 allocations + deallocations without
# much increase in memory usage.
if not PYPY:
    gc.set_threshold(100_000)

RUNTESTS_DIR = os.path.abspath(os.path.dirname(__file__))

# Add variables enabling coverage to trace code in subprocesses.
os.environ["RUNTESTS_DIR"] = RUNTESTS_DIR
os.environ["COVERAGE_PROCESS_START"] = os.path.join(RUNTESTS_DIR, ".coveragerc")


ALWAYS_INSTALLED_APPS = [
    "djrm.contrib.contenttypes",
]

TEST_HELPER_PACKAGES = {
    "djrm_smoke",
    "e2e",
    "import_error_package",
    "orm_test_migrations",
    "orm_test_helpers",
    "test_runner_apps",
}

ORM_TEST_HELPER_CONSUMERS = {
    "contenttypes_tests",
    "extra_regress",
    "field_deconstruction",
    "fixtures",
    "fixtures_regress",
    "m2m_regress",
    "m2m_through_regress",
    "migrations",
    "multiple_database",
}


def get_test_modules():
    """Scan the tests directory and yield top-level test modules."""
    with os.scandir(RUNTESTS_DIR) as entries:
        for entry in entries:
            if (
                "." in entry.name
                or entry.is_file()
                or not os.path.exists(os.path.join(entry.path, "__init__.py"))
                or entry.name in TEST_HELPER_PACKAGES
            ):
                continue
            if entry.name == "postgres_tests" and connection.vendor != "postgresql":
                continue
            yield entry.name


def get_label_module(label):
    """Return the top-level module part for a test label."""
    path = Path(label)
    if len(path.parts) == 1:
        # Interpret the label as a dotted module name.
        return label.split(".")[0]

        # Otherwise, interpret the label as a path. Check existence first to
        # provide a better error message than relative_to() if it doesn't exist.
    if not path.exists():
        raise RuntimeError(f"Test label path {label} does not exist")
    path = path.resolve()
    rel_path = path.relative_to(RUNTESTS_DIR)
    return rel_path.parts[0]


def get_filtered_test_modules(start_at, start_after, test_labels=None):
    if test_labels is None:
        test_labels = []
        # Reduce each test label to just the top-level module part.
    label_modules = set()
    for label in test_labels:
        test_module = get_label_module(label)
        label_modules.add(test_module)

    def _module_match_label(module_name, label):
        # Exact or ancestor match.
        return module_name == label or module_name.startswith(label + ".")

    start_label = start_at or start_after
    for test_module in get_test_modules():
        if start_label:
            if not _module_match_label(test_module, start_label):
                continue
            start_label = ""
            if not start_at:
                assert start_after
                # Skip the current one before starting.
                continue
                # If the module (or an ancestor) was named on the command line, or
                # no modules were named (i.e., run all), include the test module.
        if not test_labels or any(
            _module_match_label(test_module, label_module) for label_module in label_modules
        ):
            yield test_module


def setup_collect_tests(start_at, start_after, test_labels=None):
    state = {
        "INSTALLED_APPS": settings.INSTALLED_APPS,
        "LANGUAGE_CODE": settings.LANGUAGE_CODE,
        "MIDDLEWARE": settings.MIDDLEWARE,
    }

    # Redirect some settings for the duration of these tests.
    settings.INSTALLED_APPS = ALWAYS_INSTALLED_APPS
    settings.LANGUAGE_CODE = "en"
    settings.MIDDLEWARE = []
    settings.MIGRATION_MODULES = {
        # Keep content types out of serialized rollback fixtures, matching the
        # upstream test suite. orm_test_migrations still creates the migration
        # recorder table for targeted migration-suite runs.
        "contenttypes": None,
    }
    log_config = copy.deepcopy(DEFAULT_LOGGING)
    # Filter out non-error logging so we don't have to capture it in lots of
    # tests.
    log_config["loggers"]["djrm"]["level"] = "ERROR"
    settings.LOGGING = log_config
    settings.SILENCED_SYSTEM_CHECKS = [
        "fields.W342",  # ForeignKey(unique=True) -> OneToOneField
    ]

    # Load all the ALWAYS_INSTALLED_APPS.
    djrm.setup()

    test_modules = list(
        get_filtered_test_modules(
            start_at,
            start_after,
            test_labels=test_labels,
        )
    )
    return test_modules, state


def teardown_collect_tests(state):
    # Restore the old settings.
    for key, value in state.items():
        setattr(settings, key, value)


def get_installed():
    return [app_config.name for app_config in apps.get_app_configs()]


def setup_run_tests(verbosity, start_at, start_after, test_labels=None):
    test_modules, state = setup_collect_tests(start_at, start_after, test_labels=test_labels)

    if ORM_TEST_HELPER_CONSUMERS.intersection(test_modules):
        settings.INSTALLED_APPS.append("orm_test_helpers")
    if "migrations" in test_modules:
        settings.INSTALLED_APPS.append("orm_test_migrations")

    installed_apps = set(get_installed())
    for app in test_modules:
        if app in installed_apps:
            continue
        if verbosity >= 2:
            print(f"Importing application {app}")
        settings.INSTALLED_APPS.append(app)
        installed_apps.add(app)

    apps.set_installed_apps(settings.INSTALLED_APPS)

    # Force declaring available_apps in TransactionTestCase for faster tests.
    def no_available_apps(cls):
        raise Exception("Please define available_apps in TransactionTestCase and its subclasses.")

    TransactionTestCase.available_apps = classproperty(no_available_apps)
    TestCase.available_apps = None

    # Set an environment variable that other code may consult to see if
    # Django's own test suite is running.
    os.environ["RUNNING_DJANGOS_TEST_SUITE"] = "true"

    test_labels = test_labels or test_modules
    return test_labels, state


def teardown_run_tests(state):
    teardown_collect_tests(state)
    del os.environ["RUNNING_DJANGOS_TEST_SUITE"]


def django_tests(
    verbosity,
    interactive,
    failfast,
    keepdb,
    reverse,
    test_labels,
    debug_sql,
    parallel,
    tags,
    exclude_tags,
    test_name_patterns,
    start_at,
    start_after,
    pdb,
    buffer,
    timing,
    shuffle,
    durations=None,
):
    if parallel in {0, "auto"}:
        max_parallel = get_max_test_processes()
    else:
        max_parallel = parallel

    if verbosity >= 1:
        msg = "Testing against Django installed in '%s'" % os.path.dirname(djrm.__file__)
        if max_parallel > 1:
            msg += " with up to %d processes" % max_parallel
        print(msg)

    process_setup_args = (verbosity, start_at, start_after, test_labels)
    test_labels, state = setup_run_tests(*process_setup_args)
    # Run the test suite, including the extra validation tests.
    if not hasattr(settings, "TEST_RUNNER"):
        settings.TEST_RUNNER = "djrm.test.runner.DiscoverRunner"

    if parallel in {0, "auto"}:
        # This doesn't work before django.setup() on some databases.
        if all(conn.features.can_clone_databases for conn in connections.all()):
            parallel = max_parallel
        else:
            parallel = 1

    TestRunner = get_runner(settings)
    TestRunner.parallel_test_suite.process_setup = setup_run_tests
    TestRunner.parallel_test_suite.process_setup_args = process_setup_args
    test_runner = TestRunner(
        verbosity=verbosity,
        interactive=interactive,
        failfast=failfast,
        keepdb=keepdb,
        reverse=reverse,
        debug_sql=debug_sql,
        parallel=parallel,
        tags=tags,
        exclude_tags=exclude_tags,
        test_name_patterns=test_name_patterns,
        pdb=pdb,
        buffer=buffer,
        timing=timing,
        shuffle=shuffle,
        durations=durations,
    )
    failures = test_runner.run_tests(test_labels)
    teardown_run_tests(state)
    return failures


def collect_test_modules(start_at, start_after):
    test_modules, state = setup_collect_tests(start_at, start_after)
    teardown_collect_tests(state)
    return test_modules


def get_subprocess_args(options):
    subprocess_args = [sys.executable, __file__, "--settings=%s" % options.settings]
    if options.failfast:
        subprocess_args.append("--failfast")
    if options.verbosity:
        subprocess_args.append("--verbosity=%s" % options.verbosity)
    if not options.interactive:
        subprocess_args.append("--noinput")
    if options.tags:
        subprocess_args.append("--tag=%s" % options.tags)
    if options.exclude_tags:
        subprocess_args.append("--exclude_tag=%s" % options.exclude_tags)
    if options.shuffle is not False:
        if options.shuffle is None:
            subprocess_args.append("--shuffle")
        else:
            subprocess_args.append("--shuffle=%s" % options.shuffle)
    return subprocess_args


def bisect_tests(bisection_label, options, test_labels, start_at, start_after):
    if not test_labels:
        test_labels = collect_test_modules(start_at, start_after)

    print("***** Bisecting test suite: %s" % " ".join(test_labels))

    # Make sure the bisection point isn't in the test list
    # Also remove tests that need to be run in specific combinations
    for label in [bisection_label, "model_inheritance_same_model_name"]:
        try:
            test_labels.remove(label)
        except ValueError:
            pass

    subprocess_args = get_subprocess_args(options)

    iteration = 1
    while len(test_labels) > 1:
        midpoint = len(test_labels) // 2
        test_labels_a = test_labels[:midpoint] + [bisection_label]
        test_labels_b = test_labels[midpoint:] + [bisection_label]
        print("***** Pass %da: Running the first half of the test suite" % iteration)
        print("***** Test labels: %s" % " ".join(test_labels_a))
        failures_a = subprocess.run(subprocess_args + test_labels_a)

        print("***** Pass %db: Running the second half of the test suite" % iteration)
        print("***** Test labels: %s" % " ".join(test_labels_b))
        print("")
        failures_b = subprocess.run(subprocess_args + test_labels_b)

        if failures_a.returncode and not failures_b.returncode:
            print("***** Problem found in first half. Bisecting again...")
            iteration += 1
            test_labels = test_labels_a[:-1]
        elif failures_b.returncode and not failures_a.returncode:
            print("***** Problem found in second half. Bisecting again...")
            iteration += 1
            test_labels = test_labels_b[:-1]
        elif failures_a.returncode and failures_b.returncode:
            print("***** Multiple sources of failure found")
            break
        else:
            print("***** No source of failure found... try pair execution (--pair)")
            break

    if len(test_labels) == 1:
        print("***** Source of error: %s" % test_labels[0])


def paired_tests(paired_test, options, test_labels, start_at, start_after):
    if not test_labels:
        test_labels = collect_test_modules(start_at, start_after)

    print("***** Trying paired execution")

    # Make sure the constant member of the pair isn't in the test list
    # Also remove tests that need to be run in specific combinations
    for label in [paired_test, "model_inheritance_same_model_name"]:
        try:
            test_labels.remove(label)
        except ValueError:
            pass

    subprocess_args = get_subprocess_args(options)

    for i, label in enumerate(test_labels):
        print("***** %d of %d: Check test pairing with %s" % (i + 1, len(test_labels), label))
        failures = subprocess.call(subprocess_args + [label, paired_test])
        if failures:
            print("***** Found problem pair with %s" % label)
            return

    print("***** No problem pair found")


if __name__ == "__main__":
    # Create a specific subdirectory for the duration of the test suite.
    TMPDIR = tempfile.mkdtemp(prefix="django_")
    # Set the TMPDIR environment variable in addition to tempfile.tempdir
    # so that children processes inherit it.
    tempfile.tempdir = os.environ["TMPDIR"] = TMPDIR
    # Remove the temporary TMPDIR.
    atexit.register(shutil.rmtree, TMPDIR)

    parser = argparse.ArgumentParser(description="Run the Django test suite.")
    parser.add_argument(
        "modules",
        nargs="*",
        metavar="module",
        help='Optional path(s) to test modules; e.g. "i18n" or '
        '"i18n.tests.TranslationTests.test_lazy_objects".',
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        default=1,
        type=int,
        choices=[0, 1, 2, 3],
        help="Verbosity level; 0=minimal output, 1=normal output, 2=all output",
    )
    parser.add_argument(
        "--noinput",
        action="store_false",
        dest="interactive",
        help="Tells Django to NOT prompt the user for input of any kind.",
    )
    parser.add_argument(
        "--failfast",
        action="store_true",
        help="Tells Django to stop running the test suite after first failed test.",
    )
    parser.add_argument(
        "--keepdb",
        action="store_true",
        help="Tells Django to preserve the test database between runs.",
    )
    parser.add_argument(
        "--settings",
        help='Python path to settings module, e.g. "myproject.settings". If '
        "this isn't provided, either the DJANGO_SETTINGS_MODULE "
        'environment variable or "test_sqlite" will be used.',
    )
    parser.add_argument(
        "--bisect",
        help="Bisect the test suite to discover a test that causes a test "
        "failure when combined with the named test.",
    )
    parser.add_argument(
        "--pair",
        help="Run the test suite in pairs with the named test to find problem pairs.",
    )
    parser.add_argument(
        "--shuffle",
        nargs="?",
        default=False,
        type=int,
        metavar="SEED",
        help=("Shuffle the order of test cases to help check that tests are properly isolated."),
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="Sort test suites and test cases in opposite order to debug "
        "test side effects not apparent with normal execution lineup.",
    )
    parser.add_argument(
        "--debug-sql",
        action="store_true",
        help="Turn on the SQL query logger within tests.",
    )
    # 0 is converted to "auto" or 1 later on, depending on a method used by
    # multiprocessing to start subprocesses and on the backend support for
    # cloning databases.
    parser.add_argument(
        "--parallel",
        nargs="?",
        const="auto",
        default=0,
        type=parallel_type,
        metavar="N",
        help=(
            'Run tests using up to N parallel processes. Use the value "auto" '
            "to run one test process for each processor core."
        ),
    )
    parser.add_argument(
        "--tag",
        dest="tags",
        action="append",
        help="Run only tests with the specified tags. Can be used multiple times.",
    )
    parser.add_argument(
        "--exclude-tag",
        dest="exclude_tags",
        action="append",
        help="Do not run tests with the specified tag. Can be used multiple times.",
    )
    parser.add_argument(
        "--start-after",
        dest="start_after",
        help="Run tests starting after the specified top-level module.",
    )
    parser.add_argument(
        "--start-at",
        dest="start_at",
        help="Run tests starting at the specified top-level module.",
    )
    parser.add_argument(
        "--pdb", action="store_true", help="Runs the PDB debugger on error or failure."
    )
    parser.add_argument(
        "-b",
        "--buffer",
        action="store_true",
        help="Discard output of passing tests.",
    )
    parser.add_argument(
        "--timing",
        action="store_true",
        help="Output timings, including database set up and total run time.",
    )
    parser.add_argument(
        "-k",
        dest="test_name_patterns",
        action="append",
        help=(
            "Only run test methods and classes matching test name pattern. "
            "Same as unittest -k option. Can be used multiple times."
        ),
    )
    if PY312:
        parser.add_argument(
            "--durations",
            dest="durations",
            type=int,
            default=None,
            metavar="N",
            help="Show the N slowest test cases (N=0 for all).",
        )

    options = parser.parse_args()

    # Allow including a trailing slash on app_labels for tab completion convenience.
    options.modules = [os.path.normpath(labels) for labels in options.modules]

    mutually_exclusive_options = [
        options.start_at,
        options.start_after,
        options.modules,
    ]
    enabled_module_options = [bool(option) for option in mutually_exclusive_options].count(True)
    if enabled_module_options > 1:
        print("Aborting: --start-at, --start-after, and test labels are mutually exclusive.")
        sys.exit(1)
    for opt_name in ["start_at", "start_after"]:
        opt_val = getattr(options, opt_name)
        if opt_val:
            if "." in opt_val:
                print("Aborting: --%s must be a top-level module." % opt_name.replace("_", "-"))
                sys.exit(1)
            setattr(options, opt_name, os.path.normpath(opt_val))
    if options.settings:
        os.environ["DJANGO_SETTINGS_MODULE"] = options.settings
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_sqlite")
        options.settings = os.environ["DJANGO_SETTINGS_MODULE"]

    if options.bisect:
        bisect_tests(
            options.bisect,
            options,
            options.modules,
            options.start_at,
            options.start_after,
        )
    elif options.pair:
        paired_tests(
            options.pair,
            options,
            options.modules,
            options.start_at,
            options.start_after,
        )
    else:
        time_keeper = TimeKeeper() if options.timing else NullTimeKeeper()
        with time_keeper.timed("Total run"):
            failures = django_tests(
                options.verbosity,
                options.interactive,
                options.failfast,
                options.keepdb,
                options.reverse,
                options.modules,
                options.debug_sql,
                options.parallel,
                options.tags,
                options.exclude_tags,
                options.test_name_patterns,
                options.start_at,
                options.start_after,
                options.pdb,
                options.buffer,
                options.timing,
                options.shuffle,
                getattr(options, "durations", None),
            )
        time_keeper.print_results()
        if failures:
            sys.exit(1)
