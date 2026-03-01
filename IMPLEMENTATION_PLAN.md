# djo — Implementation Plan

**Upstream base:** Django 5.2 LTS (latest tag from `stable/5.2.x`)
**Goal:** Transform Django into `djo`, a standalone ORM + migrations + DB backends library.

This plan is structured as sequential phases. Each phase includes exact operations, expected issues, verification steps, and commit boundaries.

---

## Phase 0: Repository Setup

### 0.1 Objective

Set up the repository with proper remotes, branches, and verify the upstream baseline works.

### 0.2 Operations

```bash
# 1. Ensure we're on the latest 5.2.x tag
cd /path/to/django
git remote add upstream https://github.com/django/django.git 2>/dev/null || true
git fetch upstream --tags
LATEST_TAG=$(git tag -l 'v5.2*' --sort=-v:refname | head -1)
echo "Using tag: $LATEST_TAG"

# 2. Create the djo working branch from the tag
git checkout -b djo/main "$LATEST_TAG"

# 3. Verify baseline: run a minimal ORM test to confirm upstream works
cd tests/
python runtests.py --settings=test_sqlite basic --verbosity=0
# Expected: all tests pass
cd ..
```

### 0.3 Branch structure

```
djo/main              ← primary development branch (based on latest 5.2.x tag)
upstream/stable/5.2.x ← read-only tracking of Django upstream
```

### 0.4 Done check

- [x] `djo/main` branch exists, based on latest `v5.2.*` tag.
- [x] `python tests/runtests.py --settings=test_sqlite basic` passes.
- [x] `.git/config` has the upstream remote configured.

### 0.5 Commit

No commit yet — this is just setup.

---

## Phase 1: Namespace Rename (`django` → `djo`)

### 1.1 Objective

Mechanically rename the top-level Python package from `django` to `djo` and update all internal references. This is the largest single change and must be fully mechanical/reproducible.

### 1.2 Strategy

Use a scripted approach so the rename can be re-applied after any upstream rebase:

1. Rename the `django/` directory to `djo/`.
2. Find-and-replace all Python source references.
3. Update configuration files.
4. Verify tests still pass under the new namespace.

### 1.3 Operations

#### 1.3.1 Directory rename

```bash
git mv django djo
```

#### 1.3.2 Source code replacements

The replacements must be applied in a specific order to avoid partial matches:

```bash
# Create the rename script: scripts/rename_namespace.sh
# This script is idempotent and can be re-run after a rebase.

# Order matters: longer strings first to avoid partial replacement issues.

# 1. Python imports & string references in .py files
find djo tests -name '*.py' -type f -exec sed -i '' \
  -e 's/django\.contrib/djo.contrib/g' \
  -e 's/django\.core/djo.core/g' \
  -e 's/django\.db/djo.db/g' \
  -e 's/django\.apps/djo.apps/g' \
  -e 's/django\.conf/djo.conf/g' \
  -e 's/django\.dispatch/djo.dispatch/g' \
  -e 's/django\.forms/djo.forms/g' \
  -e 's/django\.http/djo.http/g' \
  -e 's/django\.middleware/djo.middleware/g' \
  -e 's/django\.shortcuts/djo.shortcuts/g' \
  -e 's/django\.template/djo.template/g' \
  -e 's/django\.templatetags/djo.templatetags/g' \
  -e 's/django\.test/djo.test/g' \
  -e 's/django\.urls/djo.urls/g' \
  -e 's/django\.utils/djo.utils/g' \
  -e 's/django\.views/djo.views/g' \
  {} +

# 2. Bare "django" references that are the package name itself
#    (more targeted to avoid false positives in comments/docs)
find djo tests -name '*.py' -type f -exec sed -i '' \
  -e 's/^import django$/import djo/g' \
  -e 's/^import django\b/import djo/g' \
  -e 's/from django import/from djo import/g' \
  -e "s/'django'/'djo'/g" \
  -e 's/"django"/"djo"/g' \
  {} +

# 3. DJANGO_SETTINGS_MODULE → DJO_SETTINGS_MODULE
find djo tests -name '*.py' -type f -exec sed -i '' \
  -e 's/DJANGO_SETTINGS_MODULE/DJO_SETTINGS_MODULE/g' \
  {} +

# 4. django-admin → djo (CLI entry point references)
find djo tests -name '*.py' -type f -exec sed -i '' \
  -e 's/django-admin/djo/g' \
  {} +

# 5. Update __main__.py
# djo/__main__.py should import from djo

# 6. Configuration files
sed -i '' \
  -e 's/known_first_party = "django"/known_first_party = "djo"/g' \
  -e 's/include = \["django\*"\]/include = ["djo*"]/g' \
  -e 's/version = {attr = "django\.__version__"}/version = {attr = "djo.__version__"}/g' \
  -e 's/django\.core\.management:execute_from_command_line/djo.core.management:execute_from_command_line/g' \
  pyproject.toml

# 7. Test settings files
find tests -name 'test_*.py' -maxdepth 1 -exec sed -i '' \
  -e 's/django\./djo./g' \
  -e 's/DJANGO_SETTINGS_MODULE/DJO_SETTINGS_MODULE/g' \
  {} +

# 8. runtests.py
sed -i '' \
  -e 's/django\./djo./g' \
  -e 's/DJANGO_SETTINGS_MODULE/DJO_SETTINGS_MODULE/g' \
  -e 's/import django/import djo/g' \
  -e 's/from django/from djo/g' \
  tests/runtests.py
```

#### 1.3.3 Handle tricky patterns

Some patterns need special attention:

