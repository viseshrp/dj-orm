# Changelog

This file records Djorm-specific changes. Django changes remain documented in the
upstream release notes for the exact tag named by each Djorm release.

## Unreleased

## [5.2.17.0] - 2026-08-15

### Added

- A `dj-orm` distribution with wheel and source-archive builds.
- A scripted Django LTS application workflow with resumable conflict handling.
- CI, release, dependency, contribution, and package verification files derived
  from the sibling `yapc` Cookiecutter.

### Changed

- The public distribution name is `dj-orm`; imports and the CLI remain `djorm`.
- Release versions map the exact Django tag plus a Djorm rebuild revision.
- Removed inherited Django documentation, browser tooling, maintainer scripts,
  and other files outside the standalone ORM project.
