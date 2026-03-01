# djo — Django ORM as a Standalone Library

## Specification Document

**Base upstream:** Django 5.2 LTS (latest tag)
**Target PyPI package:** `djo`
**Import namespace:** `djo`

---

## 1. Purpose

`djo` extracts the Django ORM, migration framework, and database backend stack from Django 5.2 LTS into a standalone Python library. It is distributed as its own package under the `djo` namespace.

### What djo IS

- The full Django ORM (models, querysets, managers, fields, expressions, aggregations, window functions, raw SQL, etc.).
- The complete migration framework (auto-detection, migration files, squashing, optimisation).
- All Django 5.2 database backends: SQLite, PostgreSQL, MySQL, Oracle.
- The `contrib.postgres` extension fields/functions/indexes/lookups/constraints.
- The `contrib.contenttypes` framework (ContentType model, GenericForeignKey/GenericRelation).
- The `contrib.gis` (GeoDjango) database layer (fields, functions, lookups, backends).
- The app registry (`djo.apps`) and settings infrastructure (`djo.conf`).
- The signal dispatcher (`djo.dispatch`).
- The system check framework (trimmed to ORM/DB-relevant checks).
- The test infrastructure needed to run the kept tests (`djo.test`).
- DB-related management commands: `makemigrations`, `migrate`, `showmigrations`, `sqlmigrate`, `sqlflush`, `sqlsequencereset`, `squashmigrations`, `optimizemigration`, `inspectdb`, `dbshell`, `flush`, `loaddata`, `dumpdata`, `diffsettings`.
- A CLI entry point (`djo`) that dispatches to the management command framework.

### What djo is NOT

- A web framework. No HTTP layer, no views, no URL routing, no middleware, no templates, no forms, no sessions, no auth/permissions, no admin, no caching framework, no static files, no ASGI/WSGI support.
- A compatibility shim. There is **no** `django` namespace. All imports use `djo`.
- A new API surface. No `djo.configure()`, no `database_url` helper, no synthetic app concept. Users interact with the same Django API patterns they already know, under the `djo.*` namespace.

### Non-goals

- Providing any web-framework functionality.
- Creating backward-compatible `django.*` imports.
- Introducing new public APIs beyond what Django 5.2 already provides.
- Supporting Django contrib apps unrelated to the ORM (admin, auth, sessions, messages, flatpages, redirects, sitemaps, syndication, humanize, staticfiles).

---

## 2. Public API Parity Statement

Every public API that exists in the retained modules is preserved with identical semantics. The **only** change is the top-level namespace prefix:

| Django 5.2 | djo |
|---|---|
| `from django.db import models` | `from djo.db import models` |
| `from django.conf import settings` | `from djo.conf import settings` |
| `from django.db import connection` | `from djo.db import connection` |
| `from django.apps import AppConfig` | `from djo.apps import AppConfig` |
| `from django.core.management import call_command` | `from djo.core.management import call_command` |
| `from django.contrib.postgres.fields import ArrayField` | `from djo.contrib.postgres.fields import ArrayField` |
| `from django.contrib.contenttypes.fields import GenericForeignKey` | `from djo.contrib.contenttypes.fields import GenericForeignKey` |

Settings keys are **unchanged**: `DATABASES`, `INSTALLED_APPS`, `DEFAULT_AUTO_FIELD`, `DATABASE_ROUTERS`, etc. String references in settings that formerly used `django.*` paths (e.g., backend engine strings like `"django.db.backends.sqlite3"`) become `"djo.db.backends.sqlite3"`.

---

## 3. Supported Usage Patterns

### 3.1 Minimal standalone ORM setup

```python
import djo
from djo.conf import settings

settings.configure(
    DATABASES={
        "default": {
            "ENGINE": "djo.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
    DEFAULT_AUTO_FIELD="djo.db.models.BigAutoField",
    INSTALLED_APPS=[
        "myapp",
    ],
)
djo.setup()

# Now use the ORM
from myapp.models import MyModel
MyModel.objects.create(name="hello")
```

