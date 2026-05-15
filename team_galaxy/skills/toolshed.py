"""Tool Shed skill — search and inspect Galaxy Tool Shed repositories.

Uses the Tool Shed public REST API (no authentication required for read operations).
Default Tool Shed: https://toolshed.g2.bx.psu.edu

Available tools
---------------
``toolshed_search``
    Search for tools by name or keyword.

    Body: plain-text search query string.  Optionally prefix with a Tool Shed
    URL to search a different instance::

        https://toolshed.g2.bx.psu.edu samtools

``toolshed_tool_info``
    Fetch detailed metadata for a specific Tool Shed repository.

    Body (one of)::

        <owner>/<name>                                  -- uses default shed
        https://toolshed.g2.bx.psu.edu <owner>/<name>  -- explicit shed URL

``toolshed_categories``
    List all Tool Shed categories.

    Body: optional Tool Shed URL (default: toolshed.g2.bx.psu.edu).

``toolshed_owner_repos``
    List all repositories owned by a specific Tool Shed user.

    Body::

        <owner>
        https://toolshed.g2.bx.psu.edu <owner>   -- explicit shed URL
"""

from __future__ import annotations

import json
import logging
from typing import Any

import requests

log = logging.getLogger(__name__)

_DEFAULT_SHED = "https://toolshed.g2.bx.psu.edu"
_MAX_OUTPUT = 4096
_TIMEOUT = 30


def _get(url: str) -> Any:
    resp = requests.get(url, timeout=_TIMEOUT, headers={"Accept": "application/json"})
    resp.raise_for_status()
    return resp.json()


def _trim(data: Any) -> str:
    out = json.dumps(data, indent=2, default=str)
    if len(out) > _MAX_OUTPUT:
        out = out[:_MAX_OUTPUT] + f"\n... [truncated at {_MAX_OUTPUT} chars]"
    return out


def _parse_shed_and_rest(body: str) -> tuple[str, str]:
    """Extract (shed_url, rest) from a body that may start with an https:// URL."""
    parts = body.strip().split(None, 1)
    if parts and (parts[0].startswith("http://") or parts[0].startswith("https://")):
        shed = parts[0].rstrip("/")
        rest = parts[1].strip() if len(parts) > 1 else ""
    else:
        shed = _DEFAULT_SHED
        rest = body.strip()
    return shed, rest


# --------------------------------------------------------------------------- #
# Tool implementations
# --------------------------------------------------------------------------- #


def _toolshed_search(body: str, **_: Any) -> str:
    shed, query = _parse_shed_and_rest(body)
    if not query:
        return "ERROR: Provide a search query string."

    url = f"{shed}/api/repositories?q={requests.utils.quote(query)}"
    try:
        data = _get(url)
    except Exception as exc:  # noqa: BLE001
        return f"ERROR: {exc}"

    if not data:
        return f"No Tool Shed repositories found matching {query!r}."

    simplified = [
        {
            "id": r.get("id"),
            "owner": r.get("owner"),
            "name": r.get("name"),
            "description": r.get("description", ""),
            "type": r.get("type"),
        }
        for r in (data if isinstance(data, list) else data.get("hits", []))
    ]
    return _trim(simplified[:30])


def _toolshed_tool_info(body: str, **_: Any) -> str:
    shed, ref = _parse_shed_and_rest(body)
    if not ref:
        return "ERROR: Provide '<owner>/<name>'."

    parts = ref.strip("/").split("/")
    if len(parts) < 2:
        return "ERROR: Provide '<owner>/<name>'."

    owner, name = parts[0], parts[1]
    url = f"{shed}/api/repositories/get_repository_revision_install_info?name={name}&owner={owner}"
    try:
        data = _get(url)
    except Exception as exc:  # noqa: BLE001
        return f"ERROR: {exc}"

    return _trim(data)


def _toolshed_categories(body: str, **_: Any) -> str:
    shed, _ = _parse_shed_and_rest(body)
    url = f"{shed}/api/categories"
    try:
        data = _get(url)
    except Exception as exc:  # noqa: BLE001
        return f"ERROR: {exc}"

    simplified = [
        {"id": c.get("id"), "name": c.get("name"), "description": c.get("description", "")}
        for c in (data if isinstance(data, list) else [])
    ]
    return _trim(simplified)


def _toolshed_owner_repos(body: str, **_: Any) -> str:
    shed, owner = _parse_shed_and_rest(body)
    if not owner:
        return "ERROR: Provide an owner username."

    url = f"{shed}/api/repositories?owner={requests.utils.quote(owner)}"
    try:
        data = _get(url)
    except Exception as exc:  # noqa: BLE001
        return f"ERROR: {exc}"

    simplified = [
        {
            "name": r.get("name"),
            "description": r.get("description", ""),
            "type": r.get("type"),
        }
        for r in (data if isinstance(data, list) else [])
    ]
    return _trim(simplified)


# --------------------------------------------------------------------------- #
# Skill exports
# --------------------------------------------------------------------------- #

TOOLS = {
    "toolshed_search": _toolshed_search,
    "toolshed_tool_info": _toolshed_tool_info,
    "toolshed_categories": _toolshed_categories,
    "toolshed_owner_repos": _toolshed_owner_repos,
}

TOOL_DESCRIPTIONS = {
    "toolshed_search": (
        "Search the Galaxy Tool Shed for repositories by name or keyword. "
        "Body: search query string.  Optionally prefix with a Tool Shed URL "
        "to search a different instance."
    ),
    "toolshed_tool_info": (
        "Fetch metadata and install info for a specific Tool Shed repository. "
        "Body: '<owner>/<name>' (optionally prefixed with a Tool Shed URL)."
    ),
    "toolshed_categories": (
        "List all categories in the Tool Shed. "
        "Body: optional Tool Shed URL (default: toolshed.g2.bx.psu.edu)."
    ),
    "toolshed_owner_repos": (
        "List all repositories owned by a specific Tool Shed user. "
        "Body: owner username (optionally prefixed with a Tool Shed URL)."
    ),
}

INJECT_INTO_CONTEXT = """\
## Galaxy Tool Shed

You can query the Galaxy Tool Shed (default: https://toolshed.g2.bx.psu.edu):
- `toolshed_search <query>` — find repositories by name or keyword
- `toolshed_tool_info <owner>/<name>` — get metadata and install info
- `toolshed_categories` — list all Tool Shed categories
- `toolshed_owner_repos <owner>` — list all repos owned by a user

Prefix any body with a different Tool Shed URL to search that instance instead.
"""
