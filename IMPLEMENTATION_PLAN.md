# djorm — Implementation Plan

> **Historical extraction record:** This plan documents how the initial fork
> was created. [`MAINTENANCE.md`](MAINTENANCE.md) and
> `scripts/apply_django_lts.py` are authoritative for current updates,
> packaging, versioning, and releases.

**Upstream base:** Django 5.2 LTS (latest tag from `stable/5.2.x`)
**Goal:** Transform Django into `djorm`, a standalone ORM + migrations + DB backends library.

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

# 2. Create the djorm working branch from the tag
git checkout -b djorm/main "$LATEST_TAG"

# 3. Verify baseline: run a minimal ORM test to confirm upstream works
cd tests/
python runtests.py --settings=test_sqlite basic --verbosity=0
# Expected: all tests pass
cd ..
```

### 0.3 Branch structure

```
djorm/main              ← primary development branch (based on latest 5.2.x tag)
upstream/stable/5.2.x ← read-only tracking of Django upstream
```

### 0.4 Done check

- [x] `djorm/main` branch exists, based on latest `v5.2.*` tag.
- [x] `python tests/runtests.py --settings=test_sqlite basic` passes.
- [x] `.git/config` has the upstream remote configured.

### 0.5 Commit

No commit yet — this is just setup.

---

## Phase 1: Namespace Rename (`django` → `djorm`)

### 1.1 Objective

Mechanically rename the top-level Python package from `django` to `djorm` and update all internal references. This is the largest single change and must be fully mechanical/reproducible.

### 1.2 Strategy

Use a scripted approach so the rename can be re-applied after any upstream rebase:

1. Rename the `django/` directory to `djorm/`.
2. Find-and-replace all Python source references.
3. Update configuration files.
4. Verify tests still pass under the new namespace.

### 1.3 Operations

#### 1.3.1 Directory rename

```bash
git mv django djorm
```

#### 1.3.2 Source code replacements

> **Note:** The sed commands below are a **reference fallback**. The preferred approach is an import-path-aware Python rewriter — see §1.7 and SPEC.md §9.6. If the sed fallback is used, the mandatory post-step is the verification grep in §1.3.4.

The replacements must be applied in a specific order to avoid partial matches:

```bash
# Create the rename script: scripts/rename_namespace.py
# This script is idempotent and can be re-run after a rebase.

# Order matters: longer strings first to avoid partial replacement issues.

# 1. Python imports & string references in .py files
find djorm tests -name '*.py' -type f -exec sed -i '' \
  -e 's/django\.contrib/djorm.contrib/g' \
  -e 's/django\.core/djorm.core/g' \
  -e 's/django\.db/djorm.db/g' \
  -e 's/django\.apps/djorm.apps/g' \
  -e 's/django\.conf/djorm.conf/g' \
  -e 's/django\.dispatch/djorm.dispatch/g' \
  -e 's/django\.forms/djorm.forms/g' \
  -e 's/django\.http/djorm.http/g' \
  -e 's/django\.middleware/djorm.middleware/g' \
  -e 's/django\.shortcuts/djorm.shortcuts/g' \
  -e 's/django\.template/djorm.template/g' \
  -e 's/django\.templatetags/djorm.templatetags/g' \
  -e 's/django\.test/djorm.test/g' \
  -e 's/django\.urls/djorm.urls/g' \
  -e 's/django\.utils/djorm.utils/g' \
  -e 's/django\.views/djorm.views/g' \
  {} +

# 2. Bare "django" references that are the package name itself
#    (more targeted to avoid false positives in comments/docs)
find djorm tests -name '*.py' -type f -exec sed -i '' \
  -e 's/^import django$/import djorm/g' \
  -e 's/^import django\b/import djorm/g' \
  -e 's/from django import/from djorm import/g' \
  -e "s/'django'/'djorm'/g" \
  -e 's/"django"/"djorm"/g' \
  {} +

# 3. DJANGO_SETTINGS_MODULE is KEPT UNCHANGED (not renamed)
#    The env var is not a Python import path; renaming it breaks operational parity.
#    Do NOT apply any sed rule for DJANGO_SETTINGS_MODULE.

# 4. django-admin → djorm (CLI entry point references)
find djorm tests -name '*.py' -type f -exec sed -i '' \
  -e 's/django-admin/djorm/g' \
  {} +

# 5. Update __main__.py
# djorm/__main__.py should import from djorm

# 6. Configuration files
sed -i '' \
  -e 's/known_first_party = "django"/known_first_party = "djorm"/g' \
  -e 's/include = \["django\*"\]/include = ["djorm*"]/g' \
  -e 's/version = {attr = "django\.__version__"}/version = {attr = "djorm.__version__"}/g' \
  -e 's/django\.core\.management:execute_from_command_line/djorm.core.management:execute_from_command_line/g' \
  pyproject.toml