### 3.2 Multi-database routing

```python
settings.configure(
    DATABASES={
        "default": {
            "ENGINE": "djo.db.backends.postgresql",
            "NAME": "primary",
        },
        "replica": {
            "ENGINE": "djo.db.backends.postgresql",
            "NAME": "replica",
        },
    },
    DATABASE_ROUTERS=["myapp.routers.ReadReplicaRouter"],
    INSTALLED_APPS=["myapp"],
)
```

### 3.3 Running migrations programmatically

```python
from djo.core.management import call_command

call_command("makemigrations", "myapp")
call_command("migrate")
```

### 3.4 Running migrations via CLI

```bash
djo makemigrations myapp
djo migrate
djo showmigrations
```

### 3.5 Using a settings module

```bash
export DJO_SETTINGS_MODULE=myproject.settings
djo migrate
```

The environment variable changes from `DJANGO_SETTINGS_MODULE` to `DJO_SETTINGS_MODULE`.

---

## 4. Module Inventory

### 4.1 Retained packages (renamed `django` → `djo`)

| Package | Notes |
|---|---|
| `djo/__init__.py` | `VERSION`, `setup()`, `__version__` |
| `djo/__main__.py` | CLI entry for `python -m djo` |
| `djo/apps/` | App registry (`AppConfig`, `Apps`) — complete |
| `djo/conf/` | Settings infrastructure, `global_settings.py` — complete |
| `djo/core/__init__.py` | Retained (minimal) |
| `djo/core/exceptions.py` | All exception classes |
| `djo/core/checks/` | System check framework — trimmed (see §6) |
| `djo/core/management/` | Management command infrastructure — trimmed (see §5) |
| `djo/core/serializers/` | Model serializers (JSON, JSONL, XML, Python, PyYAML) — used by `dumpdata`/`loaddata`/migrations |
| `djo/core/signals.py` | `request_started`, `request_finished`, `setting_changed` signals — kept because `djo.db` connects to them |
| `djo/core/validators.py` | Field validators — used by model fields |
| `djo/core/files/` | Needed by `FileField`/`ImageField` |
| `djo/core/signing.py` | May be transitively imported; keep if low-cost, stub if not |
| `djo/db/` | Complete ORM, backends, migrations — this is the core deliverable |
| `djo/db/backends/base/` | Base backend |
| `djo/db/backends/sqlite3/` | SQLite backend |
| `djo/db/backends/postgresql/` | PostgreSQL backend |
| `djo/db/backends/mysql/` | MySQL backend |
| `djo/db/backends/oracle/` | Oracle backend |
| `djo/db/backends/dummy/` | Dummy backend |
| `djo/db/migrations/` | Complete migration framework |
| `djo/db/models/` | Complete models package |
| `djo/dispatch/` | Signal dispatcher — used by ORM signals |
| `djo/utils/` | Utility modules — see §4.3 for detail |
| `djo/contrib/__init__.py` | Container |
| `djo/contrib/contenttypes/` | ContentType model, GenericForeignKey — ORM feature; remove `admin.py`, `views.py`, `forms.py` |
| `djo/contrib/postgres/` | PostgreSQL-specific fields, functions, lookups, indexes, constraints; remove `forms/`, `templates/`, `jinja2/` |
| `djo/contrib/gis/` | GeoDjango — DB layer only: `db/`, `geos/`, `gdal/`, `measure.py`, `geometry.py`, `ptr.py`, `management/`, `serializers/`, `utils/`; remove `admin/`, `feeds.py`, `forms/`, `sitemaps/`, `shortcuts.py`, `static/`, `templates/`, `views.py` |
| `djo/test/` | Test utilities (`TestCase`, `TransactionTestCase`, etc.) — needed by the test suite; remove `client.py`, `selenium.py`, `html.py` |
| `djo/_ext/` | **New.** Fork-specific glue/patch code lives here (see §9) |

