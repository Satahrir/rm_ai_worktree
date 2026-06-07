from __future__ import print_function

import argparse
import json
import os
import subprocess
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_STATUS_PATH = os.path.join(REPO_ROOT, "agents", "project_status.json")
DEFAULT_CURRENT_TASK_PATH = os.path.join(
    REPO_ROOT, "docs", "architecture", "97_current_task.md"
)

REQUIRED_TOP_LEVEL_KEYS = (
    "version",
    "project",
    "integration_branch",
    "integration_worktree",
    "active_task",
)

REQUIRED_TASK_KEYS = (
    "id",
    "status",
    "goal",
    "role",
    "branch",
    "worktree",
    "prompt",
    "allowed_paths",
    "forbidden_paths",
    "required_files",
    "checks",
)


class WorkflowError(Exception):
    pass


def _normalized_path(path):
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def load_status(path=DEFAULT_STATUS_PATH):
    try:
        with open(path, "r") as stream:
            status = json.load(stream)
    except IOError as exc:
        raise WorkflowError("cannot read status file: {0}".format(exc))
    except ValueError as exc:
        raise WorkflowError("invalid status JSON: {0}".format(exc))

    validate_status(status)
    return status


def validate_status(status):
    missing = [key for key in REQUIRED_TOP_LEVEL_KEYS if key not in status]
    if missing:
        raise WorkflowError(
            "status file missing top-level keys: {0}".format(", ".join(missing))
        )

    task = status["active_task"]
    if not isinstance(task, dict):
        raise WorkflowError("active_task must be an object")

    missing = [key for key in REQUIRED_TASK_KEYS if key not in task]
    if missing:
        raise WorkflowError(
            "active_task missing keys: {0}".format(", ".join(missing))
        )

    for key in ("allowed_paths", "forbidden_paths", "required_files", "checks"):
        if not isinstance(task[key], list):
            raise WorkflowError("active_task.{0} must be a list".format(key))

    if not task["allowed_paths"]:
        raise WorkflowError("active_task.allowed_paths must not be empty")

    return status


def render_current_task(status):
    task = status["active_task"]
    lines = [
        "# Current Task",
        "",
        "> Generated from `agents/project_status.json`. Do not edit manually.",
        "",
        "## Assignment",
        "",
        "- Task: `{0}`".format(task["id"]),
        "- Status: `{0}`".format(task["status"]),
        "- Role: `{0}`".format(task["role"]),
        "- Branch: `{0}`".format(task["branch"]),
        "- Worktree: `{0}`".format(task["worktree"]),
        "- Prompt: `{0}`".format(task["prompt"]),
        "",
        "## Goal",
        "",
        task["goal"],
        "",
        "## Allowed Paths",
        "",
    ]
    lines.extend("- `{0}`".format(path) for path in task["allowed_paths"])
    lines.extend(["", "## Forbidden Paths", ""])
    lines.extend("- `{0}`".format(path) for path in task["forbidden_paths"])
    lines.extend(["", "## Required Checks", ""])
    lines.extend("- `{0}`".format(command) for command in task["checks"])

    notes = task.get("notes", [])
    if notes:
        lines.extend(["", "## Notes", ""])
        lines.extend("- {0}".format(note) for note in notes)

    lines.append("")
    return "\n".join(lines)


def write_current_task(status, output_path=DEFAULT_CURRENT_TASK_PATH):
    rendered = render_current_task(status)
    with open(output_path, "w") as stream:
        stream.write(rendered)


