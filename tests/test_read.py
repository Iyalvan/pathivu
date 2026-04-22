"""tests for pathivu.read."""

from __future__ import annotations

import sys

import pytest

from pathivu.read import read_about


def _make_pkg(tmp_path, name, about_content):
    """create a fake installable package with an _about.json resource."""
    pkg_dir = tmp_path / name
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    if about_content is not None:
        (pkg_dir / "_about.json").write_text(about_content)
    return pkg_dir


def _cleanup(name):
    """evict the fake package from sys.modules so subsequent tests re-import."""
    sys.modules.pop(name, None)


def test_read_about_loads_json(tmp_path, monkeypatch):
    _make_pkg(tmp_path, "pathivu_fake_a", '{"about": {"app_name": "fake"}, "n": 1}')
    monkeypatch.syspath_prepend(str(tmp_path))
    try:
        assert read_about("pathivu_fake_a") == {"about": {"app_name": "fake"}, "n": 1}
    finally:
        _cleanup("pathivu_fake_a")


def test_read_about_missing_raises(tmp_path, monkeypatch):
    _make_pkg(tmp_path, "pathivu_fake_b", about_content=None)  # no _about.json
    monkeypatch.syspath_prepend(str(tmp_path))
    try:
        with pytest.raises(FileNotFoundError):
            read_about("pathivu_fake_b")
    finally:
        _cleanup("pathivu_fake_b")


def test_read_about_custom_resource_name(tmp_path, monkeypatch):
    pkg_dir = _make_pkg(tmp_path, "pathivu_fake_c", about_content=None)
    (pkg_dir / "meta.json").write_text('{"k": "v"}')
    monkeypatch.syspath_prepend(str(tmp_path))
    try:
        assert read_about("pathivu_fake_c", resource="meta.json") == {"k": "v"}
    finally:
        _cleanup("pathivu_fake_c")


def test_read_about_nonexistent_package_raises(monkeypatch):
    with pytest.raises((ModuleNotFoundError, FileNotFoundError)):
        read_about("package_that_definitely_does_not_exist_xyzzy")
