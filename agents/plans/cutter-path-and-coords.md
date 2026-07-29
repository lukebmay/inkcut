# Plan: Cutter path layers, coordinate systems, previews, weed lines

| Field | Value |
| --- | --- |
| Status | **Complete (software)** — hardware / upstream residuals noted |
| Priority | P0 (makes Summa D760 and general cutters trustworthy) |
| Working tree | **`~/dev/me/inkcut_luke/`** (branch `refactor1`) |
| Discard / reference only | **`~/dev/me/inkcut_ai_fail/`** (branch `ref2`) — failed AI rewrite |
| Upstream base | Inkcut 2.1.7 (`1453a8b`) |

## Which tree is which

| Path | Branch | What it is | Verdict |
| --- | --- | --- | --- |
| **`inkcut_luke/`** | `refactor1` | Unfinished fork: origin corner + feed-axis UI, origin-aware `Job.create()`, logging, live-preview origin marker attempt | **Continue here** |
| **`inkcut_ai_fail/`** | `ref2` | AI rewrite attempt: lots of docs, preview indicators (origin/feed/debug Cartesian), origin transform mostly in **preview only** | **Do not continue as base**; cherry-pick ideas (indicators, analysis) only |

Both remotes historically pointed at `lukebmay/inkcut`. Divergence from master:

- **inkcut_luke**: real path math in `job/models.py` + `device/plugin.py` (~470 LOC of fork work).
- **inkcut_ai_fail**: mostly docs + indicators; `Job.create()` still closer to stock; origin handling inconsistent between main vs live preview.

**Default for all future work:** implement in `inkcut_luke/`. Use `inkcut_ai_fail/` only as reference.

---

## Problem summary (user goals → root causes)

### 1. Monolithic path + transforms on machine epilogue

Today the pipeline builds one `QPainterPath` (`Job.model`) that mixes:

- design cut geometry
- copy layout
- box weedlines
- padding / origin shifts
- device scale / mirror / swap
- **epilogue motion**: stock always ends with `model.moveTo(end_point)` where return-to-origin is `(0,0)` and feed-after is a point on the feed axis

Anything that later maps that path (device `transform`, filters, preview stacking) can also move the return/feed segment. UI “Return to origin” is `not feed_to_end`; it is still a path segment in stock, not a separate machine command layer.

`move_path` / `cut_path` already *approximate* pen-up vs pen-down by reinterpreting `moveTo` vs line elements, but:

- travel between ordered subpaths is not first-class
- there is no toggle to hide travel in precut preview
- algorithm comparison (Normal vs Shortest Path, etc.) only changes order; travel visualization is weak and same style as other pen-up

### 2. Coordinate system abstraction is incomplete / overlapping

**inkcut_luke** added:

- `origin_position`: `bottom_left|bottom_right|top_left|top_right`
- `feed_axis`: `x|y`

…while **keeping** `swap_xy`, `mirror_x`, `mirror_y`, `scale`, `rotation`.

That is directionally right (physical vs protocol) but still wrong in practice for machines like the **Summa D760**:

- vinyl unrolls **toward the operator**
- origin is on the **right**
- fork still forces design transforms + origin shift inside one `create()`, reorders subpaths by distance to `(0,0)`, and ties feed offset to origin string parsing (`'left' in origin_position`)

**inkcut_ai_fail** AI rewrite mostly moved origin into **preview transforms** and wrote long docs claiming “implementation complete” while device output and main preview stayed inconsistent — classic failed rewrite.

Missing abstraction pieces:

- **feed sense / unroll direction** (toward vs away operator, or signed axis), not only “which axis”
- clear split: **physical machine frame** (what the operator sees) vs **protocol frame** (bytes to the cutter)
- no reliance on “monolithic path transforms” to place origin

### 3. Previews lack machine markings

There are two previews:

| Preview | Plugin / owner | Role |
| --- | --- | --- |
| **Precut / main** | `inkcut.job` → `inkcut.preview.preview` | Job layout before send |
| **Live** | `inkcut.device` → `inkcut.preview.live_preview` | Progress while cutting |

Stock already draws media, padding, device area, pen-up, pen-down. Missing / weak:

- origin mark (inkcut_luke live preview has a rough red `(0,0)` ellipse; main preview does not consistently)
- vinyl **unroll / feed direction** arrow
- optional axis frame (X/Y, operator-facing)
- toggles for travel vs cuts (and later weed segments)

### 4. Weed lines are only outer boxes

Existing `_add_weedline` draws a **rectangle** around plot/copy padding. That helps peel a frame; it does **not** segment large waste regions (e.g. filled circle with a letter island that must stay).

Need algorithms that cut **waste** into peelable chunks without cutting keep geometry (or only cutting along intentional bridges).

---

## Target architecture

### A. Typed toolpath layers (not one path)

