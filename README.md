# team-galaxy

Galaxy Project extensions for the [team](https://github.com/cumbof/team)
multi-agent LLM framework.

![PyPI - Version](https://img.shields.io/pypi/v/team-galaxy)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/cumbof/team-galaxy/blob/main/LICENSE)

`team-galaxy` adds Galaxy-specific skills, personas, and ready-to-run scenario
configs on top of `team-core`.  Installing `team-galaxy` is all it takes —
no environment variables or hardcoded paths required.  It integrates with
`team-core` ≥ 0.15.5 via Python entry points:

| Entry-point group | What it contributes |
|---|---|
| `team.skills` | Short skill names (`bioblend`, `planemo`, …) usable anywhere in a YAML |
| `team.persona_dirs` | Galaxy personas auto-discoverable with the `@name` shorthand |
| `team.commands` | `team galaxy` subcommand injected into the `team` CLI |

> [!NOTE]
>
> A significant portion of this code and documentation was written with the
> assistance of GitHub Copilot. All contributions have been reviewed and
> tested by the maintainers.

---

## Scenarios

| Scenario | Description | Workflow type |
|---|---|---|
| `tool-wrapper-factory` | Generate an IUC-compliant Galaxy tool XML wrapper from a `--help` text | `review_loop` |
| `iwc-compliance` | Bring a Galaxy workflow to full IWC quality-gate compliance | `sequential_chain` |
| `gtn-tutorial-generator` | Convert a `.ga` workflow into a complete GTN tutorial | `review_loop` |
| `bioblend-analysis` | Run a multi-step bioinformatics analysis via the Galaxy API | `manager` |
| `job-failure-investigator` | Diagnose failed Galaxy jobs and produce actionable reports | `sequential_chain` |

---

## Installation

### Basic (planemo scenarios, no Galaxy API)

```bash
pip install team-galaxy
```

Planemo must be installed separately and available on `PATH`:

```bash
pip install planemo
```

### With BioBlend (Galaxy API scenarios)

```bash
pip install "team-galaxy[bioblend]"
```

Set your Galaxy credentials:

```bash
export GALAXY_URL=https://usegalaxy.org
export GALAXY_API_KEY=<your_api_key>
```

### From source

```bash
git clone https://github.com/cumbof/team-galaxy
cd team-galaxy
pip install -e ".[dev,bioblend]"
```

---

## Quick Start

### 1. Initialise a scenario

```bash
team galaxy init --scenario tool-wrapper-factory
```

This copies a ready-to-edit YAML config to the current directory.  Skill
references use short registered names — no paths to edit.

### 2. Prepare your workspace

Each scenario expects one or two input files in the workspace directory.
The generated YAML contains a `# Before running:` comment describing exactly
what to provide.

For the `tool-wrapper-factory` scenario, create `tool_spec.md` in the workspace:

```markdown
# Tool: fastp

conda package: fastp
version: 0.23.4

## --help output

fastp: an ultra-fast all-in-one FASTQ preprocessor
...

## Intended Galaxy datatypes
- Input: fastqsanger, fastqsanger.gz (paired or single)
- Output: fastqsanger.gz (trimmed reads), html (QC report), json (QC metrics)
```

### 3. Run

```bash
team run tool-wrapper-factory.yaml
```

---

## Skills

After `pip install team-galaxy`, use skill names directly in any team YAML:

```yaml
defaults:
  skills:
    - bioblend        # Galaxy API tools (requires bioblend extra)
    - planemo         # planemo lint / test / autoupdate tools
    - toolshed        # Tool Shed search and metadata tools
    - iuc_standards   # IUC authoring standards (context injection)
    - iwc_checklist   # IWC workflow quality checklist (context injection)
    - gtn_format      # GTN tutorial format specification (context injection)
    - bioconda_guide  # Bioconda packaging guide (context injection)
```

### Available skills

| Name | Type | Provides |
|---|---|---|
| `bioblend` | Python tools | `galaxy_upload`, `galaxy_run_tool`, `galaxy_invoke_workflow`, `galaxy_job_status`, `galaxy_wait_for_job`, `galaxy_download`, `galaxy_search_tools`, `galaxy_create_history`, `galaxy_get_histories`, `galaxy_show_dataset` |
| `planemo` | Python tools | `planemo_lint`, `planemo_test`, `planemo_workflow_lint`, `planemo_workflow_test`, `planemo_autoupdate`, `planemo_shed_lint` |
| `toolshed` | Python tools | `toolshed_search`, `toolshed_tool_info`, `toolshed_categories`, `toolshed_owner_repos` |
| `iuc_standards` | Markdown context | IUC tool XML authoring standards injected into system prompt |
| `iwc_checklist` | Markdown context | IWC workflow quality checklist injected into system prompt |
| `gtn_format` | Markdown context | GTN tutorial Markdown format specification |
| `bioconda_guide` | Markdown context | Bioconda recipe packaging guide |

---

## Personas

Galaxy-specific personas are automatically discovered when `team-galaxy` is
installed.  No `TEAM_PERSONA_DIR` needed.

| Key | Role | Description |
|---|---|---|
| `@iuc_reviewer` | IUC Tool Reviewer | Expert in Galaxy tool XML, planemo, and IUC contribution standards |
| `@iwc_curator` | IWC Workflow Curator | Expert in IWC workflow quality standards and compliance validation |
| `@gtn_author` | GTN Tutorial Author | Expert in writing GTN tutorials in the GTN Markdown format |
| `@galaxy_admin` | Galaxy System Administrator | Manages Galaxy instance infrastructure and job routing |
| `@tool_wrapper_author` | Galaxy Tool Wrapper Author | Expert in writing IUC-compliant Galaxy tool XML wrappers |

Reference them in any team YAML:

```yaml
members:
  - name: reviewer
    persona: "@iuc_reviewer"
```

---

## How it extends `team-core`

`team-galaxy` uses the three entry-point groups added in `team-core` ≥ 0.15.5:

```
team-core plugin API
├── team.skills          ← bioblend, planemo, toolshed, iuc_standards, …
├── team.persona_dirs    ← team_galaxy/personas/ (auto-merged)
└── team.commands        ← team galaxy <subcommand>
```

This means:
- Skill names work in **any** team YAML, not just team-galaxy ones.
- Personas are available via `@name` without any env var.
- `team galaxy --help` is always accessible once `team-galaxy` is installed.

---

## CLI reference

```
team galaxy --help

Commands:
  init       Copy a scenario template to a directory, ready to run.
  scenarios  List available scenario templates.
  skills     List available Galaxy skill names and descriptions.
  personas   List available Galaxy personas with descriptions.
```

```bash
# List scenarios
team galaxy scenarios

# Initialise a scenario in the current directory
team galaxy init --scenario bioblend-analysis

# Initialise in a specific directory
team galaxy init --scenario tool-wrapper-factory --output-dir ~/my-project/
```

---

## Development

```bash
pip install -e ".[dev,bioblend]"
pytest -q
```

Integration tests (require a live Galaxy server and planemo):

```bash
pytest -m integration
```

---

## Contributing

Pull requests are welcome.  Please disclose AI assistance in the PR description
(e.g. *"co-authored with GitHub Copilot"*).  Before submitting:

- Run `pytest -q` and ensure all tests pass.
- Add or update tests for any behaviour changes.
- Follow the conventions described in [AGENTS.md](AGENTS.md).
