# Historical implementation handoff

This file records the original extraction session and is no longer the current
operator guide. See `MAINTENANCE.md` for branch, update, and release policy.

1) Repo base state
- Current branch: `feat/djorm`
- Remotes:
  - `origin https://github.com/django/django.git` (fetch/push)
  - `upstream https://github.com/django/django.git` (fetch/push)
- Upstream tag/commit currently based on:
  - tag `5.2.11`
  - commit `4a96a199bbb1d3dca45ea16bf643216e179cb8bc`

2) Plan phase state
- Last completed phase: `Phase 8: Upstream Rebase Workflow`
- Next phase to start: `None (plan complete)`

3) Commits created in this session
- Phase 5 / large test suite removals:
  - `37ac773ecd` `[prune] Remove web-related test suites`
- Phase 5 / retained-suite runtime and expectation fixes:
  - `ef39cfdc16` `[fix] Stabilize retained ORM test suite`
- Phase 6 / distribution metadata and packaging runtime fixes:
  - `c90901e886` `[packaging] Update pyproject.toml for djorm distribution`
- Phase 6 / README and `python -m djorm` packaging polish:
  - `de987a310d` `[packaging] Update README and __main__ for djorm`
- Phase 7 / fork-specific glue consolidation in `_ext`:
  - `c9b8a4d897` `[ext] Add djorm/_ext/ fork glue`
- Phase 8 / rebase workflow tooling and operator docs:
  - `7f7a10b53b` `[upstream] Add rebase workflow script and documentation`

4) Uncommitted changes
- `git status -sb`:
  - `## feat/djorm`
  - `?? HANDOFF_LOG.md`
- Working tree state:
  - only `HANDOFF_LOG.md` is uncommitted; it records handoff state after Phase 6

5) Verification commands run in this session and outcomes
- `python3 tests/runtests.py --settings=test_sqlite async check_framework utils_tests basic -v0 --parallel=1`
  - pass
  - output:
    - `Ran 622 tests in 0.309s`
    - `OK (skipped=6)`
- `python3 tests/runtests.py --settings=test_sqlite --start-at=aggregation -v0 --parallel=1`
  - pass
  - output:
    - `Ran 5429 tests in 21.441s`
    - `OK (skipped=437, expected failures=4)`
- `python3 tests/runtests.py --settings=test_sqlite backends.sqlite.tests.ThreadSharing -v2 --parallel=2`
  - pass
  - output:
    - `Ran 1 test in 0.006s`
    - `OK`
- `python3 tests/runtests.py --settings=test_sqlite backends.base -v1 --parallel=2`
  - fail
  - key error excerpt:
    - `test_execute_sql_flush_statements (backends.base.test_operations.SqlFlushTests.test_execute_sql_flush_statements) failed`
    - `ProgrammingError('Cannot operate on a closed database.')`
  - implicated file paths:
    - `tests/backends/base/test_creation.py`
    - `tests/backends/base/test_operations.py`
- `python3 tests/runtests.py --settings=test_sqlite backends.base.test_creation backends.base.test_operations -v1 --parallel=2`
  - failed before fix with the same closed-database error
  - pass after fixing `tests/backends/base/test_creation.py`
  - passing output:
    - `Ran 46 tests in 0.197s`
    - `OK (skipped=1)`
- `python3 tests/runtests.py --settings=test_sqlite -v0 --parallel`
  - fail before final fixes
  - key error excerpts:
    - initial failure:
      - `ModuleNotFoundError: No module named 'fixtures_regress.models'`
      - implicated file path: `tests/fixtures_regress/tests.py`
    - later failure:
      - `ProgrammingError('Cannot operate on a closed database.')`
      - implicated file path: `tests/backends/base/test_creation.py`
  - pass after fixes
  - output:
    - `Ran 5519 tests in 8.392s`
    - `OK (skipped=437, expected failures=4)`
- `source /tmp/djorm-phase6/bin/activate && python -m pip install -e . && djorm --help`
  - fail before fix
  - key error excerpt:
    - `NameError: name 'defaultdict' is not defined`
  - implicated file path:
    - `djorm/core/management/__init__.py`
  - pass after fix
  - key output:
    - `Available subcommands:`
    - `[djorm]`
- `source /tmp/djorm-phase6/bin/activate && python -m build`
  - pass
  - built distributions in `dist/`
  - stale `MANIFEST.in` warnings about `graft django` and `prune scripts` were present before fixing `MANIFEST.in`
- `source /tmp/djorm-phase6/bin/activate && python -m build` (after `MANIFEST.in` fix)
  - pass
  - no stale `django`/`scripts` manifest warnings
- `source /tmp/djorm-phase6/bin/activate && PYTHONPATH=tests DJANGO_SETTINGS_MODULE=test_sqlite djorm migrate --help`
  - pass
  - output begins:
    - `usage: djorm migrate [-h] [--noinput] [--database {default,other}] ...`
- `source /tmp/djorm-phase6/bin/activate && PYTHONPATH=tests DJANGO_SETTINGS_MODULE=test_sqlite djorm showmigrations --help`
  - pass
  - output begins:
    - `usage: djorm showmigrations [-h] [--database {default,other}] [--list | --plan] ...`
- `source /tmp/djorm-phase6/bin/activate && python -m zipfile -l dist/djorm-*.whl | sed -n '1,12p'`
  - pass
  - wheel contents begin with `djorm/` paths (for example `djorm/__init__.py`, `djorm/__main__.py`, `djorm/_ext/__init__.py`)
- `source /tmp/djorm-phase6-wheel/bin/activate && python -m pip install dist/djorm-*.whl && python - <<'PY' ... PY`
  - pass
  - output:
    - `djorm version: 5.2.12.dev20260301183933`
    - `OK`
- `python3 - <<'PY' ... djorm.setup() ... PY`
  - pass
  - output:
    - `setup_ok`
- `python3 - <<'PY' ... LazySettings._add_script_prefix('media/') ... PY`
  - pass
  - output:
    - `media/`
    - `/media/`
- `rg -n "_ext\\.setup\\b|setup_helpers|add_script_prefix_if_available|set_script_prefix_if_available" djorm --glob '*.py'`
  - pass
  - output confirms the fork-specific URL-prefix helpers are centralized in:
    - `djorm/_ext/setup_helpers.py`
    - `djorm/__init__.py`
    - `djorm/conf/__init__.py`
- `python3 scripts/rename_namespace.py --check`
  - pass
  - output:
    - `No residual django namespace references found.`
- `python3 -c "import djorm; print(djorm.__version__)"`
  - pass
  - output:
    - `5.2.12.dev20260301191126`
- `python3 tests/runtests.py --settings=test_sqlite -v0 --parallel`
  - pass
  - output:
    - `Ran 5519 tests in 8.130s`
    - `OK (skipped=437, expected failures=4)`

6) SPEC/PLAN conflicts discovered
- None discovered in this session
- Stop point:
  - stopped after completing Phase 8, creating commits `37ac773ecd`, `ef39cfdc16`, `c90901e886`, `de987a310d`, `c9b8a4d897`, and `7f7a10b53b`, and updating this handoff log
