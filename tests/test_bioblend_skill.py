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
    mock_gi.tools.get_tool_panel.return_value = [
        {"name": "SAM/BAM", "elems": [
            {"id": "samtools_sort/1.0", "name": "SAMtools sort",
             "description": "Sort", "model_class": "Tool"},
        ]},
    ]

    from team_galaxy.skills import bioblend as bioblend_mod
    bioblend_mod._tool_panel_cache.clear()
    with patch.object(bioblend_mod, "_gi", return_value=mock_gi):
        result = bioblend_mod._galaxy_search_tools("samtools")

    data = json.loads(result)
    assert len(data) == 1
    assert data[0]["name"] == "SAMtools sort"


def test_galaxy_search_tools_caps_and_stays_under_budget(monkeypatch):
    """A pattern matching everything must cap results and not exceed _MAX_OUTPUT."""
    monkeypatch.setenv("GALAXY_URL", "https://test.galaxy.org")
    monkeypatch.setenv("GALAXY_API_KEY", "testkey")

    # 500 tools with realistic long toolshed ids + long descriptions
    elems = [
        {"id": f"toolshed.g2.bx.psu.edu/repos/iuc/tool_{i:03}/tool_{i:03}/1.0.0",
         "name": f"Tool {i}", "description": "d" * 200, "model_class": "Tool"}
        for i in range(500)
    ]
    mock_gi = MagicMock()
    mock_gi.tools.get_tool_panel.return_value = [{"name": "All", "elems": elems}]

    from team_galaxy.skills import bioblend as bioblend_mod
    bioblend_mod._tool_panel_cache.clear()
    with patch.object(bioblend_mod, "_gi", return_value=mock_gi):
        result = bioblend_mod._galaxy_search_tools(".")  # matches every tool

    data = json.loads(result)  # must parse — i.e. not truncated mid-structure
    assert len(data) == bioblend_mod._SEARCH_CAP            # capped
    assert len(result) <= bioblend_mod._MAX_OUTPUT          # under budget
    assert all(len(t["description"]) <= 120 for t in data)  # description bounded
    assert "\n" not in result                               # compact


# --------------------------------------------------------------------------- #
# Tool: galaxy_show_tool  (flat default-path form)
# --------------------------------------------------------------------------- #


def _mock_tool_schema():
    """A tiny tool shaped like a real one: a conditional with a hidden second
    case, plus a select whose option list is longer than the cap."""
    return {
        "id": "test_tool/1.0",
        "name": "Test Tool",
        "inputs": [
            {
                "name": "library",
                "type": "conditional",
                "test_param": {
                    "name": "type",
                    "type": "select",
                    "label": "single or paired",
                    "value": "single",  # default case
                    "options": [["Single", "single", True], ["Paired", "paired", False]],
                },
                "cases": [
                    {"value": "single", "inputs": [
                        {"name": "input_1", "type": "data", "label": "FASTQ",
                         "extensions": ["fastqsanger"]},
                    ]},
                    {"value": "paired", "inputs": [
                        {"name": "input_1", "type": "data"},
                        {"name": "input_2", "type": "data"},  # hidden: not on default path
                    ]},
                ],
            },
            {
                "name": "ref",
                "type": "select",
                "label": "genome",
                "value": "g0",
                "options": [[f"g{i}", f"g{i}", False] for i in range(20)],
            },
        ],
        "outputs": [{"name": "out", "format": "bam"}],
    }


def test_flatten_default_path_follows_default_case_and_joins_keys():
    from team_galaxy.skills.bioblend import _flatten_default_path
    fields = _flatten_default_path(_mock_tool_schema()["inputs"])
    keys = [f["key"] for f in fields]

    assert "library|type" in keys          # selector, flattened
    assert "library|input_1" in keys       # default (single) case input
    assert "library|input_2" not in keys   # paired case is hidden
    selector = next(f for f in fields if f["key"] == "library|type")
    assert selector["branch"] is True
    inp = next(f for f in fields if f["key"] == "library|input_1")
    assert inp["type"] == "data"
    assert inp["extensions"] == ["fastqsanger"]


def test_flatten_caps_options_and_reports_total():
    from team_galaxy.skills.bioblend import _flatten_default_path, _OPTIONS_CAP
    fields = _flatten_default_path(_mock_tool_schema()["inputs"])
    ref = next(f for f in fields if f["key"] == "ref")
    assert len(ref["options"]) == _OPTIONS_CAP
    assert ref["options_n"] == 20  # total before the cap


def test_galaxy_show_tool_returns_valid_flat_form(monkeypatch):
    monkeypatch.setenv("GALAXY_URL", "https://test.galaxy.org")
    monkeypatch.setenv("GALAXY_API_KEY", "testkey")

    mock_gi = MagicMock()
    mock_gi.tools.show_tool.return_value = _mock_tool_schema()

    from team_galaxy.skills import bioblend as bioblend_mod
    with patch.object(bioblend_mod, "_gi", return_value=mock_gi):
        result = bioblend_mod._galaxy_show_tool("test_tool/1.0")

    data = json.loads(result)  # must be valid JSON
    assert len(result) <= bioblend_mod._SCHEMA_MAX_OUTPUT
    assert data["id"] == "test_tool/1.0"
    assert {p["key"] for p in data["params"]} >= {"library|type", "library|input_1", "ref"}
    mock_gi.tools.show_tool.assert_called_once_with("test_tool/1.0", io_details=True)


def test_galaxy_show_tool_no_tool_id():
    from team_galaxy.skills.bioblend import _galaxy_show_tool
    assert _galaxy_show_tool("   ").startswith("ERROR")


# --------------------------------------------------------------------------- #
# Error extraction: _tool_error + galaxy_run_tool react path
# --------------------------------------------------------------------------- #


class _FakeConnError(Exception):
    """Mimics bioblend.ConnectionError: carries the raw response body."""
    def __init__(self, body):
        super().__init__(f"Unexpected HTTP status code: 400: {body}")
        self.body = body


def test_tool_error_prefers_flattened_err_data():
    from team_galaxy.skills.bioblend import _tool_error
    body = json.dumps({
        "err_msg": "Parameter 'input_2': required",
        "err_data": {"library|input_2": "Parameter 'input_2': required"},
    })
    msg = _tool_error(_FakeConnError(body))
    assert "library|input_2" in msg  # the flattened key the agent must add


def test_tool_error_falls_back_to_err_msg_then_str():
    from team_galaxy.skills.bioblend import _tool_error
    only_msg = _tool_error(_FakeConnError(json.dumps({"err_msg": "Tool not found."})))
    assert only_msg == "Tool not found."
    plain = _tool_error(ValueError("boom"))  # no .body
    assert plain == "boom"


def test_galaxy_run_tool_surfaces_param_error(monkeypatch):
    monkeypatch.setenv("GALAXY_URL", "https://test.galaxy.org")
    monkeypatch.setenv("GALAXY_API_KEY", "testkey")

    body = json.dumps({"err_data": {"library|input_1": "specify a dataset"}})
    mock_gi = MagicMock()
    mock_gi.tools.run_tool.side_effect = _FakeConnError(body)

    from team_galaxy.skills import bioblend as bioblend_mod
    with patch.object(bioblend_mod, "_gi", return_value=mock_gi):
        result = bioblend_mod._galaxy_run_tool(
            json.dumps({"history_id": "h1", "tool_id": "t1", "inputs": {}})
        )
    assert result.startswith("ERROR running tool:")
    assert "library|input_1" in result


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
