# Task: Preview legend UI

| Field | Value |
| --- | --- |
| Plan | `agents/plans/cutter-path-and-coords.md` |
| Status | **in progress** |
| Tree | `~/dev/me/inkcut_luke/` (branch `refactor1`) |
| Scope | Optional residual: legend on precut + live previews |

## Goal

Show a color/style legend on the plot so origin, feed, cut, travel, weed, and epilogue pens are readable without opening settings.

## Acceptance

1. [ ] `show_legend` config toggle in Preview settings (default on)
2. [ ] Precut and live PlotViews show pyqtgraph legend when enabled
3. [ ] Legend entries match visible layers (names + pens)
4. [ ] Material / padding / device area named when present
5. [ ] `PainterPathPlotItem` constructs with path + `name` (fix broken QPainterPath ctor path)
6. [ ] Tests for named layer items + item construction
7. [ ] `pytest tests/ -q` green
8. [ ] Docs / plan residual updated

## Session handoff

*(overwrite when done)*
