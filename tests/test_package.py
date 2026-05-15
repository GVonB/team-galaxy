"""Tests for the team_galaxy package-level helpers and CLI."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from team_galaxy import examples_dir, personas_dir, skills_dir
from team_galaxy.commands import galaxy


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
    # thin wrapper modules for Markdown skills
    assert "iuc_standards_skill.py" in names
    assert "iwc_checklist_skill.py" in names
    assert "gtn_format_skill.py" in names
    assert "bioconda_guide_skill.py" in names


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
# Thin wrapper modules for Markdown skills
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("skill_name,md_name", [
    ("iuc_standards_skill", "iuc_standards.md"),
    ("iwc_checklist_skill", "iwc_checklist.md"),
    ("gtn_format_skill", "gtn_format.md"),
    ("bioconda_guide_skill", "bioconda_guide.md"),
])
def test_md_skill_wrapper_has_skill_file(skill_name, md_name):
    """Each thin wrapper module must set SKILL_FILE pointing to a real .md file."""
    import importlib
    mod = importlib.import_module(f"team_galaxy.skills.{skill_name}")
    assert hasattr(mod, "SKILL_FILE"), f"{skill_name} must define SKILL_FILE"
    sf = Path(mod.SKILL_FILE)
    assert sf.is_file(), f"SKILL_FILE points to a missing file: {sf}"
    assert sf.name == md_name


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
# Example YAML validity (parseable + has required top-level keys + uses short names)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "yaml_path",
    list((Path(__file__).parent.parent / "team_galaxy" / "examples").glob("*.yaml")),
    ids=lambda p: p.stem,
)
def test_example_yaml_parseable(yaml_path):
    """Example YAMLs should parse without errors and use short skill names."""
    content = yaml_path.read_text(encoding="utf-8")
    # No legacy path tokens should be present
    assert "${TEAM_GALAXY_SKILLS}" not in content, (
        f"{yaml_path.name} still contains legacy '${TEAM_GALAXY_SKILLS}' token"
    )
    raw = yaml.safe_load(content)
    assert isinstance(raw, dict)
    for key in ("name", "goal", "workflow", "members"):
        assert key in raw, f"{yaml_path.name} is missing top-level key: {key!r}"
    assert isinstance(raw["members"], list)
    assert len(raw["members"]) >= 2


# --------------------------------------------------------------------------- #
# CLI commands (galaxy group from commands.py)
# --------------------------------------------------------------------------- #


def test_cli_galaxy_help():
    runner = CliRunner()
    result = runner.invoke(galaxy, ["--help"])
    assert result.exit_code == 0
    assert "Galaxy" in result.output


def test_cli_scenarios_command():
    runner = CliRunner()
    result = runner.invoke(galaxy, ["scenarios"])
    assert result.exit_code == 0
    assert "tool-wrapper-factory" in result.output


def test_cli_skills_command():
    runner = CliRunner()
    result = runner.invoke(galaxy, ["skills"])
    assert result.exit_code == 0
    assert "bioblend" in result.output
    assert "planemo" in result.output
    assert "iuc_standards" in result.output


def test_cli_personas_command():
    runner = CliRunner()
    result = runner.invoke(galaxy, ["personas"])
    assert result.exit_code == 0
    assert "iuc_reviewer" in result.output
    assert "gtn_author" in result.output


def test_cli_init_creates_file(tmp_path):
    runner = CliRunner()
    result = runner.invoke(galaxy, ["init", "--scenario", "iwc-compliance", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output
    created = tmp_path / "iwc-compliance.yaml"
    assert created.is_file()
    content = created.read_text()
    # Short skill names should be in the generated file
    assert "iwc_checklist" in content
    # No legacy path tokens
    assert "${TEAM_GALAXY_SKILLS}" not in content


def test_cli_init_refuses_overwrite_without_force(tmp_path):
    runner = CliRunner()
    (tmp_path / "iwc-compliance.yaml").write_text("existing")
    result = runner.invoke(galaxy, ["init", "--scenario", "iwc-compliance", "--output-dir", str(tmp_path)])
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_cli_init_force_overwrites(tmp_path):
    runner = CliRunner()
    (tmp_path / "iwc-compliance.yaml").write_text("existing")
    result = runner.invoke(
        galaxy, ["init", "--scenario", "iwc-compliance", "--output-dir", str(tmp_path), "--force"]
    )
    assert result.exit_code == 0
    content = (tmp_path / "iwc-compliance.yaml").read_text()
    assert "IWC" in content  # real content, not "existing"
