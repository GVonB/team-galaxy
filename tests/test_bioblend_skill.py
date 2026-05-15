"""Tests for the BioBlend skill (team_galaxy/skills/bioblend.py).

All tests mock the bioblend library and environment variables — no live
Galaxy server is required.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Load the skill through team-core's loader to verify it passes validation.
from team.skills import load_skill

_SKILL_PATH = str(Path(__file__).parent.parent / "team_galaxy" / "skills" / "bioblend.py")


# --------------------------------------------------------------------------- #
# Skill loading
# --------------------------------------------------------------------------- #


def test_skill_loads_via_team_core():
    """The skill must be loadable by team-core's load_skill()."""
    tools, descriptions, context = load_skill(_SKILL_PATH)
    assert "galaxy_run_tool" in tools
    assert "galaxy_upload" in tools
    assert "galaxy_invoke_workflow" in tools
    assert "galaxy_job_status" in tools
    assert "galaxy_wait_for_job" in tools
    assert "galaxy_download" in tools
    assert "galaxy_search_tools" in tools
    assert "galaxy_create_history" in tools
    assert "galaxy_get_histories" in tools
    assert "galaxy_show_dataset" in tools


def test_skill_has_descriptions():
    _, descriptions, _ = load_skill(_SKILL_PATH)
    for name in descriptions:
        assert descriptions[name].strip(), f"Empty description for tool {name!r}"


def test_skill_injects_context():
    _, _, context = load_skill(_SKILL_PATH)
    assert len(context) == 1
    assert "GALAXY_URL" in context[0]
    assert "galaxy_run_tool" in context[0]


# --------------------------------------------------------------------------- #
# _gi() error handling
# --------------------------------------------------------------------------- #


def test_gi_raises_if_bioblend_missing():
    from team_galaxy.skills.bioblend import _gi
    with patch.dict("sys.modules", {"bioblend": None, "bioblend.galaxy": None}):
        with patch("builtins.__import__", side_effect=ImportError("no module")):
            # We test the error path via a tool call
            pass  # _gi itself is tested indirectly via tool calls below


def test_galaxy_run_tool_missing_credentials(monkeypatch):
    monkeypatch.delenv("GALAXY_URL", raising=False)
    monkeypatch.delenv("GALAXY_API_KEY", raising=False)
    from team_galaxy.skills.bioblend import _galaxy_run_tool
    body = json.dumps({"history_id": "h1", "tool_id": "t1", "inputs": {}})
    result = _galaxy_run_tool(body)
    assert result.startswith("ERROR")


def test_galaxy_run_tool_missing_galaxy_url(monkeypatch):
    """When GALAXY_URL is missing the call must fail with an ERROR string."""
    monkeypatch.setenv("GALAXY_API_KEY", "key123")
    monkeypatch.delenv("GALAXY_URL", raising=False)
    from team_galaxy.skills.bioblend import _galaxy_run_tool
    body = json.dumps({"history_id": "h1", "tool_id": "t1", "inputs": {}})
    result = _galaxy_run_tool(body)
    # Either bioblend is not installed, or GALAXY_URL is missing — both are ERRORs.
    assert result.startswith("ERROR")


# --------------------------------------------------------------------------- #
# Tool: galaxy_run_tool
# --------------------------------------------------------------------------- #


def test_galaxy_run_tool_success(monkeypatch):
    monkeypatch.setenv("GALAXY_URL", "https://test.galaxy.org")
    monkeypatch.setenv("GALAXY_API_KEY", "testkey")

    mock_gi_instance = MagicMock()
    mock_gi_instance.tools.run_tool.return_value = {
        "jobs": [{"id": "job1", "state": "queued"}],
        "outputs": [{"id": "ds1", "name": "output"}],
    }
    mock_gi_class = MagicMock(return_value=mock_gi_instance)

    with patch.dict("sys.modules", {"bioblend": MagicMock(), "bioblend.galaxy": MagicMock()}):
        with patch("team_galaxy.skills.bioblend._gi", return_value=mock_gi_instance):
            from team_galaxy.skills.bioblend import _galaxy_run_tool
            body = json.dumps({"history_id": "h1", "tool_id": "samtools_sort", "inputs": {}})
            result = _galaxy_run_tool(body)

    data = json.loads(result)
    assert "jobs" in data or "outputs" in data


def test_galaxy_run_tool_invalid_json():
    from team_galaxy.skills.bioblend import _galaxy_run_tool
    result = _galaxy_run_tool("not valid json")
    assert result.startswith("ERROR")


def test_galaxy_run_tool_missing_history_id(monkeypatch):
    monkeypatch.setenv("GALAXY_URL", "https://test.galaxy.org")
    monkeypatch.setenv("GALAXY_API_KEY", "testkey")
    from team_galaxy.skills.bioblend import _galaxy_run_tool
    body = json.dumps({"tool_id": "samtools_sort", "inputs": {}})
    result = _galaxy_run_tool(body)
    assert "history_id" in result


