# djrm library contract

## Status

- Distribution: `djrm`
- Import namespace: `djrm`
- CLI: `djrm`
- Current upstream base: Django 5.2.17
- Current supported LTS line: Django 5.2

This document describes the implemented library. It is not an extraction plan.
The exact upstream tag, commit, and distribution version are recorded in
`.djrm-maintenance.toml`.

## 1. Purpose

`djrm` packages Django's ORM, migrations, database backends, and supporting
infrastructure as a standalone library. It keeps familiar Django database APIs
under the `djrm.*` namespace without installing or exposing a `django`
package.

The supported scope includes:

- models, fields, managers, querysets, expressions, aggregates, constraints,
  indexes, transactions, and raw queries;
- migration detection, writing, execution, squashing, and optimization;
- SQLite, PostgreSQL, MySQL, and Oracle database backends;
- PostgreSQL-specific non-spatial fields, indexes, lookups, constraints, and
  aggregates;
- content types and generic relations;
- app registry, settings, model signals, dispatch, database-oriented system
  checks, serializers, and file-backed model fields;
- database and data-management commands; and
- the ORM-focused test infrastructure used by the retained suite.

The project is not a web framework or geospatial ORM. HTTP handling, URLs,
views, middleware, templates, forms, auth, sessions, admin, caching, static
files, ASGI/WSGI servers, email delivery, and GeoDjango are outside the package
contract.

## 2. Compatibility contract

`djrm` preserves Django 5.2 behavior for the documented ORM, migration, and
database APIs that remain in scope, subject to the explicit exceptions below.
The namespace change is mechanical for supported imports:

| Django 5.2 | djrm |
| --- | --- |
| `from django.db import models` | `from djrm.db import models` |
| `from django.conf import settings` | `from djrm.conf import settings` |
| `from django.db import connection` | `from djrm.db import connection` |
| `from django.apps import AppConfig` | `from djrm.apps import AppConfig` |
| `from django.core.management import call_command` | `from djrm.core.management import call_command` |
| `from django.contrib.postgres.fields import ArrayField` | `from djrm.contrib.postgres.fields import ArrayField` |
| `from django.contrib.contenttypes.fields import GenericForeignKey` | `from djrm.contrib.contenttypes.fields import GenericForeignKey` |

Settings names such as `DATABASES`, `INSTALLED_APPS`,
`DEFAULT_AUTO_FIELD`, and `DATABASE_ROUTERS` are unchanged. Python module
paths inside settings use `djrm.*`; for example, the SQLite engine is
`djrm.db.backends.sqlite3`. The environment variable remains
`DJANGO_SETTINGS_MODULE` because it is an operational name, not a Python
namespace.

### Explicit exceptions

| Surface | Implemented behavior |
| --- | --- |
| Forms | Model fields remain importable. Calling `.formfield()` on a path that requires the removed forms package raises `ImportError: djrm.forms is not available in this fork.` |
| URL script prefix | `djrm.setup(set_prefix=True)` configures logging and apps but skips URL-prefix mutation because URL routing is absent. |
| HTML test assertions | `SimpleTestCase.assertHTMLEqual()` and related HTML parsing paths raise an explicit `HTML parsing is not available in this fork` assertion. |
| HTTP test clients | `Client`, `AsyncClient`, and live-server support are not exported from `djrm.test`. `LiveServerTestCase` is unsupported. |
| Default exception reporter | Logging uses a text traceback fallback when the removed default web reporter is selected. Missing custom reporters are not suppressed. |
| Email delivery | The retained logging handler cannot send through the removed `djrm.core.mail` subsystem. |
| Translation reloader | Translation runtime works; autoreload hooks become no-ops because the development autoreloader is absent. |
| Template translation extraction | `djrm.utils.translation.templatize()` is supported by a private lexical tokenizer. The template rendering engine and `makemessages` command remain absent. |
| Optional database drivers | Backend imports and connections require the corresponding declared extra. |
| GIS | Spatial fields, functions, lookups, adapters, backends, and tests are permanently excluded. |
| Version surfaces | `djrm.__version__` reports the Django API version. Package metadata and `djrm._version.__version__` report the djrm SemVer release. |

