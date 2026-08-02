# Priority queue (inkcut_luke)

**Updated:** 2026-08-02  
**Branch:** `refactor1` (merge to master when gates pass)

## Active agent work

| Pri | Item | Status | Notes |
| --- | --- | --- | --- |
| — | *(none)* | — | Auto peel first pass on master |

## Human (does not block agent queue unless hard)

| Pri | Item | Severity | Notes |
| --- | --- | --- | --- |
| P0 | Summa D760 measure origin/feed/protocol | soft | `agents/blockers/B-summa-d760-measure.md` — unlocks named driver preset |
| P1 | Review auto weed SVG previews / real jobs | soft | `tests/data/weed_preview/`; app Weed mode = Auto peel |
| P2 | Upstream contribution packaging | soft | After D760 path trusted |

## Backlog (agent-eligible when scheduled)

| Pri | Item | Kind | Notes |
| --- | --- | --- | --- |
| P2 | Auto weed peel tuning | ready | Plan: `agents/plans/auto-weed-peel.md` — knobs, fewer false reliefs, real logos |

## Rules

- Draft / optional tasks are **not** blockers; skip them unless the user asks.
- Hardware verify stays **soft** until an agent task *requires* measured values.
- Do not invent protocol mirrors to fake origin; measure first.
