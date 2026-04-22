"""shared fixtures for pathivu tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def _g(*args: str) -> None:
    """run a git command, asserting success; stdout/stderr suppressed."""
    subprocess.run(["git", *args], check=True, capture_output=True)


@pytest.fixture
def bare_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """git repo with one commit, no tag, no remote. cwd is set to the repo root."""
    monkeypatch.chdir(tmp_path)
    _g("init", "-q", "-b", "main")
    _g("config", "user.email", "test@example.com")
    _g("config", "user.name", "Test User")
    _g("config", "commit.gpgsign", "false")
    (tmp_path / "README.md").write_text("hello\n")
    _g("add", "README.md")
    _g("commit", "-q", "-m", "initial commit")
    return tmp_path


@pytest.fixture
def tagged_repo(bare_repo: Path) -> Path:
    """bare_repo + origin remote + a v0.1.0 tag."""
    _g("remote", "add", "origin", "git@github.com:test/pathivu.git")
    _g("tag", "v0.1.0")
    return bare_repo
