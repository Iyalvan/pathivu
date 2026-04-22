"""pathivu — command-line entry point.

usage:
    pathivu <app-name> [description] [--out PATH] [--pyproject PATH]
                      [--exclude-transitive name1,name2]

equivalently:  python -m pathivu ...
"""

from __future__ import annotations

import argparse
import sys

from pathivu.core import describe, export_intel


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pathivu",
        description="record immutable git and build intel into your python artifacts",
    )
    parser.add_argument("app_name", help="name of the app, e.g. my-api")
    parser.add_argument(
        "description",
        nargs="?",
        default=None,
        help="what the app does",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="output path (default: src/<pkg>/_about.json)",
    )
    parser.add_argument(
        "--pyproject",
        default="pyproject.toml",
        help="path to pyproject.toml (default: ./pyproject.toml)",
    )
    parser.add_argument(
        "--exclude-transitive",
        default="",
        help="comma-separated deps whose transitive subtree is replaced with '...'",
    )

    args = parser.parse_args(argv)
    excluded = {x.strip() for x in args.exclude_transitive.split(",") if x.strip()}

    intel = describe(
        args.app_name,
        args.description,
        pyproject_path=args.pyproject,
        exclude_transitive=excluded or None,
    )
    result = export_intel(intel, args.app_name, out_path=args.out)
    print(result["intel_exported_to"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
