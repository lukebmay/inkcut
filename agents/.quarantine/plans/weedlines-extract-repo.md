<!-- migrated from agents/tasks/weedlines-extract-repo.md by agents migrate-layout -->

# weedlines-extract-repo — Standalone Inkscape weedlines repo

**Status:** in progress (scaffold landed)
**Plan:** (none) — primary track
**Branch:** master (weedlines repo)
**Blocker:** (none)
**Updated:** 2026-08-21
**Repo:** `~/dev/me/weedlines` → https://github.com/lukebmay/weedlines
**Source archive:** `~/dev/me/inkcut_luke` @ `archive/pre-repartner-2026-08-21`

## Goal

Standalone Inkscape weedlines + `weedlib` core. Inkcut fork on hold.

## Acceptance

- [x] Repo at `~/dev/me/weedlines` + GitHub `lukebmay/weedlines`
- [x] `weedlines install` (idempotent symlink/copy)
- [x] Algorithms: `grid`, `frame`, `island-hop` (ex-`auto`)
- [x] Start / Cancel UI + live preview (ported dialog)
- [x] Progress/cancel hooks (`weedlib.progress`)
- [x] Env-gated logging (`WEEDLINES_LOG`)
- [x] Core importable as `weedlib` (for later inkcut)
- [x] Wave of tests green (136 passed / 4 skipped Job)
- [x] Pause/resume (dialog + `progress.install(pause=…)`; cancel while paused)
- [ ] Picture QA polish on island-hop fixtures
- [x] Preview script retargeted (optional Inkcut SVG loader)

## Session note (2026-08-21)

Extracted weedlib + Inkscape extension. Renamed auto → island-hop.
CLI install/update works. Logging via `WEEDLINES_LOG`.
Installed locally via `weedlines install` (symlinks). Added Pause/Resume
in progress hooks + dialog; reinstalled (symlinks already live).
