# Maintenance and release policy

This document is the source of truth for updating and distributing djrm.

## Decisions

### Release unit

djrm follows supported Django LTS lines. It publishes a build for the initial
LTS tag and for every patch or security tag in that LTS line. It does not track
non-LTS Django feature releases.

`main` is the sole long-lived development branch and carries the current LTS
line. The automation creates an isolated candidate branch named
`release/django-<tag>` in a separate local worktree. After the full gate passes,
the candidate tree is merged into `main`; release tags are cut from `main`.

Release tags and distribution versions use SemVer. Each djrm major is assigned
to one reviewed Django LTS series:

| Django tag | djrm version | Meaning |
| --- | --- | --- |
| `5.2.17` | `0.1.0` | First release in the Django 5.2 LTS line |
| `5.2.17` | `0.1.1` | djrm-only fix from the same Django tag |
| `5.2.18` | `0.2.0` | First release from the next Django 5.2 patch tag |
| `6.2` | `1.0.0` | First release in the Django 6.2 LTS line |

The mapping is append-only and recorded in `lts_version_majors` in
`.djrm-maintenance.toml`: djrm `0.x` corresponds to Django 5.2 LTS, `1.x`
corresponds to Django 6.2 LTS, and each later reviewed LTS gets the next djrm
major. Within one LTS line, the djrm minor increments when the upstream Django
tag advances. The patch increments only for a djrm-only release from the same
Django tag. The exact upstream tag remains in the maintenance metadata instead
of being encoded in the package version. Pre-release Django tags are never
production djrm releases.

### Distribution identity

- PyPI distribution: `djrm`
- Python import namespace: `djrm`
- Console command: `djrm`
- Repository: `https://github.com/viseshrp/djrm`

The release gate enforces the same `djrm` identity across project metadata,
artifacts, imports, and the CLI before tagging or publishing.

### Source and support

The `upstream` Git remote must point to `https://github.com/django/django.git`.
Every production candidate starts from an exact upstream tag, not the tip of a
stable branch. This makes the source reproducible and lets users map a djrm build
to Django security advisories.

djrm carries the same Python floor and runtime dependency bounds as its upstream
LTS tag unless a retained module requires a documented exception. Optional
database drivers remain user-selected extras.

Support for an LTS line ends when upstream Django ends extended support. An old
djrm release remains installable, but it does not receive independent security
backports after that date.

### Packaging scaffold

The packaging and automation baseline was rendered from the sibling YAPC
Cookiecutter at commit `df3a78fefc78ffb304dd5a32196e1be7a430bbcb` with
Cookiecutter 2.7.1:

```console
uv run --project ../yapc cookiecutter ../yapc --no-input \
  project_name=djrm \
  project_description="Django ORM, migrations, and database backends as a standalone library." \
  cli_tool=y codecov=y git_init=n github_actions=y
```

The rendered project is a comparison baseline, not an overlay to copy blindly.
This fork adds the upstream-derived `djrm/` tree and scopes formatters to
fork-owned files. To adopt a later YAPC version, render it into a temporary
directory, review the infrastructure diff, and update `yapc_commit` in
`.djrm-maintenance.toml`. Routine Django LTS application does not require
rerendering YAPC; the updater applies the reviewed package infrastructure with
the maintained fork delta.

## Mechanical application

Run the tool from a clean djrm source branch:

```console
uv run python scripts/apply_django_lts.py \
  --django-ref 5.2.17 \
  --output ../djrm-5.2.17
```

The command performs these bounded operations:

1. Fetches the exact tag from the official `upstream` remote and verifies that
   the ref is a final release in the reviewed `lts_version_majors` mapping in
   `.djrm-maintenance.toml`.
2. Creates `release/django-<tag>` in a separate Git worktree.
3. Regenerates a canonical `djrm` tree for both the recorded upstream base and
   the new tag, then applies their reviewed fork delta with Git's three-way
   merge support.
4. Applies clean additions, edits, and deletions automatically. Directories
   removed by the maintained fork stay removed, including files added upstream
   after the recorded base. This permanently keeps `contrib.gis` and `gis_tests`
   out of djrm. Gettext source catalogs remain pruned while compiled runtime
   catalogs are retained. Reviewed packaging and CI files stay fork-owned;
   incompatible changes in retained Django runtime code remain as conflicts for
   human review.