Replace “one QPainterPath is the job” with a small structure built in stages:

```text
Document paths
    → filter / layer select
    → order algorithm (permutation of cut subpaths only)
    → job layout (scale, rotate, mirror, copies, padding)   [design space]
    → device frame map (origin corner, feed sense, protocol mirrors)  [machine space]
    → travel segments (pen-up between cuts) computed from ordered cuts
    → machine epilogue (return origin / feed after) appended in machine space only
    → optional weed segments (typed as cut, style=weed)
```

Suggested model (names flexible):

```python
class PathSegment:
    kind: 'cut' | 'travel' | 'weed' | 'epilogue'  # epilogue is travel-like
    path: QPainterPath
    meta: dict  # e.g. algorithm, weed_group, subpath_index

class ToolpathPlan:
    segments: list[PathSegment]
    origin: QPointF          # machine origin in preview/device space
    feed_vector: QPointF     # unit vector: material unroll / feed positive
    bounds: QRectF

    def cuts(self) -> QPainterPath: ...
    def travels(self) -> QPainterPath: ...
    def weeds(self) -> QPainterPath: ...
    def to_device_stream(self) -> QPainterPath:  # concatenate for existing protocols
```

**Rules:**

1. Job geometric transforms apply only to `cut` and `weed` (and layout of copies).
2. Device frame map applies to cuts/weeds/travels consistently **once**.
3. **Epilogue** (return to origin, feed-after) is generated **after** that map, in machine coordinates, never scaled/mirrored by job design transforms.
4. Prologue (move from current machine origin to first cut) is also travel, not part of design geometry.
5. Existing protocols can keep consuming a concatenated path; new code prefers segments.

**Where to implement:** primarily `inkcut/job/models.py` (`create` → `build_plan`), `inkcut/device/plugin.py` (`init` / `process`), preview refresh in job + device plugins.

### B. Simplest non-overlapping device settings

User-facing (physical, operator view):

| Setting | Values | Meaning |
| --- | --- | --- |
| `origin_corner` | four corners | Where machine `(0,0)` sits on the work/material rectangle when facing the machine |
| `feed_axis` | `x` / `y` | Axis along which material feeds |
| `feed_sense` | `positive` / `negative` (or `toward_operator` / `away`) | Direction of unroll / feed-after along that axis |

Driver/protocol (advanced, rarely touched; defaults per driver):

| Setting | Meaning |
| --- | --- |
| `swap_xy` | Protocol axis swap |
| `mirror_x` / `mirror_y` | Protocol axis flips |
| `scale` / `rotation` | Protocol unit/orientation fixes |

**Non-overlap rule:** user settings never encode protocol quirks; protocol settings never encode “where is the knob on my Summa.” Compose as:

```text
design_point
  → job layout (design space, origin at job-local 0)
  → map_to_machine(origin_corner, feed_axis, feed_sense)
  → map_to_protocol(swap_xy, mirrors, scale, rotation)
```

**Summa D760 profile (expected):**

- `origin_corner = bottom_right` (or top_right — confirm on machine with a 1-line test cut)
- `feed_axis = y` (or x — confirm)
- `feed_sense = toward_operator`
- protocol mirrors/swap: only whatever the HPGL/DMPL dialect needs after physical map is correct

Ship a named preset once verified; do not force users to invent mirrors to fake origin.

### C. Preview system (both precut and live)

Shared indicator helpers (salvage from `inkcut_ai_fail/inkcut/preview/indicators/` if clean):

- **Origin marker** at machine origin (crosshair + label)
- **Feed / unroll arrow** from origin or mid-bed along `feed_vector`
- **Cut** paths (solid, current pen_down or stronger)
- **Travel** paths (distinct color; default on in precut)
- **Weed** paths (third style)
- **Material** + padding + device area in the **same** machine frame as cuts

UI toggles (precut settings + maybe job panel):

- Show cuts
- Show travel / ordering paths
- Show weed lines
- Show origin
- Show feed direction

Changing **order algorithm** must immediately recompute travel segments so you can *see* Normal vs Shortest Path vs Min X, etc.

Live preview: same markers (static origin/feed); progressive pen follows segments with cut vs travel colors.

### D. Weed-line solvers

Keep existing box weedline as `WeedMode = frame`.

Add modes:

1. **`frame`** — current padded rectangle (plot and/or per-copy).
2. **`grid`** — axis-aligned grid over job bbox; **clip away** segments that intersect keep geometry (or only emit segments inside waste). Configurable spacing.
3. **`region`** (better default later):
   - Build polygons from closed cut subpaths.
   - Compute nesting (parent/child via point-in-polygon).
   - Classify annuli / waste regions (parent filled region minus children). Without explicit “cut vs weed layer” from SVG, treat **all strokes as cuts** and waste as **interior of outermost closed paths minus nested islands** when fill rule is even-odd / nesting depth odd-even — document the assumption; allow optional “weed this layer” later.
   - Segment each waste region with a **cheap** partition:
     - **v1:** grid clipped to waste (fast).
     - **v2:** ray/fan cuts from outer boundary to inner islands (good for circle+letter).
     - **v3:** constrained Delaunay on waste + spanning tree edges as weed cuts (few cuts, not optimal; avoids full set-cover NP framing).

