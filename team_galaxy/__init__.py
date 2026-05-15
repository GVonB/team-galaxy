"""team-galaxy — Galaxy Project extensions for the team multi-agent LLM framework.

Provides Galaxy-specific skills, personas, and ready-to-run example configs that
plug directly into ``team-core`` without requiring any changes to the core package.

Extension points used
---------------------
* **Skills** — ``team-core`` accepts any ``.py`` or ``.md`` file as a skill via the
  ``skills:`` list in a team YAML.  Use :func:`skills_dir` to get the path to
  the built-in team-galaxy skills, then reference individual files in your YAML.

* **Personas** — ``team-core`` scans ``TEAM_PERSONA_DIR`` (env var) in addition to
  its own built-in ``personas/`` directory.  Set it to :func:`personas_dir` to make
  Galaxy personas available with the ``@name`` shorthand.

Quick start
-----------
Install::

    pip install team-galaxy            # core only; planemo must be on PATH
    pip install "team-galaxy[bioblend]"  # include BioBlend for Galaxy API tools

Set Galaxy credentials (only needed for BioBlend skill)::

    export GALAXY_URL=https://usegalaxy.org
    export GALAXY_API_KEY=<your_api_key>

Initialise a ready-to-run scenario config in the current directory::

    team-galaxy init --scenario tool-wrapper-factory

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

``TEAM_PERSONA_DIR``
    Set to :func:`personas_dir` to activate the Galaxy persona library::

        export TEAM_PERSONA_DIR=$(python -c "from team_galaxy import personas_dir; print(personas_dir())")
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
