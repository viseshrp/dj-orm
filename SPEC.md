# djorm — Django ORM as a Standalone Library

## Specification Document

**Base upstream:** Django 5.2 LTS (latest tag)
**Target PyPI distribution:** `dj-orm`
**Import namespace:** `djorm`

---

## 1. Purpose

`djorm` extracts the Django ORM, migration framework, and database backend stack from Django 5.2 LTS into a standalone Python library. The PyPI distribution is `dj-orm`; the import namespace is `djorm` because the unrelated `djorm` distribution name is already registered.

### What djorm IS

- The full Django ORM (models, querysets, managers, fields, expressions, aggregations, window functions, raw SQL, etc.).
- The complete migration framework (auto-detection, migration files, squashing, optimisation).
- All Django 5.2 database backends: SQLite, PostgreSQL, MySQL, Oracle.
- The `contrib.postgres` extension fields/functions/indexes/lookups/constraints.
- The `contrib.contenttypes` framework (ContentType model, GenericForeignKey/GenericRelation).
- The `contrib.gis` (GeoDjango) database layer (fields, functions, lookups, backends). **Deferred to a later milestone** — see §10.7.
- The app registry (`djorm.apps`) and settings infrastructure (`djorm.conf`).
- The signal dispatcher (`djorm.dispatch`).
- All ORM model signals (`djorm.db.models.signals`): `pre_init`, `post_init`, `pre_save`, `post_save`, `pre_delete`, `post_delete`, `m2m_changed`, `class_prepared`, `pre_migrate`, `post_migrate`. These are core ORM extension points and must be fully preserved.
- The system check framework — retained only because ORM and migrations already depend on it internally (model validation, DB backend checks). No web-oriented check modules are included.
- The test infrastructure needed to run the kept tests (`djorm.test`).
- DB and data-operations management commands (see §5 for full rationale). This intentionally goes beyond strict "migrations-only" to include data import/export and DB maintenance commands that ORM-focused users commonly need. This choice brings `djorm/core/serializers/` and fixture infrastructure into scope.
- A CLI entry point (`djorm`) that dispatches to the management command framework.

### What djorm is NOT

- A web framework. No HTTP layer, no views, no URL routing, no middleware, no templates, no forms, no sessions, no auth/permissions, no admin, no caching framework, no static files, no ASGI/WSGI support.
- A compatibility shim. There is **no** `django` namespace. All imports use `djorm`.
- A new API surface. No `djorm.configure()`, no `database_url` helper, no synthetic app concept. Users interact with the same Django API patterns they already know, under the `djorm.*` namespace.

### Non-goals

- Providing any web-framework functionality.
- Creating backward-compatible `django.*` imports.
- Introducing new public APIs beyond what Django 5.2 already provides.
- Supporting Django contrib apps unrelated to the ORM (admin, auth, sessions, messages, flatpages, redirects, sitemaps, syndication, humanize, staticfiles).

---

## 2. Public API Parity Statement

Every public API that exists in the retained modules is preserved with identical semantics. The **only** change is the top-level namespace prefix:

| Django 5.2 | djorm |
|---|---|
| `from django.db import models` | `from djorm.db import models` |
| `from django.conf import settings` | `from djorm.conf import settings` |
| `from django.db import connection` | `from djorm.db import connection` |
| `from django.apps import AppConfig` | `from djorm.apps import AppConfig` |
| `from django.core.management import call_command` | `from djorm.core.management import call_command` |
| `from django.contrib.postgres.fields import ArrayField` | `from djorm.contrib.postgres.fields import ArrayField` |
| `from django.contrib.contenttypes.fields import GenericForeignKey` | `from djorm.contrib.contenttypes.fields import GenericForeignKey` |

Settings keys are **unchanged**: `DATABASES`, `INSTALLED_APPS`, `DEFAULT_AUTO_FIELD`, `DATABASE_ROUTERS`, etc. String references in settings that formerly used `django.*` paths (e.g., backend engine strings like `"django.db.backends.sqlite3"`) become `"djorm.db.backends.sqlite3"`.

---

## 3. Supported Usage Patterns

### 3.1 Minimal standalone ORM setup

```python
import djorm
from djorm.conf import settings

settings.configure(
    DATABASES={
        "default": {
            "ENGINE": "djorm.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
    DEFAULT_AUTO_FIELD="djorm.db.models.BigAutoField",
    INSTALLED_APPS=[
        "myapp",
    ],
)
djorm.setup()

# Now use the ORM
from myapp.models import MyModel
MyModel.objects.create(name="hello")
```

