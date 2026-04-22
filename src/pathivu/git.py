"""scoop git intel about the current repository.

runs a handful of git subcommands and returns a dict of what succeeded.
any command that fails is logged to stderr and omitted from the result —
pathivu is best-effort: we never block a build on missing intel.
"""

from __future__ import annotations

import subprocess
import sys

# each key maps to the git invocation that produces it.
# insertion order is preserved in the output dict (python 3.7+).
_FIELDS: dict[str, list[str]] = {
    "commit_id":   ["git", "rev-parse", "--short", "HEAD"],
    # --tags includes lightweight tags; without it we'd miss non-annotated releases
    "version_tag": ["git", "describe", "--tags", "--abbrev=0"],
    "branch":      ["git", "rev-parse", "--abbrev-ref", "HEAD"],
    "repo_url":    ["git", "config", "--get", "remote.origin.url"],
    "commit_time": ["git", "log", "-1", "--format=%cI"],  # strict iso-8601
    "author":      ["git", "log", "-1", "--pretty=format:%an"],
    "message":     ["git", "log", "-1", "--pretty=%B"],
}


def _run(args: list[str]) -> str | None:
    """run a subprocess; return stripped stdout, or None if anything goes wrong."""
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        print(f"(!) git not found on PATH, skipping: {' '.join(args)}", file=sys.stderr)
        return None
    if result.returncode != 0:
        # stderr is often empty for "not a git repo" etc; include stdout too for debugability
        err = (result.stderr or result.stdout).strip()
        print(f"(!) git failed: {' '.join(args)} -> {err}", file=sys.stderr)
        return None
    out = result.stdout.strip()
    return out or None


def _flatten(text: str) -> str:
    """collapse internal whitespace and newlines into single spaces."""
    return " ".join(text.split())


def scoop_git_intel() -> dict[str, str]:
    """return a dict of available git metadata; missing pieces are omitted.

    never raises — if git is absent or cwd is not a repo, returns {}.
    """
    intel: dict[str, str] = {}
    for key, args in _FIELDS.items():
        value = _run(args)
        if value is not None:
            intel[key] = _flatten(value)
    return intel
