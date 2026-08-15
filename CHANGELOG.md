# Changelog

This file records Djo-specific changes. Django changes remain documented in the
upstream release notes for the exact tag named by each Djo release.

## Unreleased

### Added

- A `dj-orm` distribution with wheel and source-archive builds.
- A scripted Django LTS application workflow with resumable conflict handling.
- CI, release, dependency, contribution, and package verification files derived
  from the sibling `yapc` Cookiecutter.

### Changed

- The public distribution name is `dj-orm`; imports and the CLI remain `djo`.
- Release versions map the exact Django tag plus a Djo rebuild revision.
