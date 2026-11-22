# cut-selection — Cut Selection opens only the selection

**Status:** active
**Updated:** 2026-10-16

## Goal

Inkscape's Cut Selection action opens only the objects the operator
selected. The rest of the document stays out of the job.

## Acceptance

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

Cut Selection sends element ids and opens only those objects.
`plugins/inkscape/inkcut_cut.py` passes `list(self.svg.selected.ids)`
on Inkscape 1.X. The 0.9 path still uses `self.selected` keys.
`QtSvgDoc` matches ids with `element.get("id")`, including the root,
and does not build an XPath from the id. A match keeps that element,
its descendants, and its ancestors. A non-empty id list that matches
nothing raises `ValueError` before geometry is parsed, so the other
objects are not imported. A partial match keeps the ids that exist.

`plugins/inkscape/selection.py` holds the action string, the
surviving-id filter, and the text check. A selection that contains
text, including text inside a selected group, is converted with one
`select-by-id` per id and no `select-all`. Ids that contain `;` or a
newline are refused before Inkscape runs. After a successful
conversion, `--nodes` receives the original ids that are still on an
element, in the same order. An empty id list is not passed. If the
selection has no text, the original ids are passed and Inkscape is
not asked to convert. Open in Inkcut is unchanged and still converts
the whole document. Both Inkscape `.inx` files list `selection.py` so
that module is copied with the extensions.

`QtSvgG.parse` skips an id that was not requested before it rejects
text. Unselected text no longer aborts the job. Text that was
selected, including text inside a selected group, still raises until
the extension has converted it.

`QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_svg.py tests/test_cut_selection.py -q`
passed, 24 tests. Pytest cannot import `inkex`, so it does not load
`inkcut_cut.py`. The id pass was read in that file:
`list(self.svg.selected.ids)` on Inkscape 1.X. The installed
extension files are symlinks into this tree, including
`selection.py`, so the Inkscape menu uses this code after Inkscape
is restarted. The Human checkbox is still open. Do not archive this
plan until that check is done.