### 3.2 Multi-database routing

```python
settings.configure(
    DATABASES={
        "default": {
            "ENGINE": "djorm.db.backends.postgresql",
            "NAME": "primary",
        },
        "replica": {
            "ENGINE": "djorm.db.backends.postgresql",
            "NAME": "replica",
        },
    },
    DATABASE_ROUTERS=["myapp.routers.ReadReplicaRouter"],
    INSTALLED_APPS=["myapp"],
)
```

### 3.3 Running migrations programmatically

```python
from djorm.core.management import call_command

call_command("makemigrations", "myapp")
call_command("migrate")
```

### 3.4 Running migrations via CLI

```bash
djorm makemigrations myapp
djorm migrate
djorm showmigrations
```

### 3.5 Using a settings module

```bash
export DJANGO_SETTINGS_MODULE=myproject.settings
djorm migrate
```

The `DJANGO_SETTINGS_MODULE` environment variable is **unchanged** from Django. This is part of operational API parity — the env var name is not a Python import path, so the namespace rename does not apply to it.

---

## 4. Module Inventory

### 4.1 Retained packages (renamed `django` → `djorm`)

| Package | Notes |
|---|---|
| `djorm/__init__.py` | `VERSION`, `setup()`, `__version__` |
| `djorm/__main__.py` | CLI entry for `python -m djorm` |
| `djorm/apps/` | App registry (`AppConfig`, `Apps`) — complete |
| `djorm/conf/` | Settings infrastructure, `global_settings.py` — complete |
| `djorm/core/__init__.py` | Retained (minimal) |
| `djorm/core/exceptions.py` | All exception classes |
| `djorm/core/checks/` | System check framework — trimmed (see §6) |
| `djorm/core/management/` | Management command infrastructure — trimmed (see §5) |
| `djorm/core/serializers/` | Model serializers (JSON, JSONL, XML, Python, PyYAML) — used by `dumpdata`/`loaddata`/migrations |
| `djorm/core/signals.py` | `request_started`, `request_finished`, `got_request_exception`, `setting_changed` — kept because `djorm.db.__init__` connects `reset_queries`/`close_old_connections` to `request_started`/`request_finished`, and `setting_changed` is used by caches/connection handlers. See §4.5 for signal-hookup policy. |
| `djorm/core/validators.py` | Field validators — used by model fields |
| `djorm/core/files/` | Needed by `FileField`/`ImageField` |
| `djorm/core/signing.py` | May be transitively imported; keep if low-cost, stub if not |
| `djorm/db/` | Complete ORM, backends, migrations — this is the core deliverable |
| `djorm/db/backends/base/` | Base backend |
| `djorm/db/backends/sqlite3/` | SQLite backend |
| `djorm/db/backends/postgresql/` | PostgreSQL backend |
| `djorm/db/backends/mysql/` | MySQL backend |
| `djorm/db/backends/oracle/` | Oracle backend |
| `djorm/db/backends/dummy/` | Dummy backend |
| `djorm/db/migrations/` | Complete migration framework |
| `djorm/db/models/` | Complete models package (includes `djorm/db/models/signals.py` — all ORM model signals) |
| `djorm/dispatch/` | Signal dispatcher — the `Signal` class and `receiver` decorator; used by ORM model signals and `djorm/core/signals.py` |
| `djorm/utils/` | Utility modules — see §4.3 for detail |
| `djorm/contrib/__init__.py` | Container |
| `djorm/contrib/contenttypes/` | ContentType model, GenericForeignKey — ORM feature; remove `admin.py`, `views.py`, `forms.py` |
| `djorm/contrib/postgres/` | PostgreSQL-specific fields, functions, lookups, indexes, constraints; remove `forms/`, `templates/`, `jinja2/` |
| `djorm/contrib/gis/` | **Deferred to a later milestone.** GeoDjango requires native GEOS/GDAL/PROJ libraries and has a heavy local-setup burden. Keeping it out of the initial release reduces risk. When added: retain only DB layer (`db/`, `geos/`, `gdal/`, `measure.py`, `geometry.py`, `ptr.py`, `management/`, `serializers/`, `utils/`); remove `admin/`, `feeds.py`, `forms/`, `sitemaps/`, `shortcuts.py`, `static/`, `templates/`, `views.py`. |
| `djorm/test/` | Test utilities (`TestCase`, `TransactionTestCase`, etc.) — needed by the test suite; remove `client.py`, `selenium.py`, `html.py` |
| `djorm/_ext/` | **New.** Fork-specific glue/patch code lives here (see §9) |

