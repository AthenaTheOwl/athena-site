"""Unit tests for `scripts/dec_coverage_report.py`.

The coverage generator runs against on-disk state. These tests build a
temporary fake portfolio, run the probes against it, and check that the
renderer produces a Markdown report with the expected shape. No network.

Tests cover R-CDCP-025 (portfolio DEC coverage report exists) and
R-CDCP-026 (audit workflow regenerates the report). DEC-CDCP-019
records the contract.
"""
from __future__ import annotations

import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import dec_coverage_report as dcr  # noqa: E402


def write_dec(
    dir_: Path,
    bare_id: str,
    slug: str,
    requirement: str | None = None,
    status: str = "approved",
) -> Path:
    """Write a minimal DEC file with the front-matter the parser reads."""
    dir_.mkdir(parents=True, exist_ok=True)
    full_id = f"{bare_id}-{slug}"
    body = ["---", f"id: {full_id}", "date: 2026-05-29", f"status: {status}"]
    if requirement is not None:
        body.append(f"requirement: {requirement}")
    body.append("reversible: true")
    body.append("---")
    body.append("")
    body.append("## decision")
    body.append("")
    body.append("Body text.")
    body.append("")
    path = dir_ / f"{full_id}.md"
    path.write_text("\n".join(body), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# range / list / string expansion
# ---------------------------------------------------------------------------


class ExpandRequirementTests(unittest.TestCase):
    """The R-* tokeniser is the spine of the script. Covers R-CDCP-025."""

    def test_single_id(self) -> None:
        self.assertEqual(
            dcr.expand_requirement_value("R-CDCP-011"), ["R-CDCP-011"]
        )

    def test_range(self) -> None:
        self.assertEqual(
            dcr.expand_requirement_value("R-CDCP-022..024"),
            ["R-CDCP-022", "R-CDCP-023", "R-CDCP-024"],
        )

    def test_range_reversed_is_normalized(self) -> None:
        self.assertEqual(
            dcr.expand_requirement_value("R-X-003..001"),
            ["R-X-001", "R-X-002", "R-X-003"],
        )

    def test_list_form(self) -> None:
        self.assertEqual(
            dcr.expand_requirement_value(["R-A-001", "R-A-002"]),
            ["R-A-001", "R-A-002"],
        )

    def test_comma_separated_string(self) -> None:
        # Mixed range + literal in one comma-separated string.
        out = dcr.expand_requirement_value("R-X-001..002, R-X-005")
        self.assertEqual(out, ["R-X-001", "R-X-002", "R-X-005"])

    def test_multi_family_id(self) -> None:
        # R-MCPSEC-DIFF-001 has two family segments; the parser must
        # accept the inner segment without splitting on it.
        self.assertEqual(
            dcr.expand_requirement_value("R-MCPSEC-DIFF-001"),
            ["R-MCPSEC-DIFF-001"],
        )

    def test_none_returns_empty(self) -> None:
        self.assertEqual(dcr.expand_requirement_value(None), [])

    def test_unknown_token_dropped(self) -> None:
        # No anchor / no R-* prefix -> dropped silently.
        self.assertEqual(dcr.expand_requirement_value("not-an-id"), [])

    def test_range_preserves_zero_padding(self) -> None:
        out = dcr.expand_requirement_value("R-FOO-007..009")
        self.assertEqual(out, ["R-FOO-007", "R-FOO-008", "R-FOO-009"])


# ---------------------------------------------------------------------------
# front-matter parsing + DEC collection
# ---------------------------------------------------------------------------


class ParseDecTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_parse_extracts_requirement_range(self) -> None:
        path = write_dec(
            self.repo, "DEC-CDCP-022", "evidence",
            requirement="R-CDCP-022..024",
        )
        parsed = dcr.parse_dec_file(path)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["bare_id"], "DEC-CDCP-022")
        self.assertEqual(
            parsed["requirement_ids"],
            ["R-CDCP-022", "R-CDCP-023", "R-CDCP-024"],
        )

    def test_parse_handles_missing_requirement(self) -> None:
        # DEC with no requirement field still parses; it just shows zero
        # requirement ids and will render as uncovered.
        path = write_dec(self.repo, "DEC-AAA-001", "bare", requirement=None)
        parsed = dcr.parse_dec_file(path)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["requirement_ids"], [])

    def test_collect_decs_skips_non_dec_files(self) -> None:
        decisions = self.repo / "decisions"
        write_dec(decisions, "DEC-AAA-001", "one", requirement="R-A-001")
        (decisions / "README.md").write_text("not a DEC\n", encoding="utf-8")
        decs = dcr.collect_decs(self.repo)
        self.assertEqual(len(decs), 1)
        self.assertEqual(decs[0]["bare_id"], "DEC-AAA-001")


