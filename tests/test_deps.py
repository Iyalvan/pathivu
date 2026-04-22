"""tests for pathivu.deps."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

import pytest

from pathivu.deps import build_deps_tree


def _pyproject(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "pyproject.toml"
    path.write_text(dedent(body).lstrip())
    return path


# ---- missing / empty inputs ------------------------------------------------

def test_missing_pyproject_returns_empty(tmp_path):
    assert build_deps_tree(tmp_path / "nope.toml") == {}


def test_empty_dependencies_returns_empty(tmp_path):
    path = _pyproject(tmp_path, """
        [project]
        name = "x"
    """)
    assert build_deps_tree(path) == {}


def test_invalid_toml_returns_empty(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text("not [ valid = toml")
    assert build_deps_tree(path) == {}


# ---- real installed packages -----------------------------------------------

def test_real_installed_dep_has_version_and_children(tmp_path):
    # pytest is installed in the test env and has its own requires
    path = _pyproject(tmp_path, """
        [project]
        name = "x"
        dependencies = ["pytest"]
    """)
    tree = build_deps_tree(path)
    assert "pytest" in tree
    assert tree["pytest"]["version"]  # non-empty version string
    assert isinstance(tree["pytest"].get("depends_on"), dict)
    assert len(tree["pytest"]["depends_on"]) > 0


def test_not_installed_dep_is_marked(tmp_path):
    path = _pyproject(tmp_path, """
        [project]
        name = "x"
        dependencies = ["definitely-not-a-real-package-xyzzy-42"]
    """)
    tree = build_deps_tree(path)
    node = tree["definitely-not-a-real-package-xyzzy-42"]
    assert node["not_installed"] is True
    assert node["version"] == "unknown"


def test_exclude_transitive_collapses_subtree(tmp_path):
    path = _pyproject(tmp_path, """
        [project]
        name = "x"
        dependencies = ["pytest"]
    """)
    tree = build_deps_tree(path, exclude_transitive={"pytest"})
    assert tree["pytest"]["depends_on"] == "..."


# ---- markers ---------------------------------------------------------------

def test_marker_false_excludes_dep(tmp_path):
    path = _pyproject(tmp_path, """
        [project]
        name = "x"
        dependencies = ["pytest ; python_version < '3.0'"]
    """)
    assert build_deps_tree(path) == {}


def test_marker_true_keeps_dep(tmp_path):
    path = _pyproject(tmp_path, """
        [project]
        name = "x"
        dependencies = ["pytest ; python_version >= '3.0'"]
    """)
    assert "pytest" in build_deps_tree(path)


def test_invalid_requirement_is_skipped(tmp_path, capsys):
    path = _pyproject(tmp_path, """
        [project]
        name = "x"
        dependencies = ["this is not @@ valid"]
    """)
    assert build_deps_tree(path) == {}
    assert "unparseable" in capsys.readouterr().err


# ---- cycle detection via fake metadata -------------------------------------

@dataclass
class _FakeDist:
    version: str
    requires: list[str]


def _install_fake_registry(monkeypatch, dists: dict[str, _FakeDist]):
    """swap out metadata.distribution with a lookup over fake dists."""
    from importlib import metadata

    def fake(name: str):
        key = name.lower().replace("_", "-")
        if key in dists:
            return dists[key]
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr("pathivu.deps.metadata.distribution", fake)


def test_cycle_between_two_deps_is_terminated(tmp_path, monkeypatch):
    _install_fake_registry(monkeypatch, {
        "a": _FakeDist("1.0", ["b"]),
        "b": _FakeDist("2.0", ["a"]),
    })
    path = _pyproject(tmp_path, """
        [project]
        name = "x"
        dependencies = ["a"]
    """)
    tree = build_deps_tree(path)
    assert tree["a"]["version"] == "1.0"
    assert tree["a"]["depends_on"]["b"]["version"] == "2.0"
    # b -> a closes the cycle
    assert tree["a"]["depends_on"]["b"]["depends_on"]["a"] == {"version": "...", "cycle": True}


def test_self_cycle_is_terminated(tmp_path, monkeypatch):
    _install_fake_registry(monkeypatch, {
        "self": _FakeDist("1.0", ["self"]),
    })
    path = _pyproject(tmp_path, """
        [project]
        name = "x"
        dependencies = ["self"]
    """)
    tree = build_deps_tree(path)
    assert tree["self"]["depends_on"]["self"] == {"version": "...", "cycle": True}


def test_diamond_no_false_cycle(tmp_path, monkeypatch):
    # a -> b, a -> c, b -> d, c -> d. d appears twice but is NOT a cycle.
    _install_fake_registry(monkeypatch, {
        "a": _FakeDist("1.0", ["b", "c"]),
        "b": _FakeDist("1.0", ["d"]),
        "c": _FakeDist("1.0", ["d"]),
        "d": _FakeDist("1.0", []),
    })
    path = _pyproject(tmp_path, """
        [project]
        name = "x"
        dependencies = ["a"]
    """)
    tree = build_deps_tree(path)
    # both paths to d should resolve normally with no cycle flag
    assert tree["a"]["depends_on"]["b"]["depends_on"]["d"] == {"version": "1.0"}
    assert tree["a"]["depends_on"]["c"]["depends_on"]["d"] == {"version": "1.0"}


# ---- name canonicalization --------------------------------------------------

def test_dep_name_is_canonicalized(tmp_path, monkeypatch):
    _install_fake_registry(monkeypatch, {
        "my-lib": _FakeDist("1.0", []),
    })
    path = _pyproject(tmp_path, """
        [project]
        name = "x"
        dependencies = ["My_Lib"]
    """)
    tree = build_deps_tree(path)
    # underscore + case folded
    assert "my-lib" in tree
