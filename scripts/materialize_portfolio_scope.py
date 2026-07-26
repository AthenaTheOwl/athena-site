#!/usr/bin/env python3
"""Materialize the complete on-disk scope required by portfolio audits.

The portfolio reports inspect sibling repositories directly. A CI checkout of
athena-site alone cannot produce a complete result, so this helper clones every
active repository carrying a ``cdcp_status`` declaration before the reports
run. It also provides a verification-only mode for local and CI preflight.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "ops" / "portfolio-manifest.yml"
DEFAULT_OWNER = "AthenaTheOwl"
REPO_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")

CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def active_cdcp_repos(manifest: dict[str, Any]) -> list[str]:
    """Return active CDCP sibling repos in manifest order."""

    names: list[str] = []
    for repo in manifest.get("repos", []):
        name = repo.get("name")
        if (
            repo.get("status") == "active"
            and repo.get("cdcp_status") is not None
            and name != "athena-site"
        ):
            if not isinstance(name, str) or not REPO_NAME_RE.fullmatch(name):
                raise ValueError(f"unsafe repository name in manifest: {name!r}")
            names.append(name)
    return names


def missing_repos(destination: Path, repos: list[str]) -> list[str]:
    """Return repos that are not valid Git checkouts under destination."""

    return [
        name
        for name in repos
        if not (destination / name / ".git").is_dir()
    ]


def _default_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        encoding="utf-8",
        errors="replace",
    )


def materialize(
    destination: Path,
    repos: list[str],
    owner: str = DEFAULT_OWNER,
    runner: CommandRunner = _default_runner,
) -> list[str]:
    """Clone missing public repos and return any that remain unavailable."""

    destination.mkdir(parents=True, exist_ok=True)
    for name in missing_repos(destination, repos):
        target = destination / name
        if target.exists():
            print(
                f"scope: refusing to replace non-repository path {target}",
                file=sys.stderr,
            )
            continue
        url = f"https://github.com/{owner}/{name}.git"
        result = runner(
            ["git", "clone", "--depth", "1", "--no-tags", url, str(target)]
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            print(f"scope: clone failed for {name}: {detail}", file=sys.stderr)
    return missing_repos(destination, repos)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--owner", default=DEFAULT_OWNER)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args(argv)

    manifest = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
    repos = active_cdcp_repos(manifest)
    destination = args.destination.resolve()

    missing = (
        missing_repos(destination, repos)
        if args.verify_only
        else materialize(destination, repos, owner=args.owner)
    )
    if missing:
        print(
            "portfolio scope incomplete; missing: " + ", ".join(missing),
            file=sys.stderr,
        )
        return 1

    print(
        f"portfolio scope OK ({len(repos)} sibling repos under {destination})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
