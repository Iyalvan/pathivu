"""smoke tests for the pathivu CLI."""

from __future__ import annotations

import json
from textwrap import dedent

from pathivu.__main__ import main


def test_cli_writes_about_json(tagged_repo, capsys):
    (tagged_repo / "pyproject.toml").write_text(dedent("""
        [project]
        name = "sample"
        version = "1.0.0"
        dependencies = ["pytest"]
    """).lstrip())

    exit_code = main(["sample", "I serve users"])
    assert exit_code == 0

    out_path = tagged_repo / "src" / "sample" / "_about.json"
    printed = capsys.readouterr().out.strip()
    assert printed == str(out_path.relative_to(tagged_repo))
    assert out_path.exists()

    data = json.loads(out_path.read_text())
    assert data["about"] == {"app_name": "sample", "description": "I serve users"}
    assert data["pkg"]["name"] == "sample"
    assert "pytest" in data["deps"]
    assert "commit_id" in data["git"]


def test_cli_with_custom_out_and_excludes(tagged_repo, capsys):
    (tagged_repo / "pyproject.toml").write_text(dedent("""
        [project]
        name = "sample"
        dependencies = ["pytest"]
    """).lstrip())

    custom = tagged_repo / "out.json"
    exit_code = main([
        "sample", "desc",
        "--out", str(custom),
        "--exclude-transitive", "pytest",
    ])
    assert exit_code == 0
    data = json.loads(custom.read_text())
    assert data["deps"]["pytest"]["depends_on"] == "..."


def test_cli_without_description_uses_default(tagged_repo, capsys):
    (tagged_repo / "pyproject.toml").write_text('[project]\nname = "sample"\n')
    main(["sample"])
    out = tagged_repo / "src" / "sample" / "_about.json"
    data = json.loads(out.read_text())
    assert data["about"]["description"] == "..and sample is my name"


def test_cli_missing_app_name_errors(capsys):
    import pytest
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code != 0
