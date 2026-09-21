# Weedlines extract plan

**Source:** `~/dev/me/inkcut_luke` @ `archive/pre-repartner-2026-08-21`
**Dest:** `~/dev/me/weedlines` (GitHub `lukebmay/weedlines`)
**Task:** `agents/tasks/weedlines-extract-repo.md`
**Scope:** Inkscape extension + shared solver core only — not inkcut job/TSP/send.

---

## 1. Exact files to copy vs leave

### Copy (adapt paths/names on ingress)

| Archive path | Role |
| --- | --- |
| `inkcut/weedlib/__init__.py` | Public API re-exports |
| `inkcut/weedlib/solvers.py` | frame / grid / auto(=island-hop) |
| `inkcut/weedlib/paths.py` | Path split helpers |
| `inkcut/weedlib/svg_paths.py` | SVG `d` ↔ `QPainterPath` |
| `inkcut/weedlib/qt.py` | Qt binding shim |
| `inkcut/weedlib/progress.py` | cancel / phase / `report_segment` |
| `inkcut/weedlib/debug.py` | env-gated structured logs |
| `extensions/inkscape/inkcut_weeds.py` | inkex entry (rename) |
| `extensions/inkscape/inkcut_weeds_dialog.py` | Start/Cancel + live preview |
| `extensions/inkscape/inkcut_weeds.inx` | Inkscape menu + custom GUI |
| `extensions/inkscape/README.md` | Behavior notes → seed README |
| `scripts/preview_auto_weeds.py` | Offline SVG harness (rename) |
| `tests/test_weeds.py` | Core geometry tests (strip Job) |
| `tests/test_inkscape_weeds_args.py` | MRO / `--layer_name` regression |
| `tests/data/weed_preview/*.svg` | Picture / harness fixtures |
| `agents/notes/weed-hard-rules.md` | Optional → `docs/` (D012 floors) |
| `docs/DECISIONS.md` rows D007/D012/D013 | Optional excerpts only |

Also copy **LICENSE** (GPLv3) attribution from archive.

### Leave behind (do not vendor)

| Archive path | Why |
| --- | --- |
| `inkcut/job/weeds.py` | Thin re-export into job pipeline |
| `inkcut/job/models.py`, `toolpath.py`, filters, ordering | Job / TSP / plan |
| `inkcut/device/**`, protocols, transports | Cutter send |
| `inkcut/preview/**`, `ui/**`, Enaml docks | App UI |
| `plugins/inkscape/*` (cut/open/page/4inkscape) | Send-to-Inkcut |
| `inkcut/cli/install_plugin.py` | Installs send **and** weeds; rewrite CLI |
| Most of `tests/` (`test_toolpath_plan`, filters, SVG app, …) | Unrelated |
| `test_weeds.py` Job cases | See §6 |
| Full `inkcut/` app package | Goal is standalone |

---

## 2. External deps

| Dep | Need | Notes |
| --- | --- | --- |
| **Qt binding** (`PyQt5`/`PyQt6`/`PySide2`/`PySide6`) | **Required** for core | `weedlib.qt` loads at import; geometry is `QPainterPath` |
| **`pyclipper`** | **Optional** | Required for **island-hop** collar/boolean; frame/grid work without it |
| **`inkex`** | **Optional** (runtime) | Provided by Inkscape’s extension Python; not needed for pytest of solvers |
| **`pytest`** | Dev | Unit tests |
| **`enaml` / `enaml.qt`** | Optional | Shim prefers it if present; **do not** depend on it in weedlines |
| Twisted, enamlx, pyqtgraph, pyserial, lxml, … | **Not needed** | Inkcut-app only |

Extras suggestion in packaging:

- `weedlines[island-hop]` or `weedlines[full]` → `pyclipper`
- `weedlines[qt]` → document “install any one Qt binding”
- CLI / install path needs stdlib only beyond package install

---

## 3. Rename sites: `auto` → `island-hop`

User-facing and API mode string: **`island-hop`** (hyphen). Suggested Python
symbol: **`island_hop_weeds`**. Keep `enclosure_weeds` as the internal
implementation (already is).

### Product files (must change in new repo)

