# Project: Inkcut (Luke fork)

## Overview

Fork of [Inkcut](https://github.com/inkcut/inkcut) for vinyl cutters and
plotters. Goal: correct **machine coordinate frames**, layered **toolpaths**,
**preview truth**, and smarter **weed lines** — especially for a **Summa D760**
(origin on the right; material unrolls toward the operator).

Compose rules into root `AGENTS.md`:

```sh
python3 agentsmd_build.py
python3 agentsmd_build.py --preset=full
```

## Which directory (workspace)

| Path | Role |
| --- | --- |
| **`~/dev/me/inkcut_luke/`** (this repo) | Canonical working tree (branch `refactor1`) |
| `~/dev/me/inkcut_ai_fail/` | Failed AI rewrite (`ref2`) — docs/indicators only; **do not base work here** |

Do not confuse the two. All implementation lands in **inkcut_luke**.

## Purpose

- Make Summa D760 (and similar cutters) work without hacky path transforms.
- Separate design geometry from machine epilogue (return-to-origin / feed-after).
- Mark origin and vinyl unroll direction on both previews.
- Improve weed-line algorithms beyond a single outer box.

## Stack

- Python 3, Enaml + Qt (PyQt), atom, pyqtgraph, Twisted
- Package layout: `inkcut/` under repo root; entry via `main.py` / `inkcut` package
- Job path model: `QPainterPath` in `inkcut/job/models.py` (to become layered `ToolpathPlan`)

## Priorities for agents

1. Follow [plans/cutter-path-and-coords.md](plans/cutter-path-and-coords.md).
2. Prefer small incremental changes over rewrite; never resume work in `inkcut_ai_fail`.
3. Physical device settings (`origin_corner`, feed axis/sense) must not be faked via job-path mirrors.
4. Machine epilogue (return origin / feed-after) must not be transformed with design geometry.
5. Session work → `agents/tasks/`; plan-linked naming `cutter-path-and-coords_<slice>.md`.

## Known issues / goals

See the plan. Snapshot:

| Issue | Status |
| --- | --- |
| Monolithic path; transforms hit return-to-origin | Open (Phase 1) |
| Incomplete device frame (Summa origin/unroll) | Partial UI; incomplete math |
| Precut/live previews lack origin + feed marks | Open (Phase 3) |
| Weed lines = outer box only | Open (Phase 4) |

## Project-specific rules

- **Canonical tree:** this repo only.
- **Reference tree:** `../inkcut_ai_fail/` for cherry-picking indicators/docs only.
- **Do not** apply design/job transforms to return-to-origin or feed-after segments.
- **Do not** invent overlapping settings that mix protocol quirks with physical origin.
- Keep protocol knobs (`swap_xy`, `mirror_x/y`, `scale`) as advanced/driver defaults.
- When changing path pipeline, update unit tests under `tests/` and both preview paths.

## Layout

| Path | Purpose |
| --- | --- |
| `agents/project.md` | This file |
| `agents/general.md` | Tasks/plans rules, residue checks |
| `agents/security.md` | Secrets / security |
| `agents/scripting.md` | Cross-language script rules |
| `agents/languages/` | Per-language style (on demand) |
| `agents/plans/` | Plans (kebab-case; not in core AGENTS.md) |
| `agents/tasks/` | Session tasks |
| `inkcut/` | Application package |
| `tests/` | Unit tests |
| `docs/` | Upstream-style docs |
| `agentsmd_build.py` | Composer for root `AGENTS.md` |
