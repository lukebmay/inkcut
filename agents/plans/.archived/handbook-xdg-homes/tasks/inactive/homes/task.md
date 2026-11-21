# homes

**Status:** done

## Goal

One session makes plugin state and logs use the app-home
resolver. The default config directory does not move.

## Do

Add one resolver. It is the only reader of `XDG_CONFIG_HOME`,
`XDG_DATA_HOME`, `XDG_STATE_HOME`, `XDG_CACHE_HOME`, and
`XDG_RUNTIME_DIR`.

Config is live. `inkcut/core/models.py` builds the plugin state
path from the config home. `inkcut/app.py` and the log URL in
`inkcut/ui/manifest.enaml` use the state home for logs.

State is pinned. Record the absolute state home once and keep
using that record. A later change of `INKCUT_STATE_HOME` or
`XDG_STATE_HOME` does not move logs. This repo has no install
command that records homes. Do not start
`cli-install-update-data` to make one. Record the state home
the first time the app resolves it.

Do not invent a data home, a cache home, or a runtime directory.
Do not delete logs already under `~/.config/inkcut/logs`.

## Checks

The checks are on [plan.md](../../../plan.md).

## Note

### Summary

`inkcut/core/homes.py` is the only product reader of the XDG home
variables. Plugin JSON uses the live config home. New logs use
the pinned state home. The guide was not edited.

### Context

Config is resolved on each call. A set `INKCUT_CONFIG_HOME` is
that path, with nothing appended. Otherwise
`$XDG_CONFIG_HOME/inkcut`, otherwise `~/.config/inkcut`. Plugin
state is `{config home}/{plugin id}.json`.

State is pinned because there is no install command. The first
`state_home()` writes the absolute path to
`{config home}/state-home`. A later `INKCUT_STATE_HOME` or
`XDG_STATE_HOME` does not move it. The pin is a file in the
config directory the app already uses, not a data directory.
`init_logging`, Help / Logs, and the startup error dialog use
`{state home}/logs`. Files already in `~/.config/inkcut/logs`
are not deleted or moved.

`data_home`, `cache_home`, and `runtime_dir` use the same lookup
and create no directory. The app does not call them. Data is not
pinned. Runtime raises when both variables are unset and does
not use `/tmp`.

`inkcut/core/` has more than one source file and still has no
directory index. That handbook gap was already there. It is not
this task.

### Result

No defect. See [cr-01.md](cr-01.md). Re-ran
`QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_homes.py`:
14 passed, under a temporary `HOME`. `~/.config/inkcut` was not
written: its mtime was unchanged, `state-home` was not created,
and the old logs directory's mtime was unchanged.
