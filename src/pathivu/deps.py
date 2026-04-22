"""build a resolved dependency tree by walking installed metadata, starting
from the project's declared dependencies in pyproject.toml.
"""

from __future__ import annotations

import sys
import tomllib
from importlib import metadata
from pathlib import Path

from packaging.requirements import InvalidRequirement, Requirement


def build_deps_tree(
    pyproject_path: str | Path = "pyproject.toml",
    exclude_transitive: set[str] | None = None,
) -> dict:
    """return a nested dict of direct + transitive deps with resolved versions.

    shape: {name: {"version": "...", "depends_on": {name: {...}}}}
      - cycles terminate with {"version": "...", "cycle": True}
      - transitive roots listed in exclude_transitive get depends_on = "..."
      - declared deps not installed get {"version": "unknown", "not_installed": True}

    returns {} if pyproject.toml is missing, unreadable, or has no dependencies.
    """
    path = Path(pyproject_path)
    if not path.exists():
        return {}
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return {}

    declared = (data.get("project") or {}).get("dependencies") or []
    excluded = {_canon(x) for x in (exclude_transitive or set())}

    tree: dict = {}
    for req_str in declared:
        req = _parse(req_str)
        if req is None:
            continue
        # top-level deps have no "extra" context; skip if marker fails
        if req.marker and not req.marker.evaluate({"extra": ""}):
            continue
        tree[_canon(req.name)] = _build_node(
            req.name, frozenset(req.extras), set(), excluded
        )
    return tree


def _build_node(
    name: str,
    active_extras: frozenset[str],
    seen: set[str],
    excluded: set[str],
) -> dict:
    canon = _canon(name)
    if canon in seen:
        return {"version": "...", "cycle": True}
    seen = seen | {canon}

    try:
        dist = metadata.distribution(name)
    except metadata.PackageNotFoundError:
        return {"version": "unknown", "not_installed": True}

    node: dict = {"version": dist.version}

    if canon in excluded:
        node["depends_on"] = "..."
        return node

    children: dict = {}
    for req_str in (dist.requires or []):
        req = _parse(req_str)
        if req is None:
            continue
        if not _marker_active(req, active_extras):
            continue
        children[_canon(req.name)] = _build_node(
            req.name, frozenset(req.extras), seen, excluded
        )
    if children:
        node["depends_on"] = children
    return node


def _parse(req_str: str) -> Requirement | None:
    try:
        return Requirement(req_str)
    except InvalidRequirement as e:
        print(f"(!) skipping unparseable requirement {req_str!r}: {e}", file=sys.stderr)
        return None


def _marker_active(req: Requirement, active_extras: frozenset[str]) -> bool:
    """True if req's marker is satisfied under current env + any active extra."""
    if not req.marker:
        return True
    if req.marker.evaluate({"extra": ""}):
        return True
    return any(req.marker.evaluate({"extra": e}) for e in active_extras)


def _canon(name: str) -> str:
    """pep 503 style canonicalization (case/underscore/dot folding)."""
    return name.lower().replace("_", "-").replace(".", "-")
