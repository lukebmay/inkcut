# Device frame, path layers, and weed modes

Software guide for the cutter-path model in this fork. **Not hardware-verified.**

## Coordinate layers

```text
design (SVG / job layout)
  → physical machine frame   (origin_corner, feed_axis, feed_sense)
  → protocol                 (scale, mirrors, swap_xy, rotation)
  → device stream            (filters on cut/weed; epilogue unfiltered)
```

| Layer | Settings | Meaning |
| --- | --- | --- |
| **Physical** | `origin_corner`, `feed_axis`, `feed_sense` | Where machine `(0,0)` sits on the work rectangle; feed/unroll axis and sense |
| **Protocol** | `scale`, `mirror_x/y`, `swap_xy`, `rotation` | Driver/unit quirks. Advanced; defaults should stay identity for most machines |

Physical mapping lives in `inkcut/device/frame.py` and `Job.build_plan`. Protocol is applied in `Device.init` via `Device.protocol_transform` after the plan is built. Previews show the physical plan (plus optional protocol display transform).

### Origin and feed

- **Machine origin** is always `(0, 0)` in plan space after the physical map.
- **Joystick “system origin”** moves to machine `(0,0,0)`. Virtual origin is the post–feed-after position used for stacking jobs.
- **Feed after** places an *epilogue* move past the cut bbox along `feed_axis` in the direction of `feed_sense` (`positive` / `negative`). Default `negative` matches stock bottom-left + Y feed-after.

### Path segment kinds

| Kind | Role | Filtered? |
| --- | --- | --- |
| `cut` | Design blade-down geometry | Yes |
| `weed` | Weed-line blade-down geometry | Yes |
| `travel` | Pen-up between cuts (when typed) | Yes (path filters) |
| `epilogue` | Return-to-origin or feed-after | **No** |

`ToolpathPlan` (`inkcut/job/toolpath.py`) holds ordered segments. Protocols still receive a concatenated stream from `to_device_stream()`.

### Preview layers

Precut and live previews share toggles (Preview settings):

- Cuts, travel, weeds
- Origin crosshair
- Feed / unroll arrow
- **Legend** — corner key of named pens on both plots (`show_legend`, default on)

Colors: cut (solid), travel (pen-up), weed (distinct), epilogue (dashed travel-style).
Material, usable area (padding), and device area borders also appear in the legend
when present.

## Weed modes

Job setting `weed_mode` (`inkcut/job/weeds.py`):

| Mode | Behavior |
| --- | --- |
| `frame` | Padded rectangle around plot and/or each copy (classic box weedline) |
| `grid` | Axis-aligned grid over the extent; segments clipped away from keep geometry |
| `region` | Nest closed cut paths; fan/grid inside waste (outer minus islands) |
| `auto` | **Adhesive peel (first pass):** outer frame + pocket release + outward reliefs from sharp keep corners + selective bridges + **few long strips** on oversized waste (not a dense grid). Minimizes cuts; prefers smooth straight lines. See `agents/plans/auto-weed-peel.md`. |

`weed_grid_spacing` applies to grid/region and preferred auto strip pitch. Plot vs copy weed checkboxes and padding still apply. Weeds are typed plan segments and transform with design cuts; they never rewrite the machine epilogue.

### Auto peel knobs (Weedlines dock when mode is Auto)

| Setting | Job field | Role |
| --- | --- | --- |
| Strip / grid spacing | `weed_grid_spacing` | Preferred pitch between long strip cuts |
| Max peel chunk | `weed_max_chunk` | Split waste when span exceeds this (long easy peels) |
| Bridge width | `weed_bridge_width` | Cut sticky necks thinner than this between shapes |
| Keep clearance | `weed_clearance` | Hold weeds outside keep edges |
| Min cut length | `weed_min_cut` | Drop micro-segments |
| Delicate corner ° | `weed_delicate_angle` | Outward relief when corner turn ≥ this (lower → more reliefs) |

Preview: enable **Weed lines** under Preview → Layers (and turn on plot/copy weedlines on the job). Auto weeds use the weed pen and appear in the legend.

## Summa-class setup (expected, unverified)

See `docs/SUMMA_D760.md` for a placeholder profile. Confirm origin side and feed axis with a one-line test cut before trusting a preset.