An importable name adjacent to a removed web subsystem does not expand this
contract. The exception table is authoritative.

## 3. Supported setup

### Standalone SQLite

```python
import djrm
from djrm.conf import settings

settings.configure(
    DATABASES={
        "default": {
            "ENGINE": "djrm.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    },
    DEFAULT_AUTO_FIELD="djrm.db.models.BigAutoField",
    INSTALLED_APPS=["myapp"],
)
djrm.setup()

from myapp.models import MyModel

MyModel.objects.create(name="hello")
```

### Multiple databases

```python
settings.configure(
    DATABASES={
        "default": {
            "ENGINE": "djrm.db.backends.postgresql",
            "NAME": "primary",
        },
        "replica": {
            "ENGINE": "djrm.db.backends.postgresql",
            "NAME": "replica",
        },
    },
    DATABASE_ROUTERS=["myapp.routers.ReadReplicaRouter"],
    INSTALLED_APPS=["myapp"],
)
```

### Migrations

```python
from djrm.core.management import call_command

call_command("makemigrations", "myapp")
call_command("migrate")
```

```bash
djrm makemigrations myapp
djrm migrate
djrm showmigrations
```

## 4. Included runtime surface

### Core packages

| Package | Contract |
| --- | --- |
| `djrm.apps` | App registry and `AppConfig` |
| `djrm.conf` | Lazy settings and global defaults |
| `djrm.db` | ORM, migrations, connections, routers, transactions, and backends |
| `djrm.dispatch` | Signals and receiver decorator |
| `djrm.core.checks` | Registry plus command, database, and model checks |
| `djrm.core.management` | Command framework and retained commands |
| `djrm.core.serializers` | Python, JSON, JSONL, XML, and optional YAML serializers |
| `djrm.core.files` | Storage support required by `FileField` and `ImageField` |
| `djrm.core.validators` | Validators used by model fields |
| `djrm.contrib.contenttypes` | Content types and generic relations |
| `djrm.contrib.postgres` | Non-spatial PostgreSQL extensions |
| `djrm.test` | ORM-oriented `SimpleTestCase`, `TransactionTestCase`, and `TestCase` support |
| `djrm.utils` | Utility modules retained by the supported runtime |
| `djrm._ext` | Small, tested fork-specific boundary helpers |

Compiled translation catalogs are included. Source `.po` catalogs and
translation-authoring commands are excluded.

Default settings still contain dormant values for removed Django subsystems.
They do not make those subsystems available.

### Retained management commands

- `dbshell`
- `diffsettings`
- `dumpdata`
- `flush`
- `inspectdb`
- `loaddata`
- `makemigrations`
- `migrate`
- `optimizemigration`
- `showmigrations`
- `sqlflush`
- `sqlmigrate`
- `sqlsequencereset`
- `squashmigrations`

The `check` command is not shipped. ORM checks remain available through:

```python
from djrm.core.checks import Tags, run_checks

errors = run_checks(tags=[Tags.models, Tags.database])
```

`Tags` retains Django's public constants even when a removed subsystem has no
registered checks.

### Extras

| Extra | Purpose |
| --- | --- |
| `djrm[images]` | Pillow for image fields |
| `djrm[mysql]` | MySQL driver |
| `djrm[oracle]` | Oracle driver |
| `djrm[postgresql]` | Psycopg 3 |
| `djrm[postgresql-legacy]` | Psycopg 2 |
| `djrm[yaml]` | YAML serializer |

## 5. Excluded runtime surface

The following package families are maintained deletions:

- `djrm.forms`, `djrm.http`, `djrm.middleware`, `djrm.template`,
  `djrm.templatetags`, `djrm.urls`, and `djrm.views`;
- web handlers, servers, mail, cache, pagination, ASGI, and WSGI modules under
  `djrm.core`;
- admin, auth, GIS, messages, sessions, sites, static files, and other web
  applications under `djrm.contrib`; and
