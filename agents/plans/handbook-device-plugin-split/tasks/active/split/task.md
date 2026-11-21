# split

**Status:** ready

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

The developer writes what changed, why, and how it was checked.
The reviewer then writes the summary, the context worth keeping,
and the result.
