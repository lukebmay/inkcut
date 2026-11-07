# cli-install-update-data

**Rank:** 1

## Goal

Build a Python `inkcut` CLI with install, update, and device-data
commands. This is optional. It is not on the queue. Do not start
it unless the human asks.

The August note that the fork was on hold is not a wait. This
checkout is the fork. The work was never started, and he still
marked it optional.

## Guide

[`project.md`](../../project.md) names the console entry
`inkcut = inkcut.app:main`. This plan does not change the cut
path in [`architecture.md`](../../architecture.md). Weedlines
install stays in `~/dev/me/weedlines`. Do not couple it here.

## Checks

- [ ] `inkcut install` is idempotent, safe to re-run, and upgrades
      a stock install to this fork.
- [ ] `inkcut update` pulls and installs a clean tree. A dirty tree
      installs only, with a clear message, and does not discard
      local changes.
- [ ] CLI output uses colored status lines and phases, exits
      non-zero on a real failure, and has `--dry-run` where a step
      is destructive.
- [ ] `inkcut data save`, `inkcut data load`, and `inkcut data list`
      match the old `inkcut-data.py` commands.
- [ ] `inkcut --help` or the subcommand help is enough. Do not add
      a second product README for this.
- [ ] Compare the archive `inkcut/cli/` with upstream and keep the
      better base.
