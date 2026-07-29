# Task: Phase 5 — Polish / protocol hardening

| Field | Value |
| --- | --- |
| Plan | `agents/plans/cutter-path-and-coords.md` |
| Status | **done** |
| Tree | `~/dev/me/inkcut_luke/` (branch `refactor1`) |
| Scope | Phase 5 only — close the plan |

## Goal

Hardening so filters and joystick respect layers/frame; finish residual protocol-vs-physical split where safe; document device setup. Land plan success criteria as far as software can without hardware.

## Acceptance

1. [x] Filters operate on cut/weed only (epilogue unfiltered in `Device.process`)
2. [x] Protocol scale/swap/mirrors applied in `Device.init` after physical `build_plan` (not from config into plan)
3. [x] Joystick system origin = machine `(0,0)`; noted in code + docs
4. [x] Docs: `docs/device-frame-and-weeds.md` + optional `docs/SUMMA_D760.md` (**unverified**)
5. [x] Full suite green; filter-skips-epilogue + protocol-after-plan tests
6. [x] Plan status updated; this task under plan `completed/`

## Session handoff (final)

**Status:** done — plan complete (software); hardware verification residual

**Shipped:**
- `Device.process` / `_filter_work_and_epilogue` — filters on cut/weed/travel only
- `Device.protocol_transform` + `_apply_protocol_to_plan` — protocol after physical plan; feed epilogue recomputed post-map
- `Job._resolve_device_frame` — no longer pulls protocol scale/swap from device config
- Live preview: no double swap_xy (protocol via `device.transform` only)
- Docs: `docs/device-frame-and-weeds.md`, `docs/SUMMA_D760.md` (unverified)
- Joystick comment: system origin = machine (0,0)

**Key APIs/paths:**
- `Device.protocol_transform()`, `Device._apply_protocol_to_plan(plan, job)`
- `Device._process_plan`, `Device._stream_offset` (process split)
- `Job.build_plan` — physical by default; explicit scale/swap still accepted

**Tests:** 96 passed (`PYTHONPATH=. pytest tests/ -q`)

**Residuals (plan closed with notes):**
- Summa D760 values **unverified** on hardware
- Region weeds still nesting+fan/grid (not CDT / min cuts)
- Typed travel segments still thin (moves often inside cut path)
- Upstream contribution not started
- Live/precut protocol display via `device.transform` is optional visual; physical plan is source of truth for origin/feed markers

**Next agent:** none for this plan