Do **not** chase global minimum cut count (NP-hard set-cover / arrangement problems). Target: “small number, peelable, never slice keep paths.”

Weed segments are `kind='weed'` cuts: they go to the device as blade-down, preview-toggleable, and are **not** reordered away from their region group if that hurts peeling (optional: cut all design cuts first, then weeds, or weeds last).

---

## Phased implementation

### Phase 0 — Housekeeping

- [x] Rename trees: `inkcut` → `inkcut_ai_fail`, `inkcut1` → `inkcut_luke`.
- [x] Install agentsmd system (`gen-agentsmd`); write `agents/project.md`.
- [x] This plan under `agents/plans/cutter-path-and-coords.md` with updated paths.
- [ ] Optionally tag/archive `inkcut_ai_fail` ref2 so it is not confused later.
- [x] `docs/SUMMA_D760.md` stub (**unverified** expected values; measure later).

### Phase 1 — ToolpathPlan + epilogue separation (foundation)

**Goal:** return-to-origin / feed-after never pass through job design transforms.

- [x] Introduce `ToolpathPlan` / `PathSegment` (can live in `inkcut/job/toolpath.py`).
- [x] Split `Job.create()` into: build cut geometry → map frame → append epilogue travels.
- [x] `Device.init()` consumes plan; concatenate only at protocol boundary.
- [x] Preserve current behavior for default bottom-left + feed y as regression baseline.
- [x] Unit tests: transform scale/mirror/swap does not move epilogue endpoint off machine origin; feed-after lands on correct axis/sense.

**Completed task:** `agents/plans/cutter-path-and-coords/completed/cutter-path-and-coords_phase1-toolpath-plan.md`

### Phase 2 — Device frame abstraction (Summa-correct origin)

**Goal:** Summa D760 (and similar) configured without hacky mirrors.

- [x] Stabilize `origin_corner` + `feed_axis` + `feed_sense` on device config.
- [x] Pure frame helpers (`design_to_machine_transform`, feed end/vector, material rect) in `inkcut/device/frame.py`; used by `build_plan` + live material rect.
- [x] Protocol transforms applied in `Device.protocol_transform` / init (Phase 5); `build_plan` physical by default.
- [ ] Driver preset for D760 after hardware tests (stub doc only).
- [x] Shared `material_rect` for live preview area (full origin/feed markers = Phase 3).

**Completed task:** `agents/plans/cutter-path-and-coords/completed/cutter-path-and-coords_phase2-device-frame.md`

### Phase 3 — Preview markers + travel toggles

**Goal:** both previews tell the truth about machine space and ordering.

- [x] Origin + feed indicators on precut and live.
- [x] Distinct pens: cut / travel / weed / epilogue (epilogue can share travel color with different dash).
- [x] Settings checkboxes; persist in preview plugin config.
- [x] Order algorithm changes refresh travel layer clearly.
- [ ] Optional: legend in preview.

Salvage carefully from `inkcut_ai_fail/inkcut/preview/indicators/` (origin.py, feed.py); rewrite if coupled to wrong transform assumptions.

**Completed task:** `agents/plans/cutter-path-and-coords/completed/cutter-path-and-coords_phase3-preview-markers.md`

### Phase 4 — Weed line solvers

**Goal:** peel waste without hand-cutting every time.

- [x] Refactor `_add_weedline` into weed strategy API.
- [x] Implement `frame` + `grid` (clipped).
- [x] Implement region nesting + fan or CDT-ish `region` mode for circle+letter class problems.
- [x] UI: mode select, spacing, when to apply (plot vs copies), cut order relative to design.
- [x] Tests on synthetic SVGs (nested circle+letter, multi-island, open paths edge cases).

**Completed task:** `agents/plans/cutter-path-and-coords/completed/cutter-path-and-coords_phase4-weed-solvers.md`

### Phase 5 — Polish / protocol hardening

- [x] Filters (overcut, blade offset) operate on cut/weed segments only.
- [x] Joystick “move to origin” consistent with frame model (system = machine 0,0).
- [x] Docs: `docs/device-frame-and-weeds.md`; weed modes; path layer legend; Summa stub.
- [ ] Consider upstream contribution once Summa path is clean (out of scope until hardware).

**Completed task:** `agents/plans/cutter-path-and-coords/completed/cutter-path-and-coords_phase5-polish.md`

---

## Explicit non-goals (for now)

