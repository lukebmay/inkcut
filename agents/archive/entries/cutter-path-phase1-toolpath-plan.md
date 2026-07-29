# Cutter path Phase 1 — ToolpathPlan

| Field | Value |
| --- | --- |
| Date | 2026-07-16 |
| Plan | `agents/plans/cutter-path-and-coords.md` |
| Task | `agents/plans/cutter-path-and-coords/completed/cutter-path-and-coords_phase1-toolpath-plan.md` |
| Tree | `inkcut_luke` / `refactor1` |

## What / why

Jobs mixed design geometry and feed-after/`moveTo` epilogue in one `QPainterPath`, so later transforms could drag machine return/feed. Phase 1 introduced typed segments so epilogue is built **after** frame map, in machine coordinates only.

## Design choices

- `PathSegment.kind`: cut | travel | weed | epilogue
- `Job.build_plan()` does the real work; `create()` stays as concatenated stream for callers
- Stock match: `feed_to_end=False` → no return segment (`epilogue='none'`); optional `epilogue='return'` for machine origin without design transforms
- Pure moveTo epilogues applied via element walk in `to_device_stream` (Qt `addPath` drops move-only paths)

## Major paths

- `inkcut/job/toolpath.py`
- `inkcut/job/models.py` (`build_plan`, `create`)
- `inkcut/device/plugin.py` (`Device.init`)
- `tests/test_toolpath_plan.py`