# ---------------------------------------------------------------------------
# allowlist credit
# ---------------------------------------------------------------------------


class AllowlistTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        self.decisions = self.repo / "decisions"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_note_pairs_attach_to_correct_dec(self) -> None:
        write_dec(self.decisions, "DEC-PUB-005", "publish", requirement="R-PUB-004")
        write_dec(self.decisions, "DEC-PUB-006", "review", requirement="R-PUB-010")
        (self.decisions / ".spec-check-allowlist.yaml").write_text(
            "deferred:\n"
            "  - id: R-PUB-005\n"
            "    note: resolved by DEC-PUB-005 (collective coverage)\n"
            "  - id: R-PUB-006\n"
            "    note: resolved by DEC-PUB-005 (collective coverage)\n"
            "  - id: R-NONE-001\n"
            "    note: phase 0 bootstrap; backfill pending\n",
            encoding="utf-8",
        )
        decs = dcr.collect_decs(self.repo)
        extras = dcr.collect_allowlist_extras(self.repo, decs)
        self.assertEqual(extras.get("DEC-PUB-005"), ["R-PUB-005", "R-PUB-006"])
        self.assertNotIn("DEC-PUB-006", extras)

    def test_missing_allowlist_returns_empty(self) -> None:
        write_dec(self.decisions, "DEC-A-001", "a", requirement="R-A-001")
        decs = dcr.collect_decs(self.repo)
        self.assertEqual(dcr.collect_allowlist_extras(self.repo, decs), {})


# ---------------------------------------------------------------------------
# test discovery + coverage probe
# ---------------------------------------------------------------------------


class DiscoverTestsTests(unittest.TestCase):
    def test_discover_finds_python_and_ts_tests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "tests").mkdir()
            (repo / "tests" / "test_a.py").write_text("# test\n", encoding="utf-8")
            (repo / "scripts").mkdir()
            (repo / "scripts" / "test_b.py").write_text("# test\n", encoding="utf-8")
            (repo / "src").mkdir()
            (repo / "src" / "thing.test.ts").write_text("// test\n", encoding="utf-8")
            # Exclusions: node_modules and __pycache__ are skipped.
            (repo / "node_modules" / "pkg").mkdir(parents=True)
            (repo / "node_modules" / "pkg" / "test_z.py").write_text("# nope\n", encoding="utf-8")
            (repo / "tests" / "__pycache__").mkdir()
            (repo / "tests" / "__pycache__" / "test_x.cpython-311.pyc").write_text("", encoding="utf-8")

            found = {p.name for p in dcr.discover_test_files(repo)}
            self.assertIn("test_a.py", found)
            self.assertIn("test_b.py", found)
            self.assertIn("thing.test.ts", found)
            self.assertNotIn("test_z.py", found)


# ---------------------------------------------------------------------------
# end-to-end repo indexing
# ---------------------------------------------------------------------------


