# Task: Typed travel segments between ordered cuts

| Field | Value |
| --- | --- |
| Plan | `agents/plans/cutter-path-and-coords.md` (residual) |
| Status | **in progress** (implementer done; await TF-B) |
| Tree | `~/dev/me/inkcut_luke/` (branch `refactor1`) |
| Priority | P1 |

## Goal

Emit first-class `kind='travel'` segments between ordered cut subpaths (and origin → first cut) so preview travel truth does not rely only on digging `moveTo`s out of a monolithic cut path. Device stream must stay pen-up for travels (no accidental blade-down).

## Acceptance

1. [x] After final cut subpath order in `Job.build_plan`, plan has explicit `travel` segments between consecutive cuts (and prologue travel from machine origin when start ≠ origin).
2. [x] `ToolpathPlan.to_device_stream()` concatenates cuts/weeds with pen-up between them (travel = move only, not cut); epilogue still unfiltered / after design map.
3. [x] Preview prefers `plan.travels()` (visible lines) over fallback `moves_to_lines(cuts)` when travels are present; epilogue still separate.
4. [x] Order algorithm still drives cut order via `optimized_path`; travel recomputes from that order. **Removed** `dist_to_origin` re-sort in `build_plan`.
5. [x] Unit tests: multi-subpath job has ≥1 travel; device stream / epilogue; filters skip epilogue with travels.
6. [x] Full suite green (`102 passed`).

## Non-goals

- CDT / min-cut weeds
- Hardware Summa measure
- Preview legend UI

## Session handoff (overwrite)

**Shipped (TF-A):**
- `Job.build_plan`: preserve subpath order from `optimized_path`/layout; emit `travel` (line geom) origin→first and between cuts; then weeds/epilogue.
- Travel storage: **line geometry** (`moveTo` start + `lineTo` end) for preview; `to_device_stream` converts travel → all `moveTo` (pen-up). Epilogue still move-only element walk.
- Device `process` work path: cut+weed only (travel not blade polygons).
- Preview: existing `plan.travels()` prefer path when non-empty.

**Key APIs/paths:**
- `inkcut/job/models.py` — `build_plan` segment loop
- `inkcut/job/toolpath.py` — `to_device_stream`, `_append_as_moves`
- `inkcut/device/plugin.py` — `_filter_work_and_epilogue`
- Tests: `test_toolpath_plan` (4 new), `test_preview_indicators` (+1), `test_filters` (+1)

**Next (TF-B / wrap-up):**
- Verify acceptance + suite; residual check
- Move task → `agents/plans/cutter-path-and-coords/completed/` when AGREE
- Commit on `refactor1` if not already
