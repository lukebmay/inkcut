# cut-selection — Cut Selection opens only the selection

**Status:** active
**Updated:** 2026-10-16

## Goal

Inkscape's Cut Selection action opens only the objects the operator
selected. The rest of the document stays out of the job.

## Acceptance

- [ ] The extension passes SVG element ids (`id` attributes), not
      lxml `xml_path` keys.
- [ ] `QtSvgDoc` keeps a node when its id was requested, or when the
      node is inside a requested element. A selected group includes
      its descendants.
- [ ] When the id list is non-empty and none of those ids are in the
      file, the job does not open the other objects. The operator
      gets an error instead of a full import.
- [ ] A selection that contains text is converted without
      `select-all` pulling in objects that were not selected.
- [ ] A unit test opens a fixture SVG with two paths and one group
      and checks each of those cases. No Inkscape process is required
      for that test.

## Human

- [ ] In Inkscape, select one path in a file that has several, run
      Extensions → Inkcut → Cut selection, and confirm the other
      paths are not in the Inkcut preview.

Why human-only: the unit test does not click the Inkscape menu.

## Approach

`plugins/inkscape/inkcut_cut.py` reads `self.svg.selected.keys()`.
On Inkscape 1.2 that key is `element.xml_path` (an lxml path such as
`/*/*[2]`), not the `id` attribute. The real ids are on
`self.svg.selected.ids` and on `self.options.ids`. `QtSvgDoc` looks
those strings up with `//*[@id="…"]`, finds nothing, and sets
`_nodes` to an empty set. `QtSvgG.parse` skips a child only when
`_nodes` is truthy, so an empty set keeps every object.

Pass the element ids. Treat a non-empty id list that matches nothing
as an error. When a matched node is a group, keep its descendants,
not only the group tag and its ancestors.

`inkcut4inkscape.convert_objects_to_paths` runs Inkscape with
`select-all`. That is the wrong tool for a selection. Convert only
the selected objects, and filter by ids that still exist after the
conversion.

Open in Inkcut (`inkcut_open.py`) is allowed to send the whole
document. This plan does not change that action.

## Session

Not started.

Cause, checked against Inkscape 1.2.2's inkex and this tree:

- `plugins/inkscape/inkcut_cut.py` lines 58–76 pass `nodes.keys()`.
- `/usr/share/inkscape/extensions/inkex/elements/_selected.py`
  stores `elem.xml_path` as the dict key and the real id in `.ids`.
- `inkcut/core/svg.py` `QtSvgDoc.__init__` (about 728–742) and
  `QtSvgG.parse` (about 669–676): empty `valid_nodes` disables the
  filter.
- `inkcut4inkscape.py` `convert_objects_to_paths` uses `select-all`.

Next step: a fixture test for the id filter, then the extension
change. Do not start `device-path` in the same slice.
