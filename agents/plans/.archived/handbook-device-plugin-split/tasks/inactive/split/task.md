# split

**Status:** done

## Goal

One session brings `inkcut/device/plugin.py` under 1200 lines
without changing device behavior.

## Do

Own `inkcut/device/plugin.py`. Move `DeviceTransport`,
`TestTransport`, `DeviceProtocol`, `DeviceFilter`, and
`DeviceConfig` into neighbor files named for those types.
Leave `Device`, `DevicePlugin`, and the orientation helpers
in `plugin.py` when that file is then under 1200 lines. If it
is still over, move the orientation helpers next. Do not split
`Device`.

Update imports in the same change. Callers include the device
protocols, filters, transports, `inkcut/job/plugin.py`,
`inkcut/preview/markers.py`, `inkcut/device/dialogs.enaml`,
`inkcut/device/extensions.py`, `inkcut/device/view.enaml`,
`inkcut/device/pi/driver.py`, `inkcut/joystick/plugin.py`, and
the tests named on the plan.

Do not add a directory index for `inkcut/device/`. This split
is not a file the user left large.

## Checks

The checks are on [plan.md](../../../plan.md).

## Note

`plugin.py` was 1398 lines. `DeviceTransport` and `TestTransport`
are now in `device_transport.py` (114). `DeviceProtocol` is in
`device_protocol.py` (111). `DeviceFilter` is in
`device_filter.py` (64). `DeviceConfig` and `_origin_from_legacy`
are in `device_config.py` (134). `TestTransport` stays with
`DeviceTransport` because it is that class's 27-line test double.
`Device`, `DevicePlugin`, and the orientation helpers stayed in
`plugin.py`, which is 1054 lines. `Device` is still one class.

Callers import the moved types from those modules. `Model` comes
from `inkcut.core.api`. `plugin.py` still imports the moved types
because `Device` uses them. One class body each. Saved jsonpickle
state that names `inkcut.device.plugin.DeviceConfig` (and the
other moved types) still loads, because those names are on the
plugin module. `DeviceTransport.protocol` imports `DeviceProtocol`
when the member resolves, so the two modules do not import each
other while loading.

Checked with `QT_QPA_PLATFORM=offscreen python3 -m pytest
tests/test_device_output.py tests/test_filters.py
tests/test_plotter_unit_scale.py`: 102 passed. Moved bodies match
the old `plugin.py` except that forward import. Old and new
jsonpickle `py/type` paths restore each moved type. Every file
that owns a piece of this split is under 1200 lines.

**Summary:** The review found no defect. The moved bodies match
the old `plugin.py` except the forward import on
`DeviceTransport.protocol`. `Device` is still one class.
`plugin.py` is 1054 lines. The new files are 64 to 134 lines.

**Context:** Callers import a moved class from its new module.
`Model` comes from `inkcut.core.api`. The names stay on
`inkcut.device.plugin` as the same objects, so a saved jsonpickle
`py/type` of `inkcut.device.plugin.DeviceConfig` (and the other
moved types) still loads. `DeviceTransport` and `DeviceProtocol`
do not import each other while loading. `TestTransport` stays
with `DeviceTransport`. The test edits only retarget those
imports.

**Result:** No defect. The same three tests were run again:
102 passed.
