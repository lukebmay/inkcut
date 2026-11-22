# handbook-xdg

**Rank:** 3

## Goal

Inkcut has no install record, so data and state resolve on
each run. `state_home()` in `inkcut/core/homes.py` still
writes `state-home` under the config home on first resolve
and then keeps that path. That file is a record created
only to hold the path. Stop writing it. Resolve state the
same way config resolves. Data already resolves each run.
Leave that. Do not add an install command in this plan.
Logs stay in the state home this resolve returns. This
plan stays off the queue.

## Guide

[Scripting](../../installed/scripting.md), section XDG
directory variables. Catalog 0.9.19 replaces 0.9.15. The
range is `agent-handbook changelog 0.9.18`.
[Architecture](../../architecture.md) and
[Project](../../project.md) still name plugin JSON at
`~/.config/inkcut/{plugin id}.json`. That is the config
home when both config variables are unset. Do not move
those files. Do not edit the guide.

## Checks

- [ ] `state_home()` does not read or write `state-home`.
- [ ] With no install record, a later change of
      `INKCUT_STATE_HOME` or `XDG_STATE_HOME` is honored,
      the same way config is.
- [ ] Both state variables unset uses
      `~/.local/state/inkcut`.
- [ ] A set app variable is the home. Nothing appends
      another `/inkcut`.
- [ ] `data_home()` stays a per-run resolve. It is not
      pinned.
- [ ] Logs are still under the state home. There is no
      separate log variable.
- [ ] `.travis.yml` prints logs from that state home, not
      from `~/.config/inkcut/logs`.
- [ ] No install record is added only to keep the old pin.
- [ ] The homes tests cover the live resolve and no longer
      require the `state-home` file.