### 4.2 Deleted packages

| Package | Reason |
|---|---|
| `djo/forms/` | Forms framework — web |
| `djo/http/` | HTTP request/response — web |
| `djo/middleware/` | Middleware — web |
| `djo/template/` | Template engine — web |
| `djo/templatetags/` | Template tags — web |
| `djo/urls/` | URL routing — web |
| `djo/views/` | Views — web |
| `djo/shortcuts.py` | View shortcuts — web |
| `djo/core/cache/` | Caching framework — web |
| `djo/core/handlers/` | WSGI/ASGI handlers — web |
| `djo/core/mail/` | Email — web |
| `djo/core/paginator.py` | Pagination — web |
| `djo/core/servers/` | Dev server — web |
| `djo/core/asgi.py` | ASGI — web |
| `djo/core/wsgi.py` | WSGI — web |
| `djo/contrib/admin/` | Admin — web |
| `djo/contrib/admindocs/` | Admin docs — web |
| `djo/contrib/auth/` | Authentication — web |
| `djo/contrib/flatpages/` | Flatpages — web |
| `djo/contrib/humanize/` | Humanize — web |
| `djo/contrib/messages/` | Messages — web |
| `djo/contrib/redirects/` | Redirects — web |
| `djo/contrib/sessions/` | Sessions — web |
| `djo/contrib/sitemaps/` | Sitemaps — web |
| `djo/contrib/sites/` | Sites — web |
| `djo/contrib/staticfiles/` | Static files — web |
| `djo/contrib/syndication/` | RSS/Atom feeds — web |
| `djo/conf/app_template/` | `startapp` template — web |
| `djo/conf/project_template/` | `startproject` template — web |
| `djo/conf/urls/` | Default URL configs — web |

### 4.3 djo/utils/ — retained vs removed

The `djo/utils/` package has many modules. The ORM/migrations/backends import a subset. Retain all except modules that are purely web-framework utilities:

**Retain** (used by ORM, migrations, or DB backends):

- `__init__.py`, `_os.py`, `asyncio.py`, `choices.py`, `connection.py`, `crypto.py`, `datastructures.py`, `dateformat.py`, `dateparse.py`, `dates.py`, `deconstruct.py`, `decorators.py`, `deprecation.py`, `duration.py`, `encoding.py`, `formats.py`, `functional.py`, `hashable.py`, `inspect.py`, `ipv6.py`, `itercompat.py`, `module_loading.py`, `regex_helper.py`, `termcolors.py`, `text.py`, `timesince.py`, `timezone.py`, `translation/`, `tree.py`, `version.py`, `numberformat.py`

**Remove** (web-only, not imported by retained code):

- `autoreload.py` — dev server auto-reload
- `cache.py` — cache utility
- `feedgenerator.py` — RSS/Atom feed generation
- `html.py` — HTML escaping (keep only if `djo.db` or validators import it; likely needed by validators → **keep**)
- `http.py` — HTTP utilities (urlencode, etc.) — remove unless transitively needed
- `log.py` — logging configuration (needed by `setup()` → **keep**)
- `lorem_ipsum.py` — placeholder text generation
- `safestring.py` — `mark_safe` for templates (keep only if transitively imported; likely needed by some field rendering → **keep conditionally**)
- `xmlutils.py` — XML utilities (keep if serializers use it)
- `archive.py` — file archive extraction

**Decision rule:** During implementation, use an import-tracing pass to confirm which `utils/` modules are transitively imported by the retained packages. Keep those; remove or stub the rest. The above is the expected result.

### 4.4 djo/conf/global_settings.py

Keep the file as-is. Settings that relate to removed subsystems (e.g., `TEMPLATES`, `MIDDLEWARE`, `ROOT_URLCONF`, `STATIC_URL`) remain defined with their default values — this is harmless and matches Django behavior where unused settings are simply ignored. Do **not** add validation that rejects unknown/unused settings.

