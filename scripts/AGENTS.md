# scripts/AGENTS.md

## Role

`scripts/` contains local developer helper scripts.

These scripts are used to simplify common repository operations, such as:

- creating Git worktrees
- running tests
- merging agent branches
- cleaning temporary files
- checking repository status

Scripts are convenience helpers only.

They must not hide dangerous behavior.

## Target environment

The primary development environment is Windows PowerShell.

PowerShell scripts should be clear and explicit.

If adding shell scripts for Linux/macOS, keep them separate and do not assume they are available on Windows.

## Typical scripts

Expected scripts may include:

```text
create_worktrees.ps1
run_tests.ps1
merge_agents.ps1
clean_worktrees.ps1
status_agents.ps1
```

## Safety rules

Scripts must avoid destructive behavior unless the action is clearly documented and requires confirmation.

Dangerous actions include:

```text
deleting worktrees
deleting branches
resetting branches
cleaning untracked files
force pushing
overwriting generated files
```

If a script performs a dangerous action, it should:

```text
1. print what it is going to do
2. ask for explicit confirmation
3. exit safely if confirmation is not given
```

## Git worktree rules

When managing worktrees, preserve this structure:

```text
rm_ref_main        main
rm_ref_arch        codex/arch
rm_ref_core        codex/core
rm_ref_config      codex/config
rm_ref_packer      codex/packer
rm_ref_algo_demo   codex/algo-demo
rm_ref_tests       codex/tests
rm_ref_review      codex/review
```

Do not create multiple worktrees for the same branch.

Do not run multiple agents in the same worktree.

Do not let agents work directly in `rm_ref_main` unless explicitly instructed.

## Test scripts

A test script may run:

```powershell
pytest -q
```

Focused test commands may include:

```powershell
pytest -q tests/test_core
pytest -q tests/test_schema
pytest -q tests/test_config
pytest -q tests/test_validator
pytest -q tests/test_packer
pytest -q tests/test_algorithms
pytest -q tests/test_integration
```

A test script should return a non-zero exit code if tests fail.

## Merge scripts

A merge script may help merge branches into `main`, but it should not hide conflicts.

Recommended merge order:

```text
codex/arch
codex/core
codex/config
codex/packer
codex/algo-demo
codex/tests
codex/review
```

After each merge, run tests.

If a conflict occurs, stop and ask the user to resolve or launch a dedicated merge agent.

## Logging

Scripts may print concise status messages.

Avoid noisy output unless debugging is explicitly enabled.

Good output:

```text
[INFO] Creating worktree rm_ref_core from branch codex/core
[INFO] Running pytest -q tests/test_core
[ERROR] Tests failed
```

## Path rules

Avoid hard-coded private machine paths when possible.

If a default path is used, make it easy to change.

Prefer relative paths from the repository root.

## Python environment

Scripts should not assume a specific conda environment name unless clearly documented.

If a script activates an environment, make the environment name configurable.

## Forbidden behavior

Scripts must not:

```text
silently delete worktrees
silently delete branches
silently reset user changes
silently overwrite files
force push
install dependencies without user confirmation
call network services without user confirmation
hide failing test results
```

## Completion checklist

Before finishing a script task, check:

```text
git diff --name-only
git diff --stat
```

If a script was added or changed, also check:

```text
powershell -ExecutionPolicy Bypass -File scripts/<script_name>.ps1 -Help
```

or document why the script does not support `-Help` yet.