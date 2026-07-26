from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import portfolio_audit as audit  # noqa: E402


def test_fingerprint_from_repo_extracts_latest_week(tmp_path: Path) -> None:
    repo = tmp_path / "ai-field-brief"
    (repo / "briefs").mkdir(parents=True)
    (repo / "briefs" / "INDEX.md").write_text(
        "| [2026-W30](./2026-W30/brief.md) | title |\n"
        "| [2026-W29](./2026-W29/brief.md) | older |\n",
        encoding="utf-8",
    )

    value, error = audit.fingerprint_from_repo(
        "ai-field-brief",
        {"path": "briefs/INDEX.md", "pattern": r"\[(\d{4}-W\d{2})\]"},
        tmp_path,
    )

    assert error is None
    assert value == "2026-W30"


def test_fingerprint_from_repo_rejects_path_escape(tmp_path: Path) -> None:
    (tmp_path / "ai-field-brief").mkdir()

    value, error = audit.fingerprint_from_repo(
        "ai-field-brief",
        {"path": "../secret.txt", "pattern": ".+"},
        tmp_path,
    )

    assert value is None
    assert error == "source path escapes repository root"
