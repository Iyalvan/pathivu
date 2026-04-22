"""fastapi adapter: a router that serves /about from the package's _about.json."""

from __future__ import annotations

try:
    from fastapi import APIRouter
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "fastapi is not installed. install with `pip install pathivu[fastapi]`"
    ) from e

from pathivu.read import read_about


def about_router(pkg: str, path: str = "/about") -> APIRouter:
    """return an APIRouter exposing pkg's _about.json at `path`."""
    router = APIRouter()

    @router.get(path)
    def _about():
        return read_about(pkg)

    return router