| File | Symbols / strings |
| --- | --- |
| `weedlib/solvers.py` | `WEED_MODES`; docstring “auto”; `generate_weeds` mode docs + fall-through; `auto_weeds` → `island_hop_weeds` (thin wrapper → `enclosure_weeds`); log keys `auto.start` / `auto.done` → `island_hop.start` / `.done`; pyclipper error text |
| `weedlib/__init__.py` | export `auto_weeds` → `island_hop_weeds` |
| `weedlib/debug.py` | module docstring “auto-weed”; logger name; env var (see §5) |
| Extension `.inx` | Menu “Auto-gen Weedlines…” → e.g. “Weedlines from selection…”; submenu `Inkcut` → `Weedlines`; new extension `id` |
| `*_dialog.py` | Combo `'Auto peel','auto'` → `'Island hop','island-hop'`; “Collar (mm, auto)”; window title “Inkcut — Weedlines” → “Weedlines”; logger `inkcut.weedlib` |
| Extension entry `.py` | Comments “long auto runs”; path bootstrap `inkcut/weedlib` → new package; imports |
| Extension README | Mode table `auto` row; install text |
| `scripts/preview_auto_weeds.py` | Rename file → `preview_island_hop_weeds.py`; default modes; `mode == 'auto'` |
| `tests/test_weeds.py` | All `auto_weeds` / `mode='auto'` / test names `test_auto_*` (prefer rename for clarity) |
| `tests/test_inkscape_weeds_args.py` | `--mode=auto` → `--mode=island-hop` |

### Keep (compatibility / non-user)

- Internal name `enclosure_weeds` (ok; not user-facing).
- `region` alias of `grid` — keep in `WEED_MODES` for later inkcut job
  compat; **omit from extension combo**.
- Archive docs/plans under `inkcut_luke/agents/**` — do not port wholesale;
  update only what lands in weedlines `docs/` / README.

### Compatibility shim (optional, short-lived)

Accept `mode in ('island-hop', 'auto')` in `generate_weeds` once, log a
deprecation if `'auto'` — helps ports from archive tests; drop when green.

---

## 4. Suggested package layout (`~/dev/me/weedlines`)

```text
weedlines/
  pyproject.toml          # or setup.cfg + setup.py
  README.md
  LICENSE                 # GPLv3
  src/
    weedlib/              # importable core (inkcut can depend later)
      __init__.py
      solvers.py
      paths.py
      svg_paths.py
      qt.py
      progress.py
      debug.py
    weedlines/            # CLI + install helpers only
      __init__.py
      __main__.py
      cli.py              # install / update / --help
      install_ext.py      # symlink/copy .inx+.py into Inkscape dir
  extensions/inkscape/
    weedlines.inx
    weedlines.py
    weedlines_dialog.py
  scripts/
    preview_island_hop_weeds.py
  tests/
    test_weeds.py
    test_inkscape_args.py
    test_progress.py      # new thin cancel/geometry hooks
    data/weed_preview/
  docs/                   # hard rules / decisions excerpts (optional)
```

**Packaging knobs**

| Item | Value |
| --- | --- |
| Distribution name | `weedlines` |
| Importable core | `weedlib` (stable for future inkcut) |
| CLI package | `weedlines` |
| Console entry | `weedlines = weedlines.cli:main` |
| Extension install sources | `extensions/inkscape/weedlines.{inx,py}` + `weedlines_dialog.py` |
| CLI flags | `weedlines install [--dry-run] [--copy] [--dest DIR] [--force]`; `update`; `--help` — mirror archive `inkcut/cli/install_plugin.py` weed half only |

Use `src/` layout so editable install puts `weedlib` on Inkscape’s Python
path when the extension does `import weedlib`. Extension bootstrap should
walk up to repo / use installed package — **never** look for `inkcut/`.

---

## 5. Sever inkcut-specific imports

| Current | Replacement |
| --- | --- |
| `from inkcut.weedlib …` / `import inkcut.weedlib` | `from weedlib …` |
| `_ensure_inkcut_on_path()` looking for `inkcut/weedlib` | `_ensure_weedlib_on_path()` → `weedlib` package or repo `src/` |
| `logging.getLogger('inkcut.weedlib')` | `weedlib` or `weedlines.weedlib` |
| `INKCUT_WEED_DEBUG` | Prefer `WEEDLINES_LOG=1|2` (or `WEEDLIB_DEBUG`); accept old env as alias briefly |
| Dialog forces debug `=1` during run | Gate on `WEEDLINES_LOG`; still default useful dialog verbosity without polluting global inkcut names |
| `from inkcut.job.weeds import …` (tests, preview script) | `from weedlib import …` / `from weedlib.solvers import …` |
| `from enaml.qt.QtGui import QPainterPath` in tests/scripts | `from weedlib.qt import QPainterPath, QPointF, QRectF` |
| `inkcut.core.svg.QtSvgDoc` / `Job` in tests | Drop those tests or load SVG via `svg_paths` only |
| Install via `inkcut install-plugin` | `weedlines install` only; do not pull send plugins |
| Extension menu under **Inkcut** | **Weedlines** submenu; new `.inx` `id` |

