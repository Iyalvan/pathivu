"""tests for pathivu.core — end-to-end composition + export."""

from __future__ import annotations

import json
import re
from pathlib import Path
from textwrap import dedent

from pathivu.core import describe, export_intel


def _write_pyproject(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "pyproject.toml"
    path.write_text(dedent(body).lstrip())
    return path


def test_describe_in_tagged_repo_has_all_sections(tagged_repo, tmp_path):
    _write_pyproject(tagged_repo, """
        [project]
        name = "sample"
        version = "1.2.3"
        description = "sample pkg"
        dependencies = ["pytest"]
    """)
    intel = describe("sample", "I do things")
    assert intel["about"] == {"app_name": "sample", "description": "I do things"}
    assert set(intel["git"]) >= {"commit_id", "branch", "author"}
    assert intel["pkg"]["name"] == "sample"
    assert "pytest" in intel["deps"]
    # iso-8601 utc timestamp
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$", intel["described_at"])


def test_describe_without_pyproject_omits_pkg_and_deps(tagged_repo):
    # tagged_repo has no pyproject.toml
    intel = describe("sample")
    assert "pkg" not in intel
    assert "deps" not in intel
    assert "git" in intel  # git still works


def test_describe_default_description(tagged_repo):
    intel = describe("sample")
    assert intel["about"]["description"] == "..and sample is my name"


def test_describe_outside_git_repo_has_empty_git(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    intel = describe("sample")
    assert intel["git"] == {}
    assert intel["about"]["app_name"] == "sample"


def test_export_writes_json_to_default_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    intel = {"about": {"app_name": "my-api"}, "foo": 42}
    result = export_intel(intel, "my-api")
    expected = Path("src") / "my_api" / "_about.json"
    assert result == {"intel_exported_to": str(expected)}
    assert expected.exists()
    assert json.loads(expected.read_text()) == intel


def test_export_respects_custom_out_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "custom" / "here.json"
    result = export_intel({"x": 1}, "my-api", out_path=target)
    assert result == {"intel_exported_to": str(target)}
    assert json.loads(target.read_text()) == {"x": 1}


def test_export_creates_missing_parent_dirs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    export_intel({"x": 1}, "pkg-with-dashes")
    assert (tmp_path / "src" / "pkg_with_dashes" / "_about.json").exists()


def test_end_to_end_describe_then_export(tagged_repo, monkeypatch):
    _write_pyproject(tagged_repo, """
        [project]
        name = "sample"
        version = "1.0.0"
    """)
    intel = describe("sample", "desc")
    result = export_intel(intel, "sample")
    out = Path(result["intel_exported_to"])
    # round-trips as valid json
    loaded = json.loads(out.read_text())
    assert loaded["about"]["app_name"] == "sample"
    assert loaded["pkg"]["name"] == "sample"


def test_describe_honors_exclude_transitive(tagged_repo):
    _write_pyproject(tagged_repo, """
        [project]
        name = "sample"
        dependencies = ["pytest"]
    """)
    intel = describe("sample", exclude_transitive={"pytest"})
    assert intel["deps"]["pytest"]["depends_on"] == "..."
