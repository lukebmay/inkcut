# triage

**Status:** done

## Goal

Quarantine the old handbook, install agent-handbook, carry
project facts, translate the plans, and rank the queue.

## Do

Done. Do not run this migration again. `agents/handbook.md` is
already the live handbook.

## Checks

The checks on [plan.md](../../../plan.md) are ticked.

## Note

Handoff, 2026-11-06.

No carried task had to finish before this triage. Nothing
product-side was implemented. In particular, do not treat
guide-words, nine anchors, facing view, or the Inkscape
confirmation as work this migration started.

Quarantine is `agents/.quarantine/`. It is not in force.
`agent-handbook init` did not report a flat-file migration.
Language installed: python. No extra kit. The core set came
from init. Root `agents.py` and the generated index live only
in the quarantine. Live `AGENTS.md` is the kernel. There is
no composer.

Facts carried into the live files: `project.md`, the target
cut and layers in `architecture.md`, the three product words
in `glossary.md`, the Swap X/Y leftover, one resolved row
(`Job.create` orients the document path, feed included), and
the closed issues. The old "Running code" snapshot was not
copied. It said `Job.create` still takes `swap_xy`. `create`
takes no arguments. The guide was not rewritten to
`origin_side`. Acceptance had no product checks to add.

Left in quarantine on purpose: `human.md` (collaboration,
plus the old Continue rule), the generated index, `general.md`
was not in the tree, the composer, the weedlines extract
recipe under `notes/`, and the resolved rows for `design.md`
and `HANDOFF.md` (the new glossary already says those).
`logging-verbosity` was cancelled and belongs to weedlines.
It was not copied.

Queue after triage: device-path rank 4, waiting. cut-selection
rank 3, waiting. cli-install-update-data rank 1, not listed.
weedlines-extract-repo and plotter-unit-scale are archived
with this plan. The Swap X/Y leftover stays open. It is not
an Active conflict. Do not implement either side until he
says to edit the guide.
