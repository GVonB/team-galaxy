"""galaxy subcommand group — accessible as ``team galaxy <cmd>``.

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

from team.extension import make_extension_commands
from team_galaxy import examples_dir, personas_dir, skills_dir

#: Registered skill names -> short descriptions.
_SKILL_DESCRIPTIONS: dict[str, str] = {
    "bioblend": "BioBlend tools — upload, run tools, invoke workflows, download results via Galaxy API.",
    "planemo": "Planemo tools — lint, test, and autoupdate Galaxy tool XML and workflow files.",
    "toolshed": "Tool Shed tools — search tools and fetch metadata from the Galaxy Tool Shed.",
    "iuc_standards": "Context injection — IUC tool XML authoring standards and conventions.",
    "iwc_checklist": "Context injection — IWC workflow quality checklist and required metadata.",
    "gtn_format": "Context injection — GTN tutorial Markdown format specification.",
    "bioconda_guide": "Context injection — Bioconda recipe packaging guide.",
}

#: Scenario YAML stem -> short description.
_SCENARIO_DESCRIPTIONS: dict[str, str] = {
    "tool-wrapper-factory": "Generate IUC-compliant Galaxy tool XML wrappers from a --help text.",
    "iwc-compliance": "Bring a Galaxy workflow to full IWC quality-gate compliance.",
    "gtn-tutorial-generator": "Convert a .ga workflow into a complete GTN tutorial.",
    "bioblend-analysis": "Run a multi-step bioinformatics analysis via the Galaxy API.",
    "job-failure-investigator": "Diagnose and explain failed Galaxy jobs with actionable fixes.",
}

galaxy = make_extension_commands(
    package_name="team-galaxy",
    group_name="galaxy",
    description="Galaxy Project extensions for the team multi-agent framework.",
    skills_dir=skills_dir,
    personas_dir=personas_dir,
    examples_dir=examples_dir,
    skill_descriptions=_SKILL_DESCRIPTIONS,
    scenario_descriptions=_SCENARIO_DESCRIPTIONS,
)
