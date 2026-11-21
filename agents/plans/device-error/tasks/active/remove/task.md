# remove

**Status:** ready

## Goal

`DeviceError` is gone from the device package.

## Do

Delete `class DeviceError` from `inkcut/device/plugin.py`.
Do not add a raise, a catch, or a subclass to keep the name.
Do not edit the handbook-xdg-homes files. Do not edit the guide.

## Checks

From the repo root:

1. `rg -n DeviceError` finds nothing.
1. `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_device_output.py tests/test_filters.py tests/test_plotter_unit_scale.py`

## Note

Verified on 2026-11-21. The only hit was
`class DeviceError(AssertionError)` in
`inkcut/device/plugin.py`. The check was
`rg -n DeviceError` from the repo root, skipping
`agents/.quarantine/`.