# 7. Test settings files
find tests -name 'test_*.py' -maxdepth 1 -exec sed -i '' \
  -e 's/django\./djorm./g' \
  {} +

# 8. runtests.py
sed -i '' \
  -e 's/django\./djorm./g' \
  -e 's/import django/import djorm/g' \
  -e 's/from django/from djorm/g' \
  tests/runtests.py
```

#### 1.3.3 Handle tricky patterns

Some patterns need special attention:

```bash
# a. String references in migrations (engine paths)
#    e.g., "django.db.backends.sqlite3" in test fixtures
find tests -name '*.py' -exec grep -l 'django\.db\.backends' {} + | \
  xargs sed -i '' 's/django\.db\.backends/djorm.db.backends/g'

# b. AppConfig references in test apps
#    e.g., default_app_config = 'tests.myapp.apps.MyAppConfig'
#    These usually don't contain "django" so no change needed.

# c. Model Meta.app_label values — these don't use "django" prefix typically.

# d. The django.VERSION references
find djorm -name '*.py' -exec sed -i '' \
  -e 's/django\.VERSION/djorm.VERSION/g' \
  {} +

# e. contrib.contenttypes has hardcoded "django.contrib.contenttypes" in migrations
find djorm/contrib -name '*.py' -exec sed -i '' \
  -e 's/django\.contrib/djorm.contrib/g' \
  {} +
```

#### 1.3.4 Verify no remaining "django" Python references

```bash
# Check for any remaining django references in Python files (excluding comments/docs)
grep -rn "from django\." djorm/ --include='*.py' | head -20
grep -rn "import django" djorm/ --include='*.py' | head -20
grep -rn "'django\." djorm/ --include='*.py' | head -20
# These should all return empty.

