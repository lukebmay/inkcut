# index

**Status:** in-progress

## Goal

`inkcut/core/` has a directory index.

## Do

Write `inkcut/core/README.md`. Each entry is the file name
and one sentence for what that file owns. The source files
are `__init__.py`, `api.py`, `declarative.py`, `homes.py`,
`manifest.enaml`, `models.py`, `plugin.py`, `svg.py`,
`utils.py`, `widgets.py`, and `workbench.py`. Read each
file only enough to write that sentence. Do not change
behavior. Do not edit the guide or `agents/installed/`.

## Checks

The index exists and names each of those files once.
`git diff` shows no other product file changed by this task.

## Note

The developer writes what changed, why, and how it was checked.
The reviewer then writes the summary, the context worth keeping,
and the result.
