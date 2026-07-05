from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import evidence_quorum_sentinel as eqs  # noqa: E402


NOW = dt.datetime(2026, 5, 29, tzinfo=dt.timezone.utc)


def make_row(
    name: str,
    *,
    checked_out: bool,
    passed: bool,
    recent: int = 0,
    total: int = 0,
) -> dict[str, object]:
    return {
        "name": name,
        "recent": recent,
        "total": total,
        "pass": passed,
        "checked_out": checked_out,
        "latest_path": "ops/replay-records/run-1/artifact.json" if total else None,
        "latest_ts": NOW.isoformat() if total else None,
    }


def write_manifest(tmp_path: Path, local_root: Path, repos: list[str]) -> Path:
    entries = "\n".join(f"  - name: {name}\n    status: active" for name in repos)
    manifest = tmp_path / "portfolio-manifest.yml"
    manifest.write_text(
        f"local_root: \"{local_root.as_posix()}\"\nrepos:\n{entries}\n",
        encoding="utf-8",
    )
    return manifest


def write_recent_artifact(repo_root: Path) -> None:
    artifact = repo_root / "ops" / "replay-records" / "run-1" / "artifact.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        '{"created_at": "' + dt.datetime.now(tz=dt.timezone.utc).isoformat() + '"}\n',
        encoding="utf-8",
    )


def failing_section(rendered: str) -> str:
    section = rendered.split("## Failing repos\n\n", 1)[1]
    return section.split("\n## ", 1)[0]


def test_render_report_passes_when_all_checked_out_rows_pass() -> None:
    rows = [
        make_row("chip-supply-chain-map", checked_out=True, passed=True, recent=1, total=1),
        make_row("supplier-risk-rag-agent", checked_out=False, passed=False),
    ]

    rendered = eqs.render_report(rows, 30, 1, Path("/workspace"), NOW)

    assert "- Overall: **PASS**" in rendered
    assert "| supplier-risk-rag-agent | - | - | 1 | SKIPPED | not checked out |" in rendered


def test_render_report_fails_and_names_checked_out_repo() -> None:
    rows = [
        make_row("chip-supply-chain-map", checked_out=True, passed=True, recent=1, total=1),
        make_row("procurement-negotiation-lab", checked_out=True, passed=False),
    ]

    rendered = eqs.render_report(rows, 30, 1, Path("/workspace"), NOW)

    assert "- Overall: **FAIL**" in rendered
    section = failing_section(rendered)
    assert "**procurement-negotiation-lab**" in section
    assert "**chip-supply-chain-map**" not in section


def test_render_report_skips_overall_when_no_rows_are_checked_out() -> None:
    rows = [
        make_row("chip-supply-chain-map", checked_out=False, passed=False),
        make_row("supplier-risk-rag-agent", checked_out=False, passed=False),
    ]

    rendered = eqs.render_report(rows, 30, 1, Path("/workspace"), NOW)

    assert "- Overall: **SKIPPED (no repos checked out)**" in rendered
    section = failing_section(rendered)
    assert "None." in section
    assert "replay artifact(s)" not in section


def test_main_all_checked_out_passing_exits_zero(tmp_path: Path, capsys) -> None:
    local_root = tmp_path / "siblings"
    repo_root = local_root / "chip-supply-chain-map"
    repo_root.mkdir(parents=True)
    write_recent_artifact(repo_root)
    manifest = write_manifest(tmp_path, local_root, ["chip-supply-chain-map"])
    output = tmp_path / "report.md"

    exit_code = eqs.main(
        [
            "--manifest",
            str(manifest),
            "--output",
            str(output),
            "--window-days",
            "30",
            "--threshold",
            "1",
        ]
    )

    assert exit_code == 0
    assert "- Overall: **PASS**" in output.read_text(encoding="utf-8")
    assert "evidence-quorum: OK (1 repo(s) checked)" in capsys.readouterr().err


def test_main_one_checked_out_failing_exits_one(tmp_path: Path, capsys) -> None:
    local_root = tmp_path / "siblings"
    (local_root / "procurement-negotiation-lab").mkdir(parents=True)
    manifest = write_manifest(tmp_path, local_root, ["procurement-negotiation-lab"])
    output = tmp_path / "report.md"

    exit_code = eqs.main(
        [
            "--manifest",
            str(manifest),
            "--output",
            str(output),
            "--window-days",
            "30",
            "--threshold",
            "1",
        ]
    )

    assert exit_code == 1
    assert "- Overall: **FAIL**" in output.read_text(encoding="utf-8")
    assert "evidence-quorum: FAIL (procurement-negotiation-lab)" in capsys.readouterr().err


def test_main_all_rows_skipped_exits_zero(tmp_path: Path, capsys) -> None:
    local_root = tmp_path / "siblings"
    local_root.mkdir()
    manifest = write_manifest(
        tmp_path,
        local_root,
        ["chip-supply-chain-map", "supplier-risk-rag-agent"],
    )
    output = tmp_path / "report.md"

    exit_code = eqs.main(
        [
            "--manifest",
            str(manifest),
            "--output",
            str(output),
            "--window-days",
            "30",
            "--threshold",
            "1",
        ]
    )

    rendered = output.read_text(encoding="utf-8")
    assert exit_code == 0
    assert "- Overall: **SKIPPED (no repos checked out)**" in rendered
    assert "replay artifact(s)" not in failing_section(rendered)
    assert "evidence-quorum: SKIPPED (no repos checked out)" in capsys.readouterr().err