---

## 5. Management Commands

### 5.1 Retained commands

| Command | Rationale |
|---|---|
| `makemigrations` | Core migration workflow |
| `migrate` | Core migration workflow |
| `showmigrations` | Migration inspection |
| `sqlmigrate` | SQL inspection |
| `squashmigrations` | Migration maintenance |
| `optimizemigration` | Migration maintenance |
| `inspectdb` | DB introspection |
| `dbshell` | Interactive DB shell — low-cost, no non-ORM deps |
| `flush` | DB reset — useful for testing |
| `loaddata` | Fixture loading — depends on serializers (retained) |
| `dumpdata` | Fixture dumping — depends on serializers (retained) |
| `sqlflush` | SQL generation |
| `sqlsequencereset` | Sequence management |
| `diffsettings` | Settings debugging — low-cost, no non-ORM deps |

### 5.2 Removed commands

| Command | Reason |
|---|---|
| `check` | Pulls in all check registrations including web subsystems; not worth the dependency cost. Users can call `djo.core.checks.run_checks()` programmatically with specific tags. |
| `compilemessages` | i18n — web (translation files still available but compile is not a DB operation) |
| `createcachetable` | Cache framework |
| `makemessages` | i18n — web |
| `runserver` | Dev server — web |
| `sendtestemail` | Email — web |
| `shell` | Generic Python shell — not DB-specific; users can use `python -c` or IPython |
| `startapp` | Project scaffolding — web |
| `startproject` | Project scaffolding — web |
| `test` | Test runner command — users run tests via the standard test runner directly |
| `testserver` | Test server — web |

---

## 6. System Checks Policy

### 6.1 Retained check modules

| Module | Tags | Reason |
|---|---|---|
| `djo/core/checks/__init__.py` | — | Framework infrastructure |
| `djo/core/checks/registry.py` | — | Check registration system |
| `djo/core/checks/messages.py` | — | Check message classes |
| `djo/core/checks/database.py` | `database` | DB backend validation |
| `djo/core/checks/model_checks.py` | `models` | Model validation |
| `djo/core/checks/commands.py` | `commands` | Management command checks |

### 6.2 Removed check modules

| Module | Tags | Reason |
|---|---|---|
| `async_checks.py` | `async_support` | ASGI — web |
| `caches.py` | `caches` | Cache framework |
| `files.py` | `files` | File storage — remove only if not needed by FileField checks. If FileField checks register under this tag, **keep**. |
| `compatibility/` | `compatibility` | Django-version compat checks — web-focused |
| `security/` | `security` | CSRF, sessions, HTTPS — web |
| `templates.py` | `templates` | Template engine |
| `translation.py` | `translation` | i18n |
| `urls.py` | `urls` | URL routing |

### 6.3 Implementation approach

The `djo/core/checks/__init__.py` file forces registration of checks by importing modules. Remove the import lines for deleted check modules. Keep imports for `database`, `model_checks`, `commands`, and `compatibility.django_4_0` (if it has any ORM-relevant checks; otherwise remove).

The `Tags` class in `registry.py` will retain all tag constants (removing them would be a public API change) but the removed check modules simply won't register handlers for those tags.

---

## 7. Test Strategy

### 7.1 Kept test modules (124 directories)

All test directories that test ORM, database, migrations, model fields, querysets, expressions, aggregations, backends, schema operations, serializers, signals, transactions, multi-database, fixtures, introspection, indexes, constraints, and related functionality.

**Complete list of kept test directories:**

