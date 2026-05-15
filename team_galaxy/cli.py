"""team-galaxy CLI — manage and initialise Galaxy scenario configs.

Commands
--------
``team-galaxy init``      Copy a scenario template to the current directory,
                          resolving all skill and persona paths automatically.
``team-galaxy scenarios`` List available scenario templates.
``team-galaxy skills``    List available Galaxy skills with descriptions.
``team-galaxy personas``  List available Galaxy personas with descriptions.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.table import Table

from team_galaxy import examples_dir, personas_dir, skills_dir

console = Console()

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

_SKILL_DESCRIPTIONS: dict[str, str] = {
    "bioblend.py": "BioBlend tools — upload, run tools, invoke workflows, download results via Galaxy API.",
    "planemo.py": "Planemo tools — lint, test, and autoupdate Galaxy tool XML and workflow files.",
    "toolshed.py": "Tool Shed tools — search tools and fetch metadata from the Galaxy Tool Shed.",
    "iuc_standards.md": "Context injection — IUC tool XML authoring standards and conventions.",
    "iwc_checklist.md": "Context injection — IWC workflow quality checklist and required metadata.",
    "gtn_format.md": "Context injection — GTN tutorial Markdown format specification.",
    "bioconda_guide.md": "Context injection — Bioconda recipe packaging guide.",
}


def _load_persona_desc(yaml_path: Path) -> tuple[str, str]:
    """Return (role, description) from a persona YAML file."""
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        return raw.get("role", ""), raw.get("description", "")
    except Exception:  # noqa: BLE001
        return "", ""


def _resolve_paths_in_yaml(content: str) -> str:
    """Replace placeholder path tokens in a template YAML with real installed paths."""
    content = content.replace("${TEAM_GALAXY_SKILLS}", str(skills_dir()))
    content = content.replace("${TEAM_GALAXY_PERSONAS}", str(personas_dir()))
    return content


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


@click.group()
@click.version_option(package_name="team-galaxy")
def cli() -> None:
    """team-galaxy — Galaxy Project extensions for the team multi-agent framework.

    Provides BioBlend, planemo, and Tool Shed skills; Galaxy-specific personas;
    and ready-to-run scenario configs for common Galaxy automation tasks.

    After installing, run:

      team-galaxy init --scenario tool-wrapper-factory

    to get a ready-to-edit YAML config in the current directory, then:

      team run tool-wrapper-factory.yaml
    """


@cli.command("init")
@click.option(
    "--scenario",
    "-s",
    required=True,
    type=click.Choice(
        [p.stem for p in sorted(examples_dir().glob("*.yaml"))],
        case_sensitive=False,
    ),
    help="Scenario template to initialise.",
)
@click.option(
    "--output-dir",
    "-o",
    default=".",
    show_default=True,
    help="Directory to write the scenario YAML file to.",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite an existing file.",
)
def init_cmd(scenario: str, output_dir: str, force: bool) -> None:
    """Copy a scenario template to OUTPUT_DIR with resolved skill/persona paths.

    The generated YAML is ready to run with ``team run <file>``.  Edit the
    ``goal``, ``model`` fields, and any member-specific options before running.
    """
    src = examples_dir() / f"{scenario}.yaml"
    if not src.is_file():
        console.print(f"[red]Scenario template not found:[/red] {src}")
        raise SystemExit(1)

    dest = Path(output_dir).expanduser().resolve() / f"{scenario}.yaml"
    if dest.exists() and not force:
        console.print(
            f"[yellow]{dest} already exists.[/yellow] Use --force to overwrite."
        )
        raise SystemExit(1)

    content = src.read_text(encoding="utf-8")
    content = _resolve_paths_in_yaml(content)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")

    console.print(f"[green]Created[/green] {dest}")
    console.print("")
    console.print("Next steps:")
    console.print("  1. Edit the [bold]goal[/bold] and [bold]model[/bold] fields for your use case.")
    console.print("  2. Set credentials if using the BioBlend skill:")
    console.print("       export GALAXY_URL=https://usegalaxy.org")
    console.print("       export GALAXY_API_KEY=<your_api_key>")
    console.print(f"  3. Run:  [bold]team run {dest.name}[/bold]")


@cli.command("scenarios")
def list_scenarios() -> None:
    """List available scenario templates."""
    table = Table(title="Available team-galaxy scenarios", show_lines=True)
    table.add_column("Name", style="bold cyan")
    table.add_column("Description")

    _SCENARIO_DESCRIPTIONS = {
        "tool-wrapper-factory": "Generate IUC-compliant Galaxy tool XML wrappers from a --help text.",
        "iwc-compliance": "Bring a Galaxy workflow to full IWC quality-gate compliance.",
        "gtn-tutorial-generator": "Convert a .ga workflow into a complete GTN tutorial.",
        "bioblend-analysis": "Run a multi-step bioinformatics analysis via the Galaxy API.",
        "job-failure-investigator": "Diagnose and explain failed Galaxy jobs with actionable fixes.",
    }

    for yaml_path in sorted(examples_dir().glob("*.yaml")):
        name = yaml_path.stem
        desc = _SCENARIO_DESCRIPTIONS.get(name, "")
        table.add_row(name, desc)

    console.print(table)
    console.print("")
    console.print("Initialise a scenario:  [bold]team-galaxy init --scenario <name>[/bold]")


@cli.command("skills")
def list_skills() -> None:
    """List available Galaxy skills with descriptions."""
    table = Table(title="Available team-galaxy skills", show_lines=True)
    table.add_column("File", style="bold cyan")
    table.add_column("Type")
    table.add_column("Description")

    for skill_path in sorted(skills_dir().iterdir()):
        if skill_path.suffix not in (".py", ".md"):
            continue
        kind = "Python (tools)" if skill_path.suffix == ".py" else "Markdown (context)"
        desc = _SKILL_DESCRIPTIONS.get(skill_path.name, "")
        table.add_row(skill_path.name, kind, desc)

    console.print(table)
    console.print("")
    console.print(f"Skills directory:  [bold]{skills_dir()}[/bold]")
    console.print("Add to YAML:  [bold]skills:\\n  - path: <skill_path>[/bold]")


@cli.command("personas")
def list_personas() -> None:
    """List available Galaxy personas with descriptions."""
    table = Table(title="Available team-galaxy personas", show_lines=True)
    table.add_column("Key", style="bold cyan")
    table.add_column("Role")
    table.add_column("Description")

    for yaml_path in sorted(personas_dir().glob("*.yaml")):
        role, desc = _load_persona_desc(yaml_path)
        table.add_row(f"@{yaml_path.stem}", role, desc)

    console.print(table)
    console.print("")
    console.print(f"Personas directory:  [bold]{personas_dir()}[/bold]")
    console.print(
        "Activate with:  [bold]export TEAM_PERSONA_DIR="
        + str(personas_dir())
        + "[/bold]"
    )
    console.print("Then reference in YAML as:  [bold]persona: \"@iuc_reviewer\"[/bold]")