class IndexRepoTests(unittest.TestCase):
    def test_covered_and_uncovered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            decisions = repo / "decisions"
            write_dec(decisions, "DEC-FOO-001", "covered", requirement="R-FOO-001")
            write_dec(decisions, "DEC-FOO-002", "uncovered", requirement="R-FOO-002..003")
            tests = repo / "tests"
            tests.mkdir()
            (tests / "test_a.py").write_text(
                "def test_x():\n    # references R-FOO-001\n    pass\n",
                encoding="utf-8",
            )
            record = dcr.index_repo("fake", repo)
            self.assertEqual(record["state"], "ok")
            self.assertEqual(record["total"], 2)
            self.assertEqual(record["covered"], 1)
            self.assertEqual(record["uncovered"], 1)
            assert record["coverage_pct"] is not None
            self.assertAlmostEqual(record["coverage_pct"], 50.0, places=2)

    def test_not_checked_out(self) -> None:
        record = dcr.index_repo("ghost", None)
        self.assertEqual(record["state"], "not checked out")
        self.assertEqual(record["total"], 0)
        self.assertIsNone(record["coverage_pct"])

    def test_repo_with_no_decisions_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record = dcr.index_repo("empty", Path(tmp))
            self.assertEqual(record["state"], "ok")
            self.assertEqual(record["total"], 0)
            self.assertEqual(record["covered"], 0)


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------


class RenderTests(unittest.TestCase):
    def _two_repo_rows(self) -> list[dict]:
        return [
            {
                "name": "alpha",
                "state": "ok",
                "total": 4,
                "covered": 3,
                "uncovered": 1,
                "coverage_pct": 75.0,
                "decs": [
                    {
                        "id": "DEC-A-001-x", "bare_id": "DEC-A-001",
                        "requirement_ids": ["R-A-001"], "covered": True,
                        "matched_ids": ["R-A-001"],
                    },
                    {
                        "id": "DEC-A-002-y", "bare_id": "DEC-A-002",
                        "requirement_ids": ["R-A-002"], "covered": False,
                        "matched_ids": [],
                    },
                ],
            },
            {
                "name": "beta",
                "state": "not checked out",
                "total": 0,
                "covered": 0,
                "uncovered": 0,
                "coverage_pct": None,
                "decs": [],
            },
        ]

    def test_renders_overall_and_per_repo(self) -> None:
        now = dt.datetime(2026, 5, 29, tzinfo=dt.timezone.utc)
        rendered, totals = dcr.render_report(
            self._two_repo_rows(), 70.0, Path("/tmp"), now,
        )
        self.assertIn("DEC test-coverage report - 2026-05-29", rendered)
        self.assertIn("| alpha | 4 | 3 | 1 | 75.0% | OK |", rendered)
        self.assertIn("| beta | - | - | - | - | not checked out |", rendered)
        self.assertIn("Portfolio coverage:", rendered)
        # Threshold met (75% >= 70%) -> PASS.
        self.assertIn("**PASS**", rendered)
        self.assertEqual(totals["total_decs"], 4)
        self.assertEqual(totals["decs_with_tests"], 3)
        self.assertTrue(totals["gate_pass"])

    def test_gate_fails_below_threshold(self) -> None:
        rows = self._two_repo_rows()
        rows[0]["covered"] = 1
        rows[0]["uncovered"] = 3
        rows[0]["coverage_pct"] = 25.0
        now = dt.datetime(2026, 5, 29, tzinfo=dt.timezone.utc)
        rendered, totals = dcr.render_report(rows, 70.0, Path("/tmp"), now)
        self.assertIn("**FAIL**", rendered)
        self.assertFalse(totals["gate_pass"])

    def test_uncovered_decs_section_lists_each_dec(self) -> None:
        now = dt.datetime(2026, 5, 29, tzinfo=dt.timezone.utc)
        rendered, _ = dcr.render_report(
            self._two_repo_rows(), 70.0, Path("/tmp"), now,
        )
        self.assertIn("### alpha (1 uncovered)", rendered)
        self.assertIn("`DEC-A-002-y`", rendered)

    def test_skipped_repos_listed(self) -> None:
        now = dt.datetime(2026, 5, 29, tzinfo=dt.timezone.utc)
        rendered, _ = dcr.render_report(
            self._two_repo_rows(), 70.0, Path("/tmp"), now,
        )
        self.assertIn("## Skipped repos", rendered)
        self.assertIn("`beta`", rendered)


class SelfTestEntryPoint(unittest.TestCase):
    def test_self_test_runs_clean(self) -> None:
        rc = dcr.self_test()
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