`aggregation`, `aggregation_regress`, `annotations`, `backends`, `base`, `basic`, `bulk_create`, `composite_pk`, `constraints`, `contenttypes_tests`, `custom_columns`, `custom_lookups`, `custom_managers`, `custom_methods`, `custom_migration_operations`, `custom_pk`, `datatypes`, `dates`, `datetimes`, `db_functions`, `db_typecasts`, `db_utils`, `dbshell`, `defer`, `defer_regress`, `delete`, `delete_regress`, `distinct_on_fields`, `empty`, `empty_models`, `expressions`, `expressions_case`, `expressions_window`, `extra_regress`, `field_deconstruction`, `field_defaults`, `field_subclassing`, `filtered_relation`, `fixtures`, `fixtures_model_package`, `fixtures_regress`, `force_insert_update`, `foreign_object`, `from_db_value`, `generic_relations`, `generic_relations_regress`, `get_earliest_or_latest`, `get_or_create`, `gis_tests`, `indexes`, `inspectdb`, `introspection`, `invalid_models_tests`, `known_related_objects`, `lookup`, `m2m_and_m2o`, `m2m_intermediary`, `m2m_multiple`, `m2m_recursive`, `m2m_regress`, `m2m_signals`, `m2m_through`, `m2m_through_regress`, `m2o_recursive`, `managers_regress`, `many_to_many`, `many_to_one`, `many_to_one_null`, `max_lengths`, `migrate_signals`, `migration_test_data_persistence`, `migrations`, `migrations2`, `model_enums`, `model_fields`, `model_indexes`, `model_inheritance`, `model_inheritance_regress`, `model_meta`, `model_options`, `model_package`, `model_regress`, `model_utils`, `multiple_database`, `mutually_referential`, `nested_foreign_keys`, `no_models`, `null_fk`, `null_fk_ordering`, `null_queries`, `one_to_one`, `or_lookups`, `order_with_respect_to`, `ordering`, `postgres_tests`, `prefetch_related`, `properties`, `proxy_model_inheritance`, `proxy_models`, `queries`, `queryset_pickle`, `raw_query`, `reserved_names`, `reverse_lookup`, `save_delete_hooks`, `schema`, `select_for_update`, `select_related`, `select_related_onetoone`, `select_related_regress`, `serializers`, `signals`, `str`, `string_lookup`, `swappable_models`, `timezones`, `transaction_hooks`, `transactions`, `unmanaged_models`, `update`, `update_only_fields`, `validation`, `validators`, `xor_lookups`

**Partially kept:**

- `async/` — Keep only: `test_async_queryset.py`, `test_async_model_methods.py`, `test_async_related_managers.py`. Remove: `test_async_auth.py`, `test_async_shortcuts.py`, and any other web-related async tests.

**Infrastructure tests to keep selectively:**

- `dispatch/` — Signal dispatcher tests — keep (ORM signals depend on dispatch).
- `check_framework/` — Keep only tests that exercise model/database checks. Remove tests for web-related checks (templates, URLs, caches, security).
- `utils_tests/` — Keep tests for utility modules retained in §4.3. Remove tests for removed utils.
- `apps/` — App registry is core to ORM. Keep.
- `settings_tests/` — Settings infrastructure is core. Keep.
- `version/` — Trivial. Keep.
- `test_exceptions/` — `ValidationError` is used by ORM. Keep.

### 7.2 Removed test modules (73+ directories)

All test directories related to web framework features:

`absolute_url_overrides`, `admin_autodiscover`, `admin_changelist`, `admin_checks`, `admin_custom_urls`, `admin_default_site`, `admin_docs`, `admin_filters`, `admin_inlines`, `admin_ordering`, `admin_registration`, `admin_scripts`, `admin_utils`, `admin_views`, `admin_widgets`, `asgi`, `auth_tests`, `builtin_server`, `cache`, `conditional_processing`, `context_processors`, `csrf_tests`, `decorators`, `file_storage`, `file_uploads`, `files`, `flatpages_tests`, `forms_tests`, `generic_inline_admin`, `generic_views`, `get_object_or_404`, `handlers`, `httpwrappers`, `humanize_tests`, `i18n`, `inline_formsets`, `logging_tests`, `mail`, `messages_tests`, `middleware`, `middleware_exceptions`, `model_forms`, `model_formsets`, `model_formsets_regress`, `modeladmin`, `pagination`, `project_template`, `redirects_tests`, `requests_tests`, `resolve_url`, `responses`, `sessions_tests`, `shell`, `shortcuts`, `signed_cookies_tests`, `signing`, `sitemaps_tests`, `sites_framework`, `sites_tests`, `staticfiles_tests`, `syndication_tests`, `template_backends`, `template_loader`, `template_tests`, `templates`, `test_client`, `test_client_regress`, `urlpatterns`, `urlpatterns_reverse`, `user_commands`, `view_tests`, `wsgi`

