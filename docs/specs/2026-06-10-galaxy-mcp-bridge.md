# Galaxy MCP bridge for team-galaxy

Status: proposed
Date: 2026-06-10
Repo: `team-galaxy` (extension package for `team-core`, https://github.com/cumbof/team)

## Context

This spec assumes no prior conversation context. Read it standalone.

**`team-core`** (PyPI `team-core`, repo `cumbof/team`) is a framework for
orchestrating clusters of containerized local LLMs ("members"), each with a
persona, that collaborate via a turn-based orchestrator. Members get tools
through a skill system: a `.py` file exports a `TOOLS` dict (name → callable)
plus `TOOL_DESCRIPTIONS`, optionally `INJECT_INTO_CONTEXT` (markdown injected
into the member's system prompt). Skills are referenced by name in team YAML
configs and resolved either from local files or from `team.skills` entry
points registered by extension packages (see `team/skills.py`).

**`team-galaxy`** (this repo, PyPI `team-galaxy`) is the Galaxy Project
extension for `team-core`. It currently ships:

- `team_galaxy/skills/bioblend.py` — 10 tools wrapping the `bioblend` Python
  client directly: `galaxy_upload`, `galaxy_run_tool`, `galaxy_invoke_workflow`,
  `galaxy_job_status`, `galaxy_wait_for_job`, `galaxy_download`,
  `galaxy_search_tools`, `galaxy_create_history`, `galaxy_get_histories`,
  `galaxy_show_dataset`. Reads `GALAXY_URL` / `GALAXY_API_KEY` from the
  environment. Each tool takes a single `body: str` (often JSON) — this
  matches how `team-core` calls skill tools in both `tool_mode: text` (fenced
  blocks) and `tool_mode: native` (skill tools get an auto-generated minimal
  JSON schema: a single `"input": {"type": "string"}` parameter — see
  `team/member.py` `_run_native_agentic_turn`, ~line 547).
- `team_galaxy/skills/planemo.py`, `toolshed.py` — subprocess/API wrappers.
- Markdown context-injection skills: `iuc_standards.md`, `iwc_checklist.md`,
  `gtn_format.md`, `bioconda_guide.md`.
- Personas: `galaxy_admin`, `gtn_author`, `iuc_reviewer`, `iwc_curator`,
  `tool_wrapper_author` (plus `bioinformatician` ships in `team-core`'s own
  `personas/`).
- Example scenario `bioblend-analysis.yaml` driving an analyst/programmer/
  reporter team against a live Galaxy server.

**Separately**, the Galaxy project maintains
[`galaxy-mcp`](https://github.com/galaxyproject/galaxy-mcp)
(`mcp-server-galaxy-py/`), an MCP (Model Context Protocol) server — a
subprocess speaking JSON-RPC over stdio, normally launched via `uvx
galaxy-mcp`. It wraps `bioblend` (`bioblend.galaxy.GalaxyInstance`) and
exposes **32 tools** (verified by reading
`mcp-server-galaxy-py/src/galaxy_mcp/server.py`, ~3400 lines):

| Category | Tools |
|---|---|
| Connection | `connect`, `get_server_info`, `get_user` |
| Tool discovery/exec | `search_tools_by_name`, `search_tools_by_keywords`, `get_tool_details`, `get_tool_run_examples`, `get_tool_input_template`, `get_tool_citations`, `get_tool_panel`, `run_tool` |
| Histories/datasets/jobs | `create_history`, `update_history`, `get_histories`, `list_history_ids`, `get_history_details`, `get_history_contents`, `get_job_details`, `get_dataset_details`, `get_collection_details`, `download_dataset`, `upload_file`, `upload_file_from_url` |
| Workflows (existing only) | `list_workflows`, `get_workflow_details`, `get_workflow_input_template`, `invoke_workflow`, `cancel_workflow_invocation`, `get_invocations` |
| IWC discovery | `get_iwc_workflows`, `search_iwc_workflows`, `get_iwc_workflow_details`, `recommend_iwc_workflows`, `import_workflow_from_iwc` |
| User-defined tools | `create_user_tool`, `list_user_tools`, `delete_user_tool`, `run_user_tool` |

This is the same backend `loom` (a separate, unrelated TypeScript/Pi-based
agent project) registers via `pi-mcp-adapter` for its own Galaxy access.

**Confirmed gap**: galaxy-mcp has no tool to *construct a new multi-step
workflow*. `gi.workflows.import_workflow_dict` / `export_workflow_dict`
(bioblend's workflow-JSON methods) are used internally only by
`import_workflow_from_iwc` (importing an *existing* IWC workflow) and by the
read-only workflow-detail tools — never exposed as "take this workflow
definition and create it".

## Goal

Give `team-galaxy` members the broad galaxy-mcp tool surface (32 tools,
maintained upstream, IWC discovery/import, tool introspection, user-defined
tools, etc.) **without re-implementing it**, by bridging to the `galaxy-mcp`
subprocess. Then close the one real gap — workflow *construction* — with a
small, focused addition.

## Non-goals

- Do not remove or replace `team_galaxy/skills/bioblend.py`. It's tested,
  used by the `bioblend-analysis.yaml` example, and provides a simpler,
  curated happy-path (upload → run tool → wait → download) that's good for
  `tool_mode: text`. The MCP bridge is additive — it covers what `bioblend.py`
  doesn't (IWC search/import, tool introspection, user-tools, invocation
  cancel/list, collection details).
- No changes to `team-core` itself. Everything below is new files in
  `team-galaxy` plus `pyproject.toml` entry points, consistent with the
  existing "no core changes required" extension model (see
  `team-galaxy/AGENTS.md`).
- This spec does **not** cover any integration with `loom` or
  `team_dispatch`. `team-galaxy` talks to `galaxy-mcp` directly; `loom` is
  out of scope entirely.

## Design

### Component A — generic MCP-client bridge skill (`galaxy_mcp.py`)

New file: `team_galaxy/skills/galaxy_mcp.py`. New entry point:

```toml
[project.entry-points."team.skills"]
galaxy_mcp = "team_galaxy.skills.galaxy_mcp"
```

New optional dependency group:

```toml
[project.optional-dependencies]
mcp = ["mcp>=1.0", "galaxy-mcp>=<latest>"]   # verify exact version pins
all = ["team-galaxy[bioblend,mcp]"]
```

(`mcp` is the official Anthropic MCP Python SDK — provides
`mcp.client.stdio.stdio_client` + `mcp.ClientSession`.)

#### Tool surface exposed to `team` members

Two tools only — do **not** try to hand-translate all 32 galaxy-mcp tools
into 32 separate `team` tools (high maintenance burden, goes stale when
galaxy-mcp adds/changes tools):

- **`galaxy_mcp_list_tools`** — body ignored. Returns the live JSON tool
  catalog from the MCP server's `tools/list` (names, descriptions, input
  JSON schemas). Always accurate because it's live, not hardcoded.
- **`galaxy_mcp_call`** — body is JSON: `{"tool": "<name>", "arguments":
  {...}}`. Dispatches to the MCP server's `tools/call` and returns the
  result content as a string (truncate like `bioblend.py`'s `_safe()` does,
  ~4096 chars).

`INJECT_INTO_CONTEXT` (short, static — no hardcoded tool list):

```
## Galaxy MCP access

You have access to the full Galaxy API (galaxy-mcp, ~32 tools: tool search/
execution, histories, datasets, jobs, IWC workflow discovery & import,
invocation tracking, user-defined tools) via two tools:

1. `galaxy_mcp_list_tools` — call once to see the available tools and their
   JSON-schema parameters.
2. `galaxy_mcp_call` — body: {"tool": "<name>", "arguments": {...}} to invoke
   any tool from that list.

For simple, common operations (upload a file, run one tool, wait for a job,
download a result) prefer the dedicated `galaxy_*` tools from the bioblend
skill if available — they're simpler. Use galaxy_mcp_call for anything else:
IWC workflow search/import, tool introspection, invocation management,
user-defined tools.
```

#### Process lifecycle (the hard part)

`team-core` skill tools are **synchronous** callables `(body: str, **kwargs)
-> str`. MCP is **async JSON-RPC over stdio** to a long-lived subprocess, and
galaxy-mcp is **stateful** — `connect()` must succeed before other tools work
(`ensure_connected()` in `server.py` raises if not connected; session state
is per-`SessionGalaxyConnection`, see `_get_session_connection` /
`_set_session_connection` in `server.py`).

Implement a module-level singleton `_MCPBridge`:

```python
class _MCPBridge:
    """Owns one galaxy-mcp subprocess + asyncio event loop in a background
    thread. team-core tool callables are sync; this bridges sync -> async."""

    def __init__(self):
        self._loop = None       # asyncio event loop, owned by _thread
        self._thread = None     # daemon thread running loop.run_forever()
        self._session = None    # mcp.ClientSession, created lazily
        self._connected = False

    def _ensure_started(self):
        # start daemon thread + event loop on first use (lazy — do NOT spawn
        # the subprocess at module-import time, since load_skill() execs
        # this module on every team config load)
        ...

    async def _ensure_session(self):
        # spawn `uvx galaxy-mcp` via stdio_client(StdioServerParameters(
        #   command="uvx", args=["galaxy-mcp"]))
        # ClientSession(...).initialize()
        # call tools/call("connect", {}) — galaxy-mcp should pick up
        # GALAXY_URL / GALAXY_API_KEY from its inherited environment
        # (VERIFY: read connect()'s implementation in server.py — if it does
        # NOT fall back to env vars, pass url=os.environ["GALAXY_URL"],
        # api_key=os.environ["GALAXY_API_KEY"] explicitly)
        ...

    def list_tools(self) -> str:
        # run_coroutine_threadsafe -> session.list_tools() -> JSON string
        ...

    def call_tool(self, name: str, arguments: dict) -> str:
        # run_coroutine_threadsafe -> session.call_tool(name, arguments)
        # -> JSON string, truncated
        ...

_bridge = _MCPBridge()  # module-level singleton; lazy-started
```

Register an `atexit` handler to terminate the subprocess + stop the loop on
interpreter exit (skills have no explicit teardown hook in `team-core`).

`uvx` must be on `PATH` (same requirement `loom` already documents for
galaxy-mcp). Consider an env var override `GALAXY_MCP_COMMAND` (default
`"uvx galaxy-mcp"`, shell-split) for users who `pip install galaxy-mcp`
directly and want to invoke its console script instead — but don't
over-engineer this; ship the `uvx` default first.

#### Open questions to resolve during implementation

1. Exact PyPI package name / console-script entry point for
   `mcp-server-galaxy-py` when *not* using `uvx` (needed if we add the
   `GALAXY_MCP_COMMAND` override).
2. Does galaxy-mcp's `connect()` fall back to `GALAXY_URL`/`GALAXY_API_KEY`
   env vars when called with no arguments? Read `server.py` `connect()` body
   (lines ~622-744) to confirm before relying on it.
3. Result-content shape from `session.call_tool()` — galaxy-mcp tools return
   a `GalaxyResult` dataclass; confirm how that serializes over MCP
   (structured content vs. text-wrapped JSON) so `_safe()`-style truncation
   and JSON round-tripping work correctly.

### Component B — workflow construction (`bioblend.py` extension)

Add **one new tool** to the existing `team_galaxy/skills/bioblend.py`
(reuses its `_gi()`, `_safe()`, `_parse_json()` helpers — no new module
needed):

- **`galaxy_build_workflow`** — body: a workflow definition, either:
  - a native Galaxy workflow dict (has `"a_galaxy_workflow"` /
    `"format-version"` and `"steps"` keyed by step index), passed straight to
    `gi.workflows.import_workflow_dict(workflow_dict)`; or
  - a [gxformat2](https://github.com/galaxyproject/gxformat2) YAML/dict
    (`class: GalaxyWorkflow`, `inputs:`, `steps:` as a readable list with
    `tool_id` + `in`/`out` connections by name) — detect via `class ==
    "GalaxyWorkflow"`, convert to native format with `gxformat2` (verify
    exact conversion function — likely `gxformat2.convert_to_native` /
    `gxformat2.python_to_workflow`), then `import_workflow_dict`.

  Returns the new workflow's ID (for use with `galaxy_invoke_workflow`,
  already in `bioblend.py`, or with `galaxy_mcp_call`'s `invoke_workflow`).

  New optional dependency: `gxformat2` (already a transitive dependency of
  `planemo`, which `team-galaxy` already integrates with — check if it's
  already available before adding explicitly).

Add a matching **markdown context-injection skill**:
`team_galaxy/skills/workflow_format.md` (+ thin `workflow_format_skill.py`
wrapper, following the exact pattern of `iuc_standards_skill.py` /
`iwc_checklist_skill.py` — set `SKILL_FILE` to the `.md` path). Content:
gxformat2 YAML format reference + one fully worked minimal example (e.g.
two-step: input → fastp → output), so an LLM member can author a workflow
without inventing the schema from scratch.

New entry point:

```toml
[project.entry-points."team.skills"]
workflow_format = "team_galaxy.skills.workflow_format_skill"
```

### Component C — example scenario

Add `team_galaxy/examples/galaxy-mcp-workflow.yaml`: a scenario where
`@bioinformatician` (persona from `team-core`) or `@iwc_curator` (this repo)
is given `tools: [galaxy_mcp_list_tools, galaxy_mcp_call,
galaxy_build_workflow, galaxy_invoke_workflow, galaxy_wait_for_job,
galaxy_download]` and `skills: [galaxy_mcp, workflow_format]`. Goal text:
search IWC for a relevant existing workflow first
(`galaxy_mcp_call` → `search_iwc_workflows`); if nothing matches, author a
new workflow with `galaxy_build_workflow`, invoke it, wait, download results.
Mirrors `bioblend-analysis.yaml`'s structure/header conventions.

### Component D — tests

- `tests/test_galaxy_mcp_skill.py` — mock `mcp.client.stdio.stdio_client` /
  `ClientSession` (do NOT spawn a real `uvx galaxy-mcp` subprocess in unit
  tests — no Docker/network per `team-core`'s testing guidelines). Cover:
  lazy subprocess start, `connect()` called before first real tool call,
  `galaxy_mcp_list_tools` returns the mocked catalog, `galaxy_mcp_call`
  dispatches with correct arguments and truncates long results.
- Extend `tests/test_bioblend_skill.py` with `galaxy_build_workflow`: native
  dict passthrough to `import_workflow_dict`, gxformat2 dict gets converted
  first, missing/invalid `class` field handled, bioblend-not-installed /
  credentials-missing error paths (matching existing tests' style).
- Mark anything touching a real `uvx galaxy-mcp` subprocess or live Galaxy as
  `@pytest.mark.integration` (existing convention, excluded from CI).

## Summary of file changes

```
team-galaxy/
  pyproject.toml                              # + galaxy_mcp, workflow_format
                                               #   entry points; + mcp, gxformat2 deps
  team_galaxy/skills/
    galaxy_mcp.py                             # NEW — Component A
    bioblend.py                               # + galaxy_build_workflow (Component B)
    workflow_format.md                        # NEW — Component B
    workflow_format_skill.py                  # NEW — thin .md wrapper (Component B)
  team_galaxy/examples/
    galaxy-mcp-workflow.yaml                  # NEW — Component C
  tests/
    test_galaxy_mcp_skill.py                  # NEW — Component D
    test_bioblend_skill.py                    # + galaxy_build_workflow tests
```

## Suggested implementation order

1. Component B first — smaller, self-contained, no new async/subprocess
   complexity, extends a file that already has tests and conventions.
2. Component A — the MCP bridge. Resolve the three open questions above
   (ideally by reading `mcp-server-galaxy-py/src/galaxy_mcp/server.py`'s
   `connect()` and checking the `mcp` SDK's stdio client API) before writing
   the bridge, since they affect its shape.
3. Component C (example) once A and B both work, to validate end-to-end.
4. Component D tests alongside A and B (not deferred to the end).
