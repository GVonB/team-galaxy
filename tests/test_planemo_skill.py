"""Tests for the planemo skill (team_galaxy/skills/planemo.py).

All tests mock subprocess calls — planemo does not need to be installed.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from team.skills import load_skill

_SKILL_PATH = str(Path(__file__).parent.parent / "team_galaxy" / "skills" / "planemo.py")


# --------------------------------------------------------------------------- #
# Skill loading
# --------------------------------------------------------------------------- #


def test_skill_loads_via_team_core():
    tools, descriptions, context = load_skill(_SKILL_PATH)
    assert "planemo_lint" in tools
    assert "planemo_test" in tools
    assert "planemo_workflow_lint" in tools
    assert "planemo_workflow_test" in tools
    assert "planemo_autoupdate" in tools
    assert "planemo_shed_lint" in tools


def test_skill_has_descriptions():
    _, descriptions, _ = load_skill(_SKILL_PATH)
    for name, desc in descriptions.items():
        assert desc.strip(), f"Empty description for tool {name!r}"


def test_skill_injects_context():
    _, _, context = load_skill(_SKILL_PATH)
    assert len(context) == 1
    assert "planemo_lint" in context[0]


# --------------------------------------------------------------------------- #
# planemo_lint
# --------------------------------------------------------------------------- #


def _make_completed_process(stdout="", stderr="", returncode=0):
    result = MagicMock()
    result.stdout = stdout
    result.stderr = stderr
    result.returncode = returncode
    return result


@patch("shutil.which", return_value="/usr/bin/planemo")
@patch("subprocess.run")
def test_planemo_lint_success(mock_run, mock_which, tmp_path):
    mock_run.return_value = _make_completed_process(
        stdout="All 1 lints passed\n", returncode=0
    )
    from team_galaxy.skills.planemo import _planemo_lint
    result = _planemo_lint("tool.xml", workspace_path=tmp_path)
    assert "exit 0" in result
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args[0] == "planemo"
    assert "lint" in args
    assert "tool.xml" in args


@patch("shutil.which", return_value="/usr/bin/planemo")
@patch("subprocess.run")
def test_planemo_lint_failure(mock_run, mock_which, tmp_path):
    mock_run.return_value = _make_completed_process(
        stderr="ERROR: Tool does not define a version\n", returncode=1
    )
    from team_galaxy.skills.planemo import _planemo_lint
    result = _planemo_lint("tool.xml", workspace_path=tmp_path)
    assert "exit 1" in result
    assert "version" in result


@patch("shutil.which", return_value=None)
def test_planemo_lint_not_installed(mock_which, tmp_path):
    from team_galaxy.skills.planemo import _planemo_lint
    result = _planemo_lint("tool.xml", workspace_path=tmp_path)
    assert result.startswith("ERROR")
    assert "planemo" in result.lower()


def test_planemo_lint_empty_body(tmp_path):
    from team_galaxy.skills.planemo import _planemo_lint
    result = _planemo_lint("", workspace_path=tmp_path)
    assert result.startswith("ERROR")


# --------------------------------------------------------------------------- #
# planemo_workflow_lint
# --------------------------------------------------------------------------- #


@patch("shutil.which", return_value="/usr/bin/planemo")
@patch("subprocess.run")
def test_planemo_workflow_lint_success(mock_run, mock_which, tmp_path):
    mock_run.return_value = _make_completed_process(
        stdout="All workflow lints passed\n", returncode=0
    )
    from team_galaxy.skills.planemo import _planemo_workflow_lint
    result = _planemo_workflow_lint("my_workflow.ga", workspace_path=tmp_path)
    assert "exit 0" in result
    args = mock_run.call_args[0][0]
    assert "workflow_lint" in args


def test_planemo_workflow_lint_empty_body(tmp_path):
    from team_galaxy.skills.planemo import _planemo_workflow_lint
    result = _planemo_workflow_lint("", workspace_path=tmp_path)
    assert result.startswith("ERROR")


# --------------------------------------------------------------------------- #
# planemo_autoupdate
# --------------------------------------------------------------------------- #


@patch("shutil.which", return_value="/usr/bin/planemo")
@patch("subprocess.run")
def test_planemo_autoupdate_calls_autoupdate(mock_run, mock_which, tmp_path):
    mock_run.return_value = _make_completed_process(stdout="Updated samtools 1.20 → 1.21\n", returncode=0)
    from team_galaxy.skills.planemo import _planemo_autoupdate
    result = _planemo_autoupdate("tool.xml", workspace_path=tmp_path)
    args = mock_run.call_args[0][0]
    assert "autoupdate" in args
    assert "exit 0" in result


# --------------------------------------------------------------------------- #
# planemo_shed_lint
# --------------------------------------------------------------------------- #


@patch("shutil.which", return_value="/usr/bin/planemo")
@patch("subprocess.run")
def test_planemo_shed_lint_defaults_to_dot(mock_run, mock_which, tmp_path):
    mock_run.return_value = _make_completed_process(returncode=0)
    from team_galaxy.skills.planemo import _planemo_shed_lint
    _planemo_shed_lint("", workspace_path=tmp_path)
    args = mock_run.call_args[0][0]
    assert "shed_lint" in args
    assert "." in args


# --------------------------------------------------------------------------- #
# Extra flags passthrough
# --------------------------------------------------------------------------- #


@patch("shutil.which", return_value="/usr/bin/planemo")
@patch("subprocess.run")
def test_extra_flags_passed_through(mock_run, mock_which, tmp_path):
    mock_run.return_value = _make_completed_process(returncode=0)
    from team_galaxy.skills.planemo import _planemo_lint
    _planemo_lint("tool.xml --no_cache_galaxy", workspace_path=tmp_path)
    args = mock_run.call_args[0][0]
    assert "--no_cache_galaxy" in args


# --------------------------------------------------------------------------- #
# Timeout handling
# --------------------------------------------------------------------------- #


@patch("shutil.which", return_value="/usr/bin/planemo")
@patch("subprocess.run", side_effect=__import__("subprocess").TimeoutExpired("planemo", 300))
def test_planemo_timeout_returns_error(mock_run, mock_which, tmp_path):
    from team_galaxy.skills.planemo import _planemo_lint
    result = _planemo_lint("tool.xml", workspace_path=tmp_path)
    assert "timed out" in result.lower()
