"""Tests for the Tool Shed skill (team_galaxy/skills/toolshed.py)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from team.skills import load_skill

_SKILL_PATH = str(Path(__file__).parent.parent / "team_galaxy" / "skills" / "toolshed.py")


# --------------------------------------------------------------------------- #
# Skill loading
# --------------------------------------------------------------------------- #


def test_skill_loads_via_team_core():
    tools, descriptions, context = load_skill(_SKILL_PATH)
    assert "toolshed_search" in tools
    assert "toolshed_tool_info" in tools
    assert "toolshed_categories" in tools
    assert "toolshed_owner_repos" in tools


def test_skill_injects_context():
    _, _, context = load_skill(_SKILL_PATH)
    assert len(context) == 1
    assert "toolshed_search" in context[0]


# --------------------------------------------------------------------------- #
# _parse_shed_and_rest
# --------------------------------------------------------------------------- #


def test_parse_shed_default():
    from team_galaxy.skills.toolshed import _parse_shed_and_rest
    shed, rest = _parse_shed_and_rest("samtools sort")
    assert "toolshed.g2.bx.psu.edu" in shed
    assert rest == "samtools sort"


def test_parse_shed_explicit_url():
    from team_galaxy.skills.toolshed import _parse_shed_and_rest
    shed, rest = _parse_shed_and_rest("https://toolshed.g2.bx.psu.edu samtools")
    assert shed == "https://toolshed.g2.bx.psu.edu"
    assert rest == "samtools"


def test_parse_shed_explicit_url_no_rest():
    from team_galaxy.skills.toolshed import _parse_shed_and_rest
    shed, rest = _parse_shed_and_rest("https://toolshed.g2.bx.psu.edu")
    assert shed == "https://toolshed.g2.bx.psu.edu"
    assert rest == ""


# --------------------------------------------------------------------------- #
# toolshed_search
# --------------------------------------------------------------------------- #


def test_toolshed_search_empty_query():
    from team_galaxy.skills.toolshed import _toolshed_search
    result = _toolshed_search("   ")
    assert result.startswith("ERROR")


@patch("team_galaxy.skills.toolshed._get")
def test_toolshed_search_returns_simplified(mock_get):
    mock_get.return_value = [
        {"id": "r1", "owner": "devteam", "name": "samtools", "description": "SAMtools", "type": "unrestricted"},
    ]
    from team_galaxy.skills.toolshed import _toolshed_search
    import json
    result = _toolshed_search("samtools")
    data = json.loads(result)
    assert len(data) == 1
    assert data[0]["owner"] == "devteam"
    assert data[0]["name"] == "samtools"


@patch("team_galaxy.skills.toolshed._get", side_effect=Exception("connection refused"))
def test_toolshed_search_network_error(mock_get):
    from team_galaxy.skills.toolshed import _toolshed_search
    result = _toolshed_search("samtools")
    assert result.startswith("ERROR")


@patch("team_galaxy.skills.toolshed._get")
def test_toolshed_search_empty_results(mock_get):
    mock_get.return_value = []
    from team_galaxy.skills.toolshed import _toolshed_search
    result = _toolshed_search("nonexistent_tool_xyz")
    assert "No Tool Shed repositories found" in result


# --------------------------------------------------------------------------- #
# toolshed_tool_info
# --------------------------------------------------------------------------- #


def test_toolshed_tool_info_missing_ref():
    from team_galaxy.skills.toolshed import _toolshed_tool_info
    result = _toolshed_tool_info("   ")
    assert result.startswith("ERROR")


def test_toolshed_tool_info_wrong_format():
    from team_galaxy.skills.toolshed import _toolshed_tool_info
    result = _toolshed_tool_info("just_a_name_without_slash")
    assert result.startswith("ERROR")


@patch("team_galaxy.skills.toolshed._get")
def test_toolshed_tool_info_success(mock_get):
    mock_get.return_value = [{"name": "samtools", "owner": "devteam", "version": "1.21"}]
    from team_galaxy.skills.toolshed import _toolshed_tool_info
    import json
    result = _toolshed_tool_info("devteam/samtools")
    data = json.loads(result)
    assert isinstance(data, list)


# --------------------------------------------------------------------------- #
# toolshed_owner_repos
# --------------------------------------------------------------------------- #


def test_toolshed_owner_repos_empty_owner():
    from team_galaxy.skills.toolshed import _toolshed_owner_repos
    result = _toolshed_owner_repos("   ")
    assert result.startswith("ERROR")


@patch("team_galaxy.skills.toolshed._get")
def test_toolshed_owner_repos_success(mock_get):
    mock_get.return_value = [
        {"name": "samtools_sort", "description": "Sort BAM", "type": "unrestricted"},
        {"name": "samtools_view", "description": "Filter BAM", "type": "unrestricted"},
    ]
    from team_galaxy.skills.toolshed import _toolshed_owner_repos
    import json
    result = _toolshed_owner_repos("devteam")
    data = json.loads(result)
    assert len(data) == 2
    assert data[0]["name"] == "samtools_sort"
