# Phase 4 — Weed line solvers

| Field | Value |
| --- | --- |
| Date | 2026-07-16 |
| Plan | `agents/plans/cutter-path-and-coords.md` |
| Completed task | `agents/plans/cutter-path-and-coords/completed/cutter-path-and-coords_phase4-weed-solvers.md` |

## What / why

Box-only weedlines do not peel nested waste (circle + letter). Phase 4 adds a strategy API and typed `weed` plan segments so previews can toggle weeds and the device still receives blade-down weed cuts in the stream.

## Design choices

- **`frame`**: legacy padded rect (default when weedlines enabled).
- **`grid`**: axis-aligned grid over padded bbox; sample-clip away keep fills.
- **`region`**: closed-path nesting (centroid containment) → waste = parent − children; fan rays + grid-in-waste; still adds outer frame.
- Weeds generated **after** copy layout, transformed with design through frame map, **before** machine epilogue — not mixed into cut subpath reorder.
- Copy layout extent still accounts for copy weed padding so stacks do not collide.

## Major paths

- `inkcut/job/weeds.py`
- `inkcut/job/models.py` (`build_plan`, `_weed_path_for`, config)
- `inkcut/job/view.enaml` (Weedlines dock)
- `tests/test_weeds.py`
