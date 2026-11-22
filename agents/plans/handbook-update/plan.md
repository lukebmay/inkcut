# handbook-update

**Rank:** 3

## Goal

Inkcut's installed handbook is catalog 0.9.19. Before this
update it was 0.9.18. The range is `agent-handbook changelog
0.9.18`. This plan does not edit product code. It stays off
the queue. The next handbook update rewrites this file.

## Range

0.9.19 replaces the 0.9.15 home rule. The statement is
[Scripting](../../installed/scripting.md), section XDG
directory variables (scripting 2.10.0). Any app or script
that keeps config, data, state, cache, logs, or runtime
files uses those homes, including a program that is not
installed. There is no detector for a missing XDG system,
no `~/.<app>/` default, runtime does not fall back to
`/tmp`, and logs stay in the state home. A program with no
install record resolves data and state on each run. An
install records data and state once. Do not create an
install record only to hold those paths.

0.9.18 is the handbook update procedure. That section is
already in [the handbook](../../handbook.md). Catalog 0.9.19
does not change handbook seeds. This update did not edit
`agents/handbook.md` or `architecture.md`.

The code that still pins state without an install record is
[handbook-xdg](../handbook-xdg/plan.md). That plan is not on
the queue. This plan does not make that edit.

## Older plans

The handbook plans opened for 0.9.18 are finished and
archived. They are handbook-xdg-homes,
handbook-device-plugin-split, and handbook-core-index.
Later handbook plans use the `handbook-` prefix. Those
archives were not moved.

Plans read this update:

- [_bugs](../_bugs/plan.md) does not disagree with the
  installed handbook. It was not rewritten.
- [cut-selection](../cut-selection/plan.md) changes which
  SVG objects a cut opens. It was not rewritten.
- [device-error](../device-error/plan.md) removes an unused
  class. It was not rewritten.
- [cli-install-update-data](../cli-install-update-data/plan.md)
  names the default device file
  `~/.config/inkcut/inkcut.device.json`. That path is still
  the one when neither `INKCUT_CONFIG_HOME` nor
  `XDG_CONFIG_HOME` is set. It does not tell the app to pin
  state without an install. It was not rewritten. If that
  optional install is built later, recording data and state
  belongs to that plan.

Nothing else in the repo lags this rule. Config, cache, and
runtime already resolve every run. `runtime_dir` fails when
both runtime variables are unset and does not use `/tmp`.
`data_home()` already resolves each run. Logs already go
through `state_home()`. Plugin JSON stays in the config
home, which is `~/.config/inkcut/{plugin id}.json` when both
config variables are unset. The disk transport's temp
directory is job output, not the runtime home. `~/.ssh` and
`~/.gitconfig` are not this rule.

Nothing was taken off [`priority.md`](../../priority.md).
`handbook-xdg` was not added to it.

## Guide

Follow [Handbook](../../handbook.md), section Handbook
updates. The home rule is
[Scripting](../../installed/scripting.md), section XDG
directory variables. Do not copy them.

## Checks

`agents/installed/.meta.toml` has `catalog_version` 0.9.19.
Scripting is 2.10.0. `agents/handbook.md` still has the
Handbook updates section.
[handbook-xdg](../handbook-xdg/plan.md) exists and is absent
from [`priority.md`](../../priority.md).
