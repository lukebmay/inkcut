# Task: Phase 1 — ToolpathPlan + epilogue separation

| Field | Value |
| --- | --- |
| Plan | `agents/plans/cutter-path-and-coords.md` |
| Status | **done** |
| Tree | `~/dev/me/inkcut_luke/` (branch `refactor1`) |
| Scope | Phase 1 only |

## Goal

Introduce typed toolpath layers so **return-to-origin / feed-after (epilogue)** are generated in machine space and **never** pass through job design transforms (scale / mirror / swap applied to design cuts).

## Acceptance

1. [x] New module `inkcut/job/toolpath.py` with `PathSegment` and `ToolpathPlan`
2. [x] `Job.create()` refactored via `build_plan()`: cuts → frame map → epilogue
3. [x] `Device.init()` consumes plan; concatenate at protocol boundary
4. [x] Default bottom_left + feed y regression baseline preserved (stock: no return path when `feed_to_end=False`)
5. [x] Unit tests under `tests/test_toolpath_plan.py`
6. [x] Existing tests still pass (`pytest tests/ -q` → 69 passed)
7. [x] No leftover test residue

## Session handoff (final)

**Status:** done

**Shipped:**
- `inkcut/job/toolpath.py` — `PathSegment`, `ToolpathPlan` (`cuts`/`travels`/`weeds`/`epilogue`/`to_device_stream`)
- `Job.build_plan(...)` builds cut geometry, applies device scale/swap/origin, **then** appends machine epilogue
- `Job.create()` returns `plan.to_device_stream()` for API compat
- `Device.init()` uses `job.build_plan(...).to_device_stream()`
- Stock match: `feed_to_end=False` → epilogue mode `none` (no return segment). Optional `epilogue='return'` adds `moveTo(0,0)` in machine space for tests/future.

**Key APIs/paths:**
- `inkcut/job/toolpath.py` — `PathSegment(kind, path, meta)`, `ToolpathPlan`
- `Job.build_plan(swap_xy, scale, origin_position, feed_axis, epilogue=None)`
  - `epilogue`: `None` → auto (`feed` if `feed_to_end` else `none`); or `'none'|'feed'|'return'`
- `Job.plan` — last built plan
- `ToolpathPlan.to_device_stream()` — protocol concat (handles move-only epilogue)

**Tests:** `tests/test_toolpath_plan.py` (9); full suite 69 passed

**Next agent (Phase 2):**
- Stabilize `origin_corner` + `feed_axis` + `feed_sense`
- Pure `design_to_machine_transform(...)` shared by create/previews
- Protocol transforms only in `Device.transform` / init protocol stage
- Do not invent feed_sense in residual Phase 1 code paths
