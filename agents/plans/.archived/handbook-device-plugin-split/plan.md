# handbook-device-plugin-split

**Rank:** 3

## Goal

`inkcut/device/plugin.py` is 1398 lines. The ordinary source-file
count is 1200. This file is one part of the device package, not
a one-file program, so the 5000 line ceiling does not keep it
whole. Split it on names the file already has. Behavior stays
the same. This plan stays off the queue.

## Guide

[Architecture](../../architecture.md), the device row in Layers
and steps 3–6 of How the parts fit.
[Handbook](../../handbook.md), section Source files. Do not copy
them.

## Checks

- [ ] Every file that owns a piece of this split is under 1200
      lines. `Device` stays one file. It is not split to hit a
      smaller count.
- [ ] A name that other modules import from
      `inkcut.device.plugin` still resolves. When the class
      moves, the caller changes in the same work. Do not keep a
      second copy.
- [ ] `tests/test_device_output.py`, `tests/test_filters.py`,
      and `tests/test_plotter_unit_scale.py` pass.
