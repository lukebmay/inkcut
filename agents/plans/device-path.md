# device-path — One path for the preview and the cutter

**Status:** waiting
**Updated:** 2026-10-18

## Goal

The preview shows the path the cutter will run, and it changes in
the same slice as the knife. With the D760 mounting on, Feed After
still leaves the knife past the same edge of the artwork it leaves
past when that mounting is off. On the Summa D760 that edge is the
one that advances the vinyl.

The operator places the job with an origin location and a device
feed axis. Those two replace the Swap X/Y checkbox. Origin location
is nine anchors, as in CSS: top, middle, or bottom, and left,
center, or right. The feed axis is which way that cutter's roller
advances. It is a device fact, chosen once, not a direction the job
can aim along the carriage.

## Acceptance

- [x] Each slice that moves the knife also moves the pre-cut preview
      in that same slice. A slice that only corrects the picture
      does not move the knife.
- [x] Slice 1 draws the path `Device.init` already sends, including
      today's Swap X/Y and today's feed. The protocol bytes do not
      change. The live bed uses that same path, not its private
      `rotate(90)` plus `scale(-1, 1)`.
- [x] Slice 2: `Job.create` no longer takes `swap_xy` or device
      scale. The document path includes padding, the return to
      origin, and Feed After. One device function orients that whole
      path. Saved Swap X/Y still means `QTransform.rotate(90)`,
      `(x, y) → (−y, x)`, so a D760 job that already looks right on
      the vinyl does not turn the other way.
- [x] With Swap X/Y off, a rectangle 200 by 50 (90 DPI px) and Feed
      After of 30 ends at device `(0, 80)` after the process Y-flip.
      With Swap X/Y on, that feed ends at the bottom-right, device
      `(80, 0)`: past the right edge by the feed distance, on the
      bottom edge. The artwork stays the `rotate(90)` picture.
- [x] With Swap X/Y on and Return to origin, that rectangle's final
      pen-up ends at device `(0, 0)`, the bottom-left. The artwork
      box stays `(0, 0, 50, 200)`.
- [x] The next slice replaces Swap X/Y and the final-point patch
      with a device feed direction and an origin side, left or
      right. Saved `swap_xy` true loads as the D760 mounting:
      artwork `rotate(90)`, Feed After at the bottom-right, Return
      at the bottom-left. Swap off is unchanged.
- [ ] Nine anchors come after that mounting is the only orient.
      The default anchor is the corner that mounting already uses.
- [x] Protocol code is unchanged. It still converts 90 DPI px to
      plotter units.
- [x] A unit test covers the rectangle endpoints and, once those
      controls exist, the default origin and the saved `swap_xy`
      load. No cutter is required.

## Human

- [ ] Say how the preview should sit when you face the front of the
      D760. The picture and the knife stay on the same path.

Why human-only: the sideways preview is the knife's frame. Which
way that frame should face you is your call.

- [ ] On the D760, with the usual profile (Swap X/Y on), cut a
      rectangle with Feed After set to a distance you can see. The
      vinyl should advance past the piece. The carriage should not
      travel off along the other axis instead.

Why human-only: only the cutter shows which plotter axis is the
roller.

## Approach

Do this in four slices. Do not start a slice that moves the knife
until the preview from the previous slice matches the path that was
sent. A test cut costs vinyl, time, and setup. The picture has to
move with the knife, or not move at all.

Do not patch the feed point inside `Job.create`. The feed is
appended after the rotation, at x = 0 in the rotated frame, while
the preview still draws the unrotated path. Padding already has a
hand-written axis remix (`px, py = -py, -px`) that does not match
`rotate(90)`. Another special case will drift the same way.

1. **Picture only.** Build the path `Device.init` already builds
   and draw that in the pre-cut preview and on the live bed. Delete
   the live bed's private matrix. Leave the protocol bytes as they
   are. After this slice the screen shows today's feed, including
   the one that leaves the material edge.
2. **One path.** Build the document path first, including padding,
   the return, and Feed After. Run the existing `rotate(90)` over
   that whole path when Swap X/Y is on. `Device.init` calls that
   one orient function on `job.model` instead of
   `job.create(swap_xy=…, scale=…)`. `Device.process` keeps the
   single `scale(1, -1)`. The preview draws the result of that same
   function. Job filters, including clip-to-plot-area, run on the
   document path before orientation. Device filters stay in
   `process`, after the Y-flip.
3. **Mounting.** Replace Swap X/Y, and delete the final-point
   patch, with one device feed direction and an origin side (left
   or right). A saved `swap_xy` true loads as the D760 mounting
   already cut: `rotate(90)` artwork, Feed After at the
   bottom-right, Return at the bottom-left. Feed After and Return
   are defined from that mounting, not by editing one point after
   the rotation. Job rotation stays how a single design sits on
   the sheet. It is not a second mounting.