Also remove: `admin_scripts/`, `app_loading/`, `bash_completion/`, `deprecation/`, `import_error_package/`, `sphinx/`, `test_runner/`, `test_runner_apps/`, `requirements/`

### 7.3 Running tests

Tests use Django's own test infrastructure. The test runner invocation becomes:

```bash
# SQLite (default)
cd tests/
python runtests.py --settings=test_sqlite

# PostgreSQL
python runtests.py --settings=test_postgres

# MySQL
python runtests.py --settings=test_mysql

# Oracle
python runtests.py --settings=test_oracle

# Specific test module
python runtests.py --settings=test_sqlite queries expressions migrations

# Parallel
python runtests.py --settings=test_sqlite --parallel
```

The test settings files (`test_sqlite.py`, etc.) will need their imports updated from `django.*` to `djo.*`.

### 7.4 Test triage policy

If a retained ORM test fails because it depends on a removed subsystem (e.g., it imports `djo.http` or `djo.contrib.admin`), that individual test is **removed or skipped** rather than retaining the non-ORM subsystem. Minimal ORM core is the priority.

---

## 8. Packaging & Distribution

### 8.1 Package metadata

```toml
[project]
name = "djo"
description = "Django ORM, migrations, and database backends as a standalone library."
requires-python = ">= 3.10"
dependencies = [
    "sqlparse>=0.3.1",
    "tzdata; sys_platform == 'win32'",
]
# Note: asgiref removed from core deps (it's for ASGI which is removed)
# If any retained code actually imports asgiref, add it back.

[project.scripts]
djo = "djo.core.management:execute_from_command_line"

[tool.setuptools.packages.find]
include = ["djo*"]

[tool.setuptools.dynamic]
version = {attr = "djo.__version__"}
```

### 8.2 Version strategy

- `djo` version tracks the upstream Django tag it's based on, with an additional fork suffix.
- Example: Django 5.2.1 → djo 5.2.1.0, djo 5.2.1.1 (fork patch).
- `VERSION` tuple in `djo/__init__.py` remains the Django format: `(5, 2, X, 'final'/'alpha', N)`.

### 8.3 Console script

The `djo` console script replaces `django-admin`. It invokes `djo.core.management.execute_from_command_line()`.

### 8.4 Environment variable

`DJANGO_SETTINGS_MODULE` → `DJO_SETTINGS_MODULE`. This is the one environment variable rename. The settings machinery in `djo/conf/__init__.py` must reference `DJO_SETTINGS_MODULE` instead of `DJANGO_SETTINGS_MODULE`.

---

## 9. Upstream Sync Philosophy & Code Layout

### 9.1 Minimal diff surface

The fork's changes over upstream Django fall into exactly these categories:

1. **Mechanical namespace rename** (`django` → `djo`): done via automated tooling, applied as a single rebase-able commit.
2. **File/directory deletions**: removing web-framework packages (forms, http, etc.). These are clean deletions — easy to re-apply after a rebase.
3. **Check framework trimming**: removing import lines in `__init__.py` for deleted check modules.
4. **Management command pruning**: deleting command files.
5. **`setup()` function simplification**: removing URL prefix and logging config from `djo/__init__.py`.
6. **pyproject.toml changes**: package metadata.
7. **Fork-specific glue in `djo/_ext/`**: any patches that can't be expressed as simple deletions.

