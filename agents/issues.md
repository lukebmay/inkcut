---
title: Issues
read_when: Filing a bug, reading a known miss, or about to put a bug story into architecture
order: 40
---

# Issues

**Owner:** agent. Agents read and write this file.

Bugs live here. They are not stone, and they are not the design.
How the product is built stays in [`architecture.md`](./architecture.md).
A product check stays in [`acceptance.md`](./acceptance.md). A fix
still needs a test ([`testing.md`](./testing.md)). Closing a row
does not replace that test.

A new miss gets a row under **Open** in the same turn it is found.
When a row would change the target design, stop and meet. Do not
paper the architecture with the story.

## Open

| Miss | Where it shows | Plan |
| --- | --- | --- |
| Cut Selection imports the whole SVG. The extension passes lxml paths, the id lookup matches nothing, and an empty match keeps every object. A selected group would still drop its children after the ids are fixed. | Inkscape Cut Selection | [`cut-selection`](./plans/cut-selection.md) |
| Feed After with Swap X/Y on does not stay past the same edge of the artwork as on screen. The feed is appended after the rotation, at x = 0 in the rotated frame. | D760, Swap X/Y on | [`device-path`](./plans/device-path.md) |
| The pre-cut preview does not show Swap X/Y or device mirror. The live bed rotates with a different matrix than the toolpath. | Preview vs the cut | [`device-path`](./plans/device-path.md) |
