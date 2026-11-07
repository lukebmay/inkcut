# complete-v0.1.4-v0.7.0-migration

**Rank:** 5

## Goal

Move this project from the `agents` composer handbook onto
`agent-handbook`, translate the existing plans into the new
shape, and triage the queue before any other plan continues.

Triage is finished. This plan is done. It is not on the queue.

## Guide

[`handbook.md`](../../../handbook.md),
[`plans/README.md`](../../README.md), and
[`versions.md`](../../../versions.md). The quarantined tree is not
in force.

## Checks

- [x] Steps 1–3 are done. The live handbook is
      `agents/handbook.md` and `agents/roles/`. There is no
      composer.
- [x] Every plan that was live is in the new plan shape.
      Flat plan files are translated. They are not left as
      the queue.
- [x] Each plan's status was re-read against the new handbook.
- [x] A plan that is waiting was checked again. It stays
      waiting only when the new handbook still makes that
      wait true.
- [x] A plan whose work is already done is closed, even if
      it was still sitting on the old queue.
- [x] Each remaining plan has a status and a rank, and
      `priority.md` lists them in rank order. This plan
      stayed rank 5 until that triage finished, then left
      the queue.
