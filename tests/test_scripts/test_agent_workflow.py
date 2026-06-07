import os
import sys

import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import agent_workflow


class FakeReadableFile(object):
    def __init__(self, content):
        self.content = content

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self.content


def make_status():
    return {
        "version": 1,
        "project": "demo",
        "integration_branch": "main",
        "integration_worktree": "demo_main",
        "active_task": {
            "id": "example",
            "status": "READY",
            "goal": "Implement the example.",
            "role": "example",
            "branch": "codex/example",
            "worktree": "demo_example",
            "prompt": "agents/example.md",
            "allowed_paths": ["utils/", "tests/test_utils/"],
            "forbidden_paths": ["src/core/"],
            "required_files": ["AGENTS.md", "agents/example.md"],
            "checks": ["python -m pytest -q tests/test_utils"],
            "notes": ["Example note."],
        },
    }


def test_validate_status_rejects_missing_task_key():
    status = make_status()
    del status["active_task"]["branch"]

    with pytest.raises(agent_workflow.WorkflowError) as exc_info:
        agent_workflow.validate_status(status)

    assert "active_task missing keys: branch" in str(exc_info.value)


def test_render_current_task_uses_authoritative_assignment():
    rendered = agent_workflow.render_current_task(make_status())

    assert "- Branch: `codex/example`" in rendered
    assert "- Worktree: `demo_example`" in rendered
    assert "- `utils/`" in rendered
    assert "Generated from `agents/project_status.json`" in rendered


def test_scope_violations_include_unallowed_paths():
    paths = [
        "utils/parser.py",
        "tests/test_utils/test_parser.py",
        "src/core/runner.py",
    ]

    violations = agent_workflow.scope_violations(
        paths, ["utils/", "tests/test_utils/"]
    )

    assert violations == ["src/core/runner.py"]


def test_path_is_allowed_does_not_accept_similar_prefix():
    assert agent_workflow.path_is_allowed("utils/parser.py", ["utils/"])
    assert not agent_workflow.path_is_allowed("utils_extra/parser.py", ["utils/"])


def test_changed_paths_includes_tracked_staged_and_untracked(monkeypatch):
    def fake_run_git(args, repo_root=None):
        outputs = {
            ("diff", "--name-only", "--relative"): "utils/changed.py",
            (
                "diff",
                "--cached",
                "--name-only",
                "--relative",
            ): "tests/test_utils/test_changed.py",
            (
                "ls-files",
                "--others",
                "--exclude-standard",
            ): "docs/interface/new.md",
        }
        return outputs[tuple(args)]

    monkeypatch.setattr(agent_workflow, "_run_git", fake_run_git)

    assert agent_workflow.changed_paths() == [
        "docs/interface/new.md",
        "tests/test_utils/test_changed.py",
        "utils/changed.py",
    ]


def test_preflight_reports_branch_worktree_and_tracking_errors(monkeypatch):
    status = make_status()
    repo_root = os.path.join("workspace", "wrong_worktree")

    def fake_run_git(args, repo_root=None):
        if args == ["branch", "--show-current"]:
            return "main"
        if args == ["ls-files"]:
            return "AGENTS.md"
        raise AssertionError("unexpected git arguments: {0}".format(args))

    monkeypatch.setattr(agent_workflow, "_run_git", fake_run_git)
    monkeypatch.setattr(agent_workflow.os.path, "exists", lambda path: True)
    monkeypatch.setattr(
        agent_workflow,
        "open",
        lambda path, mode: FakeReadableFile(
            agent_workflow.render_current_task(status)
        ),
        raising=False,
    )

    errors = agent_workflow.preflight_errors(
        status, repo_root=repo_root, require_clean=False
    )

    assert "branch mismatch: expected codex/example, found main" in errors
    assert any("worktree mismatch" in error for error in errors)
    assert "required file is not tracked: agents/example.md" in errors


def test_preflight_reports_stale_generated_current_task(monkeypatch):
    status = make_status()

    def fake_run_git(args, repo_root=None):
        if args == ["branch", "--show-current"]:
            return "codex/example"
        if args == ["ls-files"]:
            return "\n".join(status["active_task"]["required_files"])
        raise AssertionError("unexpected git arguments: {0}".format(args))

    monkeypatch.setattr(agent_workflow, "_run_git", fake_run_git)
    monkeypatch.setattr(agent_workflow.os.path, "exists", lambda path: True)
    monkeypatch.setattr(
        agent_workflow,
        "open",
        lambda path, mode: FakeReadableFile("stale"),
        raising=False,
    )

    errors = agent_workflow.preflight_errors(
        status,
        repo_root=os.path.join("workspace", "demo_example"),
        require_clean=False,
    )

    assert (
        "generated current-task document is stale; run "
        "python scripts/agent_workflow.py render"
    ) in errors
