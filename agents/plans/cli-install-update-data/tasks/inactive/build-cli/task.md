# build-cli

**Status:** parked

## Goal

Add `inkcut install`, `inkcut update`, and `inkcut data` when he
asks. Not before.

## Do

Do not start. The data commands read and write
`~/.config/inkcut/inkcut.device.json`. The old reference script is
`~/Desktop/inkcut-data/inkcut-data.py`. Close Inkcut before a load
so the GUI does not overwrite the file on exit.

Prefer a Python implementation in this repo. Weedlines install
stays in the weedlines repo.

## Checks

The checks are on [plan.md](../../../plan.md). None are done.

## Note

Parked at triage. The old "fork on hold" blocker is not true
anymore. Optional still means do not start unless he asks.