4. **Anchors.** Add the nine anchors only after that mounting is
   the only orient. The default is the corner the mounting already
   uses, so an existing job does not jump. Placement happens on
   the document path, before the device orient.

`config.rotation` is applied by `Device.transform` for the preview
and is not applied on the cut. Either the orient function applies
it for both, or the field stops affecting the picture. It must not
keep doing only one. Do that in slice 1 or slice 2, with the
picture.

A per-job feed direction that can point along the carriage is the
same bug as appending the feed after the rotation. The roller is a
fact about the cutter. The nine anchors are where the piece sits.

A 200 by 50 rectangle, feed 30, no padding, checked with PyQt5:

- Swap off, feed appended, then Y-flip: device end `(0, 80)`.
  Artwork occupies Y `0–50` and X `0–200`.
- Swap on, feed appended after `rotate(90)`, then Y-flip: device
  end `(0, 230)`. Artwork occupies X `0–50` and Y `0–200`. The
  extra 30 is past the original width, and X is back at 0.
- Feed appended first, then the same `rotate(90)` and Y-flip:
  device end `(80, 200)`. The extra 30 stays past the original top.
  That point is the top-right. Feed After then moves it to the
  bottom edge, device `(80, 0)`, and leaves the artwork where this
  row put it.

The second row is the old feed, appended after the rotation.

## Frames

The author's pipeline stays. `Job.create` builds one
`QPainterPath`. `Device` orients that whole path for the machine.
`Device.process` flips Y once and walks every element into protocol
commands. A pen-down stroke and a knife contour are elements of that
same path. Drawing and cutting share it. The preview has to draw
that same path. `Device.transform` is the author's display helper
(scale and rotation) and it is not applied on the cut. Giving it a
rotation the knife ignores is how the picture and the machine
drifted apart. Do not add a preview-only rotate.

There are two frames.

The document frame is the job, before the device orient. The source
SVG is y-down. The job flips each copy so the ink sits on negative
y and the baseline is y = 0. `(0, 0)` is the bottom-left. X grows
to the right. Y in this frame is the feed axis. On the default
machine the vinyl moves top to bottom. Feed After moves the head
the other way: past the top of the ink, still on x = 0, which is
the origin's side. The head finishes at the top-left. Return to
origin is `moveTo(0, 0)`, the bottom-left. Padding is the empty
margin between `(0, 0)` and the ink. The job does not know how the
cutter is mounted. The trailing point is only the last pen-up.

The device frame is `orient_path`, then `process`'s `scale(1, -1)`.
Scale, with mirror folded in, is calibration and is applied before
the mounting turn, so each design axis keeps its factor. Swap X/Y
is the author's mounting switch: `QTransform.rotate(90)`,
`(x, y) → (−y, x)`, on the whole path. The path is then parked so
the bounds include `(0, 0)` and sit in negative y for the process
flip. After that flip the protocol sees y up and positive
distances from the parked corner. The protocol still converts 90 DPI
px to plotter units. It does not learn a feed direction.

With Swap off, the head returns to the bottom-left and Feed After
finishes at the top-left. That is a quadrant-I bed: positive X to
the right, positive Y up.

With Swap on, the artwork turns 90° clockwise in the preview. A
wide design stands up. That turned artwork is the path the D760
just cut, and it stays. The final pen-up is the part that was
wrong. Rotation plus the park leaves it on the top edge of the
turned picture. Return showed at the top-left. Feed After showed
past the right edge and on the top.

The patch, in `output_path`, runs only when Swap X/Y is on. It
keeps that final move's x and sets its y to 0, which is the bottom
of the parked frame. Feed After already had its x past the right
edge, so the head ends at the bottom-right. Return already had its
x on the origin side, so the head ends at the bottom-left. Strokes
are not moved. Preview and the wire both use `output_path`, so they
get the same point. This is a patch on one point. It is not the
mounting. Delete it when the mounting itself parks Return and Feed
After.

The D760, as Luke faces it, is a different side of that frame. He
stands at the front, where the controls are. The origin he uses is
the bottom-right of the bed. The vinyl feeds from top to bottom,
toward him. Swap X/Y is how that mounting is stored today. In
Inkcut's bottom-left picture the feed runs right to left, which is
the same relative motion as the knife traveling out to the right
for Feed After. The machine still counts positive distances from
its origin. It is not a quadrant-II bed with negative X. The zero
is the other end of the carriage. Many newer cutters put that zero
on the left.

