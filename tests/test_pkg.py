"""tests for pathivu.pkg."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from pathivu.pkg import scoop_package_intel


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "pyproject.toml"
    path.write_text(dedent(body).lstrip())
    return path


def test_full_pyproject(tmp_path):
    path = _write(tmp_path, """
        [project]
        name = "sample"
        version = "1.2.3"
        description = "a sample pkg"
        authors = [{ name = "Alice", email = "a@x.com" }, { name = "Bob" }]

        [project.urls]
        Homepage = "https://example.com"
        Repository = "https://example.com/repo"
    """)
    intel = scoop_package_intel(path)
    assert intel == {
        "name": "sample",
        "version": "1.2.3",
        "description": "a sample pkg",
        "urls": {"Homepage": "https://example.com", "Repository": "https://example.com/repo"},
        "authors": [{"name": "Alice", "email": "a@x.com"}, {"name": "Bob"}],
    }


def test_minimal_pyproject_just_name(tmp_path):
    path = _write(tmp_path, """
        [project]
        name = "minimal"
    """)
    assert scoop_package_intel(path) == {"name": "minimal"}


def test_missing_file_returns_none(tmp_path, capsys):
    result = scoop_package_intel(tmp_path / "does-not-exist.toml")
    assert result is None
    assert "no" in capsys.readouterr().err.lower()


def test_no_project_table_returns_none(tmp_path, capsys):
    path = _write(tmp_path, """
        [build-system]
        requires = ["hatchling"]
    """)
    assert scoop_package_intel(path) is None
    assert "[project]" in capsys.readouterr().err


def test_invalid_toml_returns_none(tmp_path, capsys):
    path = tmp_path / "pyproject.toml"
    path.write_text("this is [ not valid = toml")
    assert scoop_package_intel(path) is None
    assert "could not parse" in capsys.readouterr().err


def test_dynamic_version_resolved_via_installed_metadata(tmp_path):
    # 'pytest' is definitely installed in the test env
    path = _write(tmp_path, """
        [project]
        name = "pytest"
        dynamic = ["version"]
    """)
    intel = scoop_package_intel(path)
    assert intel is not None
    assert "version" in intel
    assert intel["version"]  # some non-empty version string


def test_dynamic_version_unresolvable_is_omitted(tmp_path):
    path = _write(tmp_path, """
        [project]
        name = "definitely-not-a-real-package-xyzzy-42"
        dynamic = ["version"]
    """)
    intel = scoop_package_intel(path)
    assert intel is not None
    assert "version" not in intel
    assert intel["name"] == "definitely-not-a-real-package-xyzzy-42"


def test_defaults_to_cwd_pyproject(monkeypatch, tmp_path):
    _write(tmp_path, """
        [project]
        name = "cwd-test"
        version = "0.0.1"
    """)
    monkeypatch.chdir(tmp_path)
    assert scoop_package_intel() == {"name": "cwd-test", "version": "0.0.1"}


def test_authors_filters_empty_and_unknown_keys(tmp_path):
    path = _write(tmp_path, """
        [project]
        name = "a"
        authors = [{ name = "X", email = "" }, { name = "", email = "y@z" }]
    """)
    intel = scoop_package_intel(path)
    # empty values dropped; each entry keeps only populated name/email
    assert intel["authors"] == [{"name": "X"}, {"email": "y@z"}]
