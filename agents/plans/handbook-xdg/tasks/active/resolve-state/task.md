# resolve-state

**Status:** ready

## Goal

State resolves on each run because Inkcut has no install
record. The `state-home` pin is gone.

## Do

In `inkcut/core/homes.py`, make `state_home()` use the same
live resolve as `config_home()`. Delete the record helpers
and `_STATE_RECORD`. Do not write a file to remember the
path. An existing `state-home` file is not an install
record. Ignore it.

Leave `data_home()` resolving every run. Leave logs under
`state_home()`. Do not add `inkcut install`. Do not move
plugin JSON out of the config home.

In `tests/test_homes.py`, replace the tests that expect the
pin with tests that a later state variable is honored.
`test_new_logs_use_the_state_home_and_leave_old_logs` still
checks that new logs go to the state home and that old
config-home logs stay put.

In `.travis.yml`, `after_script` cats
`~/.config/inkcut/logs/*.txt`. Logs are in the state home.
With the variables unset, that is
`~/.local/state/inkcut/logs/*.txt`.

Do not edit the guide.

## Checks

The checks are on [plan.md](../../../plan.md).

From the repo root:

`QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_homes.py`

## Note

Not started. Filed with the catalog 0.9.19 update.
