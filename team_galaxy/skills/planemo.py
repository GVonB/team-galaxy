"""Planemo skill — lint, test, and update Galaxy tool XML and workflow files.

Requires ``planemo`` to be installed and on PATH::

    pip install planemo

Available tools
---------------
``planemo_lint``
    Lint a Galaxy tool XML file and report all warnings and errors.

    Body: relative path to the ``.xml`` file (from workspace root).

``planemo_test``
    Run the embedded ``<tests>`` blocks for a Galaxy tool.
    Planemo pulls the required conda dependencies automatically.

    Body: relative path to the ``.xml`` file, optionally followed by extra
    planemo flags on the same line::

        my_tool.xml --no_cleanup --test_output=/tmp/report.html

``planemo_workflow_lint``
    Lint a Galaxy workflow (``.ga``) file for structural and metadata issues.

    Body: relative path to the ``.ga`` file.

``planemo_workflow_test``
    Run the workflow test suite (requires a ``*-tests.yml`` companion file).

    Body: relative path to the ``.ga`` file, optionally followed by extra
    planemo flags::

        my_workflow.ga --galaxy_url https://usegalaxy.org --galaxy_api_key <key>

``planemo_autoupdate``
    Update tool requirement versions to the latest available on bioconda/conda-forge.
    Also works on ``.ga`` workflow files to update pinned tool versions.

    Body: relative path to the ``.xml`` or ``.ga`` file.

``planemo_shed_lint``
    Lint a Tool Shed repository structure (checks ``.shed.yml``, README, etc.).

    Body: relative path to the repository directory (default: workspace root).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

_MAX_OUTPUT = 8192


def _planemo_available() -> bool:
    return shutil.which("planemo") is not None


def _run_planemo(
    args: list[str],
    cwd: Path,
    timeout: int = 300,
) -> str:
    """Run planemo with *args* in *cwd* and return combined stdout+stderr."""
    if not _planemo_available():
        return (
            "ERROR: planemo is not installed or not on PATH.  "
            "Install it with: pip install planemo"
        )

    cmd = ["planemo"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(cwd),
            timeout=timeout,
        )
        output = (result.stdout + result.stderr).strip()
    except subprocess.TimeoutExpired:
        return f"ERROR: planemo timed out after {timeout}s."
    except Exception as exc:  # noqa: BLE001
        return f"ERROR running planemo: {exc}"

    if len(output) > _MAX_OUTPUT:
        output = output[:_MAX_OUTPUT] + f"\n... [truncated at {_MAX_OUTPUT} chars]"

    exit_label = "✓ (exit 0)" if result.returncode == 0 else f"✗ (exit {result.returncode})"
    return f"{exit_label}\n\n{output}" if output else exit_label


def _resolve_path(body_token: str, workspace_path: Path | None) -> tuple[str, list[str]]:
    """Split the body into (target_path, extra_flags).

    The first token is treated as the file/dir path; the rest are planemo flags.
    Returns the path as a string relative to workspace_path (if given) and the
    remaining tokens as a list of extra flags.
    """
    parts = body_token.strip().split()
    if not parts:
        return "", []
    return parts[0], parts[1:]


# --------------------------------------------------------------------------- #
# Tool implementations
# --------------------------------------------------------------------------- #


def _planemo_lint(body: str, *, workspace_path: Path | None = None, **_: Any) -> str:
    target, extra = _resolve_path(body, workspace_path)
    if not target:
        return "ERROR: Provide the path to a Galaxy tool XML file."

    cwd = workspace_path or Path(".")
    return _run_planemo(["lint"] + extra + [target], cwd=cwd)


def _planemo_test(body: str, *, workspace_path: Path | None = None, **_: Any) -> str:
    target, extra = _resolve_path(body, workspace_path)
    if not target:
        return "ERROR: Provide the path to a Galaxy tool XML file."

    cwd = workspace_path or Path(".")
    # Default timeout for tests is longer (10 min) to allow conda env setup.
    return _run_planemo(["test"] + extra + [target], cwd=cwd, timeout=600)


def _planemo_workflow_lint(
    body: str, *, workspace_path: Path | None = None, **_: Any
) -> str:
    target, extra = _resolve_path(body, workspace_path)
    if not target:
        return "ERROR: Provide the path to a Galaxy workflow .ga file."

    cwd = workspace_path or Path(".")
    return _run_planemo(["workflow_lint"] + extra + [target], cwd=cwd)


def _planemo_workflow_test(
    body: str, *, workspace_path: Path | None = None, **_: Any
) -> str:
    target, extra = _resolve_path(body, workspace_path)
    if not target:
        return "ERROR: Provide the path to a Galaxy workflow .ga file."

    cwd = workspace_path or Path(".")
    return _run_planemo(["workflow_test"] + extra + [target], cwd=cwd, timeout=1200)


def _planemo_autoupdate(
    body: str, *, workspace_path: Path | None = None, **_: Any
) -> str:
    target, extra = _resolve_path(body, workspace_path)
    if not target:
        return "ERROR: Provide the path to a .xml or .ga file."

    cwd = workspace_path or Path(".")
    return _run_planemo(["autoupdate"] + extra + [target], cwd=cwd)


def _planemo_shed_lint(
    body: str, *, workspace_path: Path | None = None, **_: Any
) -> str:
    target, extra = _resolve_path(body, workspace_path)
    # Default to workspace root if no target given.
    cwd = workspace_path or Path(".")
    target = target or "."
    return _run_planemo(["shed_lint", "--recursive"] + extra + [target], cwd=cwd)


# --------------------------------------------------------------------------- #
# Skill exports
# --------------------------------------------------------------------------- #

TOOLS = {
    "planemo_lint": _planemo_lint,
    "planemo_test": _planemo_test,
    "planemo_workflow_lint": _planemo_workflow_lint,
    "planemo_workflow_test": _planemo_workflow_test,
    "planemo_autoupdate": _planemo_autoupdate,
    "planemo_shed_lint": _planemo_shed_lint,
}

TOOL_DESCRIPTIONS = {
    "planemo_lint": (
        "Lint a Galaxy tool XML file with planemo and report all warnings and errors. "
        "Body: relative path to the .xml file (optionally followed by extra planemo flags)."
    ),
    "planemo_test": (
        "Run the <tests> blocks for a Galaxy tool using planemo (pulls conda deps automatically). "
        "Body: relative path to the .xml file (optionally followed by extra planemo flags)."
    ),
    "planemo_workflow_lint": (
        "Lint a Galaxy workflow .ga file for structural and metadata issues. "
        "Body: relative path to the .ga file."
    ),
    "planemo_workflow_test": (
        "Run the workflow test suite against a Galaxy server. "
        "Body: relative path to the .ga file, optionally followed by "
        "--galaxy_url and --galaxy_api_key flags."
    ),
    "planemo_autoupdate": (
        "Update tool requirement versions to the latest available on bioconda/conda-forge. "
        "Body: relative path to the .xml or .ga file."
    ),
    "planemo_shed_lint": (
        "Lint a Tool Shed repository structure (.shed.yml, README, dependencies). "
        "Body: relative path to the repository directory (default: workspace root)."
    ),
}

INJECT_INTO_CONTEXT = """\
## planemo — Galaxy tool and workflow validation

You have access to planemo for linting, testing, and updating Galaxy artifacts:
- `planemo_lint <tool.xml>` — check a tool XML file for errors and IUC violations
- `planemo_test <tool.xml>` — run the embedded <tests> blocks
- `planemo_workflow_lint <workflow.ga>` — check workflow structure and metadata
- `planemo_workflow_test <workflow.ga>` — run workflow tests against a Galaxy server
- `planemo_autoupdate <file>` — update pinned conda requirement versions
- `planemo_shed_lint` — lint a Tool Shed repository structure

All paths are relative to the shared workspace root.
planemo_lint exit 0 = no errors; non-zero = problems found (read the output carefully).
"""
