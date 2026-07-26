from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import materialize_portfolio_scope as scope  # noqa: E402


def test_active_cdcp_repos_excludes_meta_repo() -> None:
    manifest = {
        "repos": [
            {"name": "athena-site", "status": "active", "cdcp_status": ["meta"]},
            {"name": "alpha", "status": "active", "cdcp_status": ["installed"]},
            {"name": "drawer", "status": "drawer", "cdcp_status": ["installed"]},
            {"name": "plain", "status": "active"},
        ]
    }

    assert scope.active_cdcp_repos(manifest) == ["alpha"]


def test_active_cdcp_repos_rejects_path_injection() -> None:
    manifest = {
        "repos": [
            {
                "name": "../outside",
                "status": "active",
                "cdcp_status": ["installed"],
            }
        ]
    }

    with pytest.raises(ValueError, match="unsafe repository name"):
        scope.active_cdcp_repos(manifest)


def test_materialize_clones_only_missing_repos(tmp_path: Path) -> None:
    (tmp_path / "present" / ".git").mkdir(parents=True)
    commands: list[list[str]] = []

    def fake_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        Path(command[-1], ".git").mkdir(parents=True)
        return subprocess.CompletedProcess(command, 0, "", "")

    missing = scope.materialize(
        tmp_path,
        ["present", "missing"],
        owner="Example",
        runner=fake_runner,
    )

    assert missing == []
    assert len(commands) == 1
    assert commands[0][5] == "https://github.com/Example/missing.git"


def test_non_repo_path_is_not_replaced(tmp_path: Path) -> None:
    (tmp_path / "blocked").mkdir()

    missing = scope.materialize(tmp_path, ["blocked"])

    assert missing == ["blocked"]
