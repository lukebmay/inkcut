# Architecture

When to use: Which product part. Open this index, then the one
part the task names.

**Owner:** human. Agents may propose edits; apply only with explicit permission.

This file is the index of the guide: how the product is supposed
to work, including the vision that the code has not reached yet.
It records what has worked and warns about what has failed. It
is not a snapshot of today's tree, not a log of bugs, and not a
ban on a better design. Bugs live in [`issues.md`](./issues.md).

Each part of the guide lives in one file under
[`architecture/`](./architecture/). This file says how those
parts fit and which file to open. It does not restate a part.
When `architecture/` does not exist yet, this file is the whole
guide until the parts are split out.

The orchestrator reads this index and every part file. That rule
is [`roles/orchestrator.md`](roles/orchestrator.md). Another agent
opens this index and the one part the task names.

Words: [`glossary.md`](./glossary.md). When work is complete:
[`acceptance.md`](./acceptance.md). How work is run is
[`handbook.md`](handbook.md). Stone is the stone row in
[`glossary.md`](./glossary.md).

Gaps between this guide and the running code are closed with a plan.
Do not rewrite the guide to describe leftovers.

## This file can be wrong

This file is what we **currently believe**. It is not a proof. It
will change. An old sentence is not kept because it is old. The
same rule covers every file under `architecture/`.

A better design is welcome. Bring it to the orchestrator with the
argument. If a sentence in this guide is **directionally wrong** (the
structure or the product intent, not a leftover in the code),
**stop work on that issue**. Do not paper over it with a second
path. Do not silently edit the guide. Do not silently change the
code to match a sentence you suspect is stale. We meet. Write the
new sentence in the part it belongs to only when the human says to:
what is true, who does it, and what it does not cover. One sentence
of why when the choice is easy to undo the wrong way. Do not write
what was rejected, and do not record the incident.

**Why this paragraph exists:** agents treated this file as
unchangeable, then hid misses behind fallbacks.

Code that merely lags this guide is a plan, not a meeting. A meeting
is for when the guide itself looks like the mistake.

## What is being built

Inkcut opens an SVG and sends pen-up and pen-down moves to a vinyl
cutter. This checkout is Luke's fork, used with a Summa D760.
Weedlines is not this product. See [`project.md`](./project.md).

The process is an Enaml workbench. `inkcut.app:main` starts it.
Each area (job, device, preview, and the rest) is a plugin with a
manifest. Plugin state is JSON under `~/.config/inkcut/`.

## How the parts fit

A cut moves in this order. There is no `architecture/` directory.
This file is the whole guide.

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
   output scale, mirror, origin side, and rotation. Origin side is
   two radios: Origin left (feed down), the default, and Origin
   right (feed left). Saved `swap_xy` true loads as Origin right.
   Origin left is the old Swap-off path
   ([glossary](./glossary.md)). The result is the **device path**.
   Feed, return, and padding are already in the document path, so
   they take this same orientation. Nothing later adds a move in
   another frame.
4. The preview the operator sees before cutting draws the device
   path. The bed outline uses that same orientation.
5. The device flips Y once, so plotter +Y is the cutter's Y, then
   flattens curves and runs device filters (blade offset, overcut).
6. The protocol converts each point from 90 px per inch into plotter
   units. The transport writes the bytes. The protocol does not
   scale, mirror, or apply origin side.

Step 3 is one transform because the feed and the picture have to
stay on the same edge of the artwork as the knife. A second
transform for only one of them sends the carriage down a different
axis than the screen shows.

Do not add another axis correction inside `Job.create`.

## Layers

| Piece | Owns | Must not own |
| --- | --- | --- |
| `inkcut/core` | Workbench, plugin persistence, SVG to a 90 DPI path | Job layout, device orientation, plotter bytes |
| `inkcut/job` | Document, material, copies, job scale, job mirror, job rotation, weedlines, the document path | Origin side, device scale, plotter units |
| `inkcut/device` | Drivers, connect, submit, the one orientation, curve flattening, device filters, position | A second orientation for the preview, SVG parsing |
| Protocol | One `move(x, y, z)` in plotter units | Scale, mirror, origin side, preview |
| Transport | Bytes on raw, serial, printer, or file | Geometry |
| `inkcut/preview` | The plot widget. Draws the device path. May flip Y for the widget only | Its own origin side or mirror |
| `plugins/inkscape` | Starts `inkcut open` with the selected element ids | Transforms, a full-document fallback |

## Which file

| When the task is about | Read |
| --- | --- |
| Opening an SVG, including Cut Selection | This file, "How the parts fit" step 1 |
| The document path and job layout | This file, step 2, and the job row in "Layers" |
| Device orientation and the device path | This file, steps 3–6, and the device row |
| The pre-cut preview or the bed | This file, step 4, and the preview row |
| Protocol bytes or the transport | This file, steps 5–6 |

A gap between this guide and the tree is a plan. The orientation
name this file uses is the leftover in
[`conflicts.md`](./conflicts.md). Do not describe that leftover
here.
