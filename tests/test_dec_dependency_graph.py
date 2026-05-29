"""Unit tests for `scripts/dec_dependency_graph.py`.

The graph generator runs against on-disk state. These tests build a temporary
fake portfolio, run the probes against it, and check that the renderer
produces DOT and Markdown with the expected shape. No network.

Tests are runnable with stdlib `unittest`; pytest will discover them too.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import dec_dependency_graph as dg  # noqa: E402


def write_dec(
    dir_: Path,
    bare_id: str,
    slug: str,
    amends: str | None = None,
    status: str = "approved",
    date: str = "2026-05-29",
) -> Path:
    """Write a minimal DEC file with the front-matter the parser reads."""
    dir_.mkdir(parents=True, exist_ok=True)
    full_id = f"{bare_id}-{slug}"
    body = ["---", f"id: {full_id}", f"date: {date}", f"status: {status}"]
    if amends:
        body.append(f"amends: {amends}")
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


class ParseTests(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_parse_returns_none_when_no_front_matter(self) -> None:
        path = self.repo / "DEC-CDCP-001-bad.md"
        path.write_text("no front matter\n", encoding="utf-8")
        # Filename fallback still gives an id.
        parsed = dg.parse_dec_file(path)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["bare_id"], "DEC-CDCP-001")

    def test_parse_extracts_id_amends_status(self) -> None:
        path = write_dec(
            self.repo, "DEC-CDCP-002", "second",
            amends="DEC-CDCP-001-first", status="approved",
        )
        parsed = dg.parse_dec_file(path)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["id"], "DEC-CDCP-002-second")
        self.assertEqual(parsed["bare_id"], "DEC-CDCP-002")
        self.assertEqual(parsed["amends"], "DEC-CDCP-001-first")
        self.assertEqual(parsed["amends_bare"], "DEC-CDCP-001")
        self.assertEqual(parsed["status"], "approved")

    def test_collect_decs_skips_non_dec_files(self) -> None:
        decisions = self.repo / "decisions"
        write_dec(decisions, "DEC-AAA-001", "one")
        (decisions / "README.md").write_text("not a DEC\n", encoding="utf-8")
        decs = dg.collect_decs(self.repo)
        self.assertEqual(len(decs), 1)
        self.assertEqual(decs[0]["bare_id"], "DEC-AAA-001")


class GraphTests(unittest.TestCase):
    def _three_chain(self) -> list[dict]:
        return [
            {
                "id": "DEC-AAA-001-one", "bare_id": "DEC-AAA-001",
                "amends": None, "amends_bare": None, "status": "approved",
                "owner": "", "date": "2026-05-01", "filename": "DEC-AAA-001-one.md",
            },
            {
                "id": "DEC-AAA-002-two", "bare_id": "DEC-AAA-002",
                "amends": "DEC-AAA-001-one", "amends_bare": "DEC-AAA-001",
                "status": "approved", "owner": "", "date": "2026-05-02",
                "filename": "DEC-AAA-002-two.md",
            },
            {
                "id": "DEC-AAA-003-three", "bare_id": "DEC-AAA-003",
                "amends": "DEC-AAA-002-two", "amends_bare": "DEC-AAA-002",
                "status": "approved", "owner": "", "date": "2026-05-03",
                "filename": "DEC-AAA-003-three.md",
            },
        ]

    def test_build_edges_yields_later_to_earlier(self) -> None:
        edges = dg.build_edges(self._three_chain())
        self.assertEqual(
            edges,
            [
                ("DEC-AAA-002-two", "DEC-AAA-001-one"),
                ("DEC-AAA-003-three", "DEC-AAA-002-two"),
            ],
        )

    def test_build_chains_renders_full_chain(self) -> None:
        chains = dg.build_chains(self._three_chain())
        self.assertEqual(
            chains,
            [["DEC-AAA-001-one", "DEC-AAA-002-two", "DEC-AAA-003-three"]],
        )
        self.assertEqual(dg.chain_depth(chains), 2)

    def test_build_chains_handles_branching_root(self) -> None:
        # One root with two children: two chains.
        decs = [
            {
                "id": "DEC-X-001", "bare_id": "DEC-X-001",
                "amends": None, "amends_bare": None, "status": "approved",
                "owner": "", "date": "", "filename": "DEC-X-001.md",
            },
            {
                "id": "DEC-X-002", "bare_id": "DEC-X-002",
                "amends": "DEC-X-001", "amends_bare": "DEC-X-001",
                "status": "approved", "owner": "", "date": "",
                "filename": "DEC-X-002.md",
            },
            {
                "id": "DEC-X-003", "bare_id": "DEC-X-003",
                "amends": "DEC-X-001", "amends_bare": "DEC-X-001",
                "status": "approved", "owner": "", "date": "",
                "filename": "DEC-X-003.md",
            },
        ]
        chains = dg.build_chains(decs)
        self.assertEqual(len(chains), 2)
        leaves = {chain[-1] for chain in chains}
        self.assertEqual(leaves, {"DEC-X-002", "DEC-X-003"})

    def test_build_chains_empty_when_no_amends(self) -> None:
        decs = [
            {
                "id": "DEC-Y-001", "bare_id": "DEC-Y-001",
                "amends": None, "amends_bare": None, "status": "approved",
                "owner": "", "date": "", "filename": "DEC-Y-001.md",
            },
        ]
        self.assertEqual(dg.build_chains(decs), [])
        self.assertEqual(dg.chain_depth([]), 0)


class RenderTests(unittest.TestCase):
    def test_render_dot_includes_nodes_and_edges(self) -> None:
        decs = [
            {
                "id": "DEC-AAA-001-one", "bare_id": "DEC-AAA-001",
                "amends": None, "amends_bare": None, "status": "approved",
                "owner": "", "date": "", "filename": "",
            },
            {
                "id": "DEC-AAA-002-two", "bare_id": "DEC-AAA-002",
                "amends": "DEC-AAA-001-one", "amends_bare": "DEC-AAA-001",
                "status": "approved", "owner": "", "date": "", "filename": "",
            },
        ]
        edges = dg.build_edges(decs)
        dot = dg.render_dot("my-repo", decs, edges)
        self.assertIn("digraph dec_chains_my_repo", dot)
        self.assertIn("rankdir=LR;", dot)
        self.assertIn('"DEC-AAA-001-one" [shape=box, style=solid];', dot)
        self.assertIn(
            '"DEC-AAA-002-two" -> "DEC-AAA-001-one" [label="amends"];', dot
        )

    def test_render_dot_handles_empty_repo(self) -> None:
        dot = dg.render_dot("empty", [], [])
        self.assertIn("digraph dec_chains_empty", dot)
        self.assertIn("No DECs", dot)

    def test_render_repo_markdown_lists_chain_and_table(self) -> None:
        decs = [
            {
                "id": "DEC-AAA-001-one", "bare_id": "DEC-AAA-001",
                "amends": None, "amends_bare": None, "status": "approved",
                "owner": "", "date": "2026-05-01", "filename": "",
            },
            {
                "id": "DEC-AAA-002-two", "bare_id": "DEC-AAA-002",
                "amends": "DEC-AAA-001-one", "amends_bare": "DEC-AAA-001",
                "status": "approved", "owner": "", "date": "2026-05-02",
                "filename": "",
            },
        ]
        chains = dg.build_chains(decs)
        md = dg.render_repo_markdown("my-repo", decs, chains)
        self.assertIn("# DEC dependency graph — my-repo", md)
        self.assertIn("Total DECs: **2**", md)
        self.assertIn("Amendment chains: **1**", md)
        self.assertIn(
            "DEC-AAA-001-one -> DEC-AAA-002-two", md
        )
        self.assertIn("| id | status | amends | date |", md)

    def test_render_portfolio_rollup_summarizes(self) -> None:
        stats = [
            {
                "repo": "alpha", "state": "ok", "dec_count": 5,
                "chain_count": 1, "chain_depth": 2,
                "deepest_chain": ["DEC-A-001", "DEC-A-002", "DEC-A-003"],
            },
            {
                "repo": "beta", "state": "not checked out", "dec_count": 0,
                "chain_count": 0, "chain_depth": 0, "deepest_chain": [],
            },
        ]
        md = dg.render_portfolio_rollup(stats)
        self.assertIn("portfolio rollup", md)
        self.assertIn("| alpha | 5 | 1 | 2 | OK |", md)
        self.assertIn("not checked out", md)
        self.assertIn("Total DECs across portfolio: **5**", md)
        self.assertIn("DEC-A-001 -> DEC-A-002 -> DEC-A-003", md)


class EndToEndTests(unittest.TestCase):
    def test_process_repo_writes_dot_and_md(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            repo_root = tmp_root / "fake-repo"
            decisions = repo_root / "decisions"
            write_dec(decisions, "DEC-ZZZ-001", "root")
            write_dec(decisions, "DEC-ZZZ-002", "child", amends="DEC-ZZZ-001-root")
            output = tmp_root / "out"
            stats = dg.process_repo("fake-repo", repo_root, output)
            self.assertEqual(stats["state"], "ok")
            self.assertEqual(stats["dec_count"], 2)
            self.assertEqual(stats["chain_count"], 1)
            self.assertEqual(stats["chain_depth"], 1)
            dot_path = output / "fake-repo.dot"
            md_path = output / "fake-repo.md"
            self.assertTrue(dot_path.is_file())
            self.assertTrue(md_path.is_file())
            self.assertIn(
                "DEC-ZZZ-002-child", dot_path.read_text(encoding="utf-8")
            )

    def test_process_repo_handles_missing_root(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            stats = dg.process_repo("ghost-repo", None, output)
            self.assertEqual(stats["state"], "not checked out")
            self.assertFalse((output / "ghost-repo.dot").exists())


class SelfTestEntryPoint(unittest.TestCase):
    def test_self_test_runs_clean_against_athena_site(self) -> None:
        rc = dg.self_test()
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