### 4.2 Deleted packages

| Package | Reason |
|---|---|
| `djorm/forms/` | Forms framework — web |
| `djorm/http/` | HTTP request/response — web |
| `djorm/middleware/` | Middleware — web |
| `djorm/template/` | Template engine — web |
| `djorm/templatetags/` | Template tags — web |
| `djorm/urls/` | URL routing — web |
| `djorm/views/` | Views — web |
| `djorm/shortcuts.py` | View shortcuts — web |
| `djorm/core/cache/` | Caching framework — web |
| `djorm/core/handlers/` | WSGI/ASGI handlers — web |
| `djorm/core/mail/` | Email — web |
| `djorm/core/paginator.py` | Pagination — web |
| `djorm/core/servers/` | Dev server — web |
| `djorm/core/asgi.py` | ASGI — web |
| `djorm/core/wsgi.py` | WSGI — web |
| `djorm/contrib/admin/` | Admin — web |
| `djorm/contrib/admindocs/` | Admin docs — web |
| `djorm/contrib/auth/` | Authentication — web |
| `djorm/contrib/flatpages/` | Flatpages — web |
| `djorm/contrib/humanize/` | Humanize — web |
| `djorm/contrib/messages/` | Messages — web |
| `djorm/contrib/redirects/` | Redirects — web |
| `djorm/contrib/sessions/` | Sessions — web |
| `djorm/contrib/sitemaps/` | Sitemaps — web |
| `djorm/contrib/sites/` | Sites — web |
| `djorm/contrib/staticfiles/` | Static files — web |
| `djorm/contrib/syndication/` | RSS/Atom feeds — web |
| `djorm/conf/app_template/` | `startapp` template — web |
| `djorm/conf/project_template/` | `startproject` template — web |
| `djorm/conf/urls/` | Default URL configs — web |

### 4.3 djorm/utils/ — retained vs removed

The `djorm/utils/` package has many modules. The ORM/migrations/backends import a subset. Retain all except modules that are purely web-framework utilities:

**Retain** (used by ORM, migrations, or DB backends):

- `__init__.py`, `_os.py`, `asyncio.py`, `choices.py`, `connection.py`, `crypto.py`, `datastructures.py`, `dateformat.py`, `dateparse.py`, `dates.py`, `deconstruct.py`, `decorators.py`, `deprecation.py`, `duration.py`, `encoding.py`, `formats.py`, `functional.py`, `hashable.py`, `inspect.py`, `ipv6.py`, `itercompat.py`, `module_loading.py`, `regex_helper.py`, `termcolors.py`, `text.py`, `timesince.py`, `timezone.py`, `translation/`, `tree.py`, `version.py`, `numberformat.py`

**Remove** (web-only, not imported by retained code):

- `autoreload.py` — dev server auto-reload
- `cache.py` — cache utility
- `feedgenerator.py` — RSS/Atom feed generation
- `html.py` — HTML escaping (keep only if `djorm.db` or validators import it; likely needed by validators → **keep**)
- `http.py` — HTTP utilities (urlencode, etc.) — remove unless transitively needed
- `log.py` — logging configuration (needed by `setup()` → **keep**)
- `lorem_ipsum.py` — placeholder text generation
- `safestring.py` — `mark_safe` for templates (keep only if transitively imported; likely needed by some field rendering → **keep conditionally**)
- `xmlutils.py` — XML utilities (keep if serializers use it)
- `archive.py` — file archive extraction

**Decision rule:** During implementation, use an import-tracing pass to confirm which `utils/` modules are transitively imported by the retained packages. Keep those; remove or stub the rest. The above is the expected result.

### 4.4 djorm/conf/global_settings.py

Keep the file as-is. Settings that relate to removed subsystems (e.g., `TEMPLATES`, `MIDDLEWARE`, `ROOT_URLCONF`, `STATIC_URL`) remain defined with their default values — this is harmless and matches Django behavior where unused settings are simply ignored. Do **not** add validation that rejects unknown/unused settings.

### 4.5 Signals policy

