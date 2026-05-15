# team-galaxy

Galaxy Project extensions for the [team](https://github.com/cumbof/team)
multi-agent LLM framework.

![PyPI - Version](https://img.shields.io/pypi/v/team-galaxy)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/cumbof/team-galaxy/blob/main/LICENSE)

`team-galaxy` adds Galaxy-specific skills, personas, and ready-to-run scenario
configs on top of `team-core`.  It does not require any changes to `team-core`
— it uses the two built-in extension points already present in the framework:
the **skills** system (`.py` and `.md` files loaded via `skills:` in your team
YAML) and the **persona library** (any directory pointed to by `TEAM_PERSONA_DIR`).

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
team-galaxy init --scenario tool-wrapper-factory
```

This copies a ready-to-edit YAML config to the current directory with all
skill and persona paths already resolved to the installed package location.

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

### 3. Activate Galaxy personas (optional)

To use Galaxy-specific personas with the `@name` shorthand in your YAML:

```bash
export TEAM_PERSONA_DIR=$(python -c "from team_galaxy import personas_dir; print(personas_dir())")
```

### 4. Run

```bash
team run tool-wrapper-factory.yaml
```

---

## Skills

Skills are the core extension mechanism.  Add them to any team YAML under `skills:`.

```yaml
defaults:
  skills:
    - path: /path/to/team_galaxy/skills/bioblend.py    # Galaxy API tools
    - path: /path/to/team_galaxy/skills/planemo.py     # planemo tools
    - path: /path/to/team_galaxy/skills/toolshed.py    # Tool Shed tools
    - path: /path/to/team_galaxy/skills/iuc_standards.md    # context injection
    - path: /path/to/team_galaxy/skills/iwc_checklist.md    # context injection
    - path: /path/to/team_galaxy/skills/gtn_format.md       # context injection
    - path: /path/to/team_galaxy/skills/bioconda_guide.md   # context injection
```

Get the paths programmatically:

```python
from team_galaxy import skills_dir
print(skills_dir())  # /path/to/team_galaxy/skills
```

Or let `team-galaxy init` resolve them automatically in generated configs.

### Available skills

| File | Type | Provides |
|---|---|---|
| `bioblend.py` | Python | `galaxy_upload`, `galaxy_run_tool`, `galaxy_invoke_workflow`, `galaxy_job_status`, `galaxy_wait_for_job`, `galaxy_download`, `galaxy_search_tools`, `galaxy_create_history`, `galaxy_get_histories`, `galaxy_show_dataset` |
| `planemo.py` | Python | `planemo_lint`, `planemo_test`, `planemo_workflow_lint`, `planemo_workflow_test`, `planemo_autoupdate`, `planemo_shed_lint` |
| `toolshed.py` | Python | `toolshed_search`, `toolshed_tool_info`, `toolshed_categories`, `toolshed_owner_repos` |
| `iuc_standards.md` | Markdown | IUC tool XML authoring standards injected into system prompt |
| `iwc_checklist.md` | Markdown | IWC workflow quality checklist injected into system prompt |
| `gtn_format.md` | Markdown | GTN tutorial Markdown format specification |
| `bioconda_guide.md` | Markdown | Bioconda recipe packaging guide |

---

## Personas

Galaxy-specific personas extend the built-in `team-core` persona library.

| Key | Role | Description |
|---|---|---|
| `@iuc_reviewer` | IUC Tool Reviewer | Expert in Galaxy tool XML, planemo, and IUC contribution standards |
| `@iwc_curator` | IWC Workflow Curator | Expert in IWC workflow quality standards and compliance validation |
| `@gtn_author` | GTN Tutorial Author | Expert in writing GTN tutorials in the GTN Markdown format |
| `@galaxy_admin` | Galaxy System Administrator | Manages Galaxy instance infrastructure and job routing |
| `@tool_wrapper_author` | Galaxy Tool Wrapper Author | Expert in writing IUC-compliant Galaxy tool XML wrappers |

Activate them by pointing `TEAM_PERSONA_DIR` at the personas directory:

```bash
export TEAM_PERSONA_DIR=$(python -c "from team_galaxy import personas_dir; print(personas_dir())")
```

Then reference them in any team YAML:

```yaml
members:
  - name: reviewer
    persona: "@iuc_reviewer"
```

---

## How it extends `team-core`

`team-galaxy` uses `team-core`'s two existing extension points — **no core
changes required**:

```
team-core extension points
├── skills:           ← team_galaxy/skills/*.py  (new callable tools)
│                        team_galaxy/skills/*.md  (context injections)
└── TEAM_PERSONA_DIR  ← team_galaxy/personas/*.yaml  (Galaxy personas)
```

The `team-galaxy init` CLI command resolves all installed paths and writes
them into the generated YAML so you never have to find them manually.

---

## CLI reference

```
team-galaxy --help

Commands:
  init       Copy a scenario template to a directory with resolved paths.
  scenarios  List available scenario templates.
  skills     List available Galaxy skills with descriptions.
  personas   List available Galaxy personas with descriptions.
```

```bash
# List scenarios
team-galaxy scenarios

# Initialise a scenario in the current directory
team-galaxy init --scenario bioblend-analysis

# Initialise in a specific directory
team-galaxy init --scenario tool-wrapper-factory --output-dir ~/my-project/
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