<!-- migrated from agents/tasks/cli-install-update-data.md by agents migrate-layout -->

# cli-install-update-data — `inkcut` CLI: install, update, data

**Status:** optional
**Plan:** (none)
**Branch:** master
**Blocker:** (none)
**Updated:** 2026-08-21
**Target repo:** `~/dev/me/inkcut` (`lukebmay/inkcut`) — **on hold**
**Reference (archive):** `~/dev/me/inkcut_luke`
**UX reference:** `~/dev/me/shellrc` (`shellrc` install/update),
`~/dev/me/forge` (`forge install`)
**Data reference:** `~/Desktop/inkcut-data/inkcut-data.py`

**Optional — skip unless the operator asks.** Inkcut fork is on hold.
Active CLI work is `weedlines install` in the weedlines repo.

## Goal

Build a Python `inkcut` CLI (extend or replace the stock plugin CLI if
ours is better) with:

1. **`inkcut install`** — run the installer **idempotently** to upgrade
   from any prior Inkcut (upstream release **or** our fork).
2. **`inkcut update`** — if the git tree is clean: `git pull` then
   install; if dirty: **skip pull**, install the dirty tree; consistent
   status UI like `shellrc` / `forge install`.
3. **`inkcut data save|load|list|…`** — fold in the device data scripts
   from `~/Desktop/inkcut-data/` so operators no longer need a Desktop
   one-off.

Also keep / improve any useful archive CLI (e.g. `install-plugin` for
Inkscape send extensions) under the same UX family.

## Acceptance

- [ ] `inkcut install` idempotent; safe to re-run; upgrades stock → fork
- [ ] `inkcut update` clean-tree pull+install; dirty-tree install-only
  with a clear message (no silent discard of local changes)
- [ ] CLI output matches shellrc/forge style: colored status lines,
  phases, non-zero on real failure, `--dry-run` where destructive
- [ ] `inkcut data save` / `inkcut data load` / `inkcut data list`
  (parity with `inkcut-data.py`; extend if natural)
- [ ] Docs: short README or `inkcut --help` / subcommand help
- [ ] Compare archive `inkcut/cli/` vs upstream; keep the better base

## Context for the next agent (complete + succinct)

### Archive CLI

- Entry: `inkcut = inkcut.app:main` (setuptools console_scripts)
- Plugin CLI: `inkcut/cli/plugin.py` (argparse subcommands via Enaml
  declarations)
- Archive addition: `inkcut/cli/install_plugin.py` —
  `inkcut install-plugin` symlinks/copies Inkscape send + weed
  extensions (`tests/test_install_plugin.py`)
- Upstream stock has **no** device export/import commands

### Data script to port

- `~/Desktop/inkcut-data/inkcut-data.py` + README
- Reads/writes `~/.config/inkcut/inkcut.device.json` (jsonpickle Atom)
- Commands: `save`, `load`, `list`
- Warn: close Inkcut before `load` so GUI does not overwrite on exit

### Install UX to mirror

- `shellrc` install/reinstall/update flow
  (`~/dev/me/shellrc/commands/shellrc.zsh`)
- `forge install` helpers (`~/dev/me/forge/scripts/forge/_lib.zsh`,
  ansi color contract)
- Prefer Python implementation in-tree; may vendor small ansi helpers
  consistent with `agents/installed/ansi-colors.md` if present after
  agents catalog is copied — otherwise keep a thin local helper

### Suggested command map

```text
inkcut install [--dry-run]
inkcut update  [--dry-run]
inkcut data list
inkcut data save [--all | NAME…] [-o DIR]
inkcut data load FILE… [--replace]
inkcut install-plugin …   # keep if still needed for send extensions
```

Weedlines Inkscape install moves to the **weedlines** repo CLI (task 3);
do not forever couple weed extension install to inkcut once extracted.

### Enable / test

- Dry-run paths with no writes
- Dirty vs clean git fixtures (temp clone)
- Round-trip `data save` → `data load` on a copy of device json

## Session note

Created 2026-08-21 with clean-fork restart. Not started.