Signals are a core ORM extension mechanism. The policy is: **preserve all signal definitions and all signal hookups that serve ORM/DB functionality; only strip hookups that are exclusive to removed subsystems.**

**Fully retained (no changes):**

| Signal | Module | Reason |
|---|---|---|
| `pre_init` / `post_init` | `djorm.db.models.signals` | Model instance lifecycle |
| `pre_save` / `post_save` | `djorm.db.models.signals` | Model save hooks |
| `pre_delete` / `post_delete` | `djorm.db.models.signals` | Model deletion hooks |
| `m2m_changed` | `djorm.db.models.signals` | Many-to-many relationship changes |
| `class_prepared` | `djorm.db.models.signals` | App-registry model registration |
| `pre_migrate` / `post_migrate` | `djorm.db.models.signals` | Migration lifecycle |
| `setting_changed` | `djorm.core.signals` | Used by connection handlers and test infrastructure (`override_settings`) |
| `request_started` / `request_finished` | `djorm.core.signals` | `djorm.db.__init__` connects `reset_queries` and `close_old_connections` to these; see below |

**`request_started` / `request_finished` hookups in `djorm/db/__init__.py`:** These connections (`signals.request_started.connect(reset_queries)`, etc.) are ORM-serving — they reset query logs and close stale DB connections. In a non-web context the signals simply never fire unless the user sends them explicitly, which is harmless. **Keep these hookups as-is.**

**`got_request_exception`:** Defined in `djorm.core.signals`. No ORM code connects to it, but it's a one-liner and removing it would be a public API deletion with zero benefit. **Keep the definition; do not add any new connections to it.**

**Signal hookups to strip:** If any signal `.connect()` call in a retained module routes exclusively to a deleted subsystem (e.g., a hypothetical `signals.request_finished.connect(flush_sessions)`), remove that `.connect()` call. The signal *definition* stays; only the dead hookup is removed.

---

## 5. Management Commands

### 5.1 Scope decision: "DB-ops mode" (not strict migrations-only)

This project intentionally keeps data-management commands beyond strict migration commands. The rationale: ORM-focused users routinely need fixture import/export and DB maintenance operations, and the incremental dependency cost (`djorm/core/serializers/`, fixture plumbing) is modest. **This is a deliberate scope choice**, not something that happened "because it's low-cost." Accepting this scope means `djorm/core/serializers/` and its transitive dependencies are permanently in-scope for maintenance.

If a future maintainer wants to narrow scope to strict migrations-only, the commands to cut are: `dumpdata`, `loaddata`, `flush`, `sqlflush`, `sqlsequencereset`, `diffsettings`. That would also allow removing `djorm/core/serializers/`.

### 5.2 Retained commands

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
| `flush` | DB reset — useful for testing (DB-ops) |
| `loaddata` | Fixture loading — depends on serializers (DB-ops) |
| `dumpdata` | Fixture dumping — depends on serializers (DB-ops) |
| `sqlflush` | SQL generation (DB-ops) |
| `sqlsequencereset` | Sequence management (DB-ops) |
| `diffsettings` | Settings debugging — near-zero cost (DB-ops) |

### 5.3 Removed commands

| Command | Reason |
|---|---|
| `check` | Pulls in all check registrations including web subsystems; not worth the dependency cost. Users can call `djorm.core.checks.run_checks()` programmatically with specific tags. |
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

The system check framework is retained **only because ORM and migrations already depend on it** — model validation, DB backend validation, and management command checks are wired through it internally. We are not keeping checks as a general-purpose feature. The `check` management command is removed; users who want to run ORM checks programmatically can call `djorm.core.checks.run_checks(tags=[Tags.models, Tags.database])`.

### 6.1 Retained check modules

| Module | Tags | Reason |
|---|---|---|
| `djorm/core/checks/__init__.py` | — | Framework infrastructure (ORM/migrations depend on it) |
| `djorm/core/checks/registry.py` | — | Check registration system (ORM/migrations depend on it) |
| `djorm/core/checks/messages.py` | — | Check message classes (ORM/migrations depend on it) |
| `djorm/core/checks/database.py` | `database` | DB backend validation (called during migrate) |
| `djorm/core/checks/model_checks.py` | `models` | Model validation (called during migrate, makemigrations) |
| `djorm/core/checks/commands.py` | `commands` | Management command checks (near-zero incremental cost) |

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

