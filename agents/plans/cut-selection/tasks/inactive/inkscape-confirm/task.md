# inkscape-confirm

**Status:** waiting

## Goal

Confirm in Inkscape that Cut Selection opens only the selected
path.

## Do

The operator does this. An agent does not click the Inkscape menu,
and does not redo the code checks.

## Checks

- [ ] In Inkscape, select one path in a file that has several, run
      Extensions → Inkcut → Cut selection, and confirm the other
      paths are not in the Inkcut preview.

## Note

Why human-only: the unit test does not click the Inkscape menu.

On 2026-10-17 he opened one of two text objects with Cut selection
and only that object came in. That was the text case. This path
checkbox is still open.

The code checks passed before that
(`tests/test_svg.py` and `tests/test_cut_selection.py`, 24 tests).
Do not archive this plan until this check is done.