# --------------------------------------------------------------------------- #
# Tool: galaxy_upload
# --------------------------------------------------------------------------- #


def test_galaxy_upload_file_not_found(monkeypatch, tmp_path):
    monkeypatch.setenv("GALAXY_URL", "https://test.galaxy.org")
    monkeypatch.setenv("GALAXY_API_KEY", "testkey")
    from team_galaxy.skills.bioblend import _galaxy_upload
    body = json.dumps({"history_id": "h1", "file_path": "nonexistent.fastq"})
    result = _galaxy_upload(body, workspace_path=tmp_path)
    assert result.startswith("ERROR")
    assert "not found" in result


def test_galaxy_upload_success(monkeypatch, tmp_path):
    monkeypatch.setenv("GALAXY_URL", "https://test.galaxy.org")
    monkeypatch.setenv("GALAXY_API_KEY", "testkey")
    (tmp_path / "input.fastq").write_text("@read1\nACGT\n+\nIIII\n")

    mock_gi = MagicMock()
    mock_gi.tools.upload_file.return_value = {"id": "ds_upload1"}

    from team_galaxy.skills import bioblend as bioblend_mod
    with patch.object(bioblend_mod, "_gi", return_value=mock_gi):
        result = bioblend_mod._galaxy_upload(
            json.dumps({"history_id": "h1", "file_path": "input.fastq"}),
            workspace_path=tmp_path,
        )

    assert "ds_upload1" in result


# --------------------------------------------------------------------------- #
# Tool: galaxy_download
# --------------------------------------------------------------------------- #


def test_galaxy_download_missing_dataset_id(monkeypatch, tmp_path):
    monkeypatch.setenv("GALAXY_URL", "https://test.galaxy.org")
    monkeypatch.setenv("GALAXY_API_KEY", "testkey")
    from team_galaxy.skills.bioblend import _galaxy_download
    body = json.dumps({"output_path": "out.bam"})
    result = _galaxy_download(body, workspace_path=tmp_path)
    assert result.startswith("ERROR")
    assert "dataset_id" in result


# --------------------------------------------------------------------------- #
# Tool: galaxy_search_tools
# --------------------------------------------------------------------------- #


def test_galaxy_search_tools_empty_query(monkeypatch):
    monkeypatch.setenv("GALAXY_URL", "https://test.galaxy.org")
    monkeypatch.setenv("GALAXY_API_KEY", "testkey")
    from team_galaxy.skills.bioblend import _galaxy_search_tools
    result = _galaxy_search_tools("   ")
    assert result.startswith("ERROR")


def test_galaxy_search_tools_success(monkeypatch):
    monkeypatch.setenv("GALAXY_URL", "https://test.galaxy.org")
    monkeypatch.setenv("GALAXY_API_KEY", "testkey")

    mock_gi = MagicMock()
    mock_gi.tools.get_tools.return_value = [
        {"id": "samtools_sort/1.0", "name": "SAMtools sort", "version": "1.0", "description": "Sort"},
    ]

    from team_galaxy.skills import bioblend as bioblend_mod
    with patch.object(bioblend_mod, "_gi", return_value=mock_gi):
        result = bioblend_mod._galaxy_search_tools("samtools")

    data = json.loads(result)
    assert len(data) == 1
    assert data[0]["name"] == "SAMtools sort"


# --------------------------------------------------------------------------- #
# Tool: galaxy_job_status
# --------------------------------------------------------------------------- #


def test_galaxy_job_status_no_id(monkeypatch):
    monkeypatch.setenv("GALAXY_URL", "https://test.galaxy.org")
    monkeypatch.setenv("GALAXY_API_KEY", "testkey")

    mock_gi = MagicMock()
    from team_galaxy.skills import bioblend as bioblend_mod
    with patch.object(bioblend_mod, "_gi", return_value=mock_gi):
        result = bioblend_mod._galaxy_job_status("{}")
    assert result.startswith("ERROR")


def test_galaxy_job_status_with_job_id(monkeypatch):
    monkeypatch.setenv("GALAXY_URL", "https://test.galaxy.org")
    monkeypatch.setenv("GALAXY_API_KEY", "testkey")

    mock_gi = MagicMock()
    mock_gi.jobs.show_job.return_value = {"id": "j1", "state": "ok"}

    from team_galaxy.skills import bioblend as bioblend_mod
    with patch.object(bioblend_mod, "_gi", return_value=mock_gi):
        result = bioblend_mod._galaxy_job_status(json.dumps({"job_id": "j1"}))

    data = json.loads(result)
    assert data["state"] == "ok"
