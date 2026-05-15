"""team-galaxy — Galaxy Project extensions for the team multi-agent LLM framework.

Provides Galaxy-specific skills, personas, and ready-to-run example configs that
plug directly into ``team-core`` via Python entry points.  Installing
``team-galaxy`` is all it takes — no paths, no environment variables needed.

Extension points registered
---------------------------
``team.skills``
    Short skill names usable anywhere in a team YAML ``skills:`` list::

        skills:
          - bioblend        # BioBlend Galaxy API tools
          - planemo         # planemo lint / test / autoupdate tools
          - toolshed        # Tool Shed search and metadata tools
          - iuc_standards   # IUC authoring standards (context injection)
          - iwc_checklist   # IWC workflow quality checklist (context injection)
          - gtn_format      # GTN tutorial format (context injection)
          - bioconda_guide  # Bioconda packaging guide (context injection)

``team.persona_dirs``
    The ``team_galaxy/personas/`` directory is automatically merged into the
    persona library.  Reference personas with the ``@`` shorthand::

        persona: "@iuc_reviewer"

``team.commands``
    A ``galaxy`` subcommand group is injected into the ``team`` CLI::

        team galaxy --help
        team galaxy init --scenario tool-wrapper-factory
        team galaxy scenarios
        team galaxy skills
        team galaxy personas

Quick start
-----------
Install::

    pip install team-galaxy            # core only; planemo must be on PATH
    pip install "team-galaxy[bioblend]"  # include BioBlend for Galaxy API tools

Set Galaxy credentials (only needed for BioBlend skill)::

    export GALAXY_URL=https://usegalaxy.org
    export GALAXY_API_KEY=<your_api_key>

Initialise a ready-to-run scenario config in the current directory::

    team galaxy init --scenario tool-wrapper-factory

Then run it::

    team run tool-wrapper-factory.yaml

Path helpers
------------
Call these from Python to get absolute paths to the installed resources::

    from team_galaxy import skills_dir, personas_dir, examples_dir

    print(skills_dir())    # .../team_galaxy/skills
    print(personas_dir())  # .../team_galaxy/personas
    print(examples_dir())  # .../team_galaxy/examples

Environment variables
---------------------
``GALAXY_URL``
    URL of the Galaxy server (e.g. ``https://usegalaxy.org``).
    Required by the BioBlend skill.

``GALAXY_API_KEY``
    Galaxy API key with sufficient permissions.
    Required by the BioBlend skill.
"""

from __future__ import annotations

from pathlib import Path


def skills_dir() -> Path:
    """Return the absolute path to the built-in team-galaxy skills directory."""
    return Path(__file__).parent / "skills"


def personas_dir() -> Path:
    """Return the absolute path to the built-in team-galaxy personas directory."""
    return Path(__file__).parent / "personas"


def examples_dir() -> Path:
    """Return the absolute path to the built-in team-galaxy example configs directory."""
    return Path(__file__).parent / "examples"


__all__ = ["skills_dir", "personas_dir", "examples_dir"]
