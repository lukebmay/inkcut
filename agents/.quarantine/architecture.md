# Architecture

**Owner:** human. Agents may propose edits; apply only with explicit permission.

This file is the **target** architecture: how the product is supposed
to work, including the vision that the code has not reached yet. It
is not a snapshot of today's tree, and it is not a log of bugs. Bugs
live in [`issues.md`](./issues.md).

After reading it, you should be able to walk a user action from
event to result without guessing which layer owns the change.

Gaps between this file and the running code are closed with a plan.
Do not rewrite this file to describe leftovers.

Words: [`glossary.md`](./glossary.md). When work is complete:
[`acceptance.md`](./acceptance.md). How work is run, including what
is stone: catalog `general.md` and [`general.md`](./general.md) when
this project has one.

## This file can be wrong

This file is what we **currently believe** is the best structure. It
is not a proof. It will change. Parts of it will turn out to be
wrong.

If you think a lock here is **directionally wrong** (the structure
or the product intent, not a leftover in the code), **stop work on
that issue**. Do not paper over it with a second path. Do not silently
edit this file. Do not silently change the code to match a sentence
you suspect is stale. We meet. Write the new lock here only when the
human says to: what is true, who does it, and what it does not cover.
One sentence of why when the choice is easy to undo the wrong way.
Do not write what was rejected.

**Why this paragraph exists:** agents treated this file as
unchangeable, then hid misses behind fallbacks.

Code that merely lags this file is a plan, not a meeting. A meeting
is for when this file itself looks like the mistake.

## What is being built

Inkcut opens an SVG and sends pen-up and pen-down moves to a vinyl
cutter. This checkout is Luke's fork, used with a Summa D760.
Weedlines is not this product. See [`project.md`](./project.md).

The process is an Enaml workbench. `inkcut.app:main` starts it.
Each area (job, device, preview, and the rest) is a plugin with a
manifest. Plugin state is JSON under `~/.config/inkcut/`.

## A cut

1. The job plugin opens an SVG. `QtSvgDoc` in `inkcut/core/svg.py`
   turns it into a `QPainterPath` at 90 px per inch. Inkscape Cut
   Selection passes the selected element ids. The parser keeps an
   element only when its id was selected or the element sits inside
   a selected element. If none of the ids are in the file, the job
   does not open the other objects.
2. The job lays that path on the material. It applies job scale, job
   mirror, job rotation, copies, weedlines, and padding. It then
   appends either a return to the origin or a feed past the end of
   the artwork, along the material. That result is the **document
   path**. The job does not rotate for the cutter's axis mounting.
3. The device applies one orientation to the whole document path:
   output scale, mirror, Swap X/Y, and rotation. Swap X/Y means
   `QTransform.rotate(90)`, which maps `(x, y)` to `(−y, x)`. It is
   not an exchange of the axes. The result is the **device path**.
   Feed, return, and padding are already in the document path, so
   they take this same rotation. Nothing later adds a move in
   another frame.
4. The preview the operator sees before cutting draws the device
   path. The bed outline uses that same orientation.
5. The device flips Y once, so plotter +Y is the cutter's Y, then
   flattens curves and runs device filters (blade offset, overcut).
6. The protocol converts each point from 90 px per inch into plotter
   units. The transport writes the bytes. The protocol does not
   scale, mirror, or swap.

Why step 3 is one transform: the feed and the picture have to stay
on the same edge of the artwork as the knife. A second transform for
only one of them sends the carriage down a different axis than the
screen shows.

## Layers

| Piece | Owns | Must not own |
| --- | --- | --- |
| `inkcut/core` | Workbench, plugin persistence, SVG to a 90 DPI path | Job layout, device orientation, plotter bytes |
| `inkcut/job` | Document, material, copies, job scale, job mirror, job rotation, weedlines, the document path | Device Swap X/Y, device scale, plotter units |
| `inkcut/device` | Drivers, connect, submit, the one orientation, curve flattening, device filters, position | A second orientation for the preview, SVG parsing |
| Protocol | One `move(x, y, z)` in plotter units | Scale, mirror, swap, preview |
| Transport | Bytes on raw, serial, printer, or file | Geometry |
| `inkcut/preview` | The plot widget. Draws the device path. May flip Y for the widget only | Its own swap or mirror |
| `plugins/inkscape` | Starts `inkcut open` with the selected element ids | Transforms, a full-document fallback |

## Running code

The plugin split above is what the tree is built as. The path is not.
`Job.create` still takes `swap_xy` and device scale, rotates, then
appends the feed in that new frame. The main preview draws the
unrotated document path. The live bed uses another matrix. That gap
is [`device-path`](./plans/device-path.md). Cut Selection is
[`cut-selection`](./plans/cut-selection.md). Do not add another
axis correction inside `Job.create`.
