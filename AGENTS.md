# Agent Instructions for team-galaxy

## Project Overview

`team-galaxy` (PyPI: `team-galaxy`) is a Galaxy Project extension package for
[`team-core`](https://github.com/cumbof/team). It provides Galaxy-specific skills,
personas, and ready-to-run scenario configs that plug into `team-core` without
requiring any changes to the core package.

## Repository Layout

```
team_galaxy/
  __init__.py          # path helpers: skills_dir(), personas_dir(), examples_dir()
  cli.py               # team-galaxy CLI (init, scenarios, skills, personas)
  skills/
    bioblend.py        # BioBlend Galaxy API tools (galaxy_upload, galaxy_run_tool, …)
    planemo.py         # planemo CLI wrappers (planemo_lint, planemo_test, …)
    toolshed.py        # Tool Shed API tools (toolshed_search, toolshed_tool_info)
    iuc_standards.md   # IUC tool XML authoring standards (context injection)
    iwc_checklist.md   # IWC workflow quality checklist (context injection)
    gtn_format.md      # GTN tutorial format specification (context injection)
    bioconda_guide.md  # Bioconda packaging guide (context injection)
  personas/
    iuc_reviewer.yaml
    iwc_curator.yaml
    gtn_author.yaml
    galaxy_admin.yaml
    tool_wrapper_author.yaml
  examples/            # scenario YAML templates (paths use ${TEAM_GALAXY_SKILLS} tokens)

tests/                 # pytest unit tests
examples/              # symlink or note pointing to team_galaxy/examples
```

## Development Setup

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run the unit test suite
pytest -q

# Run integration tests (requires live Galaxy + planemo)
pytest -m integration
```

## Extension Model

`team-galaxy` extends `team-core` through its two built-in extension points:

1. **Skills** — `.py` and `.md` files in `team_galaxy/skills/` are loaded via
   the `skills:` list in team YAML configs.

2. **Personas** — YAML files in `team_galaxy/personas/` are activated by setting
   `TEAM_PERSONA_DIR` to the output of `from team_galaxy import personas_dir`.

No changes to `team-core` are required.

## Skill Conventions

- All Python skills must follow the team-core multi-tool format:
  `TOOLS`, `TOOL_DESCRIPTIONS`, and optionally `INJECT_INTO_CONTEXT`.
- All tool functions accept `**_` to absorb unused kwargs (`workspace_path`,
  `sandbox`, `timeout`, etc.) passed by the team orchestrator.
- BioBlend tools read credentials from `GALAXY_URL` and `GALAXY_API_KEY`
  environment variables. They must fail gracefully with an `ERROR:` string
  if bioblend is not installed or credentials are missing.
- Planemo tools run `planemo` as a subprocess. They must fail gracefully if
  planemo is not on `PATH`.
- Tool bodies are free-form text. JSON is preferred for structured inputs;
  plain text is used for simple single-argument tools.

## Persona Conventions

- Follow the same YAML schema as `team-core` personas: `role`, `description`,
  `persona` fields.
- Personas should explicitly describe familiarity with Galaxy-specific tools
  (planemo, BioBlend, ToolShed, Conda, IUC/IWC standards) in the persona text.

## Example Config Conventions

- All path references use `${TEAM_GALAXY_SKILLS}` and `${TEAM_GALAXY_PERSONAS}`
  tokens. These are replaced by `team-galaxy init` with the real installed paths.
- Every example must include a descriptive `goal:` block that explains the
  expected output.
- Examples should reference `workspace: ./runs/<scenario-name>`.

## Testing Guidelines

- Unit tests must NOT require a live Galaxy server or planemo. Mock all
  subprocess calls and bioblend imports with `pytest-mock`.
- Integration tests go in `tests/integration/` and must be marked
  `@pytest.mark.integration`.
- Test that each skill file can be loaded by `team-core`'s `load_skill()`.
- Test that each persona YAML has all required fields.
- Test the CLI commands (`init`, `scenarios`, `skills`, `personas`).
