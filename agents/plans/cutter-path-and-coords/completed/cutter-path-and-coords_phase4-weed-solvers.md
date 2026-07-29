# Task: Phase 4 — Weed line solvers

| Field | Value |
| --- | --- |
| Plan | `agents/plans/cutter-path-and-coords.md` |
| Status | **done** |
| Tree | `~/dev/me/inkcut_luke/` (branch `refactor1`) |
| Scope | Phase 4 only |

## Goal

Refactor box weedlines into a weed strategy API; implement **`frame`** (current) + **`grid`** (clipped to waste); land a practical **`region`** mode (nesting + fan or grid-in-waste) for circle+letter class problems. Weed segments are `kind='weed'` on the plan when possible.

## Acceptance

1. [x] Weed strategy API (`inkcut/job/weeds.py`): `frame`, `grid`, `region`
2. [x] `_add_weedline` delegates to `frame_weeds`; plan uses strategies via `_weed_path_for`
3. [x] `build_plan` emits `PathSegment(kind='weed')` (transforms with design; epilogue after)
4. [x] Job config: `weed_mode`, `weed_grid_spacing`; plot/copy flags + padding kept; default mode `frame`
5. [x] UI: mode combo + spacing in Weedlines dock
6. [x] Tests: frame / grid no-slice / region nested; plan typed weed
7. [x] `pytest tests/ -q` green (**91 passed**)
8. [x] No NP-hard optimization

## Session handoff (final)

**Status:** done

**Shipped:**
- `inkcut/job/weeds.py` — `generate_weeds`, `frame_weeds`, `grid_weeds`, `region_weeds`
- Job: `weed_mode`, `weed_grid_spacing`; weeds not baked into cut path; typed plan segment
- `WeedlinesDockItem`: mode combo + grid spacing
- `tests/test_weeds.py`

**Key APIs/paths:**
- `weeds.generate_weeds(keep, mode=, padding=, spacing=)`
- `Job.weed_mode` ∈ `frame|grid|region`; `Job.weed_grid_spacing` (default 25)
- `Job._weed_path_for` / `_extent_with_copy_weed`
- Plan: cut → weed → epilogue; `to_device_stream` includes weeds (blade-down)

**Tests:** 91 passed (`PYTHONPATH=. pytest tests/ -q`)

**Residual:**
- Region is nesting + fan + grid-in-waste (not CDT / min cuts)
- Keep/waste from closed-path nesting only (open strokes ignored for fill)
- Typed travel segments still thin; protocol scale/swap residual (Phase 5)

**Next agent:** Phase 5 — polish / protocol hardening