The `djorm/core/checks/__init__.py` file forces registration of checks by importing modules. Remove the import lines for deleted check modules. Keep imports for `database`, `model_checks`, `commands`, and `compatibility.django_4_0` (if it has any ORM-relevant checks; otherwise remove).

The `Tags` class in `registry.py` will retain all tag constants (removing them would be a public API change) but the removed check modules simply won't register handlers for those tags.

---

## 7. Test Strategy

### 7.1 Kept test modules (124 directories)

All test directories that test ORM, database, migrations, model fields, querysets, expressions, aggregations, backends, schema operations, serializers, signals, transactions, multi-database, fixtures, introspection, indexes, constraints, and related functionality.

**Complete list of kept test directories:**

`aggregation`, `aggregation_regress`, `annotations`, `backends`, `base`, `basic`, `bulk_create`, `composite_pk`, `constraints`, `contenttypes_tests`, `custom_columns`, `custom_lookups`, `custom_managers`, `custom_methods`, `custom_migration_operations`, `custom_pk`, `datatypes`, `dates`, `datetimes`, `db_functions`, `db_typecasts`, `db_utils`, `dbshell`, `defer`, `defer_regress`, `delete`, `delete_regress`, `distinct_on_fields`, `empty`, `empty_models`, `expressions`, `expressions_case`, `expressions_window`, `extra_regress`, `field_deconstruction`, `field_defaults`, `field_subclassing`, `filtered_relation`, `fixtures`, `fixtures_model_package`, `fixtures_regress`, `force_insert_update`, `foreign_object`, `from_db_value`, `generic_relations`, `generic_relations_regress`, `get_earliest_or_latest`, `get_or_create`, `indexes`, `inspectdb`, `introspection`, `invalid_models_tests`, `known_related_objects`, `lookup`, `m2m_and_m2o`, `m2m_intermediary`, `m2m_multiple`, `m2m_recursive`, `m2m_regress`, `m2m_signals`, `m2m_through`, `m2m_through_regress`, `m2o_recursive`, `managers_regress`, `many_to_many`, `many_to_one`, `many_to_one_null`, `max_lengths`, `migrate_signals`, `migration_test_data_persistence`, `migrations`, `migrations2`, `model_enums`, `model_fields`, `model_indexes`, `model_inheritance`, `model_inheritance_regress`, `model_meta`, `model_options`, `model_package`, `model_regress`, `model_utils`, `multiple_database`, `mutually_referential`, `nested_foreign_keys`, `no_models`, `null_fk`, `null_fk_ordering`, `null_queries`, `one_to_one`, `or_lookups`, `order_with_respect_to`, `ordering`, `postgres_tests`, `prefetch_related`, `properties`, `proxy_model_inheritance`, `proxy_models`, `queries`, `queryset_pickle`, `raw_query`, `reserved_names`, `reverse_lookup`, `save_delete_hooks`, `schema`, `select_for_update`, `select_related`, `select_related_onetoone`, `select_related_regress`, `serializers`, `signals`, `str`, `string_lookup`, `swappable_models`, `timezones`, `transaction_hooks`, `transactions`, `unmanaged_models`, `update`, `update_only_fields`, `validation`, `validators`, `xor_lookups`

**Deferred (GIS milestone):**

- `gis_tests/` — deferred along with `contrib.gis` (see §10.7).

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

The test settings files (`test_sqlite.py`, etc.) will need their imports updated from `django.*` to `djorm.*`.

### 7.4 Test triage policy

If a retained ORM test fails because it depends on a removed subsystem (e.g., it imports `djorm.http` or `djorm.contrib.admin`), that individual test is **removed or skipped** rather than retaining the non-ORM subsystem. Minimal ORM core is the priority.

---

## 8. Packaging & Distribution

### 8.1 Package metadata

> **Source of truth:** `requires-python`, dependency version pins, and Python-version classifiers must be **derived from upstream Django 5.2's `pyproject.toml`** at fork time (not hand-entered). Only change the package name, module paths, and description. If upstream updates version bounds in a patch release, the rebase picks them up automatically.

```toml
[project]
name = "dj-orm"
dynamic = ["version"]
description = "Django ORM, migrations, and database backends as a standalone library."
requires-python = ">= 3.10"  # copied from upstream Django 5.2
dependencies = [
    "asgiref>=3.8.1",    # copied from upstream; required for async ORM API
    "sqlparse>=0.3.1",   # copied from upstream
    "tzdata; sys_platform == 'win32'",  # copied from upstream
]

[project.scripts]
djorm = "djorm.core.management:execute_from_command_line"

[tool.hatch.version]
path = "djorm/_version.py"

[tool.hatch.build.targets.wheel]
packages = ["djorm"]
```

