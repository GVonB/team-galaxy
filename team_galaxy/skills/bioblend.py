"""BioBlend skill — give team members direct access to a Galaxy server.

Requires the ``bioblend`` Python package (install with
``pip install "team-galaxy[bioblend]"`` or ``pip install bioblend``).

Credentials
-----------
Set these environment variables before running ``team run``:

    export GALAXY_URL=https://usegalaxy.org
    export GALAXY_API_KEY=<your_api_key>

Available tools
---------------
``galaxy_upload``
    Upload a file from the shared workspace to a Galaxy history.

    Body (JSON)::

        {"history_id": "<hid>", "file_path": "input.fastq", "file_type": "fastqsanger"}

``galaxy_run_tool``
    Run a Galaxy tool and return the new dataset IDs.

    Body (JSON)::

        {
          "history_id": "<hid>",
          "tool_id": "toolshed.g2.bx.psu.edu/repos/devteam/samtools_sort/samtools_sort/2.0.4",
          "inputs": {"input1": {"src": "hda", "id": "<dataset_id>"}}
        }

``galaxy_invoke_workflow``
    Invoke a Galaxy workflow.

    Body (JSON)::

        {
          "workflow_id": "<wid>",
          "history_id": "<hid>",
          "inputs": {"0": {"src": "hda", "id": "<dataset_id>"}}
        }

``galaxy_job_status``
    Get the state of a job or dataset.

    Body (JSON)::

        {"job_id": "<jid>"}   -- or --   {"dataset_id": "<did>"}

``galaxy_wait_for_job``
    Block until a job/dataset reaches a terminal state (ok, error, deleted).
    Polls every 10 s; respects a timeout.

    Body (JSON)::

        {"job_id": "<jid>", "timeout": 300}

``galaxy_download``
    Download a dataset from Galaxy to the shared workspace.

    Body (JSON)::

        {"dataset_id": "<did>", "output_path": "results/output.bam"}

``galaxy_search_tools``
    Search for tools on the Galaxy server using a regex pattern matched against
    tool name and description.

    Body: regex string, e.g. ``bwa|bowtie2|hisat2``.

``galaxy_show_tool``
    Return a tool's input/output schema.  Use this before galaxy_run_tool to
    learn the exact parameter names and types.

    Body: tool_id string.

``galaxy_create_history``
    Create a new history and return its ID.

    Body: history name string.

``galaxy_get_histories``
    List recent histories (newest 20).

    Body: ignored.

``galaxy_show_dataset``
    Return metadata (name, state, file_size, genome_build, misc_info) for a dataset.

    Body (JSON)::

        {"dataset_id": "<did>", "history_id": "<hid>"}
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

_MAX_OUTPUT = 4096
_SEARCH_CAP = 15

# Tool panel cache, populated on first fetch
# empty = not yet fetched, [0] = flat list of tool dicts
_tool_panel_cache: list[list[dict]] = []


# --------------------------------------------------------------------------- #
# BioBlend connection helper
# --------------------------------------------------------------------------- #


def _gi():
    """Return an authenticated GalaxyInstance, or raise RuntimeError."""
    try:
        from bioblend.galaxy import GalaxyInstance  # type: ignore[import]
    except ImportError as exc:
        raise RuntimeError(
            "bioblend is not installed.  Run: pip install 'team-galaxy[bioblend]'"
        ) from exc

    url = os.environ.get("GALAXY_URL", "").strip()
    key = os.environ.get("GALAXY_API_KEY", "").strip()
    if not url:
        raise RuntimeError("GALAXY_URL environment variable is not set.")
    if not key:
        raise RuntimeError("GALAXY_API_KEY environment variable is not set.")
    return GalaxyInstance(url, key=key)


def _safe(fn, *args, compact: bool = False, **kwargs) -> str:
    """Call *fn* and return its string result, or an ERROR string on exception."""
    try:
        result = fn(*args, **kwargs)
        separators = (",", ":") if compact else (", ", ": ")
        indent = None if compact else 2
        out = json.dumps(result, indent=indent, separators=separators, default=str)
        return out[:_MAX_OUTPUT] if len(out) > _MAX_OUTPUT else out
    except Exception as exc:  # noqa: BLE001
        return f"ERROR: {exc}"


def _parse_json(body: str) -> dict:
    """Parse a JSON body, raising ValueError with a helpful message on failure."""
    try:
        return json.loads(body.strip())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Body must be valid JSON: {exc}") from exc


def _get_panel_flat() -> list[dict]:
    if _tool_panel_cache:
        return _tool_panel_cache[0]
    gi = _gi()
    flat: list[dict] = []
    for section in gi.tools.get_tool_panel():
        section_name = section.get("name", "")
        for t in section.get("elems", []):
            if t.get("model_class") == "Tool":
                flat.append({
                    "id": t.get("id", ""),
                    "name": t.get("name", ""),
                    "description": t.get("description") or "",
                    "section": section_name,
                })
    _tool_panel_cache.append(flat)
    return _tool_panel_cache[0]


# --------------------------------------------------------------------------- #
# Tool implementations
# --------------------------------------------------------------------------- #


def _galaxy_upload(body: str, *, workspace_path: Path | None = None, **_: Any) -> str:
    try:
        params = _parse_json(body)
    except ValueError as exc:
        return f"ERROR: {exc}"
    history_id = params.get("history_id", "")
    file_path = params.get("file_path", "")
    file_type = params.get("file_type", "auto")
    genome = params.get("dbkey", "?")

    if not history_id:
        return "ERROR: 'history_id' is required."
    if not file_path:
        return "ERROR: 'file_path' is required."

    if workspace_path:
        full_path = workspace_path / file_path
    else:
        full_path = Path(file_path)

    if not full_path.is_file():
        return f"ERROR: file not found: {full_path}"

    def _do():
        gi = _gi()
        return gi.tools.upload_file(
            str(full_path),
            history_id,
            file_type=file_type,
            dbkey=genome,
        )

    return _safe(_do)


def _galaxy_run_tool(body: str, **_: Any) -> str:
    try:
        params = _parse_json(body)
    except ValueError as exc:
        return f"ERROR: {exc}"

    history_id = params.get("history_id", "")
    tool_id = params.get("tool_id", "")
    inputs = params.get("inputs", {})

    if not history_id:
        return "ERROR: 'history_id' is required."
    if not tool_id:
        return "ERROR: 'tool_id' is required."

    def _do():
        gi = _gi()
        return gi.tools.run_tool(history_id, tool_id, inputs)

    return _safe(_do)


def _galaxy_invoke_workflow(body: str, **_: Any) -> str:
    try:
        params = _parse_json(body)
    except ValueError as exc:
        return f"ERROR: {exc}"

    workflow_id = params.get("workflow_id", "")
    history_id = params.get("history_id", "")
    inputs = params.get("inputs", {})
    params_extra = params.get("params", {})

    if not workflow_id:
        return "ERROR: 'workflow_id' is required."
    if not history_id:
        return "ERROR: 'history_id' is required."

    def _do():
        gi = _gi()
        return gi.workflows.invoke_workflow(
            workflow_id,
            inputs=inputs,
            history_id=history_id,
            params=params_extra or None,
        )

    return _safe(_do)


def _galaxy_job_status(body: str, **_: Any) -> str:
    try:
        params = _parse_json(body)
    except ValueError as exc:
        return f"ERROR: {exc}"

    def _do():
        gi = _gi()
        if "job_id" in params:
            return gi.jobs.show_job(params["job_id"], full_details=True)
        if "dataset_id" in params:
            return gi.datasets.show_dataset(params["dataset_id"])
        raise ValueError("Provide 'job_id' or 'dataset_id'.")

    return _safe(_do)


def _galaxy_wait_for_job(body: str, **_: Any) -> str:
    try:
        params = _parse_json(body)
    except ValueError as exc:
        return f"ERROR: {exc}"

    timeout = int(params.get("timeout", 300))
    poll_interval = 10
    deadline = time.time() + timeout

    job_id = params.get("job_id")
    dataset_id = params.get("dataset_id")

    if not job_id and not dataset_id:
        return "ERROR: Provide 'job_id' or 'dataset_id'."

    terminal = {"ok", "error", "deleted", "discarded", "paused"}

    try:
        gi = _gi()
    except RuntimeError as exc:
        return f"ERROR: {exc}"

    while time.time() < deadline:
        try:
            if job_id:
                info = gi.jobs.show_job(job_id)
                state = info.get("state", "unknown")
            else:
                info = gi.datasets.show_dataset(str(dataset_id))
                state = info.get("state", "unknown")
        except Exception as exc:  # noqa: BLE001
            return f"ERROR polling state: {exc}"

        if state in terminal:
            return json.dumps({"state": state, "details": info}, indent=2, default=str)

        time.sleep(poll_interval)

    return f"ERROR: Timed out after {timeout}s waiting for terminal state."


def _galaxy_download(body: str, *, workspace_path: Path | None = None, **_: Any) -> str:
    try:
        params = _parse_json(body)
    except ValueError as exc:
        return f"ERROR: {exc}"

    dataset_id = params.get("dataset_id", "")
    output_path = params.get("output_path", "")

    if not dataset_id:
        return "ERROR: 'dataset_id' is required."
    if not output_path:
        return "ERROR: 'output_path' is required."

    if workspace_path:
        dest = workspace_path / output_path
    else:
        dest = Path(output_path)

    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        gi = _gi()
        gi.datasets.download_dataset(
            dataset_id, file_path=str(dest), use_default_filename=False
        )
        return f"Downloaded dataset {dataset_id} → {dest} ({dest.stat().st_size} bytes)"
    except Exception as exc:  # noqa: BLE001
        return f"ERROR: {exc}"


def _galaxy_search_tools(body: str, **_: Any) -> str:
    raw = body.strip()
    # native tool_mode sends JSON: {"pattern": "bwa|bowtie2"}
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            raw = parsed.get("pattern") or parsed.get("query") or parsed.get("name") or raw
    except json.JSONDecodeError:
        pass

    if not raw:
        return "ERROR: Provide a regex pattern, e.g. 'bwa|bowtie2|hisat2'."
    try:
        rx = re.compile(raw, re.IGNORECASE)
    except re.error as exc:
        return f"ERROR: Invalid regex: {exc}"

    def _do():
        max_desc_len = 120
        return [
            {"id": t["id"], "name": t["name"], "description": t["description"][:max_desc_len], "section": t["section"]}
            for t in _get_panel_flat()
            if rx.search(t["name"]) or rx.search(t["description"])
        ][:_SEARCH_CAP]

    return _safe(_do, compact=True)


def _galaxy_show_tool(body: str, **_: Any) -> str:
    tool_id = body.strip()
    try:
        parsed = json.loads(tool_id)
        if isinstance(parsed, dict):
            tool_id = parsed.get("tool_id", "")
    except json.JSONDecodeError:
        pass

    if not tool_id:
        return "ERROR: Provide a tool_id string."

    def _do():
        gi = _gi()
        return gi.tools.show_tool(tool_id, io_details=True)

    return _safe(_do)


def _galaxy_create_history(body: str, **_: Any) -> str:
    name = body.strip() or "team-galaxy run"

    def _do():
        gi = _gi()
        h = gi.histories.create_history(name=name)
        return {"id": h.get("id"), "name": h.get("name")}

    return _safe(_do)


def _galaxy_get_histories(body: str, **_: Any) -> str:
    def _do():
        gi = _gi()
        histories = gi.histories.get_histories()
        simplified = [
            {
                "id": h.get("id"),
                "name": h.get("name"),
                "state": h.get("state"),
                "size": h.get("size"),
            }
            for h in (histories or [])
        ]
        return simplified[:20]

    return _safe(_do)


def _galaxy_show_dataset(body: str, **_: Any) -> str:
    try:
        params = _parse_json(body)
    except ValueError as exc:
        return f"ERROR: {exc}"

    dataset_id = params.get("dataset_id", "")
    history_id = params.get("history_id")

    if not dataset_id:
        return "ERROR: 'dataset_id' is required."

    def _do():
        gi = _gi()
        if history_id:
            return gi.histories.show_dataset(history_id, dataset_id)
        return gi.datasets.show_dataset(dataset_id)

    return _safe(_do)


# --------------------------------------------------------------------------- #
# Skill exports
# --------------------------------------------------------------------------- #

TOOLS = {
    "galaxy_upload": _galaxy_upload,
    "galaxy_run_tool": _galaxy_run_tool,
    "galaxy_invoke_workflow": _galaxy_invoke_workflow,
    "galaxy_job_status": _galaxy_job_status,
    "galaxy_wait_for_job": _galaxy_wait_for_job,
    "galaxy_download": _galaxy_download,
    "galaxy_search_tools": _galaxy_search_tools,
    "galaxy_show_tool": _galaxy_show_tool,
    "galaxy_create_history": _galaxy_create_history,
    "galaxy_get_histories": _galaxy_get_histories,
    "galaxy_show_dataset": _galaxy_show_dataset,
}

TOOL_DESCRIPTIONS = {
    "galaxy_upload": (
        "Upload a file from the shared workspace to a Galaxy history. "
        "Body: JSON with 'history_id', 'file_path' (relative to workspace), "
        "and optional 'file_type' (default: auto) and 'dbkey'."
    ),
    "galaxy_run_tool": (
        "Run a Galaxy tool and return job/dataset information. "
        "Body: JSON with 'history_id', 'tool_id', and 'inputs' dict."
    ),
    "galaxy_invoke_workflow": (
        "Invoke a Galaxy workflow. "
        "Body: JSON with 'workflow_id', 'history_id', and 'inputs' dict."
    ),
    "galaxy_job_status": (
        "Get the current state of a Galaxy job or dataset. "
        "Body: JSON with 'job_id' OR 'dataset_id'."
    ),
    "galaxy_wait_for_job": (
        "Block until a Galaxy job or dataset reaches a terminal state "
        "(ok / error / deleted). Polls every 10 s. "
        "Body: JSON with 'job_id' or 'dataset_id', and optional 'timeout' seconds (default 300)."
    ),
    "galaxy_download": (
        "Download a Galaxy dataset to the shared workspace. "
        "Body: JSON with 'dataset_id' and 'output_path' (relative to workspace)."
    ),
    "galaxy_search_tools": (
        "Search for tools on the Galaxy server using a regex pattern matched against "
        "tool id, name, and description. Body: regex string, e.g. 'bwa|bowtie2|hisat2'. "
        "Returns id, name, description, and section for each match. "
        "Call galaxy_show_tool next to see the input schema before running."
    ),
    "galaxy_show_tool": (
        "Return full metadata for a Galaxy tool, including its input and output parameter "
        "schema (use this to learn what 'inputs' dict to pass to galaxy_run_tool). "
        "Body: tool_id string."
    ),
    "galaxy_create_history": (
        "Create a new Galaxy history and return its ID. Body: history name string."
    ),
    "galaxy_get_histories": (
        "List the 20 most recent Galaxy histories. Body: ignored."
    ),
    "galaxy_show_dataset": (
        "Show metadata for a Galaxy dataset (name, state, file_size, genome_build, misc_info). "
        "Body: JSON with 'dataset_id' and optional 'history_id'."
    ),
}

INJECT_INTO_CONTEXT = """\
## Galaxy server access (BioBlend)

