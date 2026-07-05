from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import validate_sensitive_disclosures as vsd  # noqa: E402


def run_gate(capsys, root: Path, *paths: Path) -> tuple[int, str, str]:
    exit_code = vsd.main(["--root", str(root), *[str(path) for path in paths]])
    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err


def runtime_secret() -> str:
    return "".join(["s", "k", "-", "A" * 48])


def runtime_incident_phrase() -> str:
    return " ".join(["remed" + "iation", "run" + "book"])


def test_clean_markdown_passes(tmp_path: Path, capsys) -> None:
    doc = tmp_path / "clean.md"
    doc.write_text(
        "# Public note\n\nThis sanitized update has no credentials or incident details.\n",
        encoding="utf-8",
    )

    exit_code, stdout, stderr = run_gate(capsys, tmp_path, doc)

    assert exit_code == 0
    assert "validate_sensitive_disclosures OK" in stdout
    assert stderr == ""


def test_runtime_secret_is_flagged_as_openai_category(tmp_path: Path, capsys) -> None:
    doc = tmp_path / "bad.md"
    token = runtime_secret()
    doc.write_text("Do not publish this value: " + token + "\n", encoding="utf-8")

    exit_code, _stdout, stderr = run_gate(capsys, tmp_path, doc)

    assert exit_code == 1
    assert "bad.md:1: openai-api-key" in stderr
    assert token not in stderr


def test_runtime_incident_phrase_is_flagged(tmp_path: Path, capsys) -> None:
    doc = tmp_path / "incident.md"
    phrase = runtime_incident_phrase()
    doc.write_text("Internal-only note: " + phrase + "\n", encoding="utf-8")

    exit_code, _stdout, stderr = run_gate(capsys, tmp_path, doc)

    assert exit_code == 1
    assert "incident.md:1: security-incident-source-artifact" in stderr
    assert phrase not in stderr


def test_failure_output_names_policy_category(tmp_path: Path, capsys) -> None:
    doc = tmp_path / "category.md"
    doc.write_text("Internal-only note: " + runtime_incident_phrase() + "\n", encoding="utf-8")

    exit_code, _stdout, stderr = run_gate(capsys, tmp_path, doc)

    assert exit_code == 1
    assert "validate_sensitive_disclosures: blocked sensitive disclosure(s)." in stderr
    assert "security-incident-source-artifact" in stderr


def test_this_source_has_no_scanner_hits() -> None:
    assert vsd.scan_file(Path(__file__), REPO_ROOT) == []


def test_repo_tests_directory_passes_sensitive_disclosure_gate(capsys) -> None:
    exit_code, stdout, stderr = run_gate(capsys, REPO_ROOT, REPO_ROOT / "tests")

    assert exit_code == 0
    assert "validate_sensitive_disclosures OK" in stdout
    assert stderr == ""