```bash
# a. String references in migrations (engine paths)
#    e.g., "django.db.backends.sqlite3" in test fixtures
find tests -name '*.py' -exec grep -l 'django\.db\.backends' {} + | \
  xargs sed -i '' 's/django\.db\.backends/djo.db.backends/g'

# b. AppConfig references in test apps
#    e.g., default_app_config = 'tests.myapp.apps.MyAppConfig'
#    These usually don't contain "django" so no change needed.

# c. Model Meta.app_label values — these don't use "django" prefix typically.

# d. The django.VERSION references
find djo -name '*.py' -exec sed -i '' \
  -e 's/django\.VERSION/djo.VERSION/g' \
  {} +

# e. contrib.contenttypes has hardcoded "django.contrib.contenttypes" in migrations
find djo/contrib -name '*.py' -exec sed -i '' \
  -e 's/django\.contrib/djo.contrib/g' \
  {} +
```

#### 1.3.4 Verify no remaining "django" Python references

```bash
# Check for any remaining django references in Python files (excluding comments/docs)
grep -rn "from django\." djo/ --include='*.py' | head -20
grep -rn "import django" djo/ --include='*.py' | head -20
grep -rn "'django\." djo/ --include='*.py' | head -20
# These should all return empty.

# Allow "django" in:
# - Comments mentioning Django (documentation)
# - License text
# - DJANGO_VERSION_PICKLE_KEY (keep for pickle compat - this is a serialization format constant)
```

### 1.4 Special consideration: DJANGO_VERSION_PICKLE_KEY

In `djo/db/utils.py` there is a constant `DJANGO_VERSION_PICKLE_KEY`. This is used for pickle serialization compatibility. **Keep the value as `"django-version"` but rename the Python constant** to `DJANGO_VERSION_PICKLE_KEY` (unchanged name). The string value `"django-version"` is a serialization format constant, not a namespace reference. Do not change it.

### 1.5 Special consideration: `djo.setup()`

The `setup()` function in `djo/__init__.py` currently:
1. Configures logging
2. Sets URL script prefix
3. Populates the app registry

Simplify it:

```python
def setup(set_prefix=False):
    """
    Configure the settings (this happens as a side effect of accessing the
    first setting) and populate the app registry.
    """
    from djo.apps import apps
    from djo.conf import settings
    from djo.utils.log import configure_logging

    configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)
    apps.populate(settings.INSTALLED_APPS)
```

Remove the URL prefix logic entirely (no `djo.urls` module exists). Keep logging configuration as it's useful for any application. Change `set_prefix` default to `False` (it has no effect since URL system is removed, but keeping the parameter avoids signature breakage in case any code passes it).

### 1.6 Expected failures at this stage

1. **Import errors for deleted-but-still-referenced modules**: After rename but before pruning, everything still exists so there should be no import errors. But tests for web features will have namespace-updated imports. These tests will be deleted in Phase 2.

2. **`DJANGO_VERSION_PICKLE_KEY` value change**: If the sed script changed the string value, fix it back. The sed rules above should not affect it since the value `"django-version"` uses hyphen not dot, but verify.

