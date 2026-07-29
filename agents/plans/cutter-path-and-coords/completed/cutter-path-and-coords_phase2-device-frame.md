# Task: Phase 2 — Device frame abstraction

| Field | Value |
| --- | --- |
| Plan | `agents/plans/cutter-path-and-coords.md` |
| Status | **done** |
| Tree | `~/dev/me/inkcut_luke/` (branch `refactor1`) |
| Scope | Phase 2 only |

## Goal

Make physical machine frame settings (`origin_corner`, `feed_axis`, `feed_sense`) correct and **shared** so Summa-like machines do not need hacky design mirrors. Protocol knobs stay advanced.

## Acceptance

1. [x] `feed_sense` on device config (`positive`/`negative`); default `negative` preserves bottom_left + y feed-after
2. [x] Prefer `origin_corner` in new APIs; config/UI keep `origin_position` (alias)
3. [x] Pure helpers in `inkcut/device/frame.py` used by `build_plan` (+ material rect for live preview)
4. [x] Physical map via frame helpers; protocol scale/swap still residual in `build_plan` (documented)
5. [x] Tests: feed_sense flip, origin corner, baseline endpoints; suite green
6. [x] UI: feed_sense radios next to feed_axis
7. [x] No Phase 3 preview markers; no weed work; no hardware claim

## Session handoff (final)

**Status:** done

**Shipped:**
- `inkcut/device/frame.py` — pure physical frame (`origin_shift`, `design_to_machine_transform`, `feed_vector`, `feed_end_point`, `material_rect`, normalizers)
- `DeviceConfig.feed_sense` (`positive`/`negative`, default `negative`)
- `Job.build_plan(..., origin_corner=, feed_sense=)` + legacy `origin_position`
- Device UI Output tab: Feed Sense radios
- Live preview material/device area uses `material_rect`

**Key APIs/paths:**
- `inkcut/device/frame.py` — physical frame only
- `Job.build_plan(swap_xy, scale, origin_corner|origin_position, feed_axis, feed_sense, epilogue)`
- Config: `origin_position` (persist), `feed_axis`, `feed_sense`

**Mapping:** `feed_sense=negative` → −axis past min edge of cut bbox; `positive` → +axis past max edge. Default matches prior bottom_left + y.

**Tests:** `tests/test_toolpath_plan.py` (+ frame helpers); full suite **73 passed** (`PYTHONPATH=. pytest tests/ -q`)

**Residual (next / Phase 3+):**
- Protocol `scale` / `swap_xy` / mirrors still applied **inside** `build_plan` (and Device.init still passes them in). Full split to post-plan `Device.transform`/init deferred — risk to feed_after units and preview parity.
- Summa D760 values not hardware-verified; expected profile still in plan architecture B only.

**Next agent:** Phase 3 — preview origin/feed markers + travel toggles; use shared `frame.py` / plan `feed_vector`.
