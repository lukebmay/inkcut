# Phase 3 — Preview markers + travel toggles

| Field | Value |
| --- | --- |
| Date | 2026-07-16 |
| Plan | `agents/plans/cutter-path-and-coords.md` |
| Task | `agents/plans/cutter-path-and-coords/completed/cutter-path-and-coords_phase3-preview-markers.md` |

## What

Shared QPainterPath origin crosshair and feed arrow (via `frame.feed_vector` / plan), plus cut/travel/weed/epilogue layer pens and config toggles on precut and live previews.

## Why

Previews needed machine-space truth (origin, unroll) and visible ordering (travel) without GraphicsObject indicators coupled to wrong transforms from the failed rewrite tree.

## Design choices

- Prefer dict/`QPainterPath` items for `set_preview` over heavy GraphicsObjects.
- Travel from plan when typed; else synthesize with `moves_to_lines` on cut path so order changes show up without full plan travel segments yet.
- Epilogue drawn as dashed travel line using segment `meta['end']`.

## Major paths

- `inkcut/preview/indicators.py`
- `inkcut/preview/plugin.py`, `settings.enaml`
- `inkcut/job/plugin.py`, `inkcut/device/plugin.py`
