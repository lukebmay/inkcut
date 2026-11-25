# handbook-update

**Rank:** 3

## Goal

Inkcut's installed handbook is catalog 0.9.20. Before this
update it was 0.9.19. The range is `agent-handbook changelog
0.9.19`. This plan does not edit product code. It stays off
the queue. The next handbook update rewrites this file.

## Range

0.9.20 changes how an accepted plan writes the guide, adds
Clarity, names the developer as the senior developer, and
adds the regression role. Read that with the command above.
Do not copy the changelog.

The installed command does not run from the checkout. No
product correction was filed for 0.9.20.

`agents/architecture.md` still says "Opening a plan does not
write this file." `agents/acceptance.md` still says "before
or with the plan." Those files are not the blank seed. This
plan does not edit them, and it does not open a handbook
plan to edit them.

## Older plans

The handbook plans opened for 0.9.18 are finished and
archived. Later handbook plans use the `handbook-` prefix.
Those archives were not moved.

Plans read this update:

- [_bugs](../_bugs/plan.md) does not disagree. It was not
  rewritten.
- [cut-selection](../cut-selection/plan.md) was not rewritten.
- [device-error](../device-error/plan.md) does not edit the
  guide. It was not rewritten.
- [cli-install-update-data](../cli-install-update-data/plan.md)
  was not rewritten.
- [handbook-xdg](../handbook-xdg/plan.md) is the earlier
  state-home correction. It stays off the queue. It was not
  rewritten.

Nothing was taken off [`priority.md`](../../priority.md).
`handbook-xdg` was not added to it.

## Guide

Follow [Handbook](../../handbook.md), section Handbook
updates. Do not copy it.

## Checks

`agents/installed/.meta.toml` has `catalog_version` 0.9.20.
`agent-handbook update` refreshed documentation and
scripting. Nothing moved out of `agents/installed/`. Root
`AGENTS.md` was left unchanged. `agents.py` was not
restored. [handbook-xdg](../handbook-xdg/plan.md) stays
absent from [`priority.md`](../../priority.md).