# Allow "django" in:
# - Comments mentioning Django (documentation)
# - License text
# - DJANGO_VERSION_PICKLE_KEY (keep for pickle compat - this is a serialization format constant)
```

### 1.4 Special consideration: DJANGO_VERSION_PICKLE_KEY

In `djorm/db/utils.py` there is a constant `DJANGO_VERSION_PICKLE_KEY`. This is used for pickle serialization compatibility. **Keep the value as `"django-version"` but rename the Python constant** to `DJANGO_VERSION_PICKLE_KEY` (unchanged name). The string value `"django-version"` is a serialization format constant, not a namespace reference. Do not change it.

### 1.5 Special consideration: `djorm.setup()`

`djorm.setup()` is kept **semantically identical** to `django.setup()` — namespace-only rename, no logic changes. The URL-prefix code path, logging configuration, and app-registry population all remain as upstream wrote them. If the URL-prefix code path fails at runtime (because `djorm.urls` was deleted), guard it with a `try/except` in `djorm/_ext/` rather than modifying `setup()` directly. See SPEC.md §10.8 for the full rationale.

**Do not** simplify, trim, or change the default value of `set_prefix`. Keeping the signature and body identical to upstream means any user code that calls `djorm.setup(set_prefix=True)` behaves the same way, and future upstream rebases have zero conflicts in this function.

### 1.6 Special consideration: `DJANGO_SETTINGS_MODULE`

`DJANGO_SETTINGS_MODULE` is **kept unchanged** — it is an environment variable, not a Python import path, so the namespace rename does not apply. The settings machinery in `djorm/conf/__init__.py` continues to read `DJANGO_SETTINGS_MODULE`. Do not add any `DJORM_SETTINGS_MODULE` alias. See SPEC.md §8.4.

### 1.7 Rename tooling recommendation

The sed commands in §1.3.2 are an **emergency-only fallback**. The **only supported rename method** is an import-path-aware Python rewriter (`libcst` or `rope`) implemented as `scripts/rename_namespace.py`. That script rewrites imports, dotted-name string literals matching known module paths, and targeted `pyproject.toml` fields — nothing else. See SPEC.md §9.6 for the full specification.

If the sed fallback is ever used, the mandatory post-step is the verification grep in §1.3.4. Every remaining `django` occurrence in `.py` files must be manually reviewed, and the sed usage must be treated as a one-time escape, not a recurring workflow.

### 1.8 Expected failures at this stage

1. **Import errors for deleted-but-still-referenced modules**: After rename but before pruning, everything still exists so there should be no import errors. But tests for web features will have namespace-updated imports. These tests will be deleted in Phase 2.

2. **`DJANGO_VERSION_PICKLE_KEY` value change**: If the sed script changed the string value, fix it back. The sed rules above should not affect it since the value `"django-version"` uses hyphen not dot, but verify.

3. **Locale file paths**: `djorm/conf/locale/` and `djorm/contrib/*/locale/` contain `.po` files with `django` references. These are translation files. Leave them as-is (they're data files, not code).

4. **Test data/fixtures**: Some test fixture files (JSON, XML) may contain `django.contrib.contenttypes` references. These need updating.

5. **`DJANGO_SETTINGS_MODULE`**: Verify the sed script did NOT rename this env var. It must remain `DJANGO_SETTINGS_MODULE`.

### 1.9 Verification

```bash
# Quick syntax check
python -c "import djorm; print(djorm.__version__)"

# Run baseline test
cd tests/
python runtests.py --settings=test_sqlite basic -v0
cd ..
```

### 1.10 Commit

```
[namespace] Rename django → djorm in all source files

Mechanical find-and-replace of the Python package namespace from
'django' to 'djorm'. Applied via scripts/rename_namespace.py for
reproducibility during upstream rebases.

- Renamed django/ directory to djorm/
- Updated all Python imports
- DJANGO_SETTINGS_MODULE kept unchanged (operational parity)
- Updated pyproject.toml, test configs
- Preserved DJANGO_VERSION_PICKLE_KEY string value for pickle compat
- setup() left semantically identical to upstream
```

---

## Phase 2: Remove Web Framework Subsystems

### 2.1 Objective

Delete all packages and modules that are part of the web framework, not the ORM/DB stack.

### 2.2 Operations

#### 2.2.1 Top-level package deletions

```bash
rm -rf djorm/forms/
rm -rf djorm/http/
rm -rf djorm/middleware/
rm -rf djorm/template/
rm -rf djorm/templatetags/
rm -rf djorm/urls/
rm -rf djorm/views/
rm -f  djorm/shortcuts.py
```

#### 2.2.2 Core subpackage deletions

```bash
rm -rf djorm/core/cache/
rm -rf djorm/core/handlers/
rm -rf djorm/core/mail/
rm -rf djorm/core/servers/
rm -f  djorm/core/asgi.py
rm -f  djorm/core/wsgi.py
rm -f  djorm/core/paginator.py
```

#### 2.2.3 Contrib deletions

```bash
rm -rf djorm/contrib/admin/
rm -rf djorm/contrib/admindocs/
rm -rf djorm/contrib/auth/
rm -rf djorm/contrib/flatpages/
rm -rf djorm/contrib/humanize/
rm -rf djorm/contrib/messages/
rm -rf djorm/contrib/redirects/
rm -rf djorm/contrib/sessions/
rm -rf djorm/contrib/sitemaps/
rm -rf djorm/contrib/sites/
rm -rf djorm/contrib/staticfiles/
rm -rf djorm/contrib/syndication/
```

#### 2.2.4 Contrib partial cleanups

```bash
# contenttypes: remove web-facing parts
rm -f djorm/contrib/contenttypes/admin.py
rm -f djorm/contrib/contenttypes/views.py
rm -f djorm/contrib/contenttypes/forms.py

# postgres: remove web-facing parts
rm -rf djorm/contrib/postgres/forms/
rm -rf djorm/contrib/postgres/templates/
rm -rf djorm/contrib/postgres/jinja2/

# gis: DEFERRED to later milestone (see SPEC.md §10.7)
# Delete the entire contrib/gis/ for now. It will be re-added when
# the GIS milestone is implemented.
rm -rf djorm/contrib/gis/
```

#### 2.2.5 Conf cleanups

```bash
rm -rf djorm/conf/app_template/
rm -rf djorm/conf/project_template/
rm -rf djorm/conf/urls/
```

#### 2.2.6 Utils cleanups

Remove utils modules that are web-only AND confirmed not imported by any retained code:

```bash
# Definitely safe to remove
rm -f djorm/utils/autoreload.py
rm -f djorm/utils/cache.py
rm -f djorm/utils/feedgenerator.py
rm -f djorm/utils/lorem_ipsum.py
rm -f djorm/utils/archive.py
```

For these, verify with import tracing first:

```bash
# Check if anything retained imports these
grep -rn "from djorm.utils.http import\|from djorm.utils import http\|djorm\.utils\.http" djorm/ --include='*.py' | grep -v '\.pyc'
grep -rn "from djorm.utils.safestring import\|djorm\.utils\.safestring" djorm/ --include='*.py' | grep -v '\.pyc'
grep -rn "from djorm.utils.html import\|djorm\.utils\.html" djorm/ --include='*.py' | grep -v '\.pyc'
grep -rn "from djorm.utils.xmlutils import\|djorm\.utils\.xmlutils" djorm/ --include='*.py' | grep -v '\.pyc'
```

Based on expected results:
- `djorm/utils/html.py` — likely imported by validators → **keep**
- `djorm/utils/safestring.py` — likely imported by some model internals → **keep if referenced, else remove**
- `djorm/utils/http.py` — likely only imported by web modules → **remove if confirmed**
- `djorm/utils/xmlutils.py` — imported by XML serializer → **keep**

#### 2.2.7 Test infrastructure cleanup

```bash
# Remove web-related parts from djorm/test/
rm -f djorm/test/client.py
rm -f djorm/test/selenium.py
rm -f djorm/test/html.py
```

Update `djorm/test/__init__.py` to remove imports of deleted modules (TestClient, etc.).

### 2.3 Fix broken imports in retained modules

After deletion, some retained modules may import deleted modules. Find and fix:

```bash
# Find all import errors in retained code
python -c "
import sys
sys.path.insert(0, '.')
import djorm
" 2>&1 | head -50
```

Common fixes needed:

1. **`djorm/core/signals.py`** — Keep all four signal definitions (`request_started`, `request_finished`, `got_request_exception`, `setting_changed`). If the module imports anything from deleted subsystems, remove those imports but keep the `Signal()` instances. See SPEC.md §4.5 for the full signals policy.

2. **`djorm/contrib/contenttypes/admin.py`** — already deleted above.

3. **`djorm/contrib/postgres/__init__.py`** — may reference forms. Update to remove those references.

4. **`djorm/contrib/gis/`** — deleted entirely in §2.2.4 (deferred to GIS milestone). No fixup needed.

5. **`djorm/test/testcases.py`** — imports `Client` from `djorm.test.client`. Either stub the client or remove the `Client` integration from `TestCase`. The DB test infrastructure (`TransactionTestCase`, `TestCase`) should still work for direct ORM testing — they primarily manage DB transactions and fixtures. Remove/stub the HTTP client integration:
   - Remove `self.client` from `SimpleTestCase.__init__`
   - Remove `self.async_client` 
   - Remove `_pre_setup` client initialization
   - Remove `modify_settings`, `override_settings` if they import from web modules (unlikely — they're in `djorm.test.utils` and work with settings only)

6. **`djorm/test/utils.py`** — may import from `djorm.urls` or `djorm.template`. Stub out or remove the URL/template-related test utilities. Keep `override_settings`, `modify_settings`, `isolate_apps`.

7. **`djorm/core/management/base.py`** — the base command class. Should be self-contained. May reference `django.core.checks` — that's fine, we keep checks.

8. **`djorm/core/management/commands/runserver.py`** — already in the delete list (Phase 3).

9. **`djorm/core/validators.py`** — may import from `djorm.utils.html` or `djorm.utils.ipv6`. Both are kept.

10. **`djorm/db/models/fields/files.py`** — imports from `djorm.core.files`. Kept.

### 2.4 Expected failures

- `ImportError` for any retained module that references a deleted one. Address each systematically.
- Key approach: use `python -c "import djorm; djorm.setup()"` with a minimal settings configuration as the smoke test. Iterate until it works.

### 2.5 Verification

```bash
# Smoke test: can we import and setup djorm?
python -c "
import djorm
from djorm.conf import settings
settings.configure(
    DATABASES={'default': {'ENGINE': 'djorm.db.backends.sqlite3', 'NAME': ':memory:'}},
    DEFAULT_AUTO_FIELD='djorm.db.models.BigAutoField',
    INSTALLED_APPS=[],
)
djorm.setup()
from djorm.db import connection
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
contrib/contenttypes (ORM parts), contrib/postgres (ORM parts).
```

---

## Phase 3: Management Command Pruning

### 3.1 Objective

Remove management commands not related to DB/migrations. Keep only the commands listed in SPEC.md §5.1.

### 3.2 Operations

```bash
# Delete non-DB commands
rm -f djorm/core/management/commands/check.py
rm -f djorm/core/management/commands/compilemessages.py
rm -f djorm/core/management/commands/createcachetable.py
rm -f djorm/core/management/commands/makemessages.py
rm -f djorm/core/management/commands/runserver.py
rm -f djorm/core/management/commands/sendtestemail.py
rm -f djorm/core/management/commands/shell.py
rm -f djorm/core/management/commands/startapp.py
rm -f djorm/core/management/commands/startproject.py
rm -f djorm/core/management/commands/test.py
rm -f djorm/core/management/commands/testserver.py
```

#### 3.2.1 Check management/templates.py

`djorm/core/management/templates.py` is used by `startapp` and `startproject`. Since both commands are deleted, this file can be removed too:

```bash
rm -f djorm/core/management/templates.py
```

### 3.3 Verify remaining commands

```bash
ls djorm/core/management/commands/
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

Check if `djorm/core/management/__init__.py` has any hardcoded command lists. Django auto-discovers commands from the `commands/` directory, so deletion should be sufficient.

```bash
grep -n "runserver\|startapp\|startproject\|shell\|test\b\|sendtestemail\|createcachetable\|compilemessages\|makemessages\|testserver" djorm/core/management/__init__.py
```

If any references exist, remove them.

### 3.5 Verification

```bash
# List available commands
python -c "
import djorm
from djorm.conf import settings
settings.configure(
    DATABASES={'default': {'ENGINE': 'djorm.db.backends.sqlite3', 'NAME': ':memory:'}},
    DEFAULT_AUTO_FIELD='djorm.db.models.BigAutoField',
    INSTALLED_APPS=[],
)
djorm.setup()
from djorm.core.management import get_commands
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
rm -f djorm/core/checks/async_checks.py
rm -f djorm/core/checks/caches.py
rm -f djorm/core/checks/templates.py
rm -f djorm/core/checks/translation.py
rm -f djorm/core/checks/urls.py
rm -f djorm/core/checks/messages.py   # Keep this! This is CheckMessage, not the messages framework.
rm -rf djorm/core/checks/security/
```

**WAIT** — `djorm/core/checks/messages.py` contains `CheckMessage`, `Error`, `Warning`, etc. — the actual check message classes. **Do NOT delete it.** The `messages.py` here is NOT the messages framework. Keep it.

Corrected deletions:

```bash
rm -f djorm/core/checks/async_checks.py
rm -f djorm/core/checks/caches.py
rm -f djorm/core/checks/templates.py
rm -f djorm/core/checks/translation.py
rm -f djorm/core/checks/urls.py
rm -rf djorm/core/checks/security/
rm -rf djorm/core/checks/compatibility/   # Remove only if no ORM-relevant compat checks
```

Check `compatibility/django_4_0.py` first:

```bash
cat djorm/core/checks/compatibility/django_4_0.py
```

If it only checks `HttpResponse` csrf cookie settings or similar web features, delete the whole directory. If it has ORM-relevant checks, keep it.

#### 4.2.2 Update djorm/core/checks/__init__.py

Remove the import lines for deleted check modules:

**Before:**
```python
import djorm.core.checks.async_checks
import djorm.core.checks.caches
import djorm.core.checks.commands
import djorm.core.checks.compatibility.django_4_0
import djorm.core.checks.database
import djorm.core.checks.files
import djorm.core.checks.model_checks
import djorm.core.checks.security.base
import djorm.core.checks.security.csrf
import djorm.core.checks.security.sessions
import djorm.core.checks.templates
import djorm.core.checks.translation
import djorm.core.checks.urls
```

**After:**
```python
import djorm.core.checks.commands
import djorm.core.checks.database
import djorm.core.checks.model_checks
```

Optionally keep `djorm.core.checks.files` if `FileField` checks are registered there:

```bash
cat djorm/core/checks/files.py
```

If it only checks `FILE_UPLOAD_HANDLERS` or similar web settings, delete it. If it validates `MEDIA_ROOT` or similar settings that `FileField` depends on, keep it.

### 4.3 Verification

```bash
python -c "
import djorm
from djorm.conf import settings
settings.configure(
    DATABASES={'default': {'ENGINE': 'djorm.db.backends.sqlite3', 'NAME': ':memory:'}},
    DEFAULT_AUTO_FIELD='djorm.db.models.BigAutoField',
    INSTALLED_APPS=[],
)
djorm.setup()
from djorm.core.checks import run_checks, Tags
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

# GIS tests (deferred to GIS milestone — see SPEC.md §10.7)
rm -rf gis_tests/

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
    'djorm.contrib.contenttypes',
    # Remove: djorm.contrib.auth, djorm.contrib.admin, etc.
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

Some test modules import `djorm.test.client.Client` or `djorm.http.HttpRequest` in setUp methods. Fix by:
- If only a few tests in a kept module import web stuff → remove those specific tests.
- If the entire module depends on web imports → remove the test module.

#### 5.3.2 Missing INSTALLED_APPS dependencies

Some ORM tests may expect `djorm.contrib.auth` to be in INSTALLED_APPS (e.g., tests using `User` model). Fix by:
- If the test only uses `User` as a convenient model → create a simple test model instead or skip the test.
- If it deeply depends on auth → remove the test.

#### 5.3.3 Test runner infrastructure

`djorm/test/testcases.py` will have been partially stripped. Ensure `TransactionTestCase` and `TestCase` still work for DB testing:

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

Many ORM tests use `GenericForeignKey` which requires `djorm.contrib.contenttypes` in `INSTALLED_APPS`. Ensure it's included in test settings.

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
- Fix djorm.test.testcases to work without HTTP client
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
name = "dj-orm"
dynamic = ["version"]
requires-python = ">= 3.10"  # derived from upstream Django 5.2's pyproject.toml
dependencies = [
    "asgiref>=3.8.1",    # from upstream; required for async ORM API
    "sqlparse>=0.3.1",   # from upstream
    "tzdata; sys_platform == 'win32'",  # from upstream
]
# All version bounds above are copied from upstream Django 5.2.
# On rebase, re-derive them from the new upstream tag's pyproject.toml.
authors = [
  {name = "djorm contributors"},
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
djorm = "djorm.core.management:execute_from_command_line"

[project.urls]
Source = "https://github.com/<org>/dj-orm"
Tracker = "https://github.com/<org>/dj-orm/issues"

[tool.isort]
profile = "black"
default_section = "THIRDPARTY"
known_first_party = "djorm"

[tool.setuptools.dynamic]
version = {attr = "djorm.__version__"}

[tool.setuptools.packages.find]
include = ["djorm*"]
```

#### 6.2.2 Update djorm/__init__.py version

Keep the upstream version tuple. Optionally add a `DJORM_FORK_VERSION`:

```python
from djorm.utils.version import get_version

VERSION = (5, 2, 12, "alpha", 0)  # matches upstream tag
__version__ = get_version(VERSION)
```

#### 6.2.3 Create/update README.rst

Update to describe djorm, not Django. Brief, pointing to SPEC.md for details.

#### 6.2.4 Update djorm/__main__.py

Ensure it works:

```python
"""
Invokes djorm when the djorm module is run as a script.

Example: python -m djorm migrate
"""
from djorm.core import management

if __name__ == "__main__":
    management.execute_from_command_line()
```

#### 6.2.5 CLI entry point verification

```bash
# Build and install in development mode
pip install -e .

# Test CLI
djorm --help
djorm migrate --help
djorm showmigrations --help
```

#### 6.2.6 Build distribution

```bash
python -m build
ls dist/
# Expected: djorm-5.2.X.tar.gz, djorm-5.2.X-py3-none-any.whl

# Verify wheel contents
python -m zipfile -l dist/djorm-5.2.X-py3-none-any.whl | head -20
# Should list djorm/ package files, NOT django/
```

### 6.3 Verification

```bash
# Install from wheel in a fresh venv
python -m venv /tmp/djorm-test
source /tmp/djorm-test/bin/activate
pip install dist/djorm-*.whl

# Smoke test
python -c "
import djorm
from djorm.conf import settings
settings.configure(
    DATABASES={'default': {'ENGINE': 'djorm.db.backends.sqlite3', 'NAME': ':memory:'}},
    DEFAULT_AUTO_FIELD='djorm.db.models.BigAutoField',
    INSTALLED_APPS=[],
)
djorm.setup()
print('djorm version:', djorm.__version__)
print('OK')
"

# CLI test
djorm diffsettings 2>&1 | head -5

deactivate
rm -rf /tmp/djorm-test
```

### 6.4 Commits

```
[packaging] Update pyproject.toml for djorm distribution

- Package name: djorm
- Console script: djorm
- Updated classifiers and metadata
- Updated dependencies (removed web-specific extras)
```

```
[packaging] Update README and __main__ for djorm
```

---

## Phase 7: Fork Glue & _ext Package

### 7.1 Objective

Create the `djorm/_ext/` package for any fork-specific patches that can't be expressed as mechanical deletions or renames.

### 7.2 Operations

```bash
mkdir -p djorm/_ext/
```

#### 7.2.1 djorm/_ext/__init__.py

```python
"""
djorm._ext — Fork-specific extensions and patches.

This package contains all logic that is specific to the djorm fork
and does not exist in upstream Django. Keeping fork-specific code
isolated here makes upstream rebasing easier and makes it clear
which code is original vs. modified.
"""
```

#### 7.2.2 Expected contents

At minimum:

- `djorm/_ext/__init__.py` — docstring only.
- `djorm/_ext/setup_helpers.py` — if `setup()` needs fork-specific runtime guards (e.g., try/except around URL-prefix code that references deleted modules). See §1.5.

Most likely `_ext/` will remain nearly empty in the initial release. It's a convention for future changes.

### 7.3 Commit

```
[ext] Add djorm/_ext/ fork-specific extension package
```

---

## Phase 8: Upstream application workflow

### 8.1 Current workflow

Run `scripts/apply_django_lts.py` from a clean LTS source branch. The tool
fetches an exact reviewed Django LTS tag, creates an isolated candidate
worktree, performs the namespace conversion, applies the reviewed fork tree
delta with a three-way merge, and runs the package gate. It stops for
file-by-file review of semantic conflicts.

The full command, resume procedure, version mapping, and publication gate are
maintained in [`MAINTENANCE.md`](MAINTENANCE.md). This replaces the original
manual rebase and cherry-pick procedure.

---

## Phase Summary & Checklist

| Phase | Description | Key Done Check |
|---|---|---|
| 0 | Repo setup | `basic` tests pass on upstream tag |
| 1 | Namespace rename | `python -c "import djorm; print(djorm.__version__)"` works |
| 2 | Remove web subsystems | `djorm.setup()` works with sqlite config, no ImportErrors |
| 3 | Command pruning | `get_commands()` returns only DB commands |
| 4 | Checks trimming | `run_checks(tags=[Tags.models, Tags.database])` works |
| 5 | Test pruning | All retained tests pass with `runtests.py --settings=test_sqlite` |
| 6 | Packaging | `pip install -e .` works, `djorm migrate --help` works |
| 7 | Fork glue | `djorm/_ext/` exists |
| 8 | Upstream workflow | `scripts/rename_namespace.py` runs successfully |

---

## Tricky Areas & Recommendations

### T1: `djorm.test.testcases` HTTP client removal

Django's `TestCase` deeply integrates the HTTP test client. The safest approach:

1. Remove `client.py`, `selenium.py`, `html.py` from `djorm/test/`.
2. In `testcases.py`, **comment out or remove** methods/attributes that reference `Client`:  
   - `self.client`, `self.async_client`
   - `self.client_class`, `self.async_client_class`
   - `_pre_setup` client initialization lines
   - `assertRedirects`, `assertContains`, `assertNotContains`, `assertFormError`, `assertTemplateUsed`, `assertTemplateNotUsed`, `assertInHTML`
3. Keep `assertQuerySetEqual`, `assertNumQueries`, `assertQuerySetEqual`.
4. Keep the DB transaction management logic intact.

### T2: `djorm.contrib.contenttypes` cross-deps

`contenttypes` references `djorm.contrib.admin` via its `admin.py` (deleted in Phase 2). Also references `djorm.forms` via `forms.py` (deleted). These files are already removed in Phase 2. Verify `contenttypes/apps.py` and `contenttypes/__init__.py` don't import them at module level.

### T3: `djorm.contrib.postgres` cross-deps

Postgres contrib has `forms/` directory (deleted). Check that:
- `djorm/contrib/postgres/__init__.py` doesn't import forms.
- `djorm/contrib/postgres/fields/*.py` don't import forms at module level (they might import form fields for `Field.formfield()` method — this is a lazy import in Django, so it should fail only when called, not at import time). If `formfield()` methods import deleted modules, wrap in try/except or remove the method override — the base `Field.formfield()` is also likely removed since forms are gone.

**Recommendation:** In all retained model field classes that override `formfield()`, the method will naturally raise `ImportError` if someone calls it (since `djorm.forms` doesn't exist). This is acceptable — `formfield()` is not an ORM operation, it's a forms integration point. Document this as a known non-functional method. No code change needed beyond deleting the forms package.

### T4: `djorm/utils/log.py`

`setup()` calls `configure_logging` from `djorm.utils.log`. This module may import `djorm.http` for `UnreadablePostError`. Check and fix:

```bash
grep -n "from djorm\.\(http\|views\|template\|forms\|urls\|middleware\)" djorm/utils/log.py
```

If it imports web modules, either:
- Stub the import with a try/except in `djorm/utils/log.py`, or
- Move the fix to `djorm/_ext/log_patch.py` and monkey-patch.

### T5: `djorm/core/management/sql.py`

This module provides SQL output functionality used by `sqlmigrate`, `sqlflush`, etc. Verify it doesn't import web modules.

### T6: `djorm/core/serializers/` cross-deps

Serializers may import `djorm.http` for streaming response support. The core serialization (to-string, to-file) shouldn't need HTTP. If `djorm/core/serializers/base.py` has HTTP imports, they're likely for `StreamingHttpResponse` support in `dumpdata` — which we don't need. Remove those code paths.

### T7: Database backend `__init__.py` files

Each backend's `__init__.py` (e.g., `djorm/db/backends/sqlite3/__init__.py`) may import from `djorm.utils` modules. Verify these are all retained utils.

### T8: Migration autodetector

The migration autodetector (`djorm/db/migrations/autodetector.py`) should be self-contained within `djorm.db`. Verify no web imports.

### T9: GIS backend (deferred)

GeoDjango is **deferred to a later milestone** (see SPEC.md §10.7). The entire `djorm/contrib/gis/` directory is deleted in Phase 2 and `gis_tests/` is deleted in Phase 5. When the GIS milestone lands, verify the GIS DB layer imports cleanly:

```bash
python -c "from djorm.contrib.gis.db.backends.postgis.base import DatabaseWrapper; print('OK')"
```

### T10: Signals wiring in `djorm/db/__init__.py`

`djorm/db/__init__.py` connects `reset_queries` and `close_old_connections` to `request_started` and `request_finished` signals. These are ORM-serving hookups (query-log reset, stale-connection cleanup). **Keep them as-is.** In a non-web context the signals simply never fire unless the user sends them explicitly, which is harmless.

**General signals policy (see SPEC.md §4.5):** All signal *definitions* in `djorm.db.models.signals` (`pre_save`, `post_save`, `pre_delete`, `post_delete`, `m2m_changed`, `pre_init`, `post_init`, `class_prepared`, `pre_migrate`, `post_migrate`) and `djorm.core.signals` (`request_started`, `request_finished`, `got_request_exception`, `setting_changed`) are fully retained. Only strip `.connect()` calls whose handler lives in a deleted subsystem — never remove a signal definition itself.

---

## Appendix: Complete File Operations Reference

### Files/directories to DELETE (complete list)

```
# Top-level packages
djorm/forms/
djorm/http/
djorm/middleware/
djorm/template/
djorm/templatetags/
djorm/urls/
djorm/views/
djorm/shortcuts.py

# Core sub-packages
djorm/core/cache/
djorm/core/handlers/
djorm/core/mail/
djorm/core/servers/
djorm/core/asgi.py
djorm/core/wsgi.py
djorm/core/paginator.py
djorm/core/management/templates.py

# Management commands
djorm/core/management/commands/check.py
djorm/core/management/commands/compilemessages.py
djorm/core/management/commands/createcachetable.py
djorm/core/management/commands/makemessages.py
djorm/core/management/commands/runserver.py
djorm/core/management/commands/sendtestemail.py
djorm/core/management/commands/shell.py
djorm/core/management/commands/startapp.py
djorm/core/management/commands/startproject.py
djorm/core/management/commands/test.py
djorm/core/management/commands/testserver.py

# System checks
djorm/core/checks/async_checks.py
djorm/core/checks/caches.py
djorm/core/checks/security/
djorm/core/checks/templates.py
djorm/core/checks/translation.py
djorm/core/checks/urls.py
djorm/core/checks/compatibility/  (if no ORM-relevant content)

# Contrib
djorm/contrib/admin/
djorm/contrib/admindocs/
djorm/contrib/auth/
djorm/contrib/flatpages/
djorm/contrib/humanize/
djorm/contrib/messages/
djorm/contrib/redirects/
djorm/contrib/sessions/
djorm/contrib/sitemaps/
djorm/contrib/sites/
djorm/contrib/staticfiles/
djorm/contrib/syndication/

# Contrib partial
djorm/contrib/contenttypes/admin.py
djorm/contrib/contenttypes/views.py
djorm/contrib/contenttypes/forms.py
djorm/contrib/postgres/forms/
djorm/contrib/postgres/templates/
djorm/contrib/postgres/jinja2/
djorm/contrib/gis/                  # entire directory (deferred to GIS milestone)

# Conf
djorm/conf/app_template/
djorm/conf/project_template/
djorm/conf/urls/

# Utils (confirmed web-only)
djorm/utils/autoreload.py
djorm/utils/cache.py
djorm/utils/feedgenerator.py
djorm/utils/lorem_ipsum.py
djorm/utils/archive.py

# Test infrastructure
djorm/test/client.py
djorm/test/selenium.py
djorm/test/html.py

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
djorm/**/*.py          — django→djorm
tests/**/*.py        — django→djorm

# Structural modifications
djorm/__init__.py              — namespace rename only (setup() unchanged)
djorm/core/checks/__init__.py  — remove imports of deleted check modules
djorm/test/__init__.py          — remove imports of client, selenium, html
djorm/test/testcases.py         — remove HTTP client integration
pyproject.toml                — full rewrite for djorm packaging

# Test settings
tests/test_sqlite.py          — update INSTALLED_APPS, imports
tests/runtests.py             — update imports, settings reference
```

### Files to CREATE

```
djorm/_ext/__init__.py           — fork extension package
scripts/rename_namespace.py    — AST-aware reproducible rename script
SPEC.md                        — this specification
IMPLEMENTATION_PLAN.md         — this plan
```