You have access to a Galaxy server via the BioBlend skill.  The server URL and
API key are set in the environment variables GALAXY_URL and GALAXY_API_KEY.

Use these tools to interact with Galaxy:
- galaxy_get_histories — list recent histories
- galaxy_create_history — create a new history; returns history_id
- galaxy_upload — upload a file from the workspace to a history
- galaxy_search_tools — find tools by regex pattern matched against id, name, description
- galaxy_show_tool — get a tool's full input/output schema by tool_id
- galaxy_run_tool — execute a tool; returns job and dataset IDs
- galaxy_invoke_workflow — run a workflow
- galaxy_job_status — check job/dataset state
- galaxy_wait_for_job — block until a job completes (use before downloading)
- galaxy_download — download a result dataset to the workspace
- galaxy_show_dataset — inspect dataset metadata

Typical flow:
1. Create or identify a history (galaxy_create_history / galaxy_get_histories)
2. Upload input files (galaxy_upload)
3. Find the tool: galaxy_search_tools with a regex like 'bwa|bowtie2' — returns tool_id
4. Inspect its inputs: galaxy_show_tool — learn the exact parameter names and types
5. Run the tool: galaxy_run_tool with the correct inputs dict
6. Wait for completion: galaxy_wait_for_job
7. Download results: galaxy_download

Never call galaxy_run_tool without first calling galaxy_show_tool — the inputs
dict is tool-specific and cannot be guessed without seeing the schema.
"""
