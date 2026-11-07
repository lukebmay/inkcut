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

None.

## Closed

| Miss | Where it shows | Plan |
| --- | --- | --- |
| The main window has no WM_CLASS. Qt skips that property when the application is created with an empty argv, so a dock click cannot raise the window. | Ubuntu dock | Fixed in `application_factory`. Test: `tests/test_app.py`. |
| Cut Selection imports the whole SVG. The extension passes lxml paths, the id lookup matches nothing, and an empty match keeps every object. | Inkscape Cut Selection | Fixed. [cut-selection](plans/cut-selection/plan.md) |
| Feed After with the old Swap X/Y control on does not stay past the same edge of the artwork as on screen. The old name is [Swap X/Y](./glossary.md). | D760 | Fixed in slice 2. [device-path](plans/.archived/device-path/plan.md) |
| The pre-cut preview does not show the old Swap X/Y control or device mirror. The old name is [Swap X/Y](./glossary.md). | Preview vs the cut | Fixed in slice 1. [device-path](plans/.archived/device-path/plan.md) |
