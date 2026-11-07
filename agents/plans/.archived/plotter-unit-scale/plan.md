# plotter-unit-scale

**Rank:** 3

## Goal

A Summa D760 cut of a known length matches that length. Shipped
2026-10-16. Luke confirmed the scale. Do not reopen the
1021-unit bug. The remaining per-machine trim stays on the
saved device output scale and is not this plan.

## Guide

[`architecture.md`](../../../architecture.md) — the protocol
converts 90 px per inch into plotter units and does not scale.
Device output scale stays calibration. This plan does not
change that split.

## Checks

- [x] DM/PL mode 1 still sends `;:HAEC1` on connect. A 1 inch
      move (90 internal units) is emitted as 1000 plotter units
      on each axis.
- [x] DM/PL mode 2 still sends its connect string containing
      `ECN`. A 1 inch move is emitted as 1016 plotter units.
- [x] DM/PL modes 3, 4, and 6 keep their connect strings. Their
      addressing choice defaults to 1021 plotter units per inch.
      Modes 1 and 2 do not consult that choice. Setting it does
      not add an `EC` command.
- [x] HP-GL still defaults to 1021, including a saved config
      with no addressing field. 0.025 mm emits 1016. 0.001 inch
      emits 1000. 0.1 mm emits 254. 0.005 inch emits 200.
- [x] The HP-GL factory applies its `default_config` entry the
      way the DM/PL factory does.
- [x] `move` reads the live protocol config. The numeric scale
      is not tagged `config=True` and is not the saved control.
- [x] A Summa D760 declaration exists. Width is `740mm`. Length
      stays blank. Device output scale stays `[1, 1]`.
- [x] A new D760 starts on DM/PL mode 1 (1000 units per inch).
      Its HP-GL config emits 1016. A driver with no
      `initial_protocol` whose protocols are only HP-GL and
      DM/PL still starts on HP-GL. Graphtec stays on GPGL.
- [x] The Inkcut Generic Driver stays one driver. Protocol
      manifest order is unchanged.
- [x] Tests cover those cases without a window, a serial port,
      or a live cutter. They use `int()` truncation, not
      `round()`.
- [x] He cut a known length on the D760 and confirmed the scale
      on 2026-10-16.

The other measurement branches in the old human section (short,
far too long, still 2% long) were not the result he got. They
are not open work.
