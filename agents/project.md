# Project

**Owner:** human. Agents may propose edits; apply only with explicit permission.

## What this is

Inkcut opens an SVG and sends pen-up and pen-down moves to a vinyl
cutter. This checkout is Luke's fork of
[inkcut/inkcut](https://github.com/inkcut/inkcut) (package version
2.1.9). He uses it to cut on a Summa D760. Upstream stays the
reference. Weedlines is a separate repo at `~/dev/me/weedlines` and
is not this product.

How it is built: [`architecture.md`](./architecture.md). Words:
[`glossary.md`](./glossary.md). Product checks:
[`acceptance.md`](./acceptance.md). Bugs:
[`issues.md`](./issues.md).

## Stack

- Python 3, Enaml, Qt (PyQt), atom, pyqtgraph, Twisted, lxml, jsonpickle
- Package `inkcut/` at the repo root. Console entry
  `inkcut = inkcut.app:main`
- Inkscape extensions in `plugins/inkscape/` call that entry

## Conventions

- Internal geometry is 90 px per inch. Protocols convert that unit
  into plotter units. Job settings and device output scale are
  separate.
- Plugin state is jsonpickle JSON at `~/.config/inkcut/{plugin id}.json`.
  The device file is `inkcut.device.json`. Members tagged
  `config=True` are the ones that persist.
- The D760 profile in use has Swap X/Y turned on. That control is a
  90° rotation, `(x, y) → (−y, x)`, not an exchange of the axes.
  Output scale is applied as part of device orientation.
- Remotes: `origin` is `git@github.com:lukebmay/inkcut.git`.
  `upstream` is `git@github.com:inkcut/inkcut.git`.
