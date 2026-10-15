# plotter-unit-scale — Match plotter units to the command Inkcut sends

**Status:** waiting
**Updated:** 2026-10-14

## Goal

A Summa D760 cut of a known length matches that length. DM/PL mode 1
already tells the cutter that one plotter unit is 0.001 inch, and
HP-GL on a Summa is locked at 0.025 mm. Inkcut emits 1021 units per
inch for both, so the piece comes out large. This plan makes the
emitted unit follow the command Inkcut already sends, and gives the
D760 a preset that starts in DM/PL mode 1.

## Acceptance

- [x] DM/PL mode 1 still sends `;:HAEC1` on connect. A 1 inch move
      (90 internal units) is emitted as 1000 plotter units on each
      axis.
- [x] DM/PL mode 2 still sends its current connect string containing
      `ECN`. A 1 inch move is emitted as 1016 plotter units.
- [x] DM/PL modes 3, 4, and 6 keep their current connect strings
      (` ;:H A L0 ` or `IN;PA;`). Their addressing member is
      `Enum(<menu order>)(<1021 item>).tag(config=True)`. `move`
      reads that live member for those modes only. Modes 1 and 2 do
      not consult it. Left at the default, a 1 inch move is still
      1021 plotter units. Setting the choice does not add an `EC`
      command.
- [x] HP-GL still defaults to 1021 plotter units per inch, including
      a device whose saved config has no addressing field. Choosing
      0.025 mm emits 1016. Choosing 0.001 inch emits 1000. Choosing
      0.1 mm emits 254. Choosing 0.005 inch emits 200.
- [x] The HP-GL factory applies `default_config['protocol']['hpgl']`
      the way the DM/PL factory applies `default_config['protocol']['dmpl']`.
- [x] Plotter units in `move` are computed from the live protocol
      config. The numeric scale is not tagged `config=True` and is
      not the saved control.
- [x] A Summa D760 declaration exists. Width is `740mm` (SummaCut
      manual: maximum cutting area 740 mm by 50 m). Length stays
      blank, same as the other roll cutters. Device output scale
      stays `[1, 1]`.
- [x] A new D760 starts on DM/PL mode 1, so a 1 inch move emits 1000.
      Its HP-GL config emits 1016. A driver with no `initial_protocol`
      whose protocols are only HP-GL and DM/PL still starts on HP-GL.
      That test does not use a driver that also lists GPGL. Graphtec
      stays on GPGL.
- [x] The Inkcut Generic Driver stays one driver. Protocol manifest
      order is unchanged. Graphtec protocol lists are unchanged.
- [x] Tests cover the cases above without a window, a serial port, or
      a live cutter. They use `int()` truncation, not `round()`.

## Human

Not a blocker for implementation. Do this after the code is on
`master`. Only a person at the cutter can measure the line.

If Device output scale was already set near 0.979 (1000/1021) or
0.995 (1016/1021) to hide this bug, set both axes back to 1 before
the test cut.

Send a 10 inch line on the D760 with the new DM/PL mode 1 path.

- [ ] The cut is 10 inches within the cutter's own accuracy (about
      0.2% of the move, or 0.25 mm). That is the right unit. It does
      not prove the firmware honored `EC1`. The same length is what
      you get when the stored menu is already 0.001 inch.
- [ ] About 1.6% short (about 9.84 inches) means the cutter ignored
      `EC1` and the menu is 0.025 mm. Switch DM/PL to mode 2 and cut
      again.
- [ ] About 3.9 times as long means the menu is 0.1 mm. About 5 times
      as long means 0.005 inch. Set the protocol to that unit.
- [ ] Still about 2% long means 1021 units per inch are still being
      sent. That is not an ignored `EC1`. Do not compensate in the
      output-scale box.

## Approach

The unit lives on the protocol config. Device output scale stays the
calibration trim. One helper maps a unit name to plotter units per
inch (1000, 1016, 254, 200, 1021) and both protocols call it.

DM/PL modes 1 and 2 already choose the unit in the connect branch.
`move` uses that same branch. It does not parse the connect string
and it does not consult a second control:

| Mode | Connect string (unchanged) | Units per inch |
| --- | --- | --- |
| 1 | `;:HAEC1` (`EC1`, 0.001 inch) | 1000 |
| 2 | ` ;:ECN A L0 ` (`ECN`, 0.025 mm) | 1016 |
| 3, 4 | ` ;:H A L0 ` | from the addressing choice, default 1021 |
| 6 | `IN;PA;` | from the addressing choice, default 1021 |

Modes 3, 4, and 6 do not gain an `EC` command. Their addressing
member on `DMPLConfig` is `Enum(<menu order>)(<1021 item>).tag(config=True)`.
`move` reads that live member only when the mode is 3, 4, or 6.
Modes 1 and 2 keep using the connect branch and do not consult it.
On modes 1 and 2 the settings show the unit that branch commands.
They do not offer a second control that can disagree with it.

HP-GL never sends `EC`. A new `addressing` member on `HPGLConfig` is
tagged `config=True`. Atom's `Enum` uses the first item as the
default, and `default=` is invalid, so the member is built as
`Enum(<menu order>)(<1021 item>)`. The 1021 item is what a missing
saved key keeps, because `Model.__setstate__` writes only keys that
are present. `move` reads that live member. Do not copy the number
onto a `scale` Float in the factory.

`hpgl_factory` passes `HPGLConfig(**driver.get_protocol_config('hpgl'))`.
A unit key outside `default_config['protocol']` is handed to
`DeviceConfig` and never reaches the protocol.