3. **Locale file paths**: `djo/conf/locale/` and `djo/contrib/*/locale/` contain `.po` files with `django` references. These are translation files. Leave them as-is (they're data files, not code).

4. **Test data/fixtures**: Some test fixture files (JSON, XML) may contain `django.contrib.contenttypes` references. These need updating.

### 1.7 Verification

```bash
# Quick syntax check
python -c "import djo; print(djo.__version__)"

# Run baseline test
cd tests/
python runtests.py --settings=test_sqlite basic -v0
cd ..
```

### 1.8 Commit

```
[namespace] Rename django → djo in all source files

Mechanical find-and-replace of the Python package namespace from
'django' to 'djo'. Applied via scripts/rename_namespace.sh for
reproducibility during upstream rebases.

- Renamed django/ directory to djo/
- Updated all Python imports
- Updated DJANGO_SETTINGS_MODULE → DJO_SETTINGS_MODULE
- Updated pyproject.toml, test configs
- Preserved DJANGO_VERSION_PICKLE_KEY string value for pickle compat
```

---

## Phase 2: Remove Web Framework Subsystems

### 2.1 Objective

Delete all packages and modules that are part of the web framework, not the ORM/DB stack.

### 2.2 Operations

#### 2.2.1 Top-level package deletions

```bash
rm -rf djo/forms/
rm -rf djo/http/
rm -rf djo/middleware/
rm -rf djo/template/
rm -rf djo/templatetags/
rm -rf djo/urls/
rm -rf djo/views/
rm -f  djo/shortcuts.py
```

#### 2.2.2 Core subpackage deletions

```bash
rm -rf djo/core/cache/
rm -rf djo/core/handlers/
rm -rf djo/core/mail/
rm -rf djo/core/servers/
rm -f  djo/core/asgi.py
rm -f  djo/core/wsgi.py
rm -f  djo/core/paginator.py
```

#### 2.2.3 Contrib deletions

```bash
rm -rf djo/contrib/admin/
rm -rf djo/contrib/admindocs/
rm -rf djo/contrib/auth/
rm -rf djo/contrib/flatpages/
rm -rf djo/contrib/humanize/
rm -rf djo/contrib/messages/
rm -rf djo/contrib/redirects/
rm -rf djo/contrib/sessions/
rm -rf djo/contrib/sitemaps/
rm -rf djo/contrib/sites/
rm -rf djo/contrib/staticfiles/
rm -rf djo/contrib/syndication/
```

#### 2.2.4 Contrib partial cleanups

```bash
# contenttypes: remove web-facing parts
rm -f djo/contrib/contenttypes/admin.py
rm -f djo/contrib/contenttypes/views.py
rm -f djo/contrib/contenttypes/forms.py

# postgres: remove web-facing parts
rm -rf djo/contrib/postgres/forms/
rm -rf djo/contrib/postgres/templates/
rm -rf djo/contrib/postgres/jinja2/

# gis: remove web-facing parts
rm -rf djo/contrib/gis/admin/
rm -f  djo/contrib/gis/feeds.py
rm -rf djo/contrib/gis/forms/
rm -rf djo/contrib/gis/sitemaps/
rm -f  djo/contrib/gis/shortcuts.py
rm -rf djo/contrib/gis/static/
rm -rf djo/contrib/gis/templates/
rm -f  djo/contrib/gis/views.py
```

#### 2.2.5 Conf cleanups

```bash
rm -rf djo/conf/app_template/
rm -rf djo/conf/project_template/
rm -rf djo/conf/urls/
```

#### 2.2.6 Utils cleanups

Remove utils modules that are web-only AND confirmed not imported by any retained code:

```bash
# Definitely safe to remove
rm -f djo/utils/autoreload.py
rm -f djo/utils/cache.py
rm -f djo/utils/feedgenerator.py
rm -f djo/utils/lorem_ipsum.py
rm -f djo/utils/archive.py
```

For these, verify with import tracing first:

```bash
# Check if anything retained imports these
grep -rn "from djo.utils.http import\|from djo.utils import http\|djo\.utils\.http" djo/ --include='*.py' | grep -v '\.pyc'
grep -rn "from djo.utils.safestring import\|djo\.utils\.safestring" djo/ --include='*.py' | grep -v '\.pyc'
grep -rn "from djo.utils.html import\|djo\.utils\.html" djo/ --include='*.py' | grep -v '\.pyc'
grep -rn "from djo.utils.xmlutils import\|djo\.utils\.xmlutils" djo/ --include='*.py' | grep -v '\.pyc'
```

Based on expected results:
- `djo/utils/html.py` — likely imported by validators → **keep**
- `djo/utils/safestring.py` — likely imported by some model internals → **keep if referenced, else remove**
- `djo/utils/http.py` — likely only imported by web modules → **remove if confirmed**
- `djo/utils/xmlutils.py` — imported by XML serializer → **keep**

#### 2.2.7 Test infrastructure cleanup

```bash
# Remove web-related parts from djo/test/
rm -f djo/test/client.py
rm -f djo/test/selenium.py
rm -f djo/test/html.py
```

Update `djo/test/__init__.py` to remove imports of deleted modules (TestClient, etc.).

### 2.3 Fix broken imports in retained modules

After deletion, some retained modules may import deleted modules. Find and fix:

```bash
# Find all import errors in retained code
python -c "
import sys
sys.path.insert(0, '.')
import djo
" 2>&1 | head -50
```

Common fixes needed:

1. **`djo/core/signals.py`** — may import from deleted modules. Keep the signal definitions, remove any imports from deleted modules.

2. **`djo/contrib/contenttypes/admin.py`** — already deleted above.

3. **`djo/contrib/postgres/__init__.py`** — may reference forms. Update to remove those references.

4. **`djo/contrib/gis/__init__.py`** — may reference admin/views. Update.

5. **`djo/test/testcases.py`** — imports `Client` from `djo.test.client`. Either stub the client or remove the `Client` integration from `TestCase`. The DB test infrastructure (`TransactionTestCase`, `TestCase`) should still work for direct ORM testing — they primarily manage DB transactions and fixtures. Remove/stub the HTTP client integration:
   - Remove `self.client` from `SimpleTestCase.__init__`
   - Remove `self.async_client` 
   - Remove `_pre_setup` client initialization
   - Remove `modify_settings`, `override_settings` if they import from web modules (unlikely — they're in `djo.test.utils` and work with settings only)

6. **`djo/test/utils.py`** — may import from `djo.urls` or `djo.template`. Stub out or remove the URL/template-related test utilities. Keep `override_settings`, `modify_settings`, `isolate_apps`.

7. **`djo/core/management/base.py`** — the base command class. Should be self-contained. May reference `django.core.checks` — that's fine, we keep checks.

8. **`djo/core/management/commands/runserver.py`** — already in the delete list (Phase 3).

9. **`djo/core/validators.py`** — may import from `djo.utils.html` or `djo.utils.ipv6`. Both are kept.

10. **`djo/db/models/fields/files.py`** — imports from `djo.core.files`. Kept.

### 2.4 Expected failures

- `ImportError` for any retained module that references a deleted one. Address each systematically.
- Key approach: use `python -c "import djo; djo.setup()"` with a minimal settings configuration as the smoke test. Iterate until it works.

### 2.5 Verification

```bash
# Smoke test: can we import and setup djo?
python -c "
import djo
from djo.conf import settings
settings.configure(
    DATABASES={'default': {'ENGINE': 'djo.db.backends.sqlite3', 'NAME': ':memory:'}},
    DEFAULT_AUTO_FIELD='djo.db.models.BigAutoField',
    INSTALLED_APPS=[],
)
djo.setup()
from djo.db import connection
print('Connection:', connection.vendor)
print('OK')
"

# Expected output:
# Connection: sqlite
# OK
```

### 2.6 Commit

```
[prune] Remove web framework packages

Delete HTTP, forms, views, templates, middleware, URL routing, admin,
auth, sessions, messages, cache, mail, dev server, and all other
non-ORM Django subsystems.

Retained: db/, apps/, conf/, core/management/, core/checks/,
core/serializers/, core/exceptions.py, core/validators.py,
core/files/, dispatch/, utils/ (subset), test/ (DB parts),
contrib/contenttypes (ORM parts), contrib/postgres (ORM parts),
contrib/gis (DB layer).
```

---

## Phase 3: Management Command Pruning

### 3.1 Objective

Remove management commands not related to DB/migrations. Keep only the commands listed in SPEC.md §5.1.

### 3.2 Operations

```bash
# Delete non-DB commands
rm -f djo/core/management/commands/check.py
rm -f djo/core/management/commands/compilemessages.py
rm -f djo/core/management/commands/createcachetable.py
rm -f djo/core/management/commands/makemessages.py
rm -f djo/core/management/commands/runserver.py
rm -f djo/core/management/commands/sendtestemail.py
rm -f djo/core/management/commands/shell.py
rm -f djo/core/management/commands/startapp.py
rm -f djo/core/management/commands/startproject.py
rm -f djo/core/management/commands/test.py
rm -f djo/core/management/commands/testserver.py
```

#### 3.2.1 Check management/templates.py

`djo/core/management/templates.py` is used by `startapp` and `startproject`. Since both commands are deleted, this file can be removed too:

```bash
rm -f djo/core/management/templates.py
```

### 3.3 Verify remaining commands

```bash
ls djo/core/management/commands/
# Expected:
# __init__.py
# dbshell.py
# diffsettings.py
# dumpdata.py
# flush.py
# inspectdb.py
# loaddata.py
# makemigrations.py
# migrate.py
# optimizemigration.py
# showmigrations.py
# sqlflush.py
# sqlmigrate.py
# sqlsequencereset.py
# squashmigrations.py
```

### 3.4 Update management/__init__.py if needed

Check if `djo/core/management/__init__.py` has any hardcoded command lists. Django auto-discovers commands from the `commands/` directory, so deletion should be sufficient.

```bash
grep -n "runserver\|startapp\|startproject\|shell\|test\b\|sendtestemail\|createcachetable\|compilemessages\|makemessages\|testserver" djo/core/management/__init__.py
```

If any references exist, remove them.

### 3.5 Verification

```bash
# List available commands
python -c "
import djo
from djo.conf import settings
settings.configure(
    DATABASES={'default': {'ENGINE': 'djo.db.backends.sqlite3', 'NAME': ':memory:'}},
    DEFAULT_AUTO_FIELD='djo.db.models.BigAutoField',
    INSTALLED_APPS=[],
)
djo.setup()
from djo.core.management import get_commands
cmds = sorted(get_commands().keys())
print('Available commands:', cmds)
"

# Expected: dbshell, diffsettings, dumpdata, flush, inspectdb, loaddata,
#           makemigrations, migrate, optimizemigration, showmigrations,
#           sqlflush, sqlmigrate, sqlsequencereset, squashmigrations
```

### 3.6 Commit

```
[prune] Remove non-DB management commands

Keep only DB/migration-related commands: makemigrations, migrate,
showmigrations, sqlmigrate, squashmigrations, optimizemigration,
inspectdb, dbshell, flush, loaddata, dumpdata, sqlflush,
sqlsequencereset, diffsettings.
```

---

## Phase 4: System Checks Trimming

### 4.1 Objective

Keep only ORM/DB-relevant system checks. Remove checks for web subsystems.

### 4.2 Operations

#### 4.2.1 Delete check modules

```bash
rm -f djo/core/checks/async_checks.py
rm -f djo/core/checks/caches.py
rm -f djo/core/checks/templates.py
rm -f djo/core/checks/translation.py
rm -f djo/core/checks/urls.py
rm -f djo/core/checks/messages.py   # Keep this! This is CheckMessage, not the messages framework.
rm -rf djo/core/checks/security/
```

**WAIT** — `djo/core/checks/messages.py` contains `CheckMessage`, `Error`, `Warning`, etc. — the actual check message classes. **Do NOT delete it.** The `messages.py` here is NOT the messages framework. Keep it.

Corrected deletions:

```bash
rm -f djo/core/checks/async_checks.py
rm -f djo/core/checks/caches.py
rm -f djo/core/checks/templates.py
rm -f djo/core/checks/translation.py
rm -f djo/core/checks/urls.py
rm -rf djo/core/checks/security/
rm -rf djo/core/checks/compatibility/   # Remove only if no ORM-relevant compat checks
```

Check `compatibility/django_4_0.py` first:

```bash
cat djo/core/checks/compatibility/django_4_0.py
```

If it only checks `HttpResponse` csrf cookie settings or similar web features, delete the whole directory. If it has ORM-relevant checks, keep it.

#### 4.2.2 Update djo/core/checks/__init__.py

Remove the import lines for deleted check modules:

**Before:**
```python
import djo.core.checks.async_checks
import djo.core.checks.caches
import djo.core.checks.commands
import djo.core.checks.compatibility.django_4_0
import djo.core.checks.database
import djo.core.checks.files
import djo.core.checks.model_checks
import djo.core.checks.security.base
import djo.core.checks.security.csrf
import djo.core.checks.security.sessions
import djo.core.checks.templates
import djo.core.checks.translation
import djo.core.checks.urls
```

**After:**
```python
import djo.core.checks.commands
import djo.core.checks.database
import djo.core.checks.model_checks
```

Optionally keep `djo.core.checks.files` if `FileField` checks are registered there:

```bash
cat djo/core/checks/files.py
```

If it only checks `FILE_UPLOAD_HANDLERS` or similar web settings, delete it. If it validates `MEDIA_ROOT` or similar settings that `FileField` depends on, keep it.

### 4.3 Verification

```bash
python -c "
import djo
from djo.conf import settings
settings.configure(
    DATABASES={'default': {'ENGINE': 'djo.db.backends.sqlite3', 'NAME': ':memory:'}},
    DEFAULT_AUTO_FIELD='djo.db.models.BigAutoField',
    INSTALLED_APPS=[],
)
djo.setup()
from djo.core.checks import run_checks, Tags
errors = run_checks(tags=[Tags.models, Tags.database])
print('Check errors:', errors)
print('OK')
"
# Expected: Check errors: [] (no errors with empty app list)
# Expected: OK
```

### 4.4 Commit

```
[prune] Trim system checks to ORM-only

Remove check modules for async, caches, security, templates,
translation, URLs. Keep database, model_checks, commands.
Update checks/__init__.py to only import retained check modules.
```

---

## Phase 5: Test Pruning

### 5.1 Objective

Remove all test directories not related to ORM/DB/migrations. Make the remaining tests pass.

### 5.2 Operations

#### 5.2.1 Delete web-framework test directories

```bash
cd tests/

# Admin tests
rm -rf admin_autodiscover/ admin_changelist/ admin_checks/ admin_custom_urls/
rm -rf admin_default_site/ admin_docs/ admin_filters/ admin_inlines/
rm -rf admin_ordering/ admin_registration/ admin_scripts/ admin_utils/
rm -rf admin_views/ admin_widgets/ modeladmin/ generic_inline_admin/

# Auth tests
rm -rf auth_tests/

# Web framework tests
rm -rf asgi/ wsgi/ builtin_server/
rm -rf cache/ conditional_processing/ context_processors/ csrf_tests/
rm -rf decorators/ file_storage/ file_uploads/ files/
rm -rf flatpages_tests/ forms_tests/ generic_views/ get_object_or_404/
rm -rf handlers/ httpwrappers/ humanize_tests/ i18n/ inline_formsets/
rm -rf logging_tests/ mail/ messages_tests/ middleware/ middleware_exceptions/
rm -rf model_forms/ model_formsets/ model_formsets_regress/
rm -rf pagination/ project_template/ redirects_tests/ requests_tests/
rm -rf resolve_url/ responses/ sessions_tests/ shell/ shortcuts/
rm -rf signed_cookies_tests/ signing/ sitemaps_tests/ sites_framework/ sites_tests/
rm -rf staticfiles_tests/ syndication_tests/
rm -rf template_backends/ template_loader/ template_tests/ templates/
rm -rf test_client/ test_client_regress/
rm -rf urlpatterns/ urlpatterns_reverse/ user_commands/ view_tests/
rm -rf absolute_url_overrides/

# Infrastructure tests (not ORM)
rm -rf app_loading/ bash_completion/ import_error_package/
rm -rf test_runner/ test_runner_apps/ sphinx/ requirements/
```

#### 5.2.2 Partial directory cleanups

**`async/` directory:**

```bash
# Keep only ORM-related async tests
cd tests/async/
# Keep: test_async_queryset.py, test_async_model_methods.py, test_async_related_managers.py
# Remove everything else
rm -f test_async_auth.py test_async_shortcuts.py
# Check for other non-ORM files
ls *.py
cd ..
```

**`check_framework/` directory:**

```bash
# Review what's in check_framework/
ls tests/check_framework/
# Keep tests related to model/database checks
# Remove tests for web subsystem checks
# This requires reading the test files to determine
```

**`utils_tests/` directory:**

```bash
# Keep tests for retained utils modules
# Remove tests for deleted utils (autoreload, cache, feedgenerator, etc.)
cd tests/utils_tests/
rm -f test_autoreload.py test_feedgenerator.py test_lorem_ipsum.py test_archive.py
# Keep: test_dateformat.py, test_dateparse.py, test_deconstruct.py, test_duration.py,
#        test_encoding.py, test_functional.py, test_module_loading.py, test_text.py,
#        test_timezone.py, test_tree.py, test_datastructures.py, test_hashable.py,
#        test_regex_helper.py, test_termcolors.py, test_crypto.py, test_numberformat.py
# Check for web-specific test files and remove them
cd ../..
```

#### 5.2.3 Update test configuration

**`tests/runtests.py`:**

- Check for hardcoded test module lists. Django's runtests.py auto-discovers test directories, so deleted directories will simply be skipped.
- Verify that `ALWAYS_INSTALLED_APPS`, `ALWAYS_MIDDLEWARE_CLASSES`, etc. in the test settings don't reference deleted contrib apps.

```bash
grep -n "admin\|auth\|sessions\|messages\|staticfiles\|sites\|contenttypes" tests/test_sqlite.py
```

Update `INSTALLED_APPS` in test settings to only include apps that exist:

```python
INSTALLED_APPS = [
    'djo.contrib.contenttypes',
    # Remove: djo.contrib.auth, djo.contrib.admin, etc.
]
```

**`tests/runtests.py`** may have a `SUBDIRS_TO_SKIP` or similar list. Update accordingly.

### 5.3 Fix test failures iteratively

```bash
# Run all kept tests
cd tests/
python runtests.py --settings=test_sqlite -v0 2>&1 | tail -20
```

Expected categories of failures:

#### 5.3.1 Import errors in test helper code

Some test modules import `djo.test.client.Client` or `djo.http.HttpRequest` in setUp methods. Fix by:
- If only a few tests in a kept module import web stuff → remove those specific tests.
- If the entire module depends on web imports → remove the test module.

#### 5.3.2 Missing INSTALLED_APPS dependencies

Some ORM tests may expect `djo.contrib.auth` to be in INSTALLED_APPS (e.g., tests using `User` model). Fix by:
- If the test only uses `User` as a convenient model → create a simple test model instead or skip the test.
- If it deeply depends on auth → remove the test.

#### 5.3.3 Test runner infrastructure

`djo/test/testcases.py` will have been partially stripped. Ensure `TransactionTestCase` and `TestCase` still work for DB testing:

```python
# Key functionality to preserve:
# - Database creation/destruction
# - Transaction wrapping per test
# - Fixture loading
# - assertQuerySetEqual, assertNumQueries

# Functionality to remove/stub:
# - self.client (HTTP test client)
# - self.async_client
# - assertRedirects, assertTemplateUsed (HTTP assertions)
# - assertContains, assertNotContains (HTTP assertions)
# - assertFormError (form assertions)
```

#### 5.3.4 contenttypes dependency

Many ORM tests use `GenericForeignKey` which requires `djo.contrib.contenttypes` in `INSTALLED_APPS`. Ensure it's included in test settings.

### 5.4 Verification

```bash
# Run all remaining tests
cd tests/
python runtests.py --settings=test_sqlite -v0 --parallel 2>&1 | tail -5

# Expected: 
# Ran XXXX tests in YY.YYs
# OK (skipped=N)
```

Run per-backend (if available):

```bash
# PostgreSQL
python runtests.py --settings=test_postgres -v0 --parallel 2>&1 | tail -5

# MySQL
python runtests.py --settings=test_mysql -v0 --parallel 2>&1 | tail -5
```

### 5.5 Commit

```
[prune] Remove web-related test directories

Keep ORM/DB/migration test suites (124 directories).
Remove admin, auth, forms, views, templates, HTTP, middleware,
sessions, cache, URL, and other web framework test suites.
Fix test settings to reference only retained apps.
```

Then a follow-up commit:

```
[fix] Fix test failures in retained ORM tests

- Stub/remove test methods that import web framework modules
- Update test settings INSTALLED_APPS
- Fix djo.test.testcases to work without HTTP client
```

---

## Phase 6: Packaging Polish

### 6.1 Objective

Finalize pyproject.toml, versioning, console script, and distribution metadata.

### 6.2 Operations

#### 6.2.1 Update pyproject.toml

```toml
[build-system]
requires = ["setuptools>=77.0.3"]
build-backend = "setuptools.build_meta"

[project]
name = "djo"
dynamic = ["version"]
requires-python = ">= 3.10"
dependencies = [
    "asgiref>=3.8.1",
    "sqlparse>=0.3.1",
    "tzdata; sys_platform == 'win32'",
]
authors = [
  {name = "djo contributors"},
]
description = "Django ORM, migrations, and database backends as a standalone library."
readme = "README.rst"
license = "BSD-3-Clause"
license-files = ["LICENSE", "LICENSE.python", "AUTHORS"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Topic :: Database",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

[project.optional-dependencies]
postgresql = ["psycopg>=3.1.8; python_version >= '3.10'", "psycopg2>=2.9"]
mysql = ["mysqlclient>=2.1"]

[project.scripts]
djo = "djo.core.management:execute_from_command_line"

[project.urls]
Source = "https://github.com/<org>/djo"
Tracker = "https://github.com/<org>/djo/issues"

[tool.isort]
profile = "black"
default_section = "THIRDPARTY"
known_first_party = "djo"

[tool.setuptools.dynamic]
version = {attr = "djo.__version__"}

[tool.setuptools.packages.find]
include = ["djo*"]
```

#### 6.2.2 Update djo/__init__.py version

Keep the upstream version tuple. Optionally add a `DJO_FORK_VERSION`:

```python
from djo.utils.version import get_version

VERSION = (5, 2, 12, "alpha", 0)  # matches upstream tag
__version__ = get_version(VERSION)
```

#### 6.2.3 Create/update README.rst

Update to describe djo, not Django. Brief, pointing to SPEC.md for details.

#### 6.2.4 Update djo/__main__.py

Ensure it works:

```python
"""
Invokes djo when the djo module is run as a script.

Example: python -m djo migrate
"""
from djo.core import management

if __name__ == "__main__":
    management.execute_from_command_line()
```

#### 6.2.5 CLI entry point verification

```bash
# Build and install in development mode
pip install -e .

# Test CLI
djo --help
djo migrate --help
djo showmigrations --help
```

#### 6.2.6 Build distribution

```bash
python -m build
ls dist/
# Expected: djo-5.2.X.tar.gz, djo-5.2.X-py3-none-any.whl

# Verify wheel contents
python -m zipfile -l dist/djo-5.2.X-py3-none-any.whl | head -20
# Should list djo/ package files, NOT django/
```

### 6.3 Verification

```bash
# Install from wheel in a fresh venv
python -m venv /tmp/djo-test
source /tmp/djo-test/bin/activate
pip install dist/djo-*.whl

# Smoke test
python -c "
import djo
from djo.conf import settings
settings.configure(
    DATABASES={'default': {'ENGINE': 'djo.db.backends.sqlite3', 'NAME': ':memory:'}},
    DEFAULT_AUTO_FIELD='djo.db.models.BigAutoField',
    INSTALLED_APPS=[],
)
djo.setup()
print('djo version:', djo.__version__)
print('OK')
"

# CLI test
djo diffsettings 2>&1 | head -5

deactivate
rm -rf /tmp/djo-test
```

### 6.4 Commits

```
[packaging] Update pyproject.toml for djo distribution

- Package name: djo
- Console script: djo
- Updated classifiers and metadata
- Updated dependencies (removed web-specific extras)
```

```
[packaging] Update README and __main__ for djo
```

---

## Phase 7: Fork Glue & _ext Package

### 7.1 Objective

Create the `djo/_ext/` package for any fork-specific patches that can't be expressed as mechanical deletions or renames.

### 7.2 Operations

```bash
mkdir -p djo/_ext/
```

#### 7.2.1 djo/_ext/__init__.py

```python
"""
djo._ext — Fork-specific extensions and patches.

This package contains all logic that is specific to the djo fork
and does not exist in upstream Django. Keeping fork-specific code
isolated here makes upstream rebasing easier and makes it clear
which code is original vs. modified.
"""
```

#### 7.2.2 Expected contents

At minimum:

- `djo/_ext/__init__.py` — docstring only.
- `djo/_ext/setup_helpers.py` — if `setup()` needs fork-specific adjustments beyond the simple trim done in Phase 1.

Most likely `_ext/` will remain nearly empty in the initial release. It's a convention for future changes.

### 7.3 Commit

```
[ext] Add djo/_ext/ fork-specific extension package
```

---

## Phase 8: Upstream Rebase Workflow

### 8.1 Objective

Document and verify the process for incorporating new upstream Django releases.

### 8.2 Workflow

#### 8.2.1 Preparation

```bash
# Fetch latest upstream
git fetch upstream --tags

# Identify the new tag
NEW_TAG=$(git tag -l 'v5.2*' --sort=-v:refname | head -1)
echo "New upstream tag: $NEW_TAG"

# Create a rebase branch
git checkout -b djo/rebase-${NEW_TAG} ${NEW_TAG}
```

#### 8.2.2 Re-apply fork commits

The fork consists of ~7 topic commits (from phases 1-7). These should be cherry-picked or rebased:

```bash
# Option A: Cherry-pick each topic commit
git cherry-pick <namespace-rename-commit>
git cherry-pick <prune-web-commit>
git cherry-pick <prune-commands-commit>
git cherry-pick <prune-checks-commit>
git cherry-pick <prune-tests-commit>
git cherry-pick <packaging-commit>
git cherry-pick <ext-commit>

# Option B: Rebase the whole series
git rebase --onto ${NEW_TAG} <original-tag> djo/main
```

#### 8.2.3 Resolve conflicts

1. **Namespace rename conflicts**: If upstream added new files or new `from django.x import y` lines in retained modules, the sed-based rename script can be re-run:
   ```bash
   # Re-run the rename script on any conflicting files
   bash scripts/rename_namespace.sh
   ```

2. **Deletion conflicts**: Files we deleted that upstream modified → just delete them again.

3. **Content conflicts in retained files**: These are the genuine conflicts. Resolve manually, preferring upstream logic with `djo` namespace.

#### 8.2.4 Verify

```bash
# Run the full test suite
cd tests/
python runtests.py --settings=test_sqlite -v0 --parallel
cd ..

# Smoke test
python -c "import djo; print(djo.__version__)"
```

#### 8.2.5 Tag and release

```bash
git tag djo-${NEW_TAG#v}  # e.g., djo-5.2.2
git checkout djo/main
git merge djo/rebase-${NEW_TAG}
git push origin djo/main --tags
```

### 8.3 Automated rename script

Create `scripts/rename_namespace.sh` that contains all the sed commands from Phase 1. This script can be re-run on any new upstream code to apply the namespace transform:

```bash
#!/usr/bin/env bash
# scripts/rename_namespace.sh
# Mechanically rename 'django' namespace to 'djo' in all source files.
# Idempotent — safe to run multiple times.
# Run from repo root.

set -euo pipefail

if [ -d "django" ] && [ ! -d "djo" ]; then
    git mv django djo
fi

# Python source files in djo/ and tests/
find djo tests -name '*.py' -type f -exec sed -i '' \
    -e 's/from django\b/from djo/g' \
    -e 's/import django\b/import djo/g' \
    -e "s/'django\./'djo./g" \
    -e 's/"django\./"djo./g' \
    -e "s/'django'/'djo'/g" \
    -e 's/"django"/"djo"/g' \
    -e 's/DJANGO_SETTINGS_MODULE/DJO_SETTINGS_MODULE/g' \
    -e 's/django-admin/djo/g' \
    {} +

# Config files  
sed -i '' \
    -e 's/django/djo/g' \
    pyproject.toml

echo "Namespace rename complete."
```

### 8.4 Conflict minimization principles

1. **Never modify upstream file internals unless absolutely necessary.** The rename is mechanical and reproducible.
2. **All deletions are additive (remove-only).** They don't conflict with upstream changes to other files.
3. **Fork-specific logic lives in `_ext/`.** If upstream changes break something, the fix goes in `_ext/`, not in the upstream-derived module.
4. **Keep the number of topic commits minimal** (~7). Each commit has a clear, bounded scope.

### 8.5 Commit

```
[upstream] Add rebase workflow script and documentation
```

---

## Phase Summary & Checklist

| Phase | Description | Key Done Check |
|---|---|---|
| 0 | Repo setup | `basic` tests pass on upstream tag |
| 1 | Namespace rename | `python -c "import djo; print(djo.__version__)"` works |
| 2 | Remove web subsystems | `djo.setup()` works with sqlite config, no ImportErrors |
| 3 | Command pruning | `get_commands()` returns only DB commands |
| 4 | Checks trimming | `run_checks(tags=[Tags.models, Tags.database])` works |
| 5 | Test pruning | All retained tests pass with `runtests.py --settings=test_sqlite` |
| 6 | Packaging | `pip install -e .` works, `djo migrate --help` works |
| 7 | Fork glue | `djo/_ext/` exists |
| 8 | Upstream workflow | `scripts/rename_namespace.sh` runs successfully |

---

## Tricky Areas & Recommendations

### T1: `djo.test.testcases` HTTP client removal

Django's `TestCase` deeply integrates the HTTP test client. The safest approach:

1. Remove `client.py`, `selenium.py`, `html.py` from `djo/test/`.
2. In `testcases.py`, **comment out or remove** methods/attributes that reference `Client`:  
   - `self.client`, `self.async_client`
   - `self.client_class`, `self.async_client_class`
   - `_pre_setup` client initialization lines
   - `assertRedirects`, `assertContains`, `assertNotContains`, `assertFormError`, `assertTemplateUsed`, `assertTemplateNotUsed`, `assertInHTML`
3. Keep `assertQuerySetEqual`, `assertNumQueries`, `assertQuerySetEqual`.
4. Keep the DB transaction management logic intact.

### T2: `djo.contrib.contenttypes` cross-deps

`contenttypes` references `djo.contrib.admin` via its `admin.py` (deleted in Phase 2). Also references `djo.forms` via `forms.py` (deleted). These files are already removed in Phase 2. Verify `contenttypes/apps.py` and `contenttypes/__init__.py` don't import them at module level.

### T3: `djo.contrib.postgres` cross-deps

Postgres contrib has `forms/` directory (deleted). Check that:
- `djo/contrib/postgres/__init__.py` doesn't import forms.
- `djo/contrib/postgres/fields/*.py` don't import forms at module level (they might import form fields for `Field.formfield()` method — this is a lazy import in Django, so it should fail only when called, not at import time). If `formfield()` methods import deleted modules, wrap in try/except or remove the method override — the base `Field.formfield()` is also likely removed since forms are gone.

**Recommendation:** In all retained model field classes that override `formfield()`, the method will naturally raise `ImportError` if someone calls it (since `djo.forms` doesn't exist). This is acceptable — `formfield()` is not an ORM operation, it's a forms integration point. Document this as a known non-functional method. No code change needed beyond deleting the forms package.

### T4: `djo/utils/log.py`

`setup()` calls `configure_logging` from `djo.utils.log`. This module may import `djo.http` for `UnreadablePostError`. Check and fix:

```bash
grep -n "from djo\.\(http\|views\|template\|forms\|urls\|middleware\)" djo/utils/log.py
```

If it imports web modules, either:
- Stub the import with a try/except in `djo/utils/log.py`, or
- Move the fix to `djo/_ext/log_patch.py` and monkey-patch.

### T5: `djo/core/management/sql.py`

This module provides SQL output functionality used by `sqlmigrate`, `sqlflush`, etc. Verify it doesn't import web modules.

### T6: `djo/core/serializers/` cross-deps

Serializers may import `djo.http` for streaming response support. The core serialization (to-string, to-file) shouldn't need HTTP. If `djo/core/serializers/base.py` has HTTP imports, they're likely for `StreamingHttpResponse` support in `dumpdata` — which we don't need. Remove those code paths.

### T7: Database backend `__init__.py` files

Each backend's `__init__.py` (e.g., `djo/db/backends/sqlite3/__init__.py`) may import from `djo.utils` modules. Verify these are all retained utils.

### T8: Migration autodetector

The migration autodetector (`djo/db/migrations/autodetector.py`) should be self-contained within `djo.db`. Verify no web imports.

### T9: GIS backend

GeoDjango's DB backends (`djo/contrib/gis/db/`) extend the base backends. After removing GIS web features (admin, views, etc.), verify the GIS DB layer still imports cleanly:

```bash
python -c "from djo.contrib.gis.db.backends.postgis.base import DatabaseWrapper; print('OK')"
```

### T10: Signals wiring in `djo/db/__init__.py`

`djo/db/__init__.py` connects `reset_queries` and `close_old_connections` to `request_started` and `request_finished` signals. These signals still exist (in `djo/core/signals.py`). The connections just won't fire in a non-web context unless the user explicitly sends the signals. This is fine — keep as-is.

---

## Appendix: Complete File Operations Reference

### Files/directories to DELETE (complete list)

```
# Top-level packages
djo/forms/
djo/http/
djo/middleware/
djo/template/
djo/templatetags/
djo/urls/
djo/views/
djo/shortcuts.py

# Core sub-packages
djo/core/cache/
djo/core/handlers/
djo/core/mail/
djo/core/servers/
djo/core/asgi.py
djo/core/wsgi.py
djo/core/paginator.py
djo/core/management/templates.py

# Management commands
djo/core/management/commands/check.py
djo/core/management/commands/compilemessages.py
djo/core/management/commands/createcachetable.py
djo/core/management/commands/makemessages.py
djo/core/management/commands/runserver.py
djo/core/management/commands/sendtestemail.py
djo/core/management/commands/shell.py
djo/core/management/commands/startapp.py
djo/core/management/commands/startproject.py
djo/core/management/commands/test.py
djo/core/management/commands/testserver.py

# System checks
djo/core/checks/async_checks.py
djo/core/checks/caches.py
djo/core/checks/security/
djo/core/checks/templates.py
djo/core/checks/translation.py
djo/core/checks/urls.py
djo/core/checks/compatibility/  (if no ORM-relevant content)

# Contrib
djo/contrib/admin/
djo/contrib/admindocs/
djo/contrib/auth/
djo/contrib/flatpages/
djo/contrib/humanize/
djo/contrib/messages/
djo/contrib/redirects/
djo/contrib/sessions/
djo/contrib/sitemaps/
djo/contrib/sites/
djo/contrib/staticfiles/
djo/contrib/syndication/

# Contrib partial
djo/contrib/contenttypes/admin.py
djo/contrib/contenttypes/views.py
djo/contrib/contenttypes/forms.py
djo/contrib/postgres/forms/
djo/contrib/postgres/templates/
djo/contrib/postgres/jinja2/
djo/contrib/gis/admin/
djo/contrib/gis/feeds.py
djo/contrib/gis/forms/
djo/contrib/gis/sitemaps/
djo/contrib/gis/shortcuts.py
djo/contrib/gis/static/
djo/contrib/gis/templates/
djo/contrib/gis/views.py

# Conf
djo/conf/app_template/
djo/conf/project_template/
djo/conf/urls/

# Utils (confirmed web-only)
djo/utils/autoreload.py
djo/utils/cache.py
djo/utils/feedgenerator.py
djo/utils/lorem_ipsum.py
djo/utils/archive.py

# Test infrastructure
djo/test/client.py
djo/test/selenium.py
djo/test/html.py

# Test directories (73+ directories — see Phase 5 for complete list)
tests/absolute_url_overrides/
tests/admin_*/
tests/asgi/
tests/auth_tests/
tests/builtin_server/
tests/cache/
... (full list in Phase 5.2.1)
```

### Files to MODIFY (complete list)

```
# Namespace rename (mechanical, all .py files)
djo/**/*.py          — django→djo
tests/**/*.py        — django→djo

# Structural modifications
djo/__init__.py              — simplify setup()
djo/core/checks/__init__.py  — remove imports of deleted check modules
djo/test/__init__.py          — remove imports of client, selenium, html
djo/test/testcases.py         — remove HTTP client integration
pyproject.toml                — full rewrite for djo packaging

# Test settings
tests/test_sqlite.py          — update INSTALLED_APPS, imports
tests/runtests.py             — update imports, settings reference
```

### Files to CREATE

```
djo/_ext/__init__.py           — fork extension package
scripts/rename_namespace.sh    — reproducible rename script
SPEC.md                        — this specification
IMPLEMENTATION_PLAN.md         — this plan
```
