# device-path — One path for the preview and the cutter

**Status:** waiting
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
- [ ] Slice 3 adds the nine origin anchors. The default anchor is the
      origin the code uses today, so an existing job does not jump.
      The preview shows the anchor.
- [ ] Slice 4 replaces the Swap X/Y checkbox with the device feed
      axis. A saved `swap_xy` true loads as the mounting slice 2
      already cut. Feed After travels only along that axis.
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
3. **Origin.** Add the nine anchors on the job. The default is
   today's origin. Placement happens before the device orientation,
   so the feed stays on the artwork.
4. **Feed axis.** Replace the Swap X/Y checkbox with one device
   control: which way this cutter's roller advances. A saved
   `swap_xy` true becomes the mounting slice 2 cut, which is still
   `rotate(90)` of the whole document path. Feed After uses that
   axis only. Job rotation stays the control for how a single
   design sits. It is not a second mounting.

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

## Session

Slice 2 landed. `Job.create` builds the document path only. That path
has padding, the job filters, then either the return to origin or
Feed After. `create` no longer takes `swap_xy` or device scale, and
the padding axis-remix is gone.

`orient_path` is the one device orientation. It scales, with mirror
folded into that scale, then `rotate(90)` when Swap X/Y is on. It
then parks the path into the negative-y frame `Device.process`
flips. The park bounds include the document origin. Padding is the
empty margin between that origin and the ink, so parking the ink box
alone would delete it.

A 200 by 50 rectangle and Feed After of 30 ends at device `(0, 80)`
with Swap off and `(80, 0)` with Swap on. Swap on keeps the
`rotate(90)` artwork and moves only the final pen-up from the top
edge to the bottom edge, past the right side by the feed distance.
Padding left 10 and bottom 20, Swap on, puts the art at screen
`(20, 0, 50, 200)` and the feed at device `(100, 0)`.

`init` and the preview orient `job.model`. They do not call
`create()`, so they do not grow `auto_copies`. `update_document`
still does. The origin translate after orientation is unchanged.
`config.rotation` still does not affect the picture or the knife.
`Device.transform` and the field remain. Protocol bytes were not
changed. `Device.process` was not changed.

Test: `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_device_output.py -q`

Result: 18 passed. The artwork boxes are the same as before this corner change.

The dock could not raise the window because Qt never set WM_CLASS.
`application_factory` now names the application `inkcut` before the
window exists. That fix is separate from this plan.

Do not start slice 3. The preview is still the `rotate(90)` picture,
origin parked at the bottom-left. With Swap on, Feed After now ends
at the bottom-right of that picture. Luke still wants a design
meeting before any further layout change: origin at the bottom-right
as he faces the D760, vinyl moving top to bottom, picture and knife
together. Do not add a preview-only rotation.

Slice 3, when the meeting is done, is still nine origin anchors.
The default is today's origin. The feed cut checkbox stays open.
`architecture.md` Running code still says `Job.create` takes
`swap_xy`. That paragraph is stale. Do not edit it until Luke says
to. Slice 4 still waits for him to lock the feed-axis model.
