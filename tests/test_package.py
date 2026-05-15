"""Tests for the team_galaxy package-level helpers and CLI."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from team_galaxy import examples_dir, personas_dir, skills_dir
from team_galaxy.cli import cli


# --------------------------------------------------------------------------- #
# Path helpers
# --------------------------------------------------------------------------- #


def test_skills_dir_exists():
    assert skills_dir().is_dir()


def test_personas_dir_exists():
    assert personas_dir().is_dir()


def test_examples_dir_exists():
    assert examples_dir().is_dir()


def test_skills_dir_contains_expected_files():
    names = {p.name for p in skills_dir().iterdir()}
    assert "bioblend.py" in names
    assert "planemo.py" in names
    assert "toolshed.py" in names
    assert "iuc_standards.md" in names
    assert "iwc_checklist.md" in names
    assert "gtn_format.md" in names
    assert "bioconda_guide.md" in names


def test_personas_dir_contains_expected_files():
    names = {p.stem for p in personas_dir().glob("*.yaml")}
    assert "iuc_reviewer" in names
    assert "iwc_curator" in names
    assert "gtn_author" in names
    assert "galaxy_admin" in names
    assert "tool_wrapper_author" in names


def test_examples_dir_contains_expected_scenarios():
    names = {p.stem for p in examples_dir().glob("*.yaml")}
    assert "tool-wrapper-factory" in names
    assert "iwc-compliance" in names
    assert "gtn-tutorial-generator" in names
    assert "bioblend-analysis" in names
    assert "job-failure-investigator" in names


# --------------------------------------------------------------------------- #
# Persona YAML validity
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "yaml_path",
    list((Path(__file__).parent.parent / "team_galaxy" / "personas").glob("*.yaml")),
    ids=lambda p: p.stem,
)
def test_persona_yaml_has_required_fields(yaml_path):
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    assert isinstance(raw, dict), f"{yaml_path.name} is not a YAML mapping"
    for field in ("role", "description", "persona"):
        assert field in raw, f"{yaml_path.name} is missing field: {field!r}"
    assert isinstance(raw["role"], str) and raw["role"].strip()
    assert isinstance(raw["description"], str) and raw["description"].strip()
    assert isinstance(raw["persona"], str) and raw["persona"].strip()


# --------------------------------------------------------------------------- #
# Example YAML validity (parseable + has required top-level keys)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "yaml_path",
    list((Path(__file__).parent.parent / "team_galaxy" / "examples").glob("*.yaml")),
    ids=lambda p: p.stem,
)
def test_example_yaml_parseable(yaml_path):
    """Example YAMLs should parse without errors (after path token replacement)."""
    content = yaml_path.read_text(encoding="utf-8")
    # Replace path tokens so YAML parses cleanly (they contain no newlines)
    content = content.replace("${TEAM_GALAXY_SKILLS}", "/tmp/skills")
    content = content.replace("${TEAM_GALAXY_PERSONAS}", "/tmp/personas")
    raw = yaml.safe_load(content)
    assert isinstance(raw, dict)
    for key in ("name", "goal", "workflow", "members"):
        assert key in raw, f"{yaml_path.name} is missing top-level key: {key!r}"
    assert isinstance(raw["members"], list)
    assert len(raw["members"]) >= 2


# --------------------------------------------------------------------------- #
# CLI commands
# --------------------------------------------------------------------------- #


def test_cli_scenarios_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["scenarios"])
    assert result.exit_code == 0
    assert "tool-wrapper-factory" in result.output


def test_cli_skills_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["skills"])
    assert result.exit_code == 0
    assert "bioblend.py" in result.output
    assert "planemo.py" in result.output


def test_cli_personas_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["personas"])
    assert result.exit_code == 0
    assert "iuc_reviewer" in result.output
    assert "gtn_author" in result.output


def test_cli_init_creates_file(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--scenario", "iwc-compliance", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output
    created = tmp_path / "iwc-compliance.yaml"
    assert created.is_file()
    # Path tokens should be resolved
    content = created.read_text()
    assert "${TEAM_GALAXY_SKILLS}" not in content
    assert str(skills_dir()) in content


def test_cli_init_refuses_overwrite_without_force(tmp_path):
    runner = CliRunner()
    # Create the file first
    (tmp_path / "iwc-compliance.yaml").write_text("existing")
    result = runner.invoke(cli, ["init", "--scenario", "iwc-compliance", "--output-dir", str(tmp_path)])
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_cli_init_force_overwrites(tmp_path):
    runner = CliRunner()
    (tmp_path / "iwc-compliance.yaml").write_text("existing")
    result = runner.invoke(
        cli, ["init", "--scenario", "iwc-compliance", "--output-dir", str(tmp_path), "--force"]
    )
    assert result.exit_code == 0
    content = (tmp_path / "iwc-compliance.yaml").read_text()
    assert "IWC" in content  # real content, not "existing"