5. Computes the next SemVer package version, writes the exact upstream
   provenance, then runs the namespace, package, and retained-suite checks.

The source checkout is never switched or rewritten. The tool refuses a dirty
source or output directory that already exists. This tree-delta design keeps
future applications independent of historical package paths and commit names.

### Continue after a semantic conflict

The tool prints the conflicting files and stops. Compare each file with both
the new upstream implementation and the fork change. Prefer the new upstream
logic, then reapply only the ORM-only adjustment.

After resolving and staging every conflict, resume from the source checkout:

```console
uv run python scripts/apply_django_lts.py \
  --continue \
  --output ../djrm-5.2.17
```

Do not use `git checkout --ours` or `--theirs` across all content conflicts.
That can silently discard an upstream security fix or restore a removed web
dependency.

### New LTS series

Use the same command with the final LTS tag, for example `6.2`. The first run is
expected to stop where Django changed retained modules. Resolve those files,
finish the gate, and merge the generated candidate tree into `main`. Before any
later series, append its officially announced series identifier and the next
djrm major to `lts_version_majors` in `.djrm-maintenance.toml`; the tool never
guesses future LTS numbering. Never reorder or renumber an existing mapping.
Update `SPEC.md` only when the retained module contract or supported Python
versions changed.

For a djrm-only fix without a newer Django tag, pass a patch number greater
than the current one:

```console
uv run python scripts/apply_django_lts.py \
  --django-ref 5.2.17 \
  --patch 1 \
  --output ../djrm-0.1.1
```

The first application of a newer Django tag must use patch `0`. The updater
increments the minor within the current LTS line or resets to `<next-major>.0.0`
for the next configured LTS line.

## Release gate

A candidate can be tagged only when all of these pass:

```console
make check
make test
make test-external
make build
make check-dist
make inspect-dist
make release-check RELEASE_TAG=v0.1.0
```

`make release-check` verifies:

- the Git tag and package version match;
- the SemVer major maps to the recorded final Django LTS series;
- the package and maintenance metadata record the same version and exact Django
  tag;
- the source is clean and contains no `django` package;
- `djrm` is the configured distribution;
- the changelog has a dated entry for the release.

`make inspect-dist` also rejects any wheel or source archive containing
`djrm.contrib.gis`.

`make test-external` is the database compatibility gate. It uses disposable
Docker services for PostgreSQL, MySQL, and Oracle; runs the same migration,
transaction, JSON, aggregation, subquery, window-function, locking, and
introspection scenarios on those backends and SQLite; exercises the real
`sqlite3`, `psql`, `mysql`, and SQL*Plus clients through `djrm dbshell`; and
confirms that GIS remains unavailable. The command cleans up its containers,
volumes, network, and local runner image even after a failure.

Run `make tag` only from a clean `main` branch that matches its configured
remote. The tag workflow rebuilds and tests the exact tag, then creates a draft
GitHub release with the wheel and source archive. The separate release workflow
publishes those verified files to PyPI only after a maintainer publishes the
GitHub release.

## PyPI setup

Before the first release:

1. Confirm `djrm` is still available on PyPI.
2. Add a project-scoped PyPI token as the GitHub environment secret
   `PYPI_TOKEN` in the `pypi` environment.
3. Add a TestPyPI token as the GitHub environment secret `TEST_PYPI_TOKEN` in
   the `testpypi` environment.
4. Protect the `pypi` environment with a required reviewer.

Run the `Release` workflow manually from `main` for an explicit TestPyPI dry
run. Publishing a draft GitHub release triggers nothing. Publishing that GitHub
release runs the production job through the protected `pypi` environment.

PyPI publication is intentionally separate from ordinary CI. A push to `main`
builds and checks artifacts but cannot publish them.

## Current branch status

`main` is based on the exact Django `5.2.17` tag and is prepared as djrm
`0.1.0`. It remains unreleased until `v0.1.0` is created, its draft GitHub
release passes review, and a maintainer publishes that release.
