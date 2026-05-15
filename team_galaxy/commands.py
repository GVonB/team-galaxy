"""team-galaxy Galaxy subcommand group — accessible as ``team galaxy <cmd>``.

Commands
--------
``team galaxy init``      Copy a scenario template to the current directory,
                          ready to run with ``team run``.
``team galaxy scenarios`` List available scenario templates.
``team galaxy skills``    List available Galaxy skills with descriptions.
``team galaxy personas``  List available Galaxy personas with descriptions.

Registration
------------
This module is registered with ``team-core`` via the ``team.commands``
entry-point group in ``pyproject.toml``::

    [project.entry-points."team.commands"]
    galaxy = "team_galaxy.commands:galaxy"

After ``pip install team-galaxy``, the ``team galaxy`` subcommand becomes
available without any changes to ``team-core``.
"""

from __future__ import annotations

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
    "bioblend": "BioBlend tools — upload, run tools, invoke workflows, download results via Galaxy API.",
    "planemo": "Planemo tools — lint, test, and autoupdate Galaxy tool XML and workflow files.",
    "toolshed": "Tool Shed tools — search tools and fetch metadata from the Galaxy Tool Shed.",
    "iuc_standards": "Context injection — IUC tool XML authoring standards and conventions.",
    "iwc_checklist": "Context injection — IWC workflow quality checklist and required metadata.",
    "gtn_format": "Context injection — GTN tutorial Markdown format specification.",
    "bioconda_guide": "Context injection — Bioconda recipe packaging guide.",
}

_SCENARIO_DESCRIPTIONS: dict[str, str] = {
    "tool-wrapper-factory": "Generate IUC-compliant Galaxy tool XML wrappers from a --help text.",
    "iwc-compliance": "Bring a Galaxy workflow to full IWC quality-gate compliance.",
    "gtn-tutorial-generator": "Convert a .ga workflow into a complete GTN tutorial.",
    "bioblend-analysis": "Run a multi-step bioinformatics analysis via the Galaxy API.",
    "job-failure-investigator": "Diagnose and explain failed Galaxy jobs with actionable fixes.",
}


def _load_persona_desc(yaml_path: Path) -> tuple[str, str]:
    """Return (role, description) from a persona YAML file."""
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        return raw.get("role", ""), raw.get("description", "")
    except Exception:  # noqa: BLE001
        return "", ""


# --------------------------------------------------------------------------- #
# Galaxy subcommand group
# --------------------------------------------------------------------------- #


@click.group()
@click.version_option(package_name="team-galaxy")
def galaxy() -> None:
    """Galaxy Project extensions for the team multi-agent framework.

    Provides BioBlend, planemo, and Tool Shed skills; Galaxy-specific personas;
    and ready-to-run scenario configs for common Galaxy automation tasks.

    Get started:

      team galaxy init --scenario tool-wrapper-factory

    This copies a ready-to-edit YAML config to the current directory.  Then:

      team run tool-wrapper-factory.yaml
    """


@galaxy.command("init")
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
    """Copy a scenario template to OUTPUT_DIR, ready to run with ``team run``.

    Skill references in the generated YAML use short registered names
    (e.g. ``bioblend``, ``planemo``) that resolve automatically when
    ``team-galaxy`` is installed — no paths to edit.

    Edit the ``goal`` and ``model`` fields before running.
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


@galaxy.command("scenarios")
def list_scenarios() -> None:
    """List available scenario templates."""
    table = Table(title="Available team-galaxy scenarios", show_lines=True)
    table.add_column("Name", style="bold cyan")
    table.add_column("Description")

    for yaml_path in sorted(examples_dir().glob("*.yaml")):
        name = yaml_path.stem
        desc = _SCENARIO_DESCRIPTIONS.get(name, "")
        table.add_row(name, desc)

    console.print(table)
    console.print("")
    console.print("Initialise a scenario:  [bold]team galaxy init --scenario <name>[/bold]")


@galaxy.command("skills")
def list_skills() -> None:
    """List available Galaxy skill names and descriptions."""
    table = Table(title="Available team-galaxy skills", show_lines=True)
    table.add_column("Name", style="bold cyan")
    table.add_column("Type")
    table.add_column("Description")

    py_skills = {"bioblend", "planemo", "toolshed"}
    for name, desc in sorted(_SKILL_DESCRIPTIONS.items()):
        kind = "Python (tools)" if name in py_skills else "Markdown (context)"
        table.add_row(name, kind, desc)

    console.print(table)
    console.print("")
    console.print("Use in YAML:  [bold]skills:\\n  - bioblend[/bold]")


@galaxy.command("personas")
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
    console.print("Use in YAML:  [bold]persona: \"@iuc_reviewer\"[/bold]")
    console.print("(Personas are auto-discovered when team-galaxy is installed.)")