**Boundary rule:** `weedlib` must not import `weedlines` (CLI/UI). Extension
may import `weedlib` + sibling dialog module. Future inkcut depends on
**`weedlib` only**, not the Inkscape dialog.

---

## 6. Minimal test set to port first

Strip Job/Inkcut SVG from `test_weeds.py`; import `weedlib` directly;
`QT_QPA_PLATFORM=offscreen`.

**Wave 1 (smoke / API)**

1. `test_frame_weeds_padded_rect`
2. `test_generate_weeds_modes` (modes → `frame`,`grid`,`island-hop`)
3. `test_region_aliases_grid` (keep if `region` retained)
4. `test_grid_does_not_slice_keep_island`
5. `test_even_odd_letter_o_keep_is_ring`
6. `test_weed_debug_logging_is_side_effect_free` (new env var)
7. **New:** progress cancel raises `WeedCancelled`; geometry callback sees segs
8. `test_inkscape_weeds_args` MRO / `--layer_name` (point at renamed module)

**Wave 2 (island-hop correctness — needs pyclipper)**

1. `test_auto_does_not_slice_keep` → rename
2. `test_auto_letter_o_zero_weed_in_ring` / collar+channel
3. `test_auto_has_one_enclosure_not_frame_plus_collar`
4. `test_agglomerate_joins_until_one_island`
5. `test_auto_weed_ends_are_connected` / no proper crosses
6. One residual-trap smoke (`test_residual_traps_letter_o_zero`)

**Skip for weedlines repo**

- `test_job_plan_*`, `test_legacy_add_weedline_uses_frame` (need `Job`)
- Anything importing `inkcut.core.svg` / device / preview indicators

Mark island-hop tests `@pytest.mark.skipif(pyclipper is None)`.

---

## 7. Risks / traps

1. **`solvers.py` size** — ~7k+ lines, dense private helpers; copy whole
   module; do not “simplify” on extract.
2. **Qt is hard at import** — `weedlib.qt` fails if no binding; document
   Inkscape Python vs system Python mismatch (common install footgun).
3. **`pyclipper` optional until island-hop** — extension should disable or
   clear-error that mode when missing; frame/grid must still run.
4. **Global progress hooks** — `progress.install` is process-global; fine
   for one dialog thread; unsafe if inkcut later calls solvers concurrently.
5. **Cancel ≠ pause** — archive has cancel + live preview only; true
   pause/resume needs cooperative checkpoints — don’t claim resume until
   implemented; “pause-able” today = cancel + inspect preview.
6. **Dialog enables `INKCUT_WEED_DEBUG=1` for the run** — noisy by design for
   UI; separate default-quiet CLI/env logging from dialog capture.
7. **Mode string hyphen** — `'island-hop'` in UI/API vs `island_hop_weeds`
   symbol; grep both during rename.
8. **MRO bug** — `WeedLinesEffect` **before** `EffectExtension` or
   `--layer_name=Weed lines` breaks; keep the dedicated test.
9. **Units** — extension treats SVG user units as mm when doc width is mm;
   same assumption as archive; call out in README.
10. **License** — GPLv3 from Inkcut lineage; keep notices.
11. **Do not default island-hop** in any future inkcut integration until
    picture QA accepted (archive D012/D013).
12. **Inkscape flat install** — `.inx` + two `.py` files must land as
    siblings; package import of `weedlib` must work from that Python
    (editable install or `PYTHONPATH` / bootstrap).

---

## Ingress checklist (implementation order)

1. Scaffold `~/dev/me/weedlines` + `pyproject.toml` + GPL LICENSE.
2. Copy `weedlib/*`; rename package imports; env/logger; `auto` → `island-hop`.
3. Copy/rename extension trio + dialog; sever `inkcut.*`.
4. Implement `weedlines install` (weed files only).
5. Port Wave 1 tests; then Wave 2 under pyclipper.
6. Adapt preview script; smoke one `weed_preview` SVG.
7. README: install, modes, `WEEDLINES_LOG`, cancel/preview behavior.
8. `gh repo create lukebmay/weedlines` when local green.