The proper mounting is still one device transform of the whole
path.

- Feed direction is which way the roller advances the material. It
  is set once, on the device. It replaces Swap X/Y. A saved
  `swap_xy` true loads as the mounting that already cuts the D760
  artwork: today's `rotate(90)` of the document path. Feed After
  travels opposite the vinyl, by `feed_after`, and stays on the
  origin's side of the other axis. Return is the origin of that
  same frame.
- Origin side is left or right, relative to that feed direction.
  The default stays the left, today's bottom-left, so an existing
  job does not jump. The D760 chooses the right. Both sides use
  positive machine coordinates.
- Nine anchors can follow, once those two sides are the only
  orient. They place a point of the artwork on a point of the
  material. They are not a second feed direction.
- The screen shows the path the protocol will run. A control for
  "as I face the machine" has to be this mounting. It must not be a
  second rotation on the widget.
- Job rotation still turns one design on the sheet. It does not
  aim the roller.
- Job filters stay on the document path, before the orient. Device
  filters stay in `process`, after the Y-flip. Protocol code stays
  as it is.

## Session

Luke asked on 2026-10-18 to replace Swap X/Y with origin location
and feed direction. This turn did Approach step 3 only. Do not
start step 4, the nine anchors, until he asks. The default anchor
must be the corner this mounting already uses, so an existing job
does not jump.

The Output page (`inkcut/device/view.enaml`) has Feed (`down` or
`left`) and Origin (`left` or `right`). Mirror X and Mirror Y stay.
The Swap X/Y checkbox is gone. `feed_to_end` and `feed_after` stay
on the job.

`DeviceConfig` has no `swap_xy` member. `__init__` and
`__setstate__` pop that key. True, with neither new field present,
loads as feed `left` and origin `right`: `QTransform.rotate(90)`,
`(x, y) → (−y, x)`, Feed After at the bottom-right, Return at the
bottom-left. False or absent stays feed `down`, origin `left`.
Named fields win. `__getstate__` does not write `swap_xy`.

Factory dicts in `inkcut/device/drivers/manifest.enaml` were not
edited. Roland Stika SV-15, SV-12, and SV-8, and Silhouette Cameo 4
still pass `swap_xy` true and get that mounting. Cameo also keeps
scale `5.64` and both mirrors. The Summa D760 preset was not
touched. Luke's saved profile still has the old key until the app
saves; the loader maps it. Do not edit `~/.config/inkcut/`.

Opposite origin (down + right, or left + left) mirrors across the
feed axis, parks again, and seats the trailing moveTo on the origin
edge. A rectangle's endpoints match the natural side. An asymmetric
path flips. `tests/test_device_output.py` locks that and the
rectangle contract. Do not weaken it. Do not restore the old feed
at device `(0, 230)`.

`job.model` is not mutated. The document feed stays `(0, -80)`.
`init` does not call `create()`. `config.rotation` stays off the
picture and the knife. `Device.process` keeps `scale(1, -1)`.
Protocol files were not edited. The on-screen origin stays at the
parked corner. A facing view that redraws it is a later change of
picture and knife together.

Do not tick the Human checkboxes. Do not send a job to the cutter,
including `/dev/ttyUSB0`. Do not open a pull request. Luke opens
any upstream PR himself. `inkcut/inkcut#442` was closed on
2026-10-17 and branch `pr/d760-path` was deleted. Do not reopen it.
Do not edit `architecture.md`. It still names Swap X/Y. That
leftover is in `agents/conflicts.md`.

The blank-preview fix is in `inkcut/preview/plot_view.py`. Do not
put `processEvents` or a pin that reads `axis.width()` or
`maximumWidth()` back. The green and red travel lines stay the 1 px
cosmetic stroke. Do not touch pen widths or
`PainterPathPlotItem.updateData`. French and German `.ts` files
were left alone. `lrelease` is not installed. New Output strings
fall back to English.

Marks read feed direction and origin side. Down + left is labeled
Origin (Left), arrow down. Left + right is labeled Origin (Right),
arrow left. Changing Feed or Origin in the device dialog still
waits for a save, or a job change, before the preview redraws.

Tests on 2026-10-18, 74 passed:

`QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_device_output.py tests/test_preview_markers.py tests/test_plotter_unit_scale.py -q`

The Output view was constructed offscreen for a default config and
for `DeviceConfig(swap_xy=True)`.

The facing-view checkbox stays open. The feed-cut checkbox stays
open. Neither blocks a later step 4 once he asks. `44579bd` is Feed
After after he cut it. `e2920a6` is the known-good cut from before
either corner snap. He has not re-tested Return in Inkscape.
