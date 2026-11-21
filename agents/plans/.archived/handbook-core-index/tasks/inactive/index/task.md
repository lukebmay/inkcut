# index

**Status:** done

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

Added `inkcut/core/README.md`. Each listed source file is named
once, with one sentence for what that file owns. No behavior
change, and no other product file edited.

Checked that those eleven names each appear once. `git status`
shows this index as untracked and this note as the only tracked
change. No other product file changed.

Summary: the index names each of the eleven source files once.
Each sentence matches what that file owns, and it does not copy
the files. No other product file changed.

Context: `__init__.py` is empty and exports nothing. No file in
the directory is over 1200 lines, so the index has no size
exception. `svg.py` is 894. A later `git status` also shows
handbook dirt (`agents/issues.md`, `agents/priority.md`,
`agents/.quarantine/`, `agents/plans/_bugs/`). That is not this
task. The brief names no product test.

Result: no defect. The named checks passed.
