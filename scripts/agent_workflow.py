from __future__ import print_function

import argparse
import json
import os
import subprocess
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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

REQUIRED_REMOTE_KEYS = (
    "name",
    "url",
)

VALID_TASK_STATUSES = (
    "PLANNED",
    "READY_FOR_WORKTREE",
    "READY",
    "IN_PROGRESS",
    "REVIEW",
    "MERGED",
    "BLOCKED",
)

PREFLIGHT_ALLOWED_STATUSES = (
    "READY",
    "IN_PROGRESS",
)


class WorkflowError(Exception):
    pass


def _normalized_path(path):
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _read_status_json(path):
    try:
        with open(path, "r") as stream:
            return json.load(stream)
    except IOError as exc:
        raise WorkflowError("cannot read status file: {0}".format(exc))
    except ValueError as exc:
        raise WorkflowError("invalid status JSON: {0}".format(exc))


def load_status(path=None, repo_root=REPO_ROOT):
    if path is None:
        path = authoritative_status_path(repo_root)
    status = _read_status_json(path)
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

    if task["status"] not in VALID_TASK_STATUSES:
        raise WorkflowError(
            "invalid active_task.status {0!r}: expected one of {1}".format(
                task["status"], ", ".join(VALID_TASK_STATUSES)
            )
        )

    remote = status.get("remote")
    if remote is not None:
        if not isinstance(remote, dict):
            raise WorkflowError("remote must be an object")
        missing = [key for key in REQUIRED_REMOTE_KEYS if key not in remote]
        if missing:
            raise WorkflowError(
                "remote missing keys: {0}".format(", ".join(missing))
            )
        for key in REQUIRED_REMOTE_KEYS:
            if not isinstance(remote[key], str) or not remote[key].strip():
                raise WorkflowError(
                    "remote.{0} must be a non-empty string".format(key)
                )

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

    remote = status.get("remote")
    if remote:
        lines.extend(
            [
                "",
                "## Remote Sync",
                "",
                "- Remote: `{0}`".format(remote["name"]),
                "- URL: `{0}`".format(remote["url"]),
                "- Run `python scripts/agent_workflow.py check-sync` before "
                "an approved push.",
            ]
        )

    lines.append("")
    return "\n".join(lines)


def write_current_task(status, output_path=None):
    if output_path is None:
        output_path = os.path.join(
            REPO_ROOT, "docs", "architecture", "97_current_task.md"
        )
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


def _parse_worktree_list(output):
    worktrees = []
    current = {}
    for line in output.splitlines() + [""]:
        if not line:
            if current:
                worktrees.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    return worktrees


def authoritative_status_path(repo_root=REPO_ROOT):
    local_status_path = os.path.join(repo_root, "agents", "project_status.json")
    local_status = _read_status_json(local_status_path)

    integration_branch = local_status.get("integration_branch")
    integration_worktree = local_status.get("integration_worktree")
    if not integration_branch or not integration_worktree:
        raise WorkflowError(
            "local status file must define integration_branch and "
            "integration_worktree"
        )

    output = _run_git(["worktree", "list", "--porcelain"], repo_root)
    expected_branch = "refs/heads/{0}".format(integration_branch)
    matches = []
    for worktree in _parse_worktree_list(output):
        path = worktree.get("worktree")
        branch = worktree.get("branch")
        if (
            path
            and branch == expected_branch
            and os.path.basename(os.path.abspath(path)).lower()
            == integration_worktree.lower()
        ):
            matches.append(path)

    if len(matches) != 1:
        raise WorkflowError(
            "cannot locate integration worktree {0} on branch {1}".format(
                integration_worktree, integration_branch
            )
        )
    return os.path.join(matches[0], "agents", "project_status.json")


def changed_paths(repo_root=REPO_ROOT, integration_branch=None):
    tracked = _run_git(["diff", "--name-only", "--relative"], repo_root)
    staged = _run_git(
        ["diff", "--cached", "--name-only", "--relative"], repo_root
    )
    untracked = _run_git(
        ["ls-files", "--others", "--exclude-standard"], repo_root
    )
    committed = ""
    if integration_branch:
        committed = _run_git(
            [
                "diff",
                "--name-only",
                "--relative",
                "{0}...HEAD".format(integration_branch),
            ],
            repo_root,
        )
    paths = set()
    for output in (tracked, staged, untracked, committed):
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


def preflight_errors(
    status,
    repo_root=REPO_ROOT,
    require_clean=True,
    status_root=None,
):
    task = status["active_task"]
    errors = []
    if status_root is None:
        status_root = repo_root

    if task["status"] not in PREFLIGHT_ALLOWED_STATUSES:
        errors.append(
            "task status {0} does not allow feature preflight; expected one of "
            "{1}".format(
                task["status"], ", ".join(PREFLIGHT_ALLOWED_STATUSES)
            )
        )

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
        status_root, "docs", "architecture", "97_current_task.md"
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


