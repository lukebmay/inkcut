# clip-drops-short

**Status:** done

## Goal

`clip` returns a shortened string when the value is
longer than the limit.

## Do

Confirmed. `clip` in `inkcut/core/utils.py` evaluates
`v[:n] + "..."` and throws that away, then returns the
original string. The note records that and the review.

Keep the shortened value and return it. Add a test that
a string longer than the limit comes back shortened and
ends with `...`, and that a shorter string is unchanged.
Do not change other behavior.

## Checks

The new test passes. A string of 1001 `a` characters
comes back with length 1003 and ends with `...`.

## Note

Confirmed, then fixed. `clip` used to build `v[:n] + "..."`
and drop it, so `"a" * 1001` came back whole (length 1001).
It now assigns that value and returns it. A shorter string
is unchanged. Callers log the return value.

Review found no defect. See `cr-01.md`.
`python3 -m pytest tests/test_utils.py -q` passed, 2 tests.
`clip("a" * 1001)` is 1000 `a` characters plus `...`,
length 1003.
