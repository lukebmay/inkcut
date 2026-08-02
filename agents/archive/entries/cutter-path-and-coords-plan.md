# Archive: cutter-path-and-coords (full plan)

| Field | Value |
| --- | --- |
| Plan | `agents/plans/cutter-path-and-coords.md` |
| Date | 2026-07-16 |
| Status | Complete (software); hardware residuals |
| Branch | `refactor1` |

## Design choices

- Typed `ToolpathPlan` / `PathSegment` (cut | travel | weed | epilogue) instead of one monolithic path.
- Physical frame (`origin_corner`, `feed_axis`, `feed_sense`) separate from protocol (`swap_xy`, mirrors, scale).
- Epilogue (return / feed-after) generated in machine space after design map; filters must not move it.
- Preview layers drawn from plan + pure path indicators (not the failed AI rewrite’s preview-only origin).
- Weed modes: `frame` (legacy box), `grid` (clipped), `region` (nesting + fan/grid in waste) — not NP min-cut.

## Why

Summa D760 and similar need trustworthy origin/unroll without faking origin via design mirrors; return-to-origin must not ride design transforms.

## Major problems solved

- Monolithic path mixed epilogue with design transforms.
- Overlapping origin settings vs protocol quirks.
- Previews lacked origin/feed truth and travel toggles.
- Weedlines only outer rectangle.

## Residuals

- D760 not hardware-verified; no named driver preset yet.
- Typed travel still thin (moveTos often inside cut paths).
- ~~Optional preview legend~~ done; upstream packaging later.

## Key paths

- `inkcut/job/toolpath.py`, `weeds.py`, `models.py` (`build_plan`)
- `inkcut/device/frame.py`, `plugin.py` (`protocol_transform`, filter split)
- `inkcut/preview/indicators.py`
- `docs/device-frame-and-weeds.md`, `docs/SUMMA_D760.md`
- Tasks: `agents/plans/cutter-path-and-coords/completed/*`
