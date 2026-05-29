"""Unit tests for `scripts/portfolio_dashboard.py`.

The dashboard generator runs against on-disk state. These tests build a
temporary fake portfolio, run the probes against it, and check that the
renderer produces a Markdown report with the expected shape. No network,
no GitHub API.

Tests are runnable with stdlib `unittest`; pytest will discover them too.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import portfolio_dashboard as pd  # noqa: E402


def init_git_repo(path: Path) -> None:
    """Initialize a quiet git repo so commit / log probes return useful data."""
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=path, check=True)


def make_initial_commit(path: Path, msg: str = "init") -> None:
    """Add all files and produce a single commit."""
    subprocess.run(["git", "add", "-A"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=path, check=True)


class ProbeTests(unittest.TestCase):
    """Each probe runs against a constructed temp directory."""

    def setUp(self) -> None:
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_workflow_count_zero_when_dir_absent(self) -> None:
        self.assertEqual(pd.workflow_count(self.repo), 0)

    def test_workflow_count_picks_up_yml_and_yaml(self) -> None:
        wf = self.repo / ".github" / "workflows"
        wf.mkdir(parents=True)
        (wf / "a.yml").write_text("name: a\n", encoding="utf-8")
        (wf / "b.yaml").write_text("name: b\n", encoding="utf-8")
        (wf / "notes.md").write_text("ignored\n", encoding="utf-8")
        self.assertEqual(pd.workflow_count(self.repo), 2)

    def test_latest_decisions_sorted_by_mtime_descending(self) -> None:
        d = self.repo / "decisions"
        d.mkdir()
        (d / "DEC-AAA-001-first.md").write_text("a\n", encoding="utf-8")
        (d / "DEC-AAA-002-second.md").write_text("b\n", encoding="utf-8")
        (d / "DEC-AAA-003-third.md").write_text("c\n", encoding="utf-8")
        # Tweak mtimes so order is unambiguous.
        import os
        import time

        now = time.time()
        os.utime(d / "DEC-AAA-001-first.md", (now - 300, now - 300))
        os.utime(d / "DEC-AAA-002-second.md", (now - 200, now - 200))
        os.utime(d / "DEC-AAA-003-third.md", (now - 100, now - 100))
        latest = pd.latest_decisions(self.repo, n=2)
        self.assertEqual([x["name"] for x in latest], [
            "DEC-AAA-003-third.md",
            "DEC-AAA-002-second.md",
        ])

    def test_latest_dreams_prefers_ops_dreams_over_dreams(self) -> None:
        ops_dreams = self.repo / "ops" / "dreams"
        ops_dreams.mkdir(parents=True)
        (ops_dreams / "2026-W21").mkdir()
        # Should NOT be reached because ops/dreams is present.
        old_dreams = self.repo / "dreams"
        old_dreams.mkdir()
        (old_dreams / "2025-W01").mkdir()
        latest = pd.latest_dreams(self.repo, n=3)
        self.assertEqual([x["name"] for x in latest], ["2026-W21"])

    def test_latest_dreams_falls_back_to_top_level_dreams(self) -> None:
        (self.repo / "dreams").mkdir()
        (self.repo / "dreams" / "2026-W20").mkdir()
        latest = pd.latest_dreams(self.repo, n=3)
        self.assertEqual([x["name"] for x in latest], ["2026-W20"])

    def test_run_record_count(self) -> None:
        d = self.repo / "ops" / "run-records"
        d.mkdir(parents=True)
        (d / "run-aaa.json").write_text("{}\n", encoding="utf-8")
        (d / "run-bbb.json").write_text("{}\n", encoding="utf-8")
        (d / "README.md").write_text("ignored\n", encoding="utf-8")
        self.assertEqual(pd.run_record_count(self.repo), 2)

    def test_replay_artifact_count_walks_one_level_deep(self) -> None:
        d = self.repo / "ops" / "replay-records"
        (d / "run-aaa").mkdir(parents=True)
        (d / "run-bbb").mkdir()
        (d / "run-aaa" / "01.json").write_text("{}\n", encoding="utf-8")
        (d / "run-aaa" / "02.json").write_text("{}\n", encoding="utf-8")
        (d / "run-bbb" / "01.json").write_text("{}\n", encoding="utf-8")
        # A loose file at the root should NOT be counted.
        (d / "stray.json").write_text("{}\n", encoding="utf-8")
        self.assertEqual(pd.replay_artifact_count(self.repo), 3)

    def test_schema_cache_freshness_returns_none_when_script_absent(self) -> None:
        self.assertIsNone(pd.schema_cache_freshness_exit(self.repo))

    def test_recent_commits_against_real_git_repo(self) -> None:
        init_git_repo(self.repo)
        (self.repo / "f.txt").write_text("hi\n", encoding="utf-8")
        make_initial_commit(self.repo, "first")
        result = pd.recent_commits(self.repo, days=7)
        self.assertEqual(result["count"], 1)
        self.assertTrue(result["latest_sha"])
        self.assertEqual(result["latest_author"], "Test")
        self.assertTrue(result["latest_date"])


class ManifestTests(unittest.TestCase):
    def test_active_cdcp_repos_keeps_active_with_cdcp_status(self) -> None:
        manifest = {
            "repos": [
                {"name": "a", "status": "active", "cdcp_status": ["installed"]},
                {"name": "b", "status": "active"},  # no cdcp_status: drop
                {"name": "c", "status": "workshop", "cdcp_status": ["x"]},  # not active: drop
                {"name": "d", "status": "active", "cdcp_status": ["markdown-only"]},
            ]
        }
        self.assertEqual(pd.active_cdcp_repos(manifest), ["a", "d"])

    def test_active_cdcp_repos_against_real_manifest_returns_eight(self) -> None:
        import yaml

        manifest = yaml.safe_load(pd.DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        repos = pd.active_cdcp_repos(manifest)
        self.assertEqual(len(repos), 8)
        for expected in [
            "athena-site",
            "chip-supply-chain-map",
            "supplier-risk-rag-agent",
            "ai-field-brief",
            "procurement-negotiation-lab",
            "ai-supply-chain-copilot-prd",
            "mcp-security-lab",
            "trace-to-eval-harness",
        ]:
            self.assertIn(expected, repos)


class RenderTests(unittest.TestCase):
    def test_render_dashboard_has_summary_and_per_repo_sections(self) -> None:
        probes = {
            "alpha": {
                "commits": {
                    "count": 4,
                    "latest_sha": "abc1234",
                    "latest_author": "Tester",
                    "latest_date": "2026-05-29",
                },
                "decisions": [{"name": "DEC-X-001-foo.md", "mtime": "2026-05-29"}],
                "dreams": [],
                "workflow_count": 2,
                "schema_cache_exit": 0,
                "run_records": 3,
                "replay_artifacts": 1,
            },
            "beta": None,
        }
        rendered = pd.render_dashboard(["alpha", "beta"], probes, Path("/tmp"))
        self.assertIn("# Portfolio status dashboard", rendered)
        self.assertIn("## Portfolio summary", rendered)
        self.assertIn("Repos indexed | 1 / 2", rendered)
        self.assertIn("### alpha", rendered)
        self.assertIn("### beta", rendered)
        self.assertIn("Not checked out", rendered)
        self.assertIn("DEC-X-001-foo.md", rendered)
        self.assertIn("fresh (exit 0)", rendered)

    def test_render_dashboard_marks_stale_schema_cache(self) -> None:
        probes = {
            "alpha": {
                "commits": {"count": 0, "latest_sha": "", "latest_author": "", "latest_date": ""},
                "decisions": [],
                "dreams": [],
                "workflow_count": 0,
                "schema_cache_exit": 1,
                "run_records": 0,
                "replay_artifacts": 0,
            }
        }
        rendered = pd.render_dashboard(["alpha"], probes, None)
        self.assertIn("stale (exit 1)", rendered)


class SelfTestEntryPoint(unittest.TestCase):
    """Sanity-check the script's `--self-test` mode."""

    def test_self_test_runs_clean_against_athena_site(self) -> None:
        rc = pd.self_test()
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
