# Task: Phase 3 — Preview markers + travel toggles

| Field | Value |
| --- | --- |
| Plan | `agents/plans/cutter-path-and-coords.md` |
| Status | **done** |
| Tree | `~/dev/me/inkcut_luke/` (branch `refactor1`) |
| Scope | Phase 3 only |

## Goal

Both precut and live previews tell the truth about **machine space** and ordering: origin mark, feed/unroll arrow, distinct cut vs travel (and weed/epilogue if available), with settings toggles.

## Acceptance

1. [x] Shared indicator helpers (QPainterPath) for origin + feed; use `frame.feed_vector` + machine origin
2. [x] Precut `_refresh_preview` shows origin + feed when enabled
3. [x] Live `_reset_preview` shows same static markers
4. [x] Distinct pens: cut / travel / weed / epilogue (dashed travel)
5. [x] Preview settings checkboxes (`config=True`)
6. [x] Prefer `Job.plan` segments; synthesize travel from cut moveTo when plan has no travel segs; fallback move_path/cut_path
7. [x] Tests for indicator geometry / plan layers
8. [x] `pytest tests/ -q` green (**84 passed**)
9. [x] No new origin math outside `frame.py` / plan

## Session handoff (final)

**Status:** done

**Shipped:**
- `inkcut/preview/indicators.py` — pure path builders + plan layer helpers
- `PreviewPlugin` layer toggles + `layer_view_items()`; pens for weed/epilogue/origin/feed
- Precut + live wired through shared helpers
- `inkcut/preview/settings.enaml` Layers checkboxes
- `tests/test_preview_indicators.py`

**Key APIs/paths:**
- `origin_crosshair_path`, `feed_arrow_path`, `moves_to_lines`, `plan_layer_paths`, `epilogue_as_travel`
- `PreviewPlugin.layer_view_items(plot, plan=..., map_path=...)`
- Toggles: `show_cuts`, `show_travel`, `show_weeds`, `show_origin`, `show_feed` (defaults on)

**Tests:** 84 passed (`PYTHONPATH=. pytest tests/ -q`)

**Residual:**
- Plan still packs all design strokes as one `cut` segment (travel synthesized from moveTo); typed travel/weed segs wait on ordering/Phase 4
- Live progressive pen still pen_down/pen_up; static layers match toggles
- Protocol scale/swap residual from Phase 2 unchanged

**Next agent:** Phase 4 — weed line solvers (`frame` + `grid` + region)
