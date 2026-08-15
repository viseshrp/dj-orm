# Djorm LTS application

The old hand-run rebase workflow has been replaced by a resumable command:

```console
uv run python scripts/apply_django_lts.py \
  --django-ref 5.2.17 \
  --output ../djorm-5.2.17
```

The command creates a separate worktree, reruns the namespace conversion,
replays the fork commit stack, handles expected deletion conflicts, and runs
the release gate. It stops rather than guessing when upstream changed retained
code.

See [`MAINTENANCE.md`](../MAINTENANCE.md) for the authoritative branch, conflict,
versioning, and publishing policy. Do not perform the old cherry-pick sequence
by hand.
