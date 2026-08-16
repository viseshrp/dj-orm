# Maintenance and release policy

This document is the source of truth for updating and distributing Djorm.

## Decisions

### Release unit

Djorm follows supported Django LTS lines. It publishes a build for the initial
LTS tag and for every patch or security tag in that LTS line. It does not track
non-LTS Django feature releases.

`main` is the sole long-lived development branch and carries the current LTS
line. The automation creates an isolated candidate branch named
`release/django-<tag>` in a separate local worktree. After the full gate passes,
the candidate tree is merged into `main`; release tags are cut from `main`.

Release tags and distribution versions use SemVer. Each Djorm major is assigned
to one reviewed Django LTS series:

| Django tag | Djorm version | Meaning |
| --- | --- | --- |
| `5.2.17` | `0.1.0` | First release in the Django 5.2 LTS line |
| `5.2.17` | `0.1.1` | Djorm-only fix from the same Django tag |
| `5.2.18` | `0.2.0` | First release from the next Django 5.2 patch tag |
| `6.2` | `1.0.0` | First release in the Django 6.2 LTS line |

The mapping is append-only and recorded in `lts_version_majors` in
`.djorm-maintenance.toml`: Djorm `0.x` corresponds to Django 5.2 LTS, `1.x`
corresponds to Django 6.2 LTS, and each later reviewed LTS gets the next Djorm
major. Within one LTS line, the Djorm minor increments when the upstream Django
tag advances. The patch increments only for a Djorm-only release from the same
Django tag. The exact upstream tag remains in the maintenance metadata instead
of being encoded in the package version. Pre-release Django tags are never
production Djorm releases.

### Distribution identity

- PyPI distribution: `dj-orm`
- Python import namespace: `djorm`
- Console command: `djorm`
- Repository: `https://github.com/viseshrp/dj-orm`

The `djorm` name on PyPI belongs to an unrelated project, so this repository must
never attempt to publish that distribution name. A release check enforces
`dj-orm` before tagging or publishing.

### Source and support

The `upstream` Git remote must point to `https://github.com/django/django.git`.
Every production candidate starts from an exact upstream tag, not the tip of a
stable branch. This makes the source reproducible and lets users map a Djorm build
to Django security advisories.

Djorm carries the same Python floor and runtime dependency bounds as its upstream
LTS tag unless a retained module requires a documented exception. Optional
database drivers remain user-selected extras.

Support for an LTS line ends when upstream Django ends extended support. An old
Djorm release remains installable, but it does not receive independent security
backports after that date.

### Packaging scaffold

The packaging and automation baseline was rendered from the sibling YAPC
Cookiecutter at commit `df3a78fefc78ffb304dd5a32196e1be7a430bbcb` with
Cookiecutter 2.7.1:

```console
uv run --project ../yapc cookiecutter ../yapc --no-input \
  project_name=djorm \
  project_description="Django ORM, migrations, and database backends as a standalone library." \
  cli_tool=y codecov=y git_init=n github_actions=y
```

The rendered project is a comparison baseline, not an overlay to copy blindly.
Djorm adapts its package name to `dj-orm`, retains the upstream-derived `djorm/`
tree, and scopes formatters to fork-owned files. To adopt a later YAPC version,
render it into a temporary directory, review the infrastructure diff, and
update `yapc_commit` in `.djorm-maintenance.toml`. Routine Django LTS application
does not require rerendering YAPC; the updater applies the reviewed package
infrastructure with the maintained fork delta.

## Mechanical application

Run the tool from a clean Djorm source branch:

```console
uv run python scripts/apply_django_lts.py \
  --django-ref 5.2.17 \
  --output ../djorm-5.2.17
```

The command performs these bounded operations:

1. Fetches the exact tag from the official `upstream` remote and verifies that
   the ref is a final release in the reviewed `lts_version_majors` mapping in
   `.djorm-maintenance.toml`.
2. Creates `release/django-<tag>` in a separate Git worktree.
3. Regenerates a canonical `djorm` tree for both the recorded upstream base and
   the new tag, then applies their reviewed fork delta with Git's three-way
   merge support.
4. Applies clean additions, edits, and deletions automatically. Directories
   removed by the maintained fork stay removed, including files added upstream
   after the recorded base. Gettext source catalogs remain pruned while compiled
   runtime catalogs are retained. Reviewed packaging and CI files stay
   fork-owned; incompatible changes in retained Django runtime code remain as
   conflicts for human review.
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
  --output ../djorm-5.2.17
```

Do not use `git checkout --ours` or `--theirs` across all content conflicts.
That can silently discard an upstream security fix or restore a removed web
dependency.

### New LTS series

Use the same command with the final LTS tag, for example `6.2`. The first run is
expected to stop where Django changed retained modules. Resolve those files,
finish the gate, and merge the generated candidate tree into `main`. Before any
later series, append its officially announced series identifier and the next
Djorm major to `lts_version_majors` in `.djorm-maintenance.toml`; the tool never
guesses future LTS numbering. Never reorder or renumber an existing mapping.
Update `SPEC.md` only when the retained module contract or supported Python
versions changed.

For a Djorm-only fix without a newer Django tag, pass a patch number greater
than the current one:

```console
uv run python scripts/apply_django_lts.py \
  --django-ref 5.2.17 \
  --patch 1 \
  --output ../djorm-0.1.1
```

The first application of a newer Django tag must use patch `0`. The updater
increments the minor within the current LTS line or resets to `<next-major>.0.0`
for the next configured LTS line.

## Release gate

A candidate can be tagged only when all of these pass:

```console
make check
make test
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
- `dj-orm` is the configured distribution;
- the changelog has a dated entry for the release.

Run `make tag` only from a clean `main` branch that matches its configured
remote. The tag workflow rebuilds and tests the exact tag, then creates a draft
GitHub release with the wheel and source archive. The separate release workflow
publishes those verified files to PyPI only after a maintainer publishes the
GitHub release.

## PyPI setup

Before the first release:

1. Confirm `dj-orm` is still available on PyPI.
2. Add a project-scoped PyPI token as the GitHub environment secret
   `PYPI_TOKEN` in the `pypi` environment.
3. Add a TestPyPI token as `TEST_PYPI_TOKEN` only when an explicit dry run is
   needed. Normal branch pushes do not publish.
4. Protect the `pypi` environment with a required reviewer.

PyPI publication is intentionally separate from ordinary CI. A push to `main`
builds and checks artifacts but cannot publish them.

## Current branch status

`main` is based on the exact Django `5.2.17` tag and is prepared as Djorm
`0.1.0`. It remains unreleased until `v0.1.0` is created, its draft GitHub
release passes review, and a maintainer publishes that release.