- Django's documentation site, JavaScript toolchain, project templates, and
  web-only test suites.

There is no compatibility `django` package and no spatial backend alias.

## 6. Validation contract

### Local suite

```bash
make check
make test
make coverage
```

`make test` runs the fork smoke tests and the complete retained SQLite suite.
The source distribution contains the runner, settings, fixtures, and retained
tests, so the same target runs from an unpacked sdist.

`make coverage` enforces three baselines:

- 63% global branch coverage for retained packaged source;
- 65% aggregate coverage for every executable-AST-different common runtime
  file; and
- 44% aggregate coverage for fork glue and maintenance/release tooling.

The percentages are review baselines, not claims that optional backend branches
are fully line-covered.

### External databases

```bash
make test-external
```

The Docker matrix creates disposable PostgreSQL, MySQL, and Oracle servers and
also exercises SQLite. It verifies model creation, migrations, complex queries,
transactions, introspection, backend-specific behavior, and real
`dbshell` client invocation. The harness tears down containers, volumes, and
locally built images.

External database testing is required:

- by the guarded local tag helper;
- by the exact-tag GitHub workflow before a draft release;
- before TestPyPI publication; and
- again from the exact release tag before PyPI publication.

### Artifacts

`make build` removes only `dist/` before building. Artifact inspection
requires one wheel and one sdist, verifies excluded namespaces and catalogs,
checks lowercase tracked path spelling, checks the retained test suite in the
sdist, and installs the wheel in isolation.

## 7. Upstream maintenance

`scripts/apply_django_lts.py` is the supported update mechanism. It:

1. accepts an exact final Django tag from a configured LTS series;
2. verifies the official upstream tag and source checkout;
3. creates a candidate worktree and mechanically rewrites the namespace;
4. reapplies the reviewed fork tree delta with a three-way merge;
5. prunes maintained deletions, including new files under deleted directories;
6. stops on retained semantic conflicts;
7. updates provenance and SemVer; and
8. runs the complete package gate before finalizing the candidate.

`scripts/rename_namespace.py` performs syntax-aware import and module-string
rewrites. Blanket search-and-replace is unsupported.

`.djrm-upstream-delta.toml` is the machine-readable review baseline.
`scripts/audit_upstream_delta.py` reports byte differences, raw AST
differences, executable AST differences, fork-only paths, and upstream-only
paths. It fails when:

- an executable AST path leaves or enters the allowlist;
- byte, AST, or non-AST difference counts increase;
- the exact upstream tag or commit changes; or
- fork-only or pruned upstream path sets change.

An LTS update that intentionally changes the report requires human review,
followed by:

```bash
uv run python scripts/audit_upstream_delta.py --write-baseline
```

The next `make check` must pass with that reviewed baseline. This keeps the
application mechanical while preventing a new upstream file or wider patch
surface from being accepted silently.

Physical checkout spelling is separately checked against `git ls-files` so a
case-insensitive workstation cannot build a differently cased source archive.

## 8. Versioning and releases

`djrm` uses SemVer:

- `0.x` corresponds to Django 5.2 LTS;
- `1.x` corresponds to Django 6.2 LTS; and
- each later reviewed Django LTS receives the next djrm major.

Within one LTS line:

- a new upstream Django patch increments the djrm minor and resets patch to
  zero; and
- a djrm-only fix on the same Django tag increments the patch.

The exact Django tag remains in maintenance metadata and release notes instead
of being encoded in the distribution version.

Release tags are `vX.Y.Z`. GitHub Actions builds and inspects exact-tag
artifacts, creates a draft GitHub release, and publishes only through protected
TestPyPI/PyPI workflows using repository secrets.

## 9. Source of truth

When documentation and automation differ, these files are authoritative in
order:

1. `.djrm-maintenance.toml` for upstream provenance and version mapping;
2. `.djrm-upstream-delta.toml` for the reviewed fork surface;
3. `pyproject.toml` for packaging, dependencies, extras, and coverage targets;
4. `Makefile` and `.github/workflows/` for validation and release gates; and
5. this specification for the supported public contract.
