# Priority

**Owner:** agent. Session notes live on the plan.


**Updated:** 2026-08-21
**Inkcut fork:** **ON HOLD**
**Focus:** **weedlines** — https://github.com/lukebmay/weedlines

## Active

| Pri | Item | Status | Notes |
| --- | --- | --- | --- |
| P0 | Weedlines extract / refine | in progress | `~/dev/me/weedlines` scaffold landed |

## Remaining on weedlines extract task

- Pause/resume beyond cancel
- Island-hop picture QA
- Preview harness polish

See `agents/tasks/weedlines-extract-repo.md`.

## On hold / optional / cancelled

| Item | Status |
| --- | --- |
| All inkcut fork product work | hold |
| inkcut CLI install/update/data | optional |
| inkcut logging-verbosity | cancelled → weedlines `WEEDLINES_LOG` |

## Leftover handoff (fold into the active plan Session, then delete this section)

# Handoff

**Updated:** 2026-08-21
**Inkcut fork:** **ON HOLD** — `~/dev/me/inkcut` / `lukebmay/inkcut`
**Active work:** **weedlines** — `~/dev/me/weedlines` /
https://github.com/lukebmay/weedlines

## Strategy

Upstream Inkcut is maintained. This fork is only for a **later**
`weedlib` integration + PR to `inkcut/inkcut`. Do not develop product
features here now.

## Weedlines (landed scaffold)

- Algorithms: `frame`, `grid`, `island-hop` (ex-`auto`)
- CLI: `weedlines install` / `update`
- Logging: `WEEDLINES_LOG`
- Tests: 136 passed

Continue in the weedlines repo (`agents/HANDOFF.md` there).

## Cancelled / optional

- Cancelled: inkcut logging task
- Optional: inkcut CLI task (`cli-install-update-data.md`)