def _run_git(args, repo_root=REPO_ROOT):
    command = ["git"] + list(args)
    process = subprocess.Popen(
        command,
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        detail = stderr.strip() or stdout.strip()
        raise WorkflowError(
            "git command failed ({0}): {1}".format(" ".join(command), detail)
        )
    return stdout.strip()


def changed_paths(repo_root=REPO_ROOT):
    tracked = _run_git(["diff", "--name-only", "--relative"], repo_root)
    staged = _run_git(
        ["diff", "--cached", "--name-only", "--relative"], repo_root
    )
    untracked = _run_git(
        ["ls-files", "--others", "--exclude-standard"], repo_root
    )
    paths = set()
    for output in (tracked, staged, untracked):
        for line in output.splitlines():
            if line.strip():
                paths.add(_normalized_path(line.strip()))
    return sorted(paths)


def path_is_allowed(path, allowed_paths):
    normalized = _normalized_path(path)
    for allowed in allowed_paths:
        prefix = _normalized_path(allowed)
        if prefix.endswith("/"):
            if normalized.startswith(prefix):
                return True
        elif normalized == prefix:
            return True
    return False


def scope_violations(paths, allowed_paths):
    return [
        path for path in paths if not path_is_allowed(path, allowed_paths)
    ]


def tracked_files(repo_root=REPO_ROOT):
    output = _run_git(["ls-files"], repo_root)
    return set(_normalized_path(path) for path in output.splitlines() if path)


def preflight_errors(status, repo_root=REPO_ROOT, require_clean=True):
    task = status["active_task"]
    errors = []

    branch = _run_git(["branch", "--show-current"], repo_root)
    if branch != task["branch"]:
        errors.append(
            "branch mismatch: expected {0}, found {1}".format(
                task["branch"], branch or "(detached HEAD)"
            )
        )

    worktree = os.path.basename(os.path.abspath(repo_root))
    if worktree.lower() != task["worktree"].lower():
        errors.append(
            "worktree mismatch: expected {0}, found {1}".format(
                task["worktree"], worktree
            )
        )

    tracked = tracked_files(repo_root)
    for relative_path in task["required_files"]:
        normalized = _normalized_path(relative_path)
        absolute_path = os.path.join(
            repo_root, *normalized.split("/")
        )
        if not os.path.exists(absolute_path):
            errors.append("required file missing: {0}".format(normalized))
        elif normalized not in tracked:
            errors.append("required file is not tracked: {0}".format(normalized))

    current_task_path = os.path.join(
        repo_root, "docs", "architecture", "97_current_task.md"
    )
    if os.path.exists(current_task_path):
        try:
            with open(current_task_path, "r") as stream:
                current_task = stream.read()
            if current_task != render_current_task(status):
                errors.append(
                    "generated current-task document is stale; run "
                    "python scripts/agent_workflow.py render"
                )
        except IOError as exc:
            errors.append(
                "cannot read generated current-task document: {0}".format(exc)
            )

    if require_clean:
        paths = changed_paths(repo_root)
        if paths:
            errors.append(
                "worktree is not clean: {0}".format(", ".join(paths))
            )

    return errors


def _print_status(status):
    task = status["active_task"]
    print("project: {0}".format(status["project"]))
    print("task: {0}".format(task["id"]))
    print("status: {0}".format(task["status"]))
    print("role: {0}".format(task["role"]))
    print("branch: {0}".format(task["branch"]))
    print("worktree: {0}".format(task["worktree"]))


def _build_parser():
    parser = argparse.ArgumentParser(
        description="Validate and enforce the repository agent workflow."
    )
    parser.add_argument(
        "--status-file",
        default=DEFAULT_STATUS_PATH,
        help="Path to the authoritative project status JSON.",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("show", help="Print the active assignment.")
    subparsers.add_parser("validate", help="Validate the status file.")

    render_parser = subparsers.add_parser(
        "render", help="Generate docs/architecture/97_current_task.md."
    )
    render_parser.add_argument(
        "--output",
        default=DEFAULT_CURRENT_TASK_PATH,
        help="Generated current-task Markdown path.",
    )

    preflight_parser = subparsers.add_parser(
        "preflight", help="Check branch, worktree, files, and clean state."
    )
    preflight_parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Skip the clean-worktree check for diagnosis only.",
    )

    subparsers.add_parser(
        "check-scope", help="Check tracked, staged, and untracked changed files."
    )
    return parser


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 2

    try:
        status = load_status(args.status_file)
        if args.command == "show":
            _print_status(status)
        elif args.command == "validate":
            print("[OK] status file is valid")
        elif args.command == "render":
            write_current_task(status, args.output)
            print("[OK] wrote {0}".format(args.output))
        elif args.command == "preflight":
            errors = preflight_errors(
                status, require_clean=not args.allow_dirty
            )
            if errors:
                for error in errors:
                    print("[ERROR] {0}".format(error))
                return 1
            print("[OK] preflight passed")
        elif args.command == "check-scope":
            paths = changed_paths()
            violations = scope_violations(
                paths, status["active_task"]["allowed_paths"]
            )
            if violations:
                for path in violations:
                    print("[ERROR] out-of-scope change: {0}".format(path))
                return 1
            print("[OK] all changed files are within the active task scope")
        return 0
    except WorkflowError as exc:
        print("[ERROR] {0}".format(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