### 8.2 Version strategy

- The `dj-orm` distribution version tracks the exact upstream Django tag with
  an additional Djorm rebuild component.
- Example: Django 5.2.17 → `dj-orm` 5.2.17.0, then 5.2.17.1 for a Djorm-only rebuild.
- `VERSION` tuple in `djorm/__init__.py` remains the Django format: `(5, 2, X, 'final'/'alpha', N)`.
- Distribution metadata reads `djorm/_version.py`; the retained
  `djorm.__version__` remains the upstream API version.

### 8.3 Console script

The `djorm` console script replaces `django-admin`. It invokes `djorm.core.management.execute_from_command_line()`.

### 8.4 Environment variable

`DJANGO_SETTINGS_MODULE` is **kept unchanged**. The env var is part of Django's operational contract (tooling, deployment scripts, muscle memory) and is not a Python import path, so the namespace rename does not apply. The settings machinery in `djorm/conf/__init__.py` continues to read `DJANGO_SETTINGS_MODULE`.

---

## 9. Upstream Sync Philosophy & Code Layout

### 9.1 Minimal diff surface

The fork's changes over upstream Django fall into exactly these categories:

1. **Mechanical namespace rename** (`django` → `djorm`): done via automated tooling (import-path-aware, not blanket `sed` — see §9.6), applied as a single rebase-able commit.
2. **File/directory deletions**: removing web-framework packages (forms, http, etc.). These are clean deletions — easy to re-apply after a rebase.
3. **Check framework trimming**: removing import lines in `__init__.py` for deleted check modules.
4. **Management command pruning**: deleting command files.
5. **pyproject.toml changes**: package metadata.
6. **Fork-specific glue in `djorm/_ext/`**: any patches that can't be expressed as simple deletions.

`djorm.setup()` is **not** simplified or modified beyond the namespace rename. It remains semantically identical to `django.setup()`. If the URL-prefix or logging code paths become dead/unreachable after subsystem removal, they will be removed in a later pass — but not as part of the initial fork spec.

### 9.2 djorm/_ext/ package

All fork-specific logic that goes beyond mechanical rename or deletion lives in `djorm/_ext/`. This includes:

- `djorm/_ext/__init__.py`
- Any monkey-patches or compatibility shims needed to make stripped-down imports work (e.g., stubbing an import that a retained module makes into a deleted module at runtime).

Upstream-derived modules should **not** be edited with bespoke logic. If a module needs behavioral changes, it should call into `djorm._ext` or the modification should be a minimal, clearly-commented one-liner.

### 9.3 Branch strategy

```
djorm/5.2-lts          ← maintained Djorm release line
release/django-5.2.X ← generated candidate in a separate worktree
upstream/*           ← read-only refs from django/django
```

### 9.4 Rebase workflow

To incorporate a new official LTS tag, run `scripts/apply_django_lts.py` as
documented in `MAINTENANCE.md`. The tool discovers the ordered fork commit
baseline from `.djorm-maintenance.toml`, creates a candidate worktree from the
exact upstream tag, regenerates both trees under the `djorm` namespace, and
applies the reviewed tree delta with a three-way merge. It stops on semantic
conflicts for human review.

### 9.5 Conflict expectations

Most upstream changes will be in files we don't touch (views, admin, templates, etc.) — these conflict-free because we simply delete those files. Conflicts will primarily arise in:

