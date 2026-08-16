import os

# This is an example test settings file for use with the Django test suite.
#
# The 'sqlite3' backend requires only the ENGINE setting (an in-
# memory database will be used). All other backends will require a
# NAME and potentially authentication information. See the
# following section in the docs for more information:
#
# https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/unit-tests/
#
# The different databases that Django supports behave differently in certain
# situations, so it is recommended to run the test suite against as many
# database backends as possible.  You may want to create a separate settings
# file for each of the backends you test against.

DATABASES = {
    "default": {
        "ENGINE": "djrm.db.backends.sqlite3",
        "TEST": {
            "NAME": os.path.join(os.environ.get("TMPDIR", os.getcwd()), "test_default.sqlite3")
        },
    },
    "other": {
        "ENGINE": "djrm.db.backends.sqlite3",
        "TEST": {"NAME": os.path.join(os.environ.get("TMPDIR", os.getcwd()), "test_other.sqlite3")},
    },
}

SECRET_KEY = "django_tests_secret_key"

DEFAULT_AUTO_FIELD = "djrm.db.models.AutoField"

USE_TZ = False
