# homes

**Status:** ready

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

The developer writes what changed, why, and how it was checked.
The reviewer then writes the summary, the context worth keeping,
and the result.
