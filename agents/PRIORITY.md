# Priority queue (inkcut_luke)

**Updated:** 2026-08-01  
**Branch:** `refactor1` (plan work; merge to master when gates pass)

## Active agent work

| Pri | Item | Status | Notes |
| --- | --- | --- | --- |
| P1 | Typed travel segments | TF-A done → TF-B | `agents/tasks/cutter-path-and-coords_typed-travel.md` on `refactor1` |

## Human (does not block agent queue unless hard)

| Pri | Item | Severity | Notes |
| --- | --- | --- | --- |
| P0 | Summa D760 measure origin/feed/protocol | soft | `agents/blockers/B-summa-d760-measure.md` — unlocks named driver preset |
| P2 | Upstream contribution packaging | soft | After D760 path trusted |

## Backlog (agent-eligible when scheduled)

| Pri | Item | Kind | Notes |
| --- | --- | --- | --- |
| P2 | Optional preview legend UI | optional | Plan residual; skip unless asked |
| P3 | Tag/archive `inkcut_ai_fail` ref2 | optional | Housekeeping only |

## Rules

- Draft / optional tasks are **not** blockers; skip them unless the user asks.
- Hardware verify stays **soft** until an agent task *requires* measured values.
- Do not invent protocol mirrors to fake origin; measure first.
