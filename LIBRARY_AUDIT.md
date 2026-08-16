# djrm Library Audit

<!-- markdownlint-disable MD013 -->

- **Audit status:** Three passes complete
- **Snapshot time:** 2026-08-16 13:41:34 EDT
- **Repository:** `viseshrp/djrm`
- **Branch:** `main`
- **Audited commit:** `63b492251e940222accfaf6aa18b98b6fe2f0d5a`
- **Remote state before this report was added:** clean and identical to `origin/main`
- **Exact upstream base:** Django `5.2.17`, commit
  `e802ada38b3ecf345915163bb6d7f008be411664`
- **Published release:** [`djrm 0.1.1` on PyPI](https://pypi.org/project/djrm/0.1.1/),
  [`v0.1.1` on GitHub](https://github.com/viseshrp/djrm/releases/tag/v0.1.1),
  and [0.1.1 on TestPyPI](https://test.pypi.org/project/djrm/0.1.1/)

## Executive conclusion

The retained ORM library is operationally healthy for its intended database
scope. The complete retained SQLite suite passes, the supported Python matrix
passes, isolated wheel installation passes, and the new Docker gate passes
against SQLite, PostgreSQL 17, MySQL 8.4, and Oracle 23. The package contains no
`django` compatibility namespace, no GeoDjango package, no spatial backend
hooks, and no gettext source catalogs.

The audit does **not** conclude that every retained public API has Django-identical
semantics. One exported translation helper is broken, several retained test
helpers are deliberately nonfunctional, and form-related methods deliberately
raise when the removed forms framework is requested. The specification's broad
parity statement therefore exceeds the implementation's real contract.

No configured validation gate was failing at the final snapshot, but six
material follow-ups remain:

1. Resolve the broken exported `djrm.utils.translation.templatize()` path.
2. Rewrite `SPEC.md` as an implemented contract rather than a provisional
   extraction plan.
3. Decide whether the source distribution must be able to run the documented
   retained test suite; it currently cannot.
4. Reduce or explicitly accept 443 formatting/comment-only maintained deltas
   that increase future tree-delta merge risk.
5. Enforce the external database gate in remote tag CI, not only in the local
   tag helper.
6. Resolve the platform-dependent sdist path casing before treating local and
   Linux builds as reproducible.

## Post-audit remediation

All nine findings were addressed on `main` after the immutable
`63b492251e` audit snapshot. The detailed findings below remain unchanged as
evidence of what the audit observed; this table records their disposition.

| ID | Status | Remediation |
| --- | --- | --- |
| F1 | Resolved | `templatize()` now uses a private minimal lexer and matches Django 5.2.17 on inline, plural, verbatim, comment, and error-path inputs. |
| F2 | Resolved | `SPEC.md` now defines ORM/database compatibility plus an explicit exception table for forms, setup, test helpers, logging, translation reload, optional drivers, versions, and GIS. |
| F3 | Resolved | `.djrm-upstream-delta.toml` records the intended executable-AST path allowlist, count ceilings, and fork/upstream-only path digests. `make check` regenerates and validates the report. |
| F4 | Resolved | The sdist includes `tests/runtests.py`, `tests/test_sqlite.py`, fixtures, settings, smoke tests, E2E tests, and the complete retained suite. |
| F5 | Resolved | Exact-tag CI gates draft releases on `make test-external`; TestPyPI and production PyPI workflows independently rerun it before publication. |
| F6 | Resolved | Coverage now fails below 63% globally, 65% for modified common runtime files, or 44% for fork tooling. Measured remediation values were 63.32%, 66.82%, and 45.38%. |
| F7 | Resolved | Retained check imports are mandatory, and removed-subsystem fallbacks inspect `ModuleNotFoundError.name`; unexpected dependencies and missing custom reporters propagate. |
| F8 | Resolved | `make build` has a narrow `clean-dist` prerequisite and always produces exactly one version's artifacts. |
| F9 | Resolved | The physical macOS path now matches tracked lowercase spelling. A tracked-versus-physical casing gate and sdist inspection prevent recurrence. |

The 443 non-AST byte differences were explicitly accepted rather than silently
ignored. The reviewed split is now 158 package and 285 test differences.
Any increase fails the delta gate, while a decrease remains allowed.

## Severity model

| Level | Meaning in this audit |
| --- | --- |
| High | A retained public contract is broken or materially misleading. |
| Medium | Release, maintenance, reproducibility, or regression risk that should be planned. |
| Low | Defensive hardening or cleanup with limited present impact. |
| Note | Verified behavior, deliberate trade-off, or observation with no required change. |

## Findings summary

| ID | Severity | Finding | Current effect |
| --- | --- | --- | --- |
| F1 | High | `templatize()` is exported but imports the deleted template engine. | A retained public translation call raises `ModuleNotFoundError`. |
| F2 | High | `SPEC.md` promises identical semantics for every API in retained modules. | The promise is false for translation, forms, setup, and test-helper edges. |
| F3 | Medium | 443 common source/test files differ only in non-AST text. | The byte-level tree-delta updater carries avoidable merge-conflict surface. |
| F4 | Medium | The sdist omits `tests/runtests.py`, `tests/test_sqlite.py`, and the retained suite. | `make test` cannot run from the sdist even though the sdist ships that instruction. |
| F5 | Medium | External DB testing is enforced by `scripts/tag_release.sh`, not remote tag CI. | A manually pushed tag can bypass PostgreSQL/MySQL/Oracle validation. |
| F6 | Medium | Coverage is 63.43% and informational; optional backends are mostly uncovered by coverage. | Green CI does not imply a configured coverage floor or line-level backend coverage. |
| F7 | Low | Broad `ImportError` guards can hide internal defects. | A broken retained check/reporter import can be mistaken for an intentionally absent subsystem. |
| F8 | Low | Build targets do not clear `dist/` before producing artifacts. | Multiple versions make `make inspect-dist` fail and require an explicit clean step. |
| F9 | Medium | macOS and Linux sdists from the exact commit contain different PR-template path casing. | Exact-commit source archives are not content-reproducible across the audited environments. |

## Three-pass method

### Pass 1: Structural and provenance audit

This pass established what exists, what was removed, and what differs from the
exact upstream tag.

- Resolved the renamed checkout from the stale `djo` path to the live `djrm`
  repository.
- Verified the local branch, remote branch, upstream remote, exact upstream tag,
  upstream commit, release tag target, GitHub release, and PyPI release.
- Compared the tracked `djrm/` and `tests/` trees with a namespace-normalized
  Django 5.2.17 tree.
- Counted common, removed, and fork-only paths.
- Compared common Python files at three levels: bytes, parsed AST, and AST after
  docstrings were removed.
- Inventoried retained packages, commands, checks, utilities, test directories,
  compiled locale assets, and packaging metadata.
- Searched tracked source and built archives for old distribution names,
  `django/` package residue, GIS packages, spatial backend hooks, and `.po`
  catalogs.

### Pass 2: Behavioral and artifact audit

This pass tested the retained library as a user and maintainer would use it.

- Ran maintained quality, lock, audit, formatting, type, spelling, and security
  checks.
- Ran 59 fork smoke tests and 5,530 retained ORM tests.
- Ran the suite across Python 3.10, 3.11, 3.12, 3.13, and 3.14.
- Generated branch coverage and inspected the uncovered concentration.
- Imported every discoverable retained module after app setup.
- Probed removed namespaces, lazy forms failures, translation, test helpers,
  setup behavior, version surfaces, and CLI behavior.
- Built wheel and sdist artifacts, checked metadata, inspected archive contents,
  and installed the wheel in an isolated environment.
- Ran the Docker database matrix, complex ORM exercises, migration flow,
  introspection, transactions, and each real `dbshell` client.

### Pass 3: Adversarial contract and release audit

This pass looked for statements or gates that could appear green while hiding a
real defect.

- Compared `SPEC.md`, `README.md`, `MAINTENANCE.md`, `CHANGELOG.md`, Make targets,
  workflows, and release scripts against observed behavior.
- Tested retained APIs that sit next to removed subsystems.
- Checked whether source artifacts can reproduce the documented validation.
- Tested stale-artifact behavior in `dist/`.
- Checked whether external DB validation can be bypassed by a direct remote tag.
- Followed live CI and re-ran checks after concurrent repository changes landed.
- Separated resolved during-audit issues from findings still present at the final
  snapshot.

## Snapshot and provenance

### Git state

At the final snapshot, both local and remote `main` pointed at:

```text
63b492251e940222accfaf6aa18b98b6fe2f0d5a
[release] Prepare djrm 0.1.1
```

The seven commits after the published `v0.1.0` release commit are:

```text
2ce821d216 [fix] Decouple PostgreSQL fields from removed forms
d15b4f8bc0 [scope] Remove residual GIS runtime hooks
82e407e203 [docs] Make GIS exclusion permanent
489b09c08b [test] Add Docker database end-to-end matrix
348b7a0c41 [test] Fix SQLPlus wrapper lint
e72cadce4b [release] Enforce external database tag gate
63b492251e [release] Prepare djrm 0.1.1
```

The published `v0.1.0` tag peels to release commit
`a600ca9c37eef50bce4d67ec4b05c0ff1f1a1ed3`. Its two published assets match
PyPI:

| Artifact | SHA-256 | Bytes |
| --- | --- | ---: |
| `djrm-0.1.0-py3-none-any.whl` | `466a953c0e5e6549d776edbf1c73599e73c61e7e361df6691cfbd6911a1c7e72` | 1,976,442 |
| `djrm-0.1.0.tar.gz` | `48062c95bd65360906c98b09f71e7965589d569fb6d70bd35df90ca9fbf3f9e6` | 1,615,872 |

At final snapshot time, the remote annotated `v0.1.1` tag peeled to audited
commit `63b492251e940222accfaf6aa18b98b6fe2f0d5a`. The exact-tag Main workflow
passed, the GitHub release was published at 2026-08-16 17:37:59 UTC, and the
protected production workflow completed successfully. TestPyPI and production
PyPI both serve the Linux-built 0.1.1 artifact pair recorded later in this
report.

### Upstream freshness

`.djrm-maintenance.toml` records Django `5.2.17` and exact commit
`e802ada38b3ecf345915163bb6d7f008be411664`. The official
[Django downloads page](https://www.djangoproject.com/download/) identifies
5.2.17 as the current 5.2 LTS patch and lists extended support through April
2028. The audited base was therefore current at snapshot time.

### Version surfaces

The dual-version behavior is intentional and implemented:

| Surface | Value | Meaning |
| --- | --- | --- |
| Wheel metadata / `importlib.metadata.version("djrm")` | `0.1.1` | djrm distribution version |
| `djrm._version.__version__` | `0.1.1` | djrm build version source |
| `djrm.__version__` | `5.2.17` | retained upstream Django API version |
| `djrm.VERSION` | `(5, 2, 17, "final", 0)` | retained upstream version tuple |
| `djrm --version` | `5.2.17` | retained management CLI behavior |

This is documented in `SPEC.md` section 8.2. Consumers must use distribution
metadata, not `djrm.__version__`, when they need the djrm release version.

## What is retained

### Quantitative package inventory

The runtime package contains 705 tracked files: 439 Python files, 265 compiled
`.mo` catalogs, and one remaining non-Python/non-`.mo` package file. The Python
source totals 81,871 lines.

| Package area | Files | Python files | Python lines | Retained role |
| --- | ---: | ---: | ---: | --- |
| root package files | 3 | 3 | 40 | Setup, CLI module, and distribution version |
| `_ext` | 3 | 3 | 47 | Fork-specific forms/setup helpers |
| `apps` | 3 | 3 | 710 | App configuration and registry |
| `conf` | 269 | 171 | 4,301 | Settings and compiled locale formats/catalogs |
| `contrib` | 204 | 37 | 4,081 | Content types and PostgreSQL extensions |
| `core` | 53 | 53 | 9,499 | Checks, management, serializers, files, validation |
| `db` | 122 | 122 | 50,997 | ORM, migrations, schema editors, database backends |
| `dispatch` | 3 | 2 | 480 | Signal dispatcher |
| `test` | 5 | 5 | 4,189 | Retained database-oriented test helpers |
| `utils` | 40 | 40 | 7,527 | Transitive ORM/management utilities |
| **Total** | **705** | **439** | **81,871** | |

### Core runtime

The following are retained as first-class library scope:

- App registry and `AppConfig` support under `djrm.apps`.
- Lazy and configured settings infrastructure under `djrm.conf`.
- Model base classes, managers, querysets, lookups, transforms, expressions,
  functions, aggregates, window functions, constraints, indexes, generated
  fields, composite primary keys, JSON fields, file fields, and relation fields.
- The full migration graph, loader, executor, autodetector, optimizer, recorder,
  operations, state model, schema editors, and migration writer.
- Connection handling, routers, transaction management, query logging, database
  exceptions, backend feature flags, and backend operations.
- Base, dummy, SQLite, PostgreSQL, MySQL, and Oracle backends.
- Model lifecycle and migration signals plus the generic dispatch framework.
- Model serialization in Python, JSON, JSONL, XML, and YAML when its optional
  dependency is installed.
- Content types, `GenericForeignKey`, and `GenericRelation`.
- PostgreSQL arrays, hstore, ranges, indexes, constraints, lookups, aggregates,
  search, operations, and related field/function support.
- `FileField` and `ImageField` support, including core file abstractions and
  optional Pillow support.
- Async ORM entry points through the retained `asgiref` dependency.

### Retained management commands

Exactly 14 built-in commands remain:

```text
dbshell
diffsettings
dumpdata
flush
inspectdb
loaddata
makemigrations
migrate
optimizemigration
showmigrations
sqlflush
sqlmigrate
sqlsequencereset
squashmigrations
```

This is deliberately broader than migrations alone. Fixture serialization,
database reset, inspection, raw SQL generation, and settings inspection remain
part of the maintained DB-operations contract.

### Retained checks

The check registry and six files remain:

```text
djrm/core/checks/__init__.py
djrm/core/checks/commands.py
djrm/core/checks/database.py
djrm/core/checks/messages.py
djrm/core/checks/model_checks.py
djrm/core/checks/registry.py
```

`Tags` still exposes compatibility constants for `admin`, `async_support`,
`caches`, `commands`, `compatibility`, `database`, `files`, `models`, `security`,
`signals`, `sites`, `staticfiles`, `templates`, `translation`, and `urls`.
Removed subsystems simply do not register handlers for most of those tags.

### Retained utilities

The actual retained `djrm.utils` inventory is:

```text
__init__.py        _os.py             asyncio.py         choices.py
connection.py      crypto.py          datastructures.py  dateformat.py
dateparse.py       dates.py           deconstruct.py     decorators.py
deprecation.py     duration.py        encoding.py        formats.py
functional.py      hashable.py        html.py            http.py
inspect.py         ipv6.py            itercompat.py      log.py
module_loading.py  numberformat.py    regex_helper.py    safestring.py
termcolors.py      text.py            timesince.py       timezone.py
translation/       tree.py            version.py         xmlutils.py
```

`translation/` contains six Python files. Compiled runtime catalogs are retained
even though authoring commands and `.po` source files are removed.

### Retained tests

The tracked test tree contains 865 files, including 832 Python files and 108,616
Python lines. It has 116 top-level test directories/packages when the fork smoke
and E2E packages are included.

The retained suite covers ORM construction and querying, migration behavior,
schema changes, backend behavior, transactions, multi-database routing,
serialization, content types, PostgreSQL extensions, signals, field behavior,
constraints, indexes, database shell behavior, introspection, app loading,
settings, utilities, and the retained check framework.

Fork-specific validation now includes:

- Three `tests/djrm_smoke` files.
- Fourteen tracked `tests/e2e` files.
- Docker services for PostgreSQL 17.11, MySQL 8.4.10, and Oracle Free 23.26.1.
- An SQLite control run in the same E2E scenario.
- Migration, aggregate, subquery, window, JSON, update, transaction, uniqueness,
  locking, introspection, and database-shell exercises.
- A runtime assertion that `djrm.contrib.gis` remains unavailable.

### Packaging and maintenance infrastructure

The following operational surfaces are retained:

- Hatchling builds with a dynamic version from `djrm/_version.py`.
- Python 3.10 through 3.14 metadata and CI.
- Required dependencies copied from Django 5.2: `asgiref`, `sqlparse`, and
  Windows-only `tzdata`.
- Optional extras for Pillow, MySQL, Oracle, Psycopg 3, Psycopg 2, and PyYAML.
- A `djrm` console script mapped to the management dispatcher.
- Ruff, ty, Bandit, pip-audit, codespell, markdown, and pre-commit checks.
- Tox environments for all supported Python versions.
- GitHub Actions for quality, test matrix, macOS/Windows smoke portability,
  package inspection, CodeQL, release creation, TestPyPI, and PyPI.
- The tree-delta LTS updater, namespace rewriter, release validator, artifact
  inspector, and guarded tag helper.
- Exact upstream provenance in `.djrm-maintenance.toml`.

## What is intentionally left out

### Entire runtime subsystems

The following upstream Django packages are absent by design:

```text
forms/
http/
middleware/
template/
templatetags/
urls/
views/
shortcuts.py
```

The following `core` areas are absent:

```text
core/cache/
core/handlers/
core/mail/
core/servers/
core/asgi.py
core/paginator.py
core/wsgi.py
```

The absent functionality includes HTTP request/response handling, URL routing,
templates, forms/rendering, middleware, cache framework, email, pagination,
ASGI/WSGI handlers, the development server, view shortcuts, and project/app
scaffolding.

### Contrib packages

Only `contenttypes` and `postgres` remain. The following are absent:

```text
admin          admindocs      auth           flatpages
gis            humanize       messages       redirects
sessions       sitemaps       sites          staticfiles
syndication
```

Within retained contrib packages, web-facing pieces are also removed:

- `contenttypes`: admin registration, forms, and views.
- `postgres`: forms, widget templates, and Jinja templates.
- Both: gettext source catalogs that are unnecessary at runtime.

### GeoDjango and spatial hooks

GeoDjango is fully excluded, not merely unadvertised:

- No `djrm.contrib.gis` package.
- No `gis_tests` retained suite.
- No SpatiaLite schema/editor feature branch.
- No PostGIS adapter registration.
- No Oracle Spatial feature flags.
- No spatial field, lookup, function, aggregate, serializer, widget, or native
  library integration.
- Wheel and sdist inspection explicitly reject `djrm/contrib/gis`.
- The updater treats GIS package and test paths as maintained deletions.

Current tracked runtime source contains no residual GIS/spatial hook. The only
GIS strings in the fork-specific test layer are assertions that GIS stays
absent.

### Removed management commands

Exactly 11 upstream built-ins are absent:

```text
check
compilemessages
createcachetable
makemessages
runserver
sendtestemail
shell
startapp
startproject
test
testserver
```

### Removed check modules

The following check registrations are absent:

- Async/ASGI checks.
- Cache checks.
- Compatibility checks, including the Django 4.0 compatibility module.
- File subsystem checks.
- Security checks.
- Template checks.
- Translation checks.
- URL checks.

### Removed utilities

Five upstream utility files are absent:

```text
archive.py
autoreload.py
cache.py
feedgenerator.py
lorem_ipsum.py
```

### Removed upstream repository material

The standalone repository does not retain Django's complete documentation site,
JavaScript/browser tooling, web tests, maintainer release tooling, benchmark
material, project templates, or the full upstream repository history as active
package material. The retained legal attribution files remain.

## Quantified upstream delta

### Raw Git delta

Compared directly with upstream commit
`e802ada38b3ecf345915163bb6d7f008be411664`, the audited commit reports:

```text
6,700 files changed
15,439 insertions
882,655 deletions
```

That raw result is dominated by the namespace relocation and deliberate tree
pruning. The normalized comparison below is more useful.

### Namespace-normalized package comparison

| Metric | Count |
| --- | ---: |
| Current tracked package files | 705 |
| Upstream package files | 3,660 |
| Common relative paths | 701 |
| Deliberately removed upstream paths | 2,959 |
| Fork-only paths | 4 |
| Byte-identical common files | 511 |
| Byte-different common files | 190 |
| Common Python files | 435 |
| AST-identical common Python files | 404 |
| AST-different common Python files | 31 |
| Executable-AST-different files after docstring stripping | 29 |

The four fork-only runtime paths are:

```text
djrm/_ext/__init__.py
djrm/_ext/forms.py
djrm/_ext/setup_helpers.py
djrm/_version.py
```

### Removed package paths by top-level area

| Upstream area | Removed files |
| --- | ---: |
| `contrib` | 2,595 |
| `conf` | 114 |
| `forms` | 105 |
| `core` | 54 |
| `views` | 28 |
| `template` | 27 |
| `middleware` | 9 |
| `urls` | 7 |
| `templatetags` | 6 |
| `utils` | 5 |
| `http` | 5 |
| `test` | 3 |
| `shortcuts.py` | 1 |
| **Total** | **2,959** |

The largest second-level deletion groups are `contrib/admin` (594),
`contrib/gis` (328), `contrib/auth` (235), `contrib/sessions` (213),
`contrib/sites` (207), `contrib/admindocs` (204), `contrib/flatpages` (203),
`contrib/redirects` (202), `contrib/humanize` (196), `conf/locale` source files
(98), web-facing/source-locale portions of `contrib/contenttypes` (98), and
web-facing/source-locale portions of `contrib/postgres` (78).

### Namespace-normalized test comparison

| Metric | Count |
| --- | ---: |
| Current tracked test files | 865 |
| Upstream test files | 2,493 |
| Common relative paths | 848 |
| Removed upstream paths | 1,645 |
| Fork-only paths | 17 |
| Byte-identical common files | 546 |
| Byte-different common files | 302 |
| Common Python files | 818 |
| AST-identical common Python files | 800 |
| AST-different common Python files | 18 |
| Executable-AST-different files after docstring stripping | 17 |

The 17 fork-only test paths are the three smoke files and the fourteen E2E
files. They are enumerated in Appendix C.

## Maintained semantic divergence

### Executable source differences

After normalizing `django` to `djrm`, 29 common package files have an executable
AST difference from Django 5.2.17. They fall into these intentional categories:

1. Guard `setup(set_prefix=True)` when the URL subsystem is absent.
2. Defer forms failures until a user explicitly asks a field for a form field.
3. Remove GIS, SpatiaLite, PostGIS adapter, and Oracle Spatial hooks.
4. Remove web checks and management commands from registration/discovery.
5. Adapt backend test metadata and SQLite test-database cloning to the retained
   suite.
6. Adapt test infrastructure around deleted HTTP clients, HTML parsing, live
   servers, mail, and templates.
7. Provide logging and translation-reloader fallbacks when web modules are
   absent.

Appendix A lists all 29 files.

### Nonsemantic byte drift

The AST comparison found a larger byte-level maintenance surface:

- 190 common package files are byte-different, but only 31 are AST-different.
  Therefore 159 package files differ only in comments, formatting, literal
  spelling that parses identically, encoding details, or other non-AST text.
- 302 common test files are byte-different, but only 18 are AST-different.
  Therefore 284 test files have the same category of drift.
- Combined non-AST byte drift: **443 files**.

AST identity is a useful maintenance heuristic, not proof of semantic identity;
runtime can observe source text, line numbers, and some literal representation
details. Even with that caveat, 443 files are a substantial byte-level delta for
an updater that reapplies a reviewed tree delta with a three-way merge.

This conflicts with `SPEC.md` section 9's description of an almost exclusively
mechanical rename/deletion model. Either normalize these files back toward the
generated upstream tree or document the wider maintained patch surface and its
expected conflict cost.

## Detailed findings

### F1 — Exported `templatize()` is broken

**Severity:** High
**Location:** `djrm/utils/translation/__init__.py` and
`djrm/utils/translation/template.py`

`djrm.utils.translation.templatize` remains exported. Calling it lazily imports
`djrm.utils.translation.template`, which imports `Lexer` and `TokenType` from
the deliberately deleted `djrm.template.base` module.

Observed result:

```text
ModuleNotFoundError: No module named 'djrm.template'
```

This was the only non-driver failure in an exhaustive configured import sweep.
The module sweep discovered 439 modules and imported 430. Eight failures were
expected because the local environment did not install MySQL or Oracle drivers;
the ninth was `djrm.utils.translation.template`.

Recommended decision:

1. If `templatize()` belongs to the retained translation contract, move or
   reproduce its minimal lexer dependency outside the deleted template engine
   and add a direct smoke test.
2. If it is web-only, remove it from the retained public surface and explicitly
   document the exception to Django parity.

Leaving an exported call that always fails is the least clear option.

### F2 — The public parity statement is broader than reality

**Severity:** High
**Location:** `SPEC.md` sections 2, 4, 7, 9, and 10

`SPEC.md` says every public API in retained modules has identical semantics and
that the only difference is the top-level namespace. Current implementation
requires several deliberate exceptions:

- `templatize()` fails because its template dependency was removed.
- Standard and PostgreSQL model field `formfield()` paths raise the fork's
  documented forms-unavailable `ImportError` when invoked.
- `djrm.setup()` delegates URL-prefix handling to a fork helper and skips it when
  URL routing is absent; this is not identical to upstream setup behavior.
- `SimpleTestCase.assertHTMLEqual()` remains reachable but always fails with
  `HTML parsing is not available in this fork.`
- `LiveServerTestCase` remains defined in `djrm.test.testcases`, depends on
  deleted web infrastructure, and is intentionally not exported from
  `djrm.test`.
- Logging and translation reloader paths use fork-specific absence fallbacks.

The same document still uses planning language such as "likely needed," "keep
conditionally," "during implementation," "if it has any ORM-relevant checks,"
and "will need." It also names PostgreSQL, MySQL, and Oracle `tests/test_*.py`
settings files that do not exist; the implemented cross-backend path is now
`make test-external`.

Recommended action: convert `SPEC.md` from extraction plan to precise current
contract. Define parity as the retained ORM/database surface plus an explicit
exception table. Do not claim parity merely because a class or function name is
still importable.

### F3 — Tree-delta maintenance surface is larger than specified

**Severity:** Medium
**Location:** namespace-normalized common package and test paths

The 443 non-AST byte differences described above are carried by the tree-delta
updater even though they do not represent the 29 source and 17 test executable
AST adaptations. Every extra byte delta can become a conflict when the next
Django LTS patch changes the same region.

Recommended action:

- Generate a machine-readable allowlist of intended executable source deltas.
- Normalize unrelated files to the regenerated upstream tree.
- Add an audit command that reports common byte differences, AST differences,
  and new upstream files in pruned directories before accepting a candidate.
- Treat an unexpected increase in any of those counts as review-required drift.

### F4 — The sdist cannot run its documented full test target

**Severity:** Medium
**Location:** `pyproject.toml` sdist include list and shipped `Makefile`

The 0.1.1 sdist contains smoke tests and E2E tests, but it does not
contain:

```text
tests/runtests.py
tests/test_sqlite.py
the 848 retained upstream-relative test files
```

The sdist ships `README.md`, `MAINTENANCE.md`, and `Makefile`, all of which make
`make test` part of the normal validation path. From an unpacked sdist,
`make test-upstream` cannot start because its runner and settings module are
missing.

This is not a wheel defect; wheels normally exclude tests. It is a source
artifact reproducibility/documentation mismatch.

Recommended decision:

- Include the retained runner/settings/suite in the sdist, or
- Change source-artifact instructions to a target the sdist actually contains,
  and explicitly state that full repository validation requires a Git checkout.

### F5 — External database release testing can be bypassed remotely

**Severity:** Medium
**Location:** `scripts/tag_release.sh`, `.github/workflows/main.yml`, and
`.github/workflows/release.yml`

The guarded local tag command now runs:

```text
make check
make test
make test-external
make build
make check-dist
make inspect-dist
```

That is a strong local release path. However:

- The GitHub Main workflow does not run `make test-external` on a pushed tag.
- The release workflow does not run it before TestPyPI or PyPI publication.
- A maintainer can push a tag directly without using `make tag`.

Therefore the external DB gate is policy-enforced by the helper script, not
server-enforced by release CI. A direct tag can reach draft-release packaging
after only SQLite tests.

Recommended action: add a tag-only external database job and make package/draft
release depend on it. If hosted Oracle is too expensive or unreliable, define a
protected manual environment approval or attach a signed/result artifact from a
required external run. The remote release path should be able to prove the gate
ran for the exact tag commit.

### F6 — Coverage is informative, not a gate

**Severity:** Medium
**Location:** `codecov.yml`, coverage configuration, and Main workflow

Observed packaged-source branch coverage:

```text
39,052 statements
13,518 missed statements
13,482 branches
1,072 partial branches
63.43% total coverage
```

Coverage is uploaded from Python 3.14 but thresholds are informational. Locale
format modules, optional driver branches, and much of PostgreSQL/MySQL/Oracle
support remain uncovered in this metric because the coverage run uses SQLite.
The E2E matrix adds real behavioral confidence but does not currently contribute
to the coverage report.

Recommended action: first establish a stable baseline and path-specific targets
for fork glue and modified common files. A blunt high global threshold would be
misleading because retained upstream optional-backend code is environment
dependent.

### F7 — Broad absence guards may hide real import defects

**Severity:** Low
**Locations:** `djrm/core/checks/__init__.py` and `djrm/utils/log.py`

The checks package uses a helper that catches broad `ImportError` while importing
optional retained check modules. The logging fallback also catches broad
`ImportError` around reporter/mail integration.

This supports a stripped distribution, but it cannot distinguish:

- The intended missing top-level web subsystem.
- A new missing dependency inside a retained module.
- A typo or refactor defect inside that module.

Recommended action: catch only the expected missing module name, or inspect
`ModuleNotFoundError.name` before suppressing it. Re-raise unexpected import
failures.

### F8 — Stale artifacts make the standard build sequence fail

**Severity:** Low
**Location:** `Makefile` build and artifact targets

`make build` appends artifacts to `dist/`; it does not clear old versions.
`make check-dist` accepts all matching files, but `make inspect-dist` requires
exactly one wheel and one sdist. During this audit, retaining 0.1.0 artifacts and
building 0.1.1 produced:

```text
ERROR: Expected one *.whl artifact, found 2.
```

This fails safely before tagging, but the documented sequence is not repeatable
after a version bump unless the maintainer knows to run `make clean` first.

Recommended action: make the release/tag path build into a fresh temporary or
version-specific directory, or add a narrow `clean-dist` prerequisite. Avoid a
broad clean in ordinary development targets.

### F9 — The sdist is path-case-dependent across macOS and Linux

**Severity:** Medium
**Location:** tracked `.github/pull_request_template.md`, the physical macOS
checkout, and the sdist `.github/**` include

The Git index records:

```text
.github/pull_request_template.md
```

The case-insensitive macOS checkout physically exposes:

```text
.github/PULL_REQUEST_TEMPLATE.md
```

Hatch builds the sdist from the physical tree. As a result, two builds from
exact commit `63b492251e` passed all artifact checks but differed:

| Builder | Sdist SHA-256 | PR-template member |
| --- | --- | --- |
| Audited macOS checkout | `4db618f20d3b0ceb2ac912829c910172e5382245c7e3569938e0c2232c7bb097` | `.github/PULL_REQUEST_TEMPLATE.md` |
| GitHub Linux tag job | `2a0e681b8519343079b82a647d31f321ca15c872dde049bc6a6948bae4b3fdff` | `.github/pull_request_template.md` |

Both archives have 757 members. Extracted-content comparison found only that
path-name difference; the runtime package and wheel were identical. The
case-conflict hook does not catch this because the index contains only one path
and `core.ignorecase=true` hides the worktree spelling mismatch.

Recommended action: align the physical checkout spelling with the tracked path
through a safe two-step case rename, then add a check that compares actual
walked path spelling with `git ls-files`. Alternatively, exclude `.github/**`
from the sdist if repository automation has no source-distribution purpose.
The published Linux artifact, with the lowercase tracked path, is now the
canonical 0.1.1 sdist and cannot be replaced on PyPI. Fix the macOS checkout and
path-case validation before the next release rather than attempting to
republish the same version.

## Validation results

### Current audited HEAD

| Check | Result | Detail |
| --- | --- | --- |
| `make check` | Pass | Lock, pre-commit, YAML/TOML, whitespace, Markdown, Ruff, ty, pip-audit, Bandit, codespell |
| `make test` | Pass | 59 smoke tests and 5,530 retained tests |
| Retained-suite skips | Expected | 437 skipped, 4 expected failures on Python 3.13 |
| `make test-external` | Pass | SQLite 3.40.1, PostgreSQL 17.11, MySQL 8.4.10, Oracle 23.26.1 |
| External `dbshell` | Pass | `sqlite3`, `psql`, `mysql`, and SQL*Plus wrapper |
| GIS exclusion E2E | Pass | `DJRM_GIS_EXCLUSION_OK` |
| `make release-check RELEASE_TAG=v0.1.1` | Pass | Version, provenance, changelog, namespace, clean tree |
| Exact-HEAD isolated build | Pass | Wheel and sdist built in a fresh temporary directory |
| `twine check` | Pass | Both exact-HEAD release artifacts |
| `scripts/inspect_dist.py` | Pass | Archive shape, isolated install, setup, model import, translation, CLI |

The exact-HEAD temporary artifacts built from the audited macOS checkout were:

| Artifact | Entries | Python files | `.mo` files | SHA-256 |
| --- | ---: | ---: | ---: | --- |
| `djrm-0.1.1-py3-none-any.whl` | 712 | 439 | 265 | `315252f5a4e35f8bec5dfe25c3c7be83476dd9c6afec6cbd25b741d4a26f2927` |
| `djrm-0.1.1.tar.gz` | 757 | 458 | 265 | `4db618f20d3b0ceb2ac912829c910172e5382245c7e3569938e0c2232c7bb097` |

The wheel's 705 package entries exactly match the tracked runtime package. It
contains no `.pyc`, `django/`, `djrm/contrib/gis/`, or `.po` entries.

The successful Linux exact-tag workflow attached these files to the GitHub
release. TestPyPI and production PyPI published the same pair:

| Artifact | Bytes | SHA-256 | Comparison with local build |
| --- | ---: | --- | --- |
| `djrm-0.1.1-py3-none-any.whl` | 1,975,830 | `315252f5a4e35f8bec5dfe25c3c7be83476dd9c6afec6cbd25b741d4a26f2927` | Identical |
| `djrm-0.1.1.tar.gz` | 1,627,868 | `2a0e681b8519343079b82a647d31f321ca15c872dde049bc6a6948bae4b3fdff` | Differs only in the PR-template path case after extraction |

That sdist divergence is F9. Artifact structural checks passed on both versions
because neither check currently validates the exact case of every repository
metadata member.

### Supported Python matrix

`uv run tox run -r` passed on Python 3.10, 3.11, 3.12, 3.13, and 3.14. Each
environment ran 59 smoke tests and 5,530 retained tests. Python 3.10 through
3.13 reported 437 skips and four expected failures; Python 3.14 reported 435
skips and four expected failures.

That matrix was run before the final documentation/release-test commits. The
retained ORM tree did not change afterward; current GitHub CI independently ran
the same version matrix for the final commit.

### Import sweep

With settings configured for SQLite plus `contenttypes` and `postgres`, the
audit discovered 439 modules:

| Outcome | Count |
| --- | ---: |
| Imported successfully | 430 |
| Expected MySQL driver failures | 2 |
| Expected Oracle driver failures | 6 |
| Unexpected retained-module failure | 1 |

The unexpected failure is F1. Driver-installed behavior is independently
covered by the passing Docker E2E gate.

### Removed-namespace probes

Imports of the following failed as intended:

```text
djrm.forms
djrm.http
djrm.urls
djrm.template
djrm.contrib.auth
djrm.contrib.gis
```

No top-level `django` package was present in source or artifacts. No tracked or
artifact path used the previous `djo`, `djorm`, `dj-orm`, or `dj_orm` identity.

### Live CI at audit completion

For final commit and remote tag `63b492251e`, the exact-tag Main workflow
completed successfully. Quality, Python 3.10-3.14, coverage upload,
macOS/Windows portability, package build/inspection, and draft-release creation
all passed. CodeQL for the same commit also completed successfully. The manual
TestPyPI workflow and release-triggered protected PyPI workflow both completed
successfully, and `v0.1.1` is public.

The green tag workflow does not change F5: it did not itself execute the
external database matrix.

## Issues resolved while the audit was running

The repository changed several times during the three passes. The final snapshot
includes these fixes and additions, so they are not open findings:

- PostgreSQL retained fields no longer import removed forms eagerly.
- Residual GIS backend/runtime hooks were removed.
- Documentation now makes GIS exclusion permanent.
- A disposable four-backend E2E matrix was added.
- Early fixed host-port mappings, which caused a concurrent-run collision, were
  removed. The final Compose file uses service networking and a unique project
  name.
- `make check` initially caught an unsorted import in the new SQLPlus wrapper;
  commit `348b7a0c41` fixed it, and current `make check` passes.
- The stale `MAINTENANCE.md` statement that 0.1.0 was unreleased was replaced by
  release-state-neutral provenance language.
- Post-release source originally still built as 0.1.0. Commit `63b492251e`
  prepares 0.1.1 and removes that version collision for future builds.
- The guarded tag helper now invokes `make test-external`.

## Work left after remediation

No F1-F9 code, documentation, maintenance, artifact, or CI remediation remains.
Two release/operations steps are separate from closing the findings:

1. Push the focused remediation commits and require exact-SHA GitHub CI to pass.
2. Prepare and publish `0.1.2` when authorized. Published `0.1.1` is
   immutable and still contains the original `templatize()` defect.

Future Django tags still require the normal generated-candidate review. That is
the maintained update process, not an open audit defect.

## Deliberate behaviors that should remain documented

These are not defects if kept explicit:

- `DJANGO_SETTINGS_MODULE` remains unchanged because it is an environment
  variable contract, not an import namespace.
- Default settings continue to contain strings for removed web subsystems. They
  are dormant until a caller selects those features.
- Form conversion fails lazily instead of making model-field imports fail.
- `djrm.__version__` reports the upstream Django API version, while distribution
  metadata reports the djrm release version.
- Optional backend modules require their declared driver extras.
- Compiled translations remain; translation authoring commands and sources do
  not.
- Request lifecycle signals and their DB connection hooks remain harmless and
  useful when explicitly sent outside a web server.
- `Tags` constants remain for public compatibility even when no handler is
  registered for a removed subsystem.
- SQLite is the full retained-suite backend; the other engines use a smaller but
  real E2E contract suite.

## Appendix A: Executable-AST-different common package files

```text
djrm/__init__.py
djrm/conf/__init__.py
djrm/contrib/postgres/fields/array.py
djrm/contrib/postgres/fields/hstore.py
djrm/contrib/postgres/fields/ranges.py
djrm/contrib/postgres/operations.py
djrm/core/checks/__init__.py
djrm/core/management/__init__.py
djrm/db/backends/base/creation.py
djrm/db/backends/base/operations.py
djrm/db/backends/mysql/features.py
djrm/db/backends/oracle/features.py
djrm/db/backends/sqlite3/creation.py
djrm/db/backends/sqlite3/features.py
djrm/db/models/base.py
djrm/db/models/fields/__init__.py
djrm/db/models/fields/files.py
djrm/db/models/fields/json.py
djrm/db/models/fields/related.py
djrm/db/models/functions/math.py
djrm/db/models/sql/compiler.py
djrm/test/__init__.py
djrm/test/runner.py
djrm/test/signals.py
djrm/test/testcases.py
djrm/test/utils.py
djrm/utils/log.py
djrm/utils/translation/__init__.py
djrm/utils/translation/reloader.py
```

Two additional common source files have an AST difference that disappears when
docstrings are stripped:

```text
djrm/__main__.py
djrm/db/backends/base/schema.py
```

## Appendix B: Executable-AST-different common test files

```text
tests/aggregation_regress/tests.py
tests/backends/base/test_base.py
tests/backends/base/test_creation.py
tests/contenttypes_tests/models.py
tests/contenttypes_tests/test_models.py
tests/model_fields/test_textfield.py
tests/model_fields/tests.py
tests/model_inheritance_regress/tests.py
tests/postgres_tests/test_integration.py
tests/prefetch_related/tests.py
tests/queries/tests.py
tests/raw_query/tests.py
tests/runtests.py
tests/test_sqlite.py
tests/utils_tests/test_html.py
tests/utils_tests/test_module_loading.py
tests/utils_tests/test_text.py
```

## Appendix C: Fork-only test paths

```text
tests/djrm_smoke/__init__.py
tests/djrm_smoke/test_distribution.py
tests/djrm_smoke/test_maintenance.py
tests/e2e/Dockerfile
tests/e2e/__init__.py
tests/e2e/bin/sqlplus
tests/e2e/compose.yaml
tests/e2e/e2e_app/__init__.py
tests/e2e/e2e_app/apps.py
tests/e2e/e2e_app/migrations/0001_initial.py
tests/e2e/e2e_app/migrations/__init__.py
tests/e2e/e2e_app/models.py
tests/e2e/exercise_backend.py
tests/e2e/run_container.py
tests/e2e/settings.py
tests/e2e/verify_dbshell.py
tests/e2e/verify_gis_exclusion.py
```

## Appendix D: Current top-level test directories

```text
aggregation
aggregation_regress
annotations
async
backends
base
basic
bulk_create
check_framework
composite_pk
constraints
contenttypes_tests
custom_columns
custom_lookups
custom_managers
custom_methods
custom_migration_operations
custom_pk
datatypes
dates
datetimes
db_functions
db_typecasts
db_utils
dbshell
defer
defer_regress
delete
delete_regress
distinct_on_fields
djrm_smoke
e2e
empty
empty_models
expressions
expressions_case
expressions_window
field_defaults
field_subclassing
filtered_relation
fixtures_model_package
force_insert_update
foreign_object
from_db_value
generic_relations
get_earliest_or_latest
get_or_create
indexes
inspectdb
introspection
invalid_models_tests
known_related_objects
lookup
m2m_and_m2o
m2m_intermediary
m2m_multiple
m2m_recursive
m2m_signals
m2m_through
m2o_recursive
many_to_many
many_to_one
many_to_one_null
max_lengths
migrate_signals
migration_test_data_persistence
migrations
migrations2
model_fields
model_indexes
model_inheritance
model_inheritance_regress
model_meta
model_options
model_package
model_regress
model_utils
multiple_database
mutually_referential
nested_foreign_keys
no_models
null_fk
null_fk_ordering
null_queries
one_to_one
or_lookups
order_with_respect_to
ordering
postgres_tests
prefetch_related
properties
proxy_model_inheritance
queries
queryset_pickle
raw_query
reserved_names
reverse_lookup
save_delete_hooks
schema
select_for_update
select_related
select_related_onetoone
select_related_regress
serializers
signals
str
string_lookup
transaction_hooks
transactions
unmanaged_models
update
update_only_fields
utils_tests
validation
validators
xor_lookups
```

## Appendix E: Audit command ledger

Representative commands used across the three passes:

```text
git -c core.fsmonitor=false status --short --branch
git log / git diff / git ls-files / git ls-remote
gh api .../releases/tags/v0.1.0
gh api .../commits/<sha>/check-runs
make check
make test
uv run tox run -r
make coverage
make test-external
make release-check RELEASE_TAG=v0.1.1
uv build --out-dir <fresh-temp-dir>
uv run twine check <fresh-temp-dir>/*
uv run python scripts/inspect_dist.py <fresh-temp-dir>
configured pkgutil/importlib module sweep
namespace-normalized byte and AST comparison scripts
wheel and tar member inspection
removed-namespace and retained-edge runtime probes
```

No library source, tests, configuration, release metadata, tag, or remote state
was changed by this audit. The only audit deliverable is this Markdown file.