- `djorm/db/` — the core code we care about (low conflict risk since we don't modify internals).
- `djorm/conf/global_settings.py` — upstream may add settings.
- `djorm/core/management/` — upstream may change command infrastructure.
- `djorm/utils/` — upstream may change utilities.

The namespace tree is regenerated rather than replayed from historical paths,
which keeps the largest transformation reproducible.

### 9.6 Namespace rename tooling

**Do not use blanket `sed` over all tokens.** A naive `sed 's/django/djorm/g'` will corrupt comments, documentation strings, license text, locale data, and serialization constants (e.g., `DJANGO_VERSION_PICKLE_KEY`'s string value `"django-version"`).

**Required approach — syntax-aware rewriter (`scripts/rename_namespace.py`):**

Use Python tokenization plus literal parsing so the tool only rewrites:
- `import` statements and `from … import` statements referencing `django.*`.
- Dotted-name string literals that match known module paths (`django.db.*`, `django.conf.*`, etc.).
- Targeted field-level edits in `pyproject.toml` (package name, console script, version attr) — not a blanket replace.

The rewriter must **not** touch:
- `DJANGO_SETTINGS_MODULE` (env var, not a Python path).
- Serialization constants whose *string value* contains `django` (e.g., `"django-version"`).
- Comments, license text, locale `.po` files, or documentation.

**Mandatory post-step:** After every rename pass, run the script's `--check`
mode. It must fail loudly if a rewritable `django` namespace reference remains.

The script (`scripts/rename_namespace.py`) must be checked into the repo and be idempotent so it can be re-run on every upstream rebase.

Blanket search-and-replace is never a supported fallback.

---

## 10. Disagreements / Adjustments

### 10.1 `asgiref` dependency

Django 5.2 uses `asgiref` for async support in the ORM (`QuerySet.aiterator()`, `Model.asave()`, etc.). Even though we remove the ASGI web stack, **`asgiref` is a required dependency** because the async ORM methods depend on `asgiref.sync.sync_to_async`. Dropping async ORM methods would be a massive parity break and is not recommended. The packaging section (§8.1) lists `asgiref` in `dependencies`.

### 10.2 `djorm/core/files/` retention

`FileField` and `ImageField` are ORM field types that depend on `djorm.core.files`. Even though file storage is web-adjacent, these fields are part of the ORM public API. We retain `djorm/core/files/` and `djorm/core/files/storage.py` to keep `FileField`/`ImageField` functional. The `file_storage` and `file_uploads` test directories are still removed since they test the web upload pipeline.

### 10.3 `djorm/utils/translation/` retention

The Django ORM uses `gettext_lazy` and translation utilities throughout model field definitions (`verbose_name`, `help_text`, etc.) and migration files. The translation utility (`djorm/utils/translation/`) must be retained even though we remove the i18n management commands (`makemessages`, `compilemessages`) and the full i18n middleware.

### 10.4 `dumpdata` / `loaddata` / `flush` retention (DB-ops scope)

These are data-management commands that operate on model data and fixtures. They depend on `djorm/core/serializers/` which becomes a permanently in-scope module. This is a deliberate scope expansion from "strict migrations-only" to "DB-ops mode." The rationale and opt-out path are documented in §5.1.

### 10.5 `diffsettings` retention

Nearly zero-cost command useful for debugging settings. No non-ORM dependencies.

### 10.6 `check` management command

Removed as specified. However, users can still run ORM-relevant checks programmatically:

```python
from djorm.core.checks import run_checks, Tags
errors = run_checks(tags=[Tags.models, Tags.database])
```

### 10.7 GeoDjango (`contrib.gis`) deferral

GeoDjango's DB layer (spatial fields, functions, lookups, PostGIS/SpatiaLite backends) is a legitimate ORM feature. However, it requires native C libraries (GEOS, GDAL, PROJ) that make local setup painful — especially on macOS where dynamic linking, `brew` paths, and environment variables are common friction points.

**Decision:** Defer `contrib.gis` to a later milestone. The initial release ships without it. When adding GIS support:

- Keep only the DB layer: `db/`, `geos/`, `gdal/`, `measure.py`, `geometry.py`, `ptr.py`, `management/`, `serializers/`, `utils/`.
- Remove web parts: `admin/`, `feeds.py`, `forms/`, `sitemaps/`, `shortcuts.py`, `static/`, `templates/`, `views.py`.
- Document GEOS/GDAL/PROJ as hard prerequisites.
- Add `gis_tests/` back to the test suite at that point.

This does **not** affect API parity for non-GIS users.

### 10.8 `djorm.setup()` is unchanged

`djorm.setup()` is kept **semantically identical** to `django.setup()` (namespace-only rename). The URL-prefix and logging code paths remain even if they reference modules from deleted subsystems. If those code paths fail at runtime (e.g., because `djorm.urls` was deleted), they should be guarded with try/except in `djorm/_ext/` rather than modifying `setup()` itself. This preserves API parity and avoids subtle edge-case breakage in tests or user code that calls `setup(set_prefix=True)`.

If a future audit proves specific code paths are genuinely dead/unreachable after subsystem removal, they can be removed in a later maintenance pass — but that cleanup is not part of the initial fork spec.
