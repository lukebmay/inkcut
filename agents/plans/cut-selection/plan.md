# cut-selection

**Rank:** 3

## Goal

Inkscape's Cut Selection action opens only the objects the operator
selected. The rest of the document stays out of the job.

## Guide

[`architecture.md`](../../architecture.md) — "How the parts fit"
step 1, and the `plugins/inkscape` row. Open in Inkcut may still
send the whole document. This plan does not change that action.

## Checks

- [x] The extension passes SVG element ids (`id` attributes), not
      lxml `xml_path` keys.
- [x] `QtSvgDoc` keeps a node when its id was requested, or when the
      node is inside a requested element. A selected group includes
      its descendants.
- [x] When the id list is non-empty and none of those ids are in the
      file, the job does not open the other objects. The operator
      gets an error instead of a full import.
- [x] A selection that contains text is converted without
      `select-all` pulling in objects that were not selected.
- [x] A unit test opens a fixture SVG with two paths and one group
      and checks each of those cases. No Inkscape process is required
      for that test.
- [ ] The Inkscape menu check is still open. It is
      [inkscape-confirm](tasks/inactive/inkscape-confirm/task.md).
      An agent cannot tick it.
