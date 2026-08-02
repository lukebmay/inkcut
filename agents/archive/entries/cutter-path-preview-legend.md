# Preview legend UI

| Field | Value |
| --- | --- |
| Date | 2026-08-01 |
| Plan | cutter-path-and-coords |
| Task | `agents/plans/cutter-path-and-coords/completed/cutter-path-and-coords_preview-legend.md` |

## What / why

Phase 3 left an optional residual: a plot legend so users can read cut/travel/weed/origin/feed pens without memorizing colors. Implemented as a config-backed `show_legend` toggle and pyqtgraph corner legend on precut + live views.

## Design choices

- Reuse pyqtgraph `PlotItem.addLegend` + `name` on plot items (auto-register on `addItem`).
- Legend only lists items currently drawn (respects layer toggles).
- Fixed `PainterPathPlotItem` construction: never pass `QPainterPath` into `PlotCurveItem.setData` (that path threw `TypeError` / wrong `updateData` signature).

## Paths

- `inkcut/preview/plot_view.py`, `plugin.py`, `settings.enaml`, `view.enaml`
- `inkcut/job/plugin.py`, `inkcut/device/plugin.py`, `inkcut/device/view.enaml`
- `tests/test_preview_indicators.py`
