"""compose git/pkg/deps intel into one dict, and export it as json."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from pathivu.deps import build_deps_tree
from pathivu.git import scoop_git_intel
from pathivu.pkg import scoop_package_intel


def describe(
    app_name: str,
    description: str | None = None,
    pyproject_path: str | Path = "pyproject.toml",
    exclude_transitive: set[str] | None = None,
) -> dict:
    """gather all intel sources into a single dict.

    missing pieces (no git, no pyproject) are omitted, never fatal.
    """
    intel: dict = {
        "about": {
            "app_name": app_name,
            "description": description or f"..and {app_name} is my name",
        },
        "git": scoop_git_intel(),
        "described_at": _utcnow_iso(),
    }
    pkg = scoop_package_intel(pyproject_path)
    if pkg:
        intel["pkg"] = pkg
    deps = build_deps_tree(pyproject_path, exclude_transitive)
    if deps:
        intel["deps"] = deps
    return intel


def export_intel(
    intel: dict,
    app_name: str,
    out_path: str | Path | None = None,
) -> dict:
    """write intel as pretty-printed json.

    default path is src/<importable_name>/_about.json (src-layout).
    pass out_path for flat layouts or custom locations.
    """
    path = Path(out_path) if out_path else _default_out_path(app_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(intel, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return {"intel_exported_to": str(path)}


def _default_out_path(app_name: str) -> Path:
    """normalize app-name to an importable package name, then src/<name>/_about.json."""
    pkg = app_name.replace("-", "_").replace(".", "_")
    return Path("src") / pkg / "_about.json"


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