### 9.2 djo/_ext/ package

All fork-specific logic that goes beyond mechanical rename or deletion lives in `djo/_ext/`. This includes:

- `djo/_ext/__init__.py`
- `djo/_ext/setup.py` — fork-specific `setup()` adjustments (simplified setup without URL/logging if needed).
- Any monkey-patches or compatibility shims needed to make stripped-down imports work.

Upstream-derived modules should **not** be edited with bespoke logic. If a module needs behavioral changes, it should call into `djo._ext` or the modification should be a minimal, clearly-commented one-liner.

### 9.3 Branch strategy

```
main              ← djo stable releases
upstream/main     ← tracks django/django:main (read-only mirror)
upstream/stable/5.2.x ← tracks django/django:stable/5.2.x
```

### 9.4 Rebase workflow

To incorporate a new upstream tag:

1. Fetch the upstream tag.
2. Create a fresh branch from the tag.
3. Re-apply the fork's topic commits (namespace rename, deletions, pyproject changes, `_ext/` additions).
4. Run tests. Fix any conflicts.
5. Tag and release.

Topic commits are structured to be individually re-applicable:

- `[namespace] Rename django → djo in all source files`
- `[prune] Remove web framework packages`
- `[prune] Remove non-DB management commands`
- `[prune] Trim system checks to ORM-only`
- `[prune] Remove web-related test directories`
- `[packaging] Update pyproject.toml for djo`
- `[ext] Add djo/_ext/ fork glue`
- `[setup] Simplify djo.setup()`

Each commit is self-contained and can be cherry-picked or rebased independently.

### 9.5 Conflict expectations

Most upstream changes will be in files we don't touch (views, admin, templates, etc.) — these conflict-free because we simply delete those files. Conflicts will primarily arise in:

- `djo/db/` — the core code we care about (low conflict risk since we don't modify internals).
- `djo/conf/global_settings.py` — upstream may add settings.
- `djo/core/management/` — upstream may change command infrastructure.
- `djo/utils/` — upstream may change utilities.

The rename commit is the most conflict-prone. Using `sed`-based mechanical transforms makes it reproducible.

---

## 10. Disagreements / Adjustments

### 10.1 `asgiref` dependency

Django 5.2 uses `asgiref` for async support in the ORM (`QuerySet.aiterator()`, `Model.asave()`, etc.). Even though we remove the ASGI web stack, **`asgiref` must remain a dependency** because the async ORM methods depend on `asgiref.sync.sync_to_async`. This is a correction from the user's implicit assumption that removing web features means removing `asgiref`.

### 10.2 `djo/core/files/` retention

`FileField` and `ImageField` are ORM field types that depend on `djo.core.files`. Even though file storage is web-adjacent, these fields are part of the ORM public API. We retain `djo/core/files/` and `djo/core/files/storage.py` to keep `FileField`/`ImageField` functional. The `file_storage` and `file_uploads` test directories are still removed since they test the web upload pipeline.

### 10.3 `djo/utils/translation/` retention

The Django ORM uses `gettext_lazy` and translation utilities throughout model field definitions (`verbose_name`, `help_text`, etc.) and migration files. The translation utility (`djo/utils/translation/`) must be retained even though we remove the i18n management commands (`makemessages`, `compilemessages`) and the full i18n middleware.

### 10.4 `dumpdata` / `loaddata` / `flush` retention

These are DB-related management commands that operate on model data and fixtures. They depend on `djo/core/serializers/` which is a retained module. Including them adds value for ORM-only users. The user's spec mentioned only migration commands, but these are data-management commands that fit squarely within "DB operations."

### 10.5 `diffsettings` retention

Nearly zero-cost command useful for debugging settings. No non-ORM dependencies.

### 10.6 `check` management command

Removed as specified. However, users can still run ORM-relevant checks programmatically:

```python
from djo.core.checks import run_checks, Tags
errors = run_checks(tags=[Tags.models, Tags.database])
```
