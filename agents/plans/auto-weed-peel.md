# Plan: Auto weed peel (adhesive vinyl)

| Field | Value |
| --- | --- |
| Status | **in progress** — first-pass `auto` shipped; tune next |
| Tree | `~/dev/me/inkcut_luke/` (branch `refactor1`) |
| Material | Adhesive vinyl first (HTV / reverse-weed later) |
| Depends on | Existing weed API (`inkcut/job/weeds.py`), ToolpathPlan `kind='weed'`, preview weed layer |

## Problem

Shop weeding is not “draw a grid over waste.” The waste sheet has **industrial adhesive**. A human peels waste off the liner while **keep graphics must stay put**. Bad weeds cause:

- One sticky mass connected through thin necks → pull lifts delicate keep corners
- Having to **work around** a fragile stem/corner instead of isolating it
- Huge connected waste fields that re-stick to the job mid-peel
- Too many jagged micro-cuts → slow, hard to grab, easy to snag keep edges

`frame` / `grid` / `region` are geometric partitions. They do not encode peel quality.

## Operator goals (product constraints)

| Priority | Constraint | Implication for cuts |
| --- | --- | --- |
| 1 | **Minimize cut count** | Prefer few strategic reliefs over dense lattices |
| 2 | **Smooth lines** | Long straight (or gently bent) cuts; avoid zig-zag / noisy polylines |
| 3 | **Protect delicate corners / thin stems** | **Relief from the delicate feature outward** so waste does **not** peel *around* that corner as one piece |
| 4 | **Bound sticky hazard** | Large waste must not stay connected through/near fragile keep areas |
| 5 | **Simple pieces, long peels when possible** | Each waste chunk should be an easy grab-and-pull strip or flap — not a complex maze per piece |
| 6 | **Peel direction irrelevant** | No preferred feed/operator axis; isotropic strategy |

**Adhesive vinyl only** for v1. Other materials later.

## Non-goals (v1)

- Global minimum cut count (NP-hard); “few and good” is enough
- HTV / reverse-weeding / transfer-tape workflows
- Perfect keep classification from open strokes (need closed outlines or layer hints later)
- CDT-as-default; only if a later slice proves it reduces cuts without jagging

## Existing baseline (keep)

| Mode | Keep as |
| --- | --- |
| `frame` | Outer box; always useful |
| `grid` | Manual dense fallback |
| `region` | Nesting + fan + grid demo; not the product default |

New mode: **`auto`** (UI label: **Auto peel**). Default when weedlines enabled once proven; until then opt-in next to frame/grid/region.

## Mental model

```text
keep  = design that stays on liner
waste = everything else still adhered

auto weeds = few smooth blade-down cuts ONLY through waste that:
  (a) open enclosed pockets (counters / holes) to outer waste
  (b) isolate delicate keep features so peels don't wrap them
  (c) split oversized waste into long, simple strips/flaps
```

## Algorithm: `auto` pipeline

All stages emit **smooth** segments (prefer single straight lines; optional one-bend polylines). Never cross keep fills (clearance inset).

### 0. Build waste topology

1. Closed cut subpaths → keep faces; nest via containment.
2. **Keep union** (with optional clearance inflate ≈ user param, default small).
3. **Outer waste** = padded work rect − keep union.
4. **Pockets** = interior holes / parent−children annuli (counters).
5. **Delicate sites** (heuristic):
   - high curvature tips / sharp convex corners of keep outline
   - thin stems (local width below threshold via offset or sample)
   - acute exterior corners that would snag a wrap-around peel
6. **Bridges**: thin waste corridors linking large waste cells past keep gaps.

### 1. Pocket release (must)

Each enclosed pocket gets **one smooth channel** to outer waste (shortest clear path or ray to nearest outer waste, clipped to waste, simplified to a straight cut when possible).

Goal: counters (O, A, logo holes) peel without digging.

### 2. Delicate isolation (highest quality win)

For each delicate site:

- Emit a **short smooth relief from the corner/stem outward into waste**, terminating at outer margin, a prior weed cut, or a safe waste node — **not** around the feature.
- Effect: splits “waste that would wrap the corner” into separate peels so the operator never peels one sticky piece **around** a thin tip.

This matches shop practice: *line from the bad corner out*, then peel the big field separately.

### 3. Bridge cuts (selective)

Only where waste necks are thinner than **bridge threshold** *and* connect large areas or pass near delicate sites:

- One **straight cut across the neck** (orthogonal to neck axis).

Skip bridges that are already wide enough for safe peel.

### 4. Oversized waste partition (few long strips)

If a waste connected component’s area (or max span) exceeds **max chunk size**:

