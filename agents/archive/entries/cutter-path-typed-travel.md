# Archive: typed travel residual

| Field | Value |
| --- | --- |
| Plan | `agents/plans/cutter-path-and-coords.md` |
| Date | 2026-08-01 |
| Status | Complete |
| Branch | `refactor1` |

## Design choices

- Travel segments store **line geometry** for preview; `to_device_stream` emits all `moveTo` (pen-up).
- Device `process` work path = cut+weed only so travel lines never become blade polygons.
- Removed `dist_to_origin` re-sort so job order algorithms survive layout/copies.

## Why

Preview and ordering truth need first-class pen-up hops; digging `moveTo`s out of one cut path was thin and order was silently overwritten.

## Key paths

- `inkcut/job/models.py` (`build_plan`), `toolpath.py` (`_append_as_moves`)
- `inkcut/device/plugin.py` (`_filter_work_and_epilogue`)
- Task: `agents/plans/cutter-path-and-coords/completed/cutter-path-and-coords_typed-travel.md`
