# handbook-update

**Rank:** 3

## Goal

Inkcut's installed handbook is catalog 0.9.18. Before this update
it was 0.9.15. The range is `agent-handbook changelog 0.9.15`.
This plan does not edit product code. It stays off the queue. The
next handbook update rewrites this file.

## Range

0.9.18 is the handbook update procedure. That section is now in
[the handbook](../../handbook.md). It asks for no product edit.

0.9.17 says a program that is one source file, and a script that
is the whole program, stays one file until it passes 5000 lines.
That replaced the 3000 line count. Skip that older count. This
repo has no one-file program or whole-program script over 5000
lines, and no plan that would split one.

0.9.16 says a source file aims for under 1200 ordinary lines. A
split noticed during other work is a later file-size plan. The
one-file count in that entry is the one 0.9.17 replaced.
`inkcut/device/plugin.py` was 1398 lines. It is part of the device
package, not a one-file program. That split is done. The plan is
[handbook-device-plugin-split](../.archived/handbook-device-plugin-split/plan.md).
`plugin.py` is under 1200 lines.

0.9.15 says an installable app reads `INKCUT_CONFIG_HOME` and the
other app homes. The resolver is the only reader of the XDG
variables. That correction is done. The plan is
[handbook-xdg-homes](../.archived/handbook-xdg-homes/plan.md).
With both variables unset, plugin state stays
`~/.config/inkcut/{plugin id}.json`.

## Older plans

Plans opened before catalog 0.9.18 may omit the `handbook-`
prefix. This is the first handbook-update in this repo. Those
plans were found by what they change, not by the prefix. After
the handbook plans opened for 0.9.18 are finished, later
handbook plans use the prefix.

[cut-selection](../cut-selection/plan.md) changes which SVG
objects a cut opens. It does not disagree with the installed
handbook. It was not rewritten.

[cli-install-update-data](../cli-install-update-data/plan.md)
is the optional install CLI. It names the default device file
`~/.config/inkcut/inkcut.device.json`. That path is still the
one when neither `INKCUT_CONFIG_HOME` nor `XDG_CONFIG_HOME` is
set. It was not rewritten. The home rule is the XDG plan above.

No file-size plan said 1000 lines. None was dropped. Nothing
was taken off [`priority.md`](../../priority.md).

## Guide

Follow [Handbook](../../handbook.md), section Handbook updates
and section Source files. The home rule is
[Scripting](../../installed/scripting.md), section XDG directory
variables. Do not copy them.

## Checks

`agents/installed/.meta.toml` has `catalog_version` 0.9.18.
`agents/handbook.md` has the Source files counts from this range
and the Handbook updates section. The topic plans above exist
and are absent from [`priority.md`](../../priority.md).
