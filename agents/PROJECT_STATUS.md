# Project Status

This file is a compatibility pointer for older startup instructions.

The authoritative active-task state is:

```text
agents/project_status.json
```

The human-readable generated view is:

```text
docs/architecture/97_current_task.md
```

Do not add live branch, worktree, status, scope, or task details here. Keeping
those details in multiple files caused stale and contradictory assignments.

Use:

```powershell
python scripts/agent_workflow.py show
python scripts/agent_workflow.py validate
```