`get_device_from_driver` filters protocols in workbench registration
order. HP-GL is registered before DM/PL, so `protocols[0]` is HP-GL
even when the declaration lists DM/PL first. Do not reorder
`ProtocolManifest` and do not make declaration order win for every
driver. That would move the Graphtec drivers off GPGL. Add one
optional `initial_protocol` id on `DeviceDriver`. When set,
`get_device_from_driver` moves that id to the front of the filtered
list. Unset leaves today's order. The D760 sets it to `dmpl`.

The D760 declaration is:

```python
manufacturer = 'Summa'
model = 'D760'
width = '740mm'
initial_protocol = 'dmpl'
protocols = ['hpgl', 'dmpl']
connections = ['serial', 'printer']
default_config = {
    'protocol': {
        'dmpl': {'mode': 1},
        'hpgl': {'addressing': '<0.025 mm item>'},
    },
}
```

`protocols` lists both languages. Startup is `initial_protocol`, not
list order. HP-GL's 0.025 mm item is whatever string the Enum uses
for 1016 units per inch. DM/PL mode 1 is what produces 1000.

The settings view for DM/PL is the second `DMPLConfigView` in
`inkcut/device/protocols/view.enaml`. The first definition is unused.
Edit the one `dmpl_config_view` returns.

Do not query the cutter. Summa Cutter Control uses its own parameter
protocol. DM/PL `ER` and `Q` do not report addressing.

Do not change `set_pen`. It writes `EC` plus a pen index, which is
addressing, not a pen command, and the job loop does not call it.

Tests capture bytes with `TestTransport` from `inkcut.device.plugin`:
construct the protocol, `TestTransport(protocol=p)`, `connect()` so
`connection_made` runs, then `move(90, 0, z)` and read
`buffer.getvalue()`. Importing the plugin loads Qt and does not open
a window. Do not boot `tests/test_app.py`. Slice 2 calls the real
`dmpl_factory` and `hpgl_factory` with the D760 declaration, and
asserts the `initial_protocol` rule. It does not need the workbench.

Shipped cut size changes for DM/PL modes 1 and 2. `agents/acceptance.md`
is human-owned. Do not edit it unless the operator asks.

## Slices

Serial. No parallel implementation.

1. **Protocol units.** Non-trivial. A/B taskforce (implement, then
   verify). Shared unit helper, DM/PL scale from the connect branch,
   HP-GL addressing member, factory reads protocol config, settings
   text, byte tests.
2. **D760 preset and initial protocol.** A/B taskforce after slice 1
   signs off. `initial_protocol` on the driver, the declaration
   above, and the factory-plus-startup test. No Graphtec edits. No
   protocol-manifest reorder.

## Session

**Status:** waiting on the Human test cut. Both slices are verified.
Slice 1 verifier PASS (33 tests). Slice 2 verifier PASS (35 tests
in `tests/test_plotter_unit_scale.py`). Do not re-implement. The
next step is the person at the cutter, in the Human section.

**Slice 1:** `units_per_inch` lives in
`inkcut/device/protocols/units.py`. Menu order, then the legacy rate:
`0.001 inch` = 1000, `0.025 mm` = 1016, `0.1 mm` = 254,
`0.005 inch` = 200, `1021 per inch` = 1021. Slice 2's HP-GL
`0.025 mm` item is the string `0.025 mm`. Both configs use
`Enum(*ADDRESSING_ORDER)(ADDRESSING_LEGACY).tag(config=True)`.
`move` does `int(internal * per_inch / INKCUT_DPI)`. DM/PL modes 1
and 2 do not read `addressing` (1000 and 1016). Modes 3, 4, and 6
do. There is no `scale` Float. Connect strings and `set_pen` are
unchanged. `hpgl_factory` now builds
`HPGLConfig(**driver.get_protocol_config('hpgl'))`. A missing
addressing key stays `1021 per inch` because `__setstate__` writes
only keys that are present.

Settings edit the second `DMPLConfigView` only. Modes 1 and 2 show
the commanded unit as a label (`0.001 inch` or `0.025 mm`), not a
second control. Modes 3, 4, and 6, and HP-GL, show the addressing
combo. The default selection is `1021 per inch`.

**Tests:** `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_plotter_unit_scale.py -q`
→ 33 passed. No window, serial port, or `tests/test_app.py`.

**Slice 2:** `DeviceDriver.initial_protocol` is optional. Empty keeps
registration order. `get_device_from_driver` stable-sorts that id to
the front of the local filtered list only. `self.protocols` is not
mutated. Summa D760 is declared after the T600: width `740mm`, no
length, `initial_protocol = 'dmpl'`, protocols `hpgl` and `dmpl`,
connections `serial` and `printer`, DM/PL mode 1, HP-GL addressing
`0.025 mm`. No `scale` key. Output scale stays `[1, 1]`. Protocol
manifest order and Graphtec lists are unchanged.

**Tests:** `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/test_plotter_unit_scale.py -q`
→ 35 passed (33 from slice 1, plus D760 factories and the startup
rule). The startup test feeds `get_device_from_driver` a registry
ordered gpgl, hpgl, dmpl. D760 starts on dmpl. A driver with no
`initial_protocol` and only hpgl+dmpl starts on hpgl. No Graphtec
startup assertion.

**Guessed:** this D760 honors `EC1`. The Human section is the
measurement, not a proof of that command.
