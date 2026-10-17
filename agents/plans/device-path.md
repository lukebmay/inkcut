# device-path — One path for the preview and the cutter

**Status:** active
**Updated:** 2026-10-17

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

- [ ] Each slice that moves the knife also moves the pre-cut preview
      in that same slice. A slice that only corrects the picture
      does not move the knife.
- [ ] Slice 1 draws the path `Device.init` already sends, including
      today's Swap X/Y and today's feed. The protocol bytes do not
      change. The live bed uses that same path, not its private
      `rotate(90)` plus `scale(-1, 1)`.
- [ ] Slice 2: `Job.create` no longer takes `swap_xy` or device
      scale. The document path includes padding, the return to
      origin, and Feed After. One device function orients that whole
      path. Saved Swap X/Y still means `QTransform.rotate(90)`,
      `(x, y) → (−y, x)`, so a D760 job that already looks right on
      the vinyl does not turn the other way.
- [ ] With Swap X/Y off, a rectangle 200 by 50 (90 DPI px) and Feed
      After of 30 ends at device `(0, 80)` after the process Y-flip.
      With Swap X/Y on, that feed ends at the bottom-right, device
      `(80, 0)`: past the right edge by the feed distance, on the
      bottom edge. The artwork stays the `rotate(90)` picture.
- [ ] With Swap X/Y on and Return to origin, that rectangle's final
      pen-up ends at device `(0, 0)`, the bottom-left. The artwork
      box stays `(0, 0, 50, 200)`.
- [ ] The next slice replaces Swap X/Y and the final-point patch
      with a device feed direction and an origin side, left or
      right. Saved `swap_xy` true loads as the D760 mounting:
      artwork `rotate(90)`, Feed After at the bottom-right, Return
      at the bottom-left. Swap off is unchanged.
- [ ] Nine anchors come after that mounting is the only orient.
      The default anchor is the corner that mounting already uses.
- [ ] Protocol code is unchanged. It still converts 90 DPI px to
      plotter units.
- [ ] A unit test covers the rectangle endpoints and, once those
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

Next session implements Approach step 3 only. Luke asked for that
on 2026-10-17. The open Human checkboxes stay open and do not block
this slice. Do not tick them. Do not edit `architecture.md`. Do not
send a job to the cutter, including `/dev/ttyUSB0`. Do not open a
pull request. Luke opens any upstream PR himself.
`inkcut/inkcut#442` was closed on 2026-10-17 and branch
`pr/d760-path` was deleted. Do not reopen it.

On Continue, orchestrate this slice with one implementer. Do not
start step 4 in the same turn. Do not resume a finished subagent.
Do not hold another design meeting. Frames is the model.

Replace the Swap X/Y checkbox on the device Output page
(`inkcut/device/view.enaml`) with two device facts: feed direction
and origin side (left or right). One source of truth. Do not leave
the checkbox beside the new controls. `feed_to_end` and
`feed_after` stay on the job. Feed direction is not a job setting.
Build Return and Feed After from that mounting inside the orient,
on the whole path, strokes and pen-ups together. Then delete the
`setElementPositionAt` y = 0 patch in `Device.output_path`.
`orient_path`, `orient_bed`, `output_path`, the pre-cut preview,
and the live bed (`inkcut/job/plugin.py` and `inkcut/device/plugin.py`)
share that mounting. `Device.process` keeps `scale(1, -1)`.
Protocol files stay.

`tests/test_device_output.py` must stay green. Rectangle 200 by 50,
feed 30, 90 DPI px. Device end is `(path_x, -path_y)`.

- Saved `swap_xy` false, and the new default (origin on the left):
  feed device `(0, 80)`, path point `(0, -80)`, art screen
  `(0, 0, 200, 50)`. Return device `(0, 0)`, same art. Padding
  `[10, 0, 0, 20]`: feed `(0, 100)`, art `(10, 20, 200, 50)`.
- Saved `swap_xy` true loads as today's `rotate(90)` mounting. Do
  not turn the artwork the other way. Feed device `(80, 0)`, path
  point `(80, 0)`, art `(0, 0, 50, 200)`. Return device `(0, 0)`,
  same art. Padding `[10, 0, 0, 20]`: feed `(100, 0)`, art
  `(20, 0, 50, 200)`. Scale `(2, 1)` with that pad: feed
  `(100, 0)`, art `(20, 0, 50, 400)`. Device origin `(5, 7)`
  applies only when `feed_to_end`, after the mounting: feed path
  point `(85, -7)`. Return is not origin-translated.
- Factory presets that set `swap_xy` true must keep that geometry:
  Roland Stika SV-15, SV-12, and SV-8, and Silhouette Cameo 4
  (Cameo also scale `5.64` and both mirrors) in
  `inkcut/device/drivers/manifest.enaml`. The Summa D760 factory
  preset does not set `swap_xy`. Luke's saved profile does. Do not
  change that preset's raw path.
- `job.model` is not mutated. The document feed stays `(0, -80)`.
  `init` does not call `create()`, so `auto_copies` do not grow.
  `config.rotation` stays off both the picture and the knife. Do
  not give `Device.transform` a preview-only rotation. Leave the
  commented rotation widget commented.
- Do not move the on-screen origin to the widget's bottom-right.
  That would move the knife. A facing view that redraws the origin
  is a later change of picture and knife together, and it needs a
  test cut.

The measurement paragraph above Frames that cites device `(0, 230)`
is the feed from before the y = 0 patch. Do not restore it.
Acceptance and the tests are the contract.

Test: `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_device_output.py -q`

Last run on this contract: 20 passed, at `7705c1c`. That commit is
the Return bookmark. `44579bd` is Feed After after Luke cut it.
`e2920a6` is the known-good cut from before either corner snap. He
has not re-tested Return in Inkscape.

The facing-view checkbox stays open until he says Frames is right.
The feed-cut checkbox stays open. Neither blocks step 3.
`architecture.md` Running code still says `Job.create` takes
`swap_xy`. Leave that until he says to edit it.
