# Project: Inkcut (lukebmay fork — clean restart)

## Overview

Fresh fork of [inkcut/inkcut](https://github.com/inkcut/inkcut) at
`~/dev/me/inkcut/`, GitHub remote `lukebmay/inkcut`.

Restarted from upstream tip (v2.1.8 / `c7a0c68`) on 2026-08-21.
**Upstream is still maintained** — this fork is staging for eventual
weedlines integration + PR to the OG maintainer, not a full soft-fork.

| Path | Role |
| --- | --- |
| **`~/dev/me/weedlines/`** | **Primary work** — Inkscape weedlines algos |
| `~/dev/me/inkcut/` (this repo) | Clean fork; later integrate + upstream PR |
| `~/dev/me/inkcut_luke/` | Local-only archive of the old custom fork |

Port from `inkcut_luke` only what weedlines (and later integration)
needs — do not dump the old tree wholesale.

## Stack

- Python 3, Enaml + Qt (PyQt), atom, pyqtgraph, Twisted
- Package: `inkcut/` under repo root; console entry `inkcut = inkcut.app:main`

## Remotes

| Remote | URL |
| --- | --- |
| `origin` | `git@github.com:lukebmay/inkcut.git` |
| `upstream` | `git@github.com:inkcut/inkcut.git` |

## Priorities

See `agents/PRIORITY.md`. Active: `agents/tasks/weedlines-extract-repo.md`.
