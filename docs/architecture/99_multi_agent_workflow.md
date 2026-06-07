# Multi-Agent Workflow

## 1. Goals

The workflow prevents four common failures:

1. An agent starts on the wrong branch or worktree.
2. Multiple files claim different active tasks.
3. An agent modifies files outside its assigned scope.
4. Untracked files are omitted from review.

## 2. Ownership Model

Use one branch and one worktree per feature agent.

```text
rm_ref_main        main               integration only
rm_ref_core        codex/core
rm_ref_config      codex/config
rm_ref_packer      codex/packer
rm_ref_algo_demo   codex/algo-demo
rm_ref_tests       codex/tests
rm_ref_review      codex/review
rm_ref_uvm_parser  codex/uvm-parser
```

Do not run multiple agents in one worktree. Do not perform feature
implementation in `rm_ref_main`.

## 3. Status Sources

There is one authoritative active-task source:

```text
agents/project_status.json
```

This file owns:

- task id and status
- role prompt
- branch and worktree
- allowed and forbidden paths
- required startup files
- required checks

The following files have narrower roles:

```text
docs/architecture/97_current_task.md
  Generated human-readable view. Never edit manually.

docs/architecture/96_agent_journal.md
  Append-only integration history.

docs/architecture/98_project_progress_snapshot.md
  Historical project overview.

agents/PROJECT_STATUS.md
  Compatibility pointer only.
```

If any generated or historical document disagrees with
`agents/project_status.json`, the JSON file wins.

## 4. Coordinator Setup

The integration coordinator updates `agents/project_status.json`, validates it,
and generates the readable task document:

```powershell
python scripts/agent_workflow.py validate
python scripts/agent_workflow.py render
git status --short
```

The coordinator commits the status JSON, generated task document, role prompt,
fixtures, and required workflow files before creating a feature worktree.

Create the worktree from `rm_ref_main`:

```powershell
git worktree add ..\rm_ref_uvm_parser -b codex/uvm-parser
```

The branch and worktree names must match the authoritative status exactly.

## 5. Agent Startup

From the assigned worktree:

```powershell
python scripts/agent_workflow.py preflight
```

Preflight checks:

- task status allows feature work
- valid status schema
- expected branch
- expected worktree directory
- required files exist
- required files are tracked
- worktree is clean

An agent must stop before implementation when preflight fails.

Feature preflight is allowed only for `READY` and `IN_PROGRESS`. It rejects
planned, setup-only, review, merged, and blocked tasks.

After preflight, read:

1. `AGENTS.md`
2. `agents/README.md`
3. the active role prompt
4. the nearest `AGENTS.md` files for allowed directories

Then report the assignment and planned work.

## 6. Scope Enforcement

The active task's `allowed_paths` list is the complete write boundary.

Before finishing:

```powershell
python scripts/agent_workflow.py check-scope
```

The command checks:

- unstaged tracked changes
- staged changes
- untracked files

This is stricter than `git diff --name-only`, which does not show untracked
files.

Explicit user approval is required to expand scope. The coordinator must update
the authoritative status before work continues.

## 7. Agent Finish

The feature agent:

1. Runs focused tests from the role prompt.
2. Runs the scope check.
3. Reports files changed, tests, failures, limitations, and follow-up.
4. Does not update shared task status or the journal.
5. Does not commit unless explicitly requested.

This avoids conflicts when agents run concurrently.

## 8. Integration

The integration coordinator reviews:

```powershell
git status --short
git diff --name-only
git diff --stat
```

The coordinator verifies scope, commits the feature branch if requested,
merges one branch at a time, and runs the relevant tests after each merge.

After review or merge, the coordinator:

1. Updates `agents/project_status.json`.
2. Runs `python scripts/agent_workflow.py render`.
3. Appends a concise entry to `docs/architecture/96_agent_journal.md`.
4. Commits the JSON, generated view, and journal together.

## 9. Status Values

Use explicit values:

```text
PLANNED
READY_FOR_WORKTREE
READY
IN_PROGRESS
REVIEW
MERGED
BLOCKED
```

`IN_PROGRESS` is valid only after the assigned branch and worktree exist and
preflight passes.

`READY` and `IN_PROGRESS` are the only statuses that allow feature preflight.
All status values are validated against the list above.

## 10. Safety Rules

- Never delete or reset user changes during workflow setup.
- Never create two worktrees for the same branch.
- Never treat a generated file as the status source.
- Never require a planned output document as a startup prerequisite.
- Never hide merge conflicts or failed tests.
- Never use cache files as project artifacts.
- Keep workflow documents UTF-8 and preferably ASCII-only where practical.

## 11. Common Commands

```powershell
python scripts/agent_workflow.py show
python scripts/agent_workflow.py validate
python scripts/agent_workflow.py render
python scripts/agent_workflow.py preflight
python scripts/agent_workflow.py check-scope
git worktree list
git status --short
python -m pytest -q
```

## 12. Recovery

If preflight reports a branch or worktree mismatch, do not edit files. Return
to `rm_ref_main`, review `git worktree list`, and create or select the assigned
worktree.

If required files are untracked, commit the workflow setup on `main` before
creating the feature worktree.

If scope check reports an unrelated existing change, do not revert it. Move
the feature to a clean worktree or ask the coordinator to resolve ownership.
