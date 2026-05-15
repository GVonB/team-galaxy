"""IUC Standards context skill wrapper.

This thin module registers the ``iuc_standards.md`` Markdown context file with
the ``team.skills`` entry-point group.  When ``team-galaxy`` is installed,
``team-core`` resolves the skill name ``"iuc_standards"`` to this module, reads
``SKILL_FILE``, and injects the Markdown content into the member's system prompt.
"""

from __future__ import annotations

from pathlib import Path

#: Absolute path to the Markdown context file for this skill.
SKILL_FILE: str = str(Path(__file__).parent / "iuc_standards.md")
