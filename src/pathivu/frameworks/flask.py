"""flask adapter: a blueprint that serves /about from the package's _about.json."""

from __future__ import annotations

try:
    from flask import Blueprint, jsonify
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "flask is not installed. install with `pip install pathivu[flask]`"
    ) from e

from pathivu.read import read_about


def about_blueprint(
    pkg: str,
    path: str = "/about",
    name: str = "pathivu_about",
) -> Blueprint:
    """return a blueprint with a single GET `path` returning pkg's _about.json."""
    bp = Blueprint(name, __name__)

    @bp.get(path)
    def _about():
        return jsonify(read_about(pkg))

    return bp
