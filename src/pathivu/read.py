"""read the _about.json baked into a package at build time."""

from __future__ import annotations

import json
from importlib.resources import files


def read_about(pkg: str, resource: str = "_about.json") -> dict:
    """load and return the about dict from pkg's embedded json resource.

    raises FileNotFoundError if the resource is missing — callers can decide
    whether to degrade gracefully (recommended for /about endpoints).
    """
    ref = files(pkg).joinpath(resource)
    if not ref.is_file():
        raise FileNotFoundError(f"{resource} not found in package {pkg!r}")
    return json.loads(ref.read_text(encoding="utf-8"))
