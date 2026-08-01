# B-summa-d760-measure — Measure Summa D760 origin / feed / protocol

**Status:** open  
**Severity:** soft  
**Owner:** human  
**Kind:** physical  
**Plan:** cutter-path-and-coords  
**Unblocks:** named D760 driver preset; verified `docs/SUMMA_D760.md` values  
**Priority:** P0  
**Created:** 2026-08-01  
**Updated:** 2026-08-01

## What the human must do

- [ ] Load material; note which corner the machine treats as `(0,0)` when facing the cutter.
- [ ] Confirm feed / unroll axis and sense (toward vs away operator).
- [ ] 1-line test cut (and optional small square) with software frame settings only — no design mirrors to “fix” origin.
- [ ] Note any protocol `swap_xy` / mirrors still required after physical frame is correct.
- [ ] Update `docs/SUMMA_D760.md` with measured values (or mark confirmed).

## Done when

Measured values recorded in `docs/SUMMA_D760.md` (no longer “unverified” stub), enough to add a named driver preset.

## Notes

Software stack is ready (ToolpathPlan, frame, previews, weeds). This item does **not** block other agent work.
