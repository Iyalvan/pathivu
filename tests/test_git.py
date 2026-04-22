"""tests for pathivu.git."""

from __future__ import annotations

import re
import subprocess

from pathivu.git import scoop_git_intel


def test_all_fields_present_for_tagged_repo(tagged_repo):
    intel = scoop_git_intel()
    assert set(intel) == {
        "commit_id", "version_tag", "branch", "repo_url",
        "commit_time", "author", "message",
    }


def test_commit_id_is_short_sha(tagged_repo):
    cid = scoop_git_intel()["commit_id"]
    assert len(cid) == 7
    assert all(c in "0123456789abcdef" for c in cid)


def test_version_tag(tagged_repo):
    assert scoop_git_intel()["version_tag"] == "v0.1.0"


def test_branch(tagged_repo):
    assert scoop_git_intel()["branch"] == "main"


def test_repo_url(tagged_repo):
    assert scoop_git_intel()["repo_url"] == "git@github.com:test/pathivu.git"


def test_commit_time_is_iso8601(tagged_repo):
    # e.g. 2026-04-21T10:00:00+00:00
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", scoop_git_intel()["commit_time"])


def test_author_and_message(tagged_repo):
    intel = scoop_git_intel()
    assert intel["author"] == "Test User"
    assert intel["message"] == "initial commit"


def test_missing_tag_is_omitted_but_rest_present(bare_repo):
    intel = scoop_git_intel()
    assert "version_tag" not in intel
    assert "commit_id" in intel
    assert "branch" in intel
    assert "author" in intel


def test_missing_origin_is_omitted(bare_repo):
    assert "repo_url" not in scoop_git_intel()


def test_not_a_repo_returns_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert scoop_git_intel() == {}


def test_multiline_commit_message_is_flattened(bare_repo):
    subprocess.run(
        ["git", "commit", "--allow-empty",
         "-m", "subject",
         "-m", "body line 1\nbody line 2"],
        check=True, capture_output=True,
    )
    msg = scoop_git_intel()["message"]
    assert "\n" not in msg
    assert "subject" in msg
    assert "body line 1" in msg
    assert "body line 2" in msg