- Full AI rewrite of Inkcut UI/stack.
- Optimal NP-hard weed minimization.
- Replacing enaml/Qt.
- Deriving protocol `swap_xy` solely from origin corner (keep both layers).
- Perfect automatic keep/waste from arbitrary SVG fills without user hints (start with nesting heuristics + modes).

---

## Key files (inkcut_luke)

| Area | Path |
| --- | --- |
| Job path build | `inkcut/job/models.py` (`create`, `_add_weedline`, `move_path`, `cut_path`) |
| Ordering algorithms | `inkcut/job/ordering.py` |
| Job precut preview | `inkcut/job/plugin.py` (`_refresh_preview`) |
| Device config / init / live preview | `inkcut/device/plugin.py` |
| Device UI | `inkcut/device/view.enaml` |
| Plot feeding UI | `inkcut/job/view.enaml` (Return to origin / Feed after) |
| Weed UI | `inkcut/job/view.enaml` (`WeedlinesDockItem`) |
| Preview pens / grid | `inkcut/preview/plugin.py`, `settings.enaml`, `view.enaml` |
| Reference indicators (other tree) | `../inkcut_ai_fail/inkcut/preview/indicators/` |
| Failed rewrite analysis | `../inkcut_ai_fail/docs/COORDINATE_*.md`, `ARCHITECTURE_DECISION.md` |

---

## Risks

| Risk | Mitigation |
| --- | --- |
| Breaking existing bottom-left devices | Golden tests on stock defaults; gate new feed_sense behind defaults matching old behavior |
| Double Y-flip / preview vs device mismatch | One shared `design_to_machine` + one preview Y-flip; no third ad-hoc origin translate |
| Protocol still needs mirrors | Keep advanced protocol block; document Summa preset after measurement |
| Weed false cuts on keep art | Clip to waste; tests; optional manual weed layer later |
| Scope creep into rewrite | Phases 1–2 only until D760 return-to-origin + origin are correct |

---

## Success criteria

| # | Criterion | Status |
| --- | --- | --- |
| 1 | Return-to-origin → **machine origin** after job scale/rotate/mirror/copies | **Met** (epilogue after design map; filters skip epilogue; protocol keeps (0,0)) |
| 2 | Summa D760: origin side, unroll, feed-after without abusing design transforms | **Software ready**; physical values **unverified** (`docs/SUMMA_D760.md` stub) |
| 3 | Precut + live: origin/feed markers; travel toggleable; order changes travel | **Met** (Phase 3) |
| 4 | Weed mode splits circle+letter-class waste | **Met** (region mode; not min-cut optimal) |
| 5 | Work in `inkcut_luke` with tests; not based on `inkcut_ai_fail` | **Met** |

---

## Residuals (after Phase 5)

- Hardware verification of Summa D760 origin/feed/protocol
- Named D760 driver preset after measurement
- Optional preview legend UI
- Optional tag/archive of `inkcut_ai_fail` ref2
- Upstream contribution packaging
- Typed travel segments still thin (pen-up often inside cut path MoveTos)
- Region weeds: nesting + fan/grid, not CDT / global min cuts

---

## Status log

- **2026-07-16:** Analysis of former `inkcut/` vs `inkcut1/`; plan drafted.
- **2026-07-16:** Renamed workspace dirs to `inkcut_ai_fail` and `inkcut_luke`. Installed agentsmd; plan path names updated.
- **2026-07-16:** Taskforce started Phase 1.
- **2026-07-16:** **Phase 1 done.** ToolpathPlan + epilogue separation landed; tests green.
- **2026-07-16:** **Phase 2 done.** `feed_sense` + pure `inkcut/device/frame.py`; protocol split residual.
- **2026-07-16:** **Phase 3 done.** Shared QPainterPath origin/feed indicators; layer toggles on both previews.
- **2026-07-16:** **Phase 4 done.** Weed strategy API (`frame`/`grid`/`region`); typed weed plan segments; UI mode+spacing.
- **2026-07-16:** **Phase 5 done.** Filters cut/weed-only; protocol after physical plan; docs; plan closed (software).

### Session handoff (overwrite; keep short)

**Phase:** 5 complete — **plan closed (software)**  
**Status:** Complete with residuals (hardware / upstream only)

**Shipped (Phase 5):**
- Filters skip epilogue (`Device._filter_work_and_epilogue` / process)
- Protocol via `Device.protocol_transform` + `_apply_protocol_to_plan` after physical `build_plan`
- Docs: `docs/device-frame-and-weeds.md`, `docs/SUMMA_D760.md` (unverified)
- Tests: **96 passed**

**Key APIs:** `Device.protocol_transform`, `Device._apply_protocol_to_plan`, `Device._process_plan`

**Residuals:** hardware Summa verify; upstream PR; optional legend; thin typed travel

**Next:** none for this plan
