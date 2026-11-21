# handbook-xdg-homes

**Rank:** 3

## Goal

The running app follows the catalog 0.9.15 home rule. One
resolver is the only code that reads the XDG home variables.
Everyone else uses `INKCUT_CONFIG_HOME`, `INKCUT_DATA_HOME`,
`INKCUT_STATE_HOME`, `INKCUT_CACHE_HOME`, and
`INKCUT_RUNTIME_DIR`. When neither `INKCUT_CONFIG_HOME` nor
`XDG_CONFIG_HOME` is set, plugin state stays
`~/.config/inkcut/{plugin id}.json`. Logs move to the state
home. Do not add a data, cache, or runtime directory the app
does not already use. Do not build the install CLI. This plan
stays off the queue.

## Guide

[Project](../../project.md) and
[Architecture](../../architecture.md) name today's plugin
state directory. That sentence stays the default. Do not edit
the guide. The rule to reach is
[Scripting](../../installed/scripting.md), section XDG
directory variables. Do not copy it.

## Checks

- [ ] A set `INKCUT_CONFIG_HOME` is the config home. Nothing
      appends another `/inkcut`.
- [ ] The app variable unset and `XDG_CONFIG_HOME` set uses
      `$XDG_CONFIG_HOME/inkcut`.
- [ ] Both unset uses `~/.config/inkcut`.
- [ ] Plugin JSON is still `{plugin id}.json` in that home.
- [ ] New logs are written under the state home. The old
      `~/.config/inkcut/logs` files are left in place.
- [ ] No file outside the resolver reads an XDG home variable.
