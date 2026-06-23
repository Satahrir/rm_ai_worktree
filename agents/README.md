# Agent Workflow

## Purpose

This directory contains role prompts and the authoritative active-task status
used by the multi-agent workflow.

## Sources Of Truth

The copy of `agents/project_status.json` in the integration worktree is the
only authoritative source for the active task, assigned branch, worktree,
allowed paths, forbidden paths, and required checks.

Feature worktrees contain tracked snapshots of the file. After branches
diverge, those snapshots are not authoritative. Workflow commands locate the
integration worktree with `git worktree list` and read status from there unless
an explicit `--status-file` is provided.

`docs/architecture/97_current_task.md` is generated from that JSON file. Do not
edit it manually.

`docs/architecture/96_agent_journal.md` is append-only history maintained by
the integration coordinator after review or merge.

`docs/architecture/98_project_progress_snapshot.md` is a maintained project
overview. It must not override the active-task JSON.

## Roles

Each role has one prompt:

```text
arch_agent_prompt.md
core_agent_prompt.md
core_hardening_agent_prompt.md
config_agent_prompt.md
packer_agent_prompt.md
algo_demo_agent_prompt.md
runtime_agent_prompt.md
tests_agent_prompt.md
review_agent_prompt.md
uvm_table_parser_agent_prompt.md
uvm_table_json_agent_prompt.md
uvm_table_schema_adapter_agent_prompt.md
```

The role prompt defines task-specific behavior. The active status JSON defines
the current assignment. The narrower applicable rule wins, but no role prompt
may expand beyond the paths listed in the active status without explicit user
approval.

## Startup

From the assigned worktree:

```powershell
python scripts/agent_workflow.py preflight
```

Preflight verifies:

- the status file is valid
- the authoritative status comes from the integration worktree
- the task status allows feature work
- the current branch matches the assignment
- the worktree directory matches the assignment
- required startup files exist and are tracked
- the worktree is clean before feature work begins

Do not start implementation when preflight fails.

## Finish

Run focused tests and:

```powershell
python scripts/agent_workflow.py check-scope
```

Scope checking includes committed feature-branch changes since divergence from
the integration branch, staged changes, unstaged changes, and untracked files.

The feature agent reports results but does not edit shared status or journal
files. The integration coordinator owns status transitions and journal
updates.

## Status Update

The integration coordinator:

1. Edits `agents/project_status.json`.
2. Runs `python scripts/agent_workflow.py validate`.
3. Runs `python scripts/agent_workflow.py render`.
4. Reviews `git status --short`, including untracked files.
5. Commits the status source and generated current-task document together.

After a milestone or workflow-rule change, the coordinator also audits the
maintained README, progress snapshot, workflow guide, and affected interface or
architecture documents for stale implemented-status claims.

## Safety

- One agent uses one branch and one worktree.
- `rm_ref_main` is for integration and explicitly approved workflow work.
- Do not run multiple agents in one worktree.
- Do not use `git diff --name-only` alone; it omits untracked files.
- Do not commit automatically unless the user explicitly requests it.
