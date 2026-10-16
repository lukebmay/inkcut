# Architecture

**Owner:** human. Agents may propose edits; apply only with explicit permission.

This file is the **target** architecture: how the product is supposed
to work, including the vision that the code has not reached yet. It
is not a snapshot of today's tree, and it is not a log of bugs. Bugs
live in [`issues.md`](./issues.md).

After reading it, you should be able to walk a user action from
event to result without guessing which layer owns the change.

Gaps between this file and the running code are closed with a plan.
Do not rewrite this file to describe leftovers.

Words: [`glossary.md`](./glossary.md). When work is complete:
[`acceptance.md`](./acceptance.md). How work is run, including what
is stone: catalog `general.md` and [`general.md`](./general.md) when
this project has one.

## This file can be wrong

This file is what we **currently believe** is the best structure. It
is not a proof. It will change. Parts of it will turn out to be
wrong.

If you think a lock here is **directionally wrong** (the structure
or the product intent, not a leftover in the code), **stop work on
that issue**. Do not paper over it with a second path. Do not silently
edit this file. Do not silently change the code to match a sentence
you suspect is stale. We meet. Write the new lock here only when the
human says to: what is true, who does it, and what it does not cover.
One sentence of why when the choice is easy to undo the wrong way.
Do not write what was rejected.

**Why this paragraph exists:** agents treated this file as
unchangeable, then hid misses behind fallbacks.

Code that merely lags this file is a plan, not a meeting. A meeting
is for when this file itself looks like the mistake.

## What is being built

This fork of Inkcut is a **staging tree** for weedlines integration
and an eventual PR to upstream. Product work on the fork is on hold;
active cutting algorithms live in `~/dev/me/weedlines`.

Do not treat this checkout as the weedlines product.

## Layers

| Piece | Owns | Must not own |
| --- | --- | --- |
| (name) | (facts) | (facts) |

## Notes

(key inner workings / tech choices — keep focused; include **why**)
