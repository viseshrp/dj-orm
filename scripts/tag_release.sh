#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

branch=$(git rev-parse --abbrev-ref HEAD)
if [[ ! "$branch" =~ ^(djo/.+-lts|release/django-.+)$ ]]; then
  fail "Release tags must be created from a djo/*-lts or release/django-* branch."
fi

if [[ -n "$(git status --porcelain)" ]]; then
  fail "Working directory is dirty. Commit tracked and untracked changes first."
fi

if ! tracking_branch=$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null); then
  fail "$branch has no configured tracking branch."
fi
remote=$(git config --get "branch.$branch.remote")
git fetch --quiet "$remote"
read -r behind ahead < <(git rev-list --left-right --count "$tracking_branch...HEAD")
if [[ "$behind" != "0" || "$ahead" != "0" ]]; then
  fail "$branch must match $tracking_branch exactly (behind=$behind, ahead=$ahead)."
fi

version=$(uv run hatch version)
tag="v$version"

make release-check RELEASE_TAG="$tag"
make check
make test
make build
make check-dist
make inspect-dist

if git show-ref --quiet --verify "refs/tags/$tag"; then
  fail "Tag $tag already exists locally."
fi
if git ls-remote --exit-code --refs --tags "$remote" "refs/tags/$tag" >/dev/null 2>&1; then
  fail "Tag $tag already exists on $remote."
else
  remote_status=$?
  if [[ "$remote_status" != "2" ]]; then
    fail "Could not verify whether tag $tag exists on $remote."
  fi
fi

git tag "$tag" -m "Release $tag"
git push "$remote" "refs/tags/$tag"
echo "Pushed release tag $tag."
