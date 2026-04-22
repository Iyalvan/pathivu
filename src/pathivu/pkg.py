"""scoop package metadata from pyproject.toml (pep 621)."""

from __future__ import annotations

import sys
import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def scoop_package_intel(pyproject_path: str | Path = "pyproject.toml") -> dict | None:
    """read the [project] table and return selected fields.

    returns None if the file is missing, unreadable, or lacks [project] —
    pathivu should skip the pkg section rather than fail the build.

    if version is declared dynamic, tries importlib.metadata to resolve it.
    """
    path = Path(pyproject_path)
    if not path.exists():
        print(f"(!) no {path} found, skipping pkg intel", file=sys.stderr)
        return None

    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        print(f"(!) could not parse {path}: {e}", file=sys.stderr)
        return None

    project = data.get("project")
    if not project:
        print(f"(!) no [project] table in {path}, skipping pkg intel", file=sys.stderr)
        return None

    intel: dict = {}

    name = project.get("name")
    if name:
        intel["name"] = name

    ver = project.get("version") or _resolve_dynamic_version(project, name)
    if ver:
        intel["version"] = ver

    description = project.get("description")
    if description:
        intel["description"] = description

    urls = project.get("urls")
    if urls:
        intel["urls"] = dict(urls)

    authors = project.get("authors")
    if authors:
        # keep only name/email on each entry, drop empties
        intel["authors"] = [
            {k: v for k, v in a.items() if k in ("name", "email") and v}
            for a in authors
        ]

    return intel or None


def _resolve_dynamic_version(project: dict, name: str | None) -> str | None:
    """if version is declared dynamic, try to resolve it via installed metadata."""
    dynamic = project.get("dynamic") or []
    if "version" not in dynamic or not name:
        return None
    try:
        return version(name)
    except PackageNotFoundError:
        return None
