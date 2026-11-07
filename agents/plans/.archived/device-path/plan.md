# device-path

**Rank:** 4

## Goal

The preview shows the path the cutter will run, and it changes in
the same slice as the knife. With the D760 mounting on, Feed After
still leaves the knife past the same edge of the artwork it leaves
past when that mounting is off. On the Summa D760 that edge is the
one that advances the vinyl.

This pass stores one origin side and offers two radios. Origin left
(feed down) is the default. Origin right feeds left. They replace
the old Swap X/Y checkbox
([glossary](../../../glossary.md)). The graph keeps its origin at
the bottom-left. Nine anchors wait until he asks. The feed axis
is which way that cutter's roller advances. It is a device fact,
chosen once, not a direction the job can aim along the carriage.

## Guide

[`architecture.md`](../../../architecture.md) — "How the parts fit"
steps 2–4, and the job, device, and preview rows. Do not copy the
guide into this plan.

## Checks

- [x] Each slice that moves the knife also moves the pre-cut preview
      in that same slice. A slice that only corrects the picture
      does not move the knife.
- [x] Slice 1 draws the path `Device.init` already sends, including
      the old Swap X/Y control ([glossary](../../../glossary.md))
      and the feed of that day. The protocol bytes do not
      change. The live bed uses that same path, not its private
      `rotate(90)` plus `scale(-1, 1)`.
- [x] Slice 2: `Job.create` no longer takes `swap_xy` or device
      scale. The document path includes padding, the return to
      origin, and Feed After. One device function orients that whole
      path. A saved value of the old Swap X/Y control
      ([glossary](../../../glossary.md)) still means
      `QTransform.rotate(90)`, `(x, y) → (−y, x)`, so a D760 job
      that already looks right on the vinyl does not turn the other
      way.
- [x] With the old Swap X/Y control off
      ([glossary](../../../glossary.md)), a rectangle 200 by 50
      (90 DPI px) and Feed After of 30 ends at device `(0, 80)`
      after the process Y-flip. With that control on, that feed
      ends at the bottom-right, device `(80, 0)`: past the right
      edge by the feed distance, on the bottom edge. The artwork
      stays the `rotate(90)` picture.
- [x] With the old Swap X/Y control on
      ([glossary](../../../glossary.md)) and Return to origin, that
      rectangle's final pen-up ends at device `(0, 0)`, the
      bottom-left. The artwork box stays `(0, 0, 50, 200)`.
- [x] The mounting slice replaces the old Swap X/Y control
      ([glossary](../../../glossary.md)) and the final-point
      patch with two radios: Origin left (feed down), the default,
      and Origin right (feed left). One stored `origin_side`
      derives the feed. Saved `swap_xy` true loads as Origin right:
      artwork `rotate(90)`, Feed After at the bottom-right, Return
      at the bottom-left. Origin left is the old Swap-off path. A
      saved origin left with feed left, or origin right with feed
      down, loads as origin left.
- [ ] Nine anchors come after that mounting is the only orient.
      The default anchor is the corner that mounting already uses.
      That check is parked. It is not active work.
- [x] Protocol code is unchanged. It still converts 90 DPI px to
      plotter units.
- [x] A unit test covers the rectangle endpoints and the default
      origin and the saved `swap_xy` load. No cutter is required.
- [x] On the D760, with the usual profile (Origin right, feed
      left), a rectangle with Feed After advances the vinyl past
      the piece. The carriage does not travel off along the other
      axis. He confirmed this on 2026-10-19.