def remote_sync_report(status, repo_root=REPO_ROOT):
    remote = status.get("remote")
    if not remote:
        raise WorkflowError("status file does not define remote sync settings")

    remote_name = remote["name"]
    configured_url = remote["url"]
    actual_url = _run_git(["remote", "get-url", remote_name], repo_root)
    branch = _run_git(["branch", "--show-current"], repo_root)
    dirty_output = _run_git(["status", "--porcelain"], repo_root)
    errors = []

    if actual_url != configured_url:
        errors.append(
            "remote {0} URL mismatch: expected {1}, found {2}".format(
                remote_name, configured_url, actual_url
            )
        )
    if not branch:
        errors.append("cannot sync from detached HEAD")
    if dirty_output:
        errors.append("worktree must be clean before remote sync")

    upstream = None
    behind = None
    ahead = None
    if branch:
        upstream = _run_git(
            [
                "for-each-ref",
                "--format=%(upstream:short)",
                "refs/heads/{0}".format(branch),
            ],
            repo_root,
        ) or None

    if upstream:
        expected_upstream = "{0}/{1}".format(remote_name, branch)
        if upstream != expected_upstream:
            errors.append(
                "upstream mismatch: expected {0}, found {1}".format(
                    expected_upstream, upstream
                )
            )
        counts = _run_git(
            ["rev-list", "--left-right", "--count", "{0}...HEAD".format(upstream)],
            repo_root,
        ).split()
        if len(counts) != 2:
            raise WorkflowError(
                "unexpected ahead/behind output for {0}: {1}".format(
                    upstream, " ".join(counts)
                )
            )
        behind = int(counts[0])
        ahead = int(counts[1])
        if behind:
            errors.append(
                "local branch is behind {0} by {1} commit(s)".format(
                    upstream, behind
                )
            )

    return {
        "remote_name": remote_name,
        "remote_url": actual_url,
        "branch": branch,
        "upstream": upstream,
        "behind": behind,
        "ahead": ahead,
        "errors": errors,
    }


def _print_remote_sync_report(report):
    print("remote: {0}".format(report["remote_name"]))
    print("remote_url: {0}".format(report["remote_url"]))
    print("branch: {0}".format(report["branch"] or "(detached HEAD)"))
    print("upstream: {0}".format(report["upstream"] or "(not set)"))
    if report["upstream"]:
        print("behind: {0}".format(report["behind"]))
        print("ahead: {0}".format(report["ahead"]))


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
        help=(
            "Path to the authoritative project status JSON. By default, "
            "locate it in the integration worktree."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("show", help="Print the active assignment.")
    subparsers.add_parser("validate", help="Validate the status file.")

    render_parser = subparsers.add_parser(
        "render", help="Generate docs/architecture/97_current_task.md."
    )
    render_parser.add_argument(
        "--output",
        help=(
            "Generated current-task Markdown path. By default, write it in "
            "the integration worktree."
        ),
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
    subparsers.add_parser(
        "check-sync",
        help="Check whether the current branch is ready for an approved push.",
    )
    return parser


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 2

    try:
        status_path = (
            args.status_file
            if args.status_file
            else authoritative_status_path()
        )
        status = load_status(status_path)
        status_root = os.path.dirname(os.path.dirname(status_path))
        if args.command == "show":
            _print_status(status)
        elif args.command == "validate":
            print("[OK] status file is valid")
        elif args.command == "render":
            output_path = args.output
            if not output_path:
                output_path = os.path.join(
                    status_root,
                    "docs",
                    "architecture",
                    "97_current_task.md",
                )
            write_current_task(status, output_path)
            print("[OK] wrote {0}".format(output_path))
        elif args.command == "preflight":
            errors = preflight_errors(
                status,
                require_clean=not args.allow_dirty,
                status_root=status_root,
            )
            if errors:
                for error in errors:
                    print("[ERROR] {0}".format(error))
                return 1
            print("[OK] preflight passed")
        elif args.command == "check-scope":
            paths = changed_paths(
                integration_branch=status["integration_branch"]
            )
            violations = scope_violations(
                paths, status["active_task"]["allowed_paths"]
            )
            if violations:
                for path in violations:
                    print("[ERROR] out-of-scope change: {0}".format(path))
                return 1
            print("[OK] all changed files are within the active task scope")
        elif args.command == "check-sync":
            report = remote_sync_report(status)
            _print_remote_sync_report(report)
            if report["errors"]:
                for error in report["errors"]:
                    print("[ERROR] {0}".format(error))
                return 1
            if report["upstream"]:
                print("[OK] branch is ready for an approved git push")
            else:
                print(
                    "[OK] branch is ready for initial push: git push -u {0} {1}".format(
                        report["remote_name"], report["branch"]
                    )
                )
        return 0
    except WorkflowError as exc:
        print("[ERROR] {0}".format(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