- Prefer **few long parallel strip cuts** (or a single mid split + recurse) so pieces are **long easy peels**.
- Spacing ≈ max chunk width; **not** a full dense grid.
- Align strips to component principal axis (long direction) for longer pulls — direction is free, not tied to machine feed.
- Stop when every component is under the size cap.

### 5. Optional outer frame

If plot/copy frame padding is on, keep the classic outer rectangle (1 closed loop counts as few “cuts” for peel start). Configurable: always / never / only if no other weeds.

### Ordering of emission

1. Design cuts (unchanged)  
2. Weed segment(s): auto lines (pockets → delicate → bridges → strips → frame)  
3. Epilogue  

Preview: existing weed layer + legend. Meta: `mode='auto'`, stage tags for debug if needed.

## Parameters (user-facing, physical)

| Param | Meaning | Default (start) |
| --- | --- | --- |
| `weed_mode=auto` | Enable peel solver | opt-in, then default |
| Max chunk size | Largest waste span/area before strip split | ~50–80 mm span (tunable) |
| Clearance | Inset from keep so weeds don’t nick edges | small (device units) |
| Bridge threshold | Neck width that must be cut | ~2–4 mm |
| Delicate sensitivity | How eagerly corner/stem reliefs fire | normal |
| Min cut length | Drop micro-cuts | ~1–2 mm |
| Spacing (reuse) | Strip spacing when partitioning | maps from `weed_grid_spacing` or new field |

No peel-direction control (irrelevant).

## Quality criteria (acceptance for `auto`)

1. **Fewer cuts than `grid`** on typical logos/text at same padding (measure total weed path length and segment count).
2. **No keep slicing** (same test style as current grid/region).
3. Nested counters get **≥1 release** path to outer waste.
4. Synthetic **thin corner** fixture: at least one relief leaves the corner into waste (not only a wrap-around frame).
5. Oversized empty margin: **long strips**, not dense mesh.
6. Lines are **straight** (or very low vertex count) after simplify.
7. Preview shows weeds; plot/copy toggles still gate generation.
8. `pytest` green; new unit tests for stages.

## Implementation slices

### A — Topology + pocket release + mode wiring
- `auto` in `WEED_MODES`; UI option
- Pocket channels; tests; docs note

### B — Delicate corner/stem outward reliefs
- Heuristic + fixtures for thin corners / letter serifs class shapes
- Verify isolation behavior in tests (geometry probes)

### C — Bridges + oversized long strips
- Size cap; principal-axis strips; bridge cuts
- Compare cut count vs grid on fixtures

### D — Defaults + polish
- Consider defaulting weed mode to `auto` when enabling weedlines
- Docs in `docs/device-frame-and-weeds.md`; knobs in Weedlines dock
- Optional debug stage colors later (out of scope unless useful)

## Key files

| Area | Path |
| --- | --- |
| Solvers | `inkcut/job/weeds.py` (or `weeds/` package if it grows) |
| Job wiring | `inkcut/job/models.py` |
| UI | `inkcut/job/view.enaml` (WeedlinesDockItem) |
| Tests | `tests/test_weeds.py` + synthetic paths |
| Docs | `docs/device-frame-and-weeds.md` |

## Risks

| Risk | Mitigation |
| --- | --- |
| Delicate heuristic false positives → extra cuts | Sensitivity knob; prefer fewer; tests on simple rect (minimal extras) |
| Open SVG paths no fills | Fall back to frame + outer strips only; document |
| Over-aggressive bridges | Threshold + min length |
| Complexity explosion | Hard cap on weed segment count; then coarsen strips |

## Success

An adhesive-vinyl job with weedlines on + **Auto peel** produces **few smooth relief cuts** that make waste peelable in **simple long pieces**, isolate **delicate corners** with outward lines, open **holes**, and avoid one sticky mass threatening the rest of the design — without a jagged grid.

## Session handoff

**Design inputs locked (2026-08-02):** adhesive only; direction irrelevant; min cuts; smooth lines; outward relief from delicate corners; bound big sticky areas near delicate features; simple peels; prefer long weed areas.

**First pass (2026-08-02):**
- `weed_mode='auto'` in `inkcut/job/weeds.py` (`auto_weeds`): frame + pocket release + outward delicate reliefs + bridges + sparse strips
- UI: Weedlines dock “Auto peel (adhesive)”
- Preview: existing weed layer (`show_weeds`); job plot/copy weedlines on
- Visual SVG compare: `scripts/preview_auto_weeds.py` → `tests/data/weed_preview/`
- Tests: 110 passed (incl. auto fewer-than-grid, pocket, delicate tip, job plan)

**Next tune:** fewer false corner reliefs on rects; better bridge gap metric; max_chunk UI knobs; real SVG logos.
