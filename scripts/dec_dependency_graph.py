#!/usr/bin/env python3
"""DEC dependency graph generator.

For each active CDCP repo declared in `ops/portfolio-manifest.yml`, walk the
`decisions/` directory, parse front-matter, and emit:

- `ops/dec-graphs/<repo>.dot` — Graphviz DOT file with one edge per `amends`
  reference (later DEC -> earlier DEC).
- `ops/dec-graphs/<repo>.md` — Markdown summary: total DECs, list of amendment
  chains rendered as arrow-joined strings.
- `ops/dec-graphs/portfolio-rollup.md` — Portfolio-wide rollup: DECs per repo,
  chain depth per repo, deepest chain head.

The script is designed to run against a local checkout (no GitHub API). DOT
output stops at the .dot file; we do not invoke graphviz to render images.

Run:
    python scripts/dec_dependency_graph.py
    python scripts/dec_dependency_graph.py --output ops/dec-graphs
    python scripts/dec_dependency_graph.py --self-test
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "ops" / "portfolio-manifest.yml"
DEFAULT_OUTPUT_DIR = ROOT / "ops" / "dec-graphs"

# DEC id without the trailing slug. Front-matter `id:` and `amends:` values
# may be either form (with or without slug); we normalize to the slug-bearing
# id when possible, falling back to the bare DEC-FAMILY-NNN form.
DEC_FILENAME_RE = re.compile(r"^(DEC-[A-Z0-9]+-\d+)(?:-(.+))?\.md$")
DEC_ID_RE = re.compile(r"^DEC-[A-Z0-9]+-\d+(?:-[A-Za-z0-9\-]+)?$")
DEC_BARE_RE = re.compile(r"^(DEC-[A-Z0-9]+-\d+)")


# ---------------------------------------------------------------------------
# manifest / root resolution (mirrors portfolio_audit / portfolio_dashboard)
# ---------------------------------------------------------------------------


def resolve_local_root(manifest: dict[str, Any]) -> Path | None:
    """Workspace path where sibling repos live."""
    candidates: list[str] = []
    env = os.environ.get("RANDOM_APPS_ROOT")
    if env:
        candidates.append(env)
    declared = manifest.get("local_root")
    if isinstance(declared, str) and declared:
        candidates.append(declared)
    for cand in candidates:
        path = Path(cand).expanduser()
        if path.is_dir():
            return path.resolve()
    return None


def active_cdcp_repos(manifest: dict[str, Any]) -> list[str]:
    """Active repos with a `cdcp_status` field. Order preserved from the manifest."""
    out: list[str] = []
    for r in manifest.get("repos", []):
        if r.get("status") == "active" and r.get("cdcp_status") is not None:
            out.append(r["name"])
    return out


# ---------------------------------------------------------------------------
# front-matter parsing
# ---------------------------------------------------------------------------


def parse_front_matter(text: str) -> dict[str, Any]:
    """Extract the YAML front-matter from a Markdown file. Returns {} on miss."""
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def bare_id(value: str) -> str:
    """Return the DEC-FAMILY-NNN form of a value, or the input if no match."""
    m = DEC_BARE_RE.match(value.strip())
    return m.group(1) if m else value.strip()


def parse_dec_file(path: Path) -> dict[str, Any] | None:
    """Parse one DEC file. Returns a dict with id, amends, status, owner, date.

    Returns None when the file has no parseable front-matter id.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    fm = parse_front_matter(text)
    dec_id = fm.get("id")
    if not isinstance(dec_id, str) or not dec_id.strip():
        # Fall back to filename: DEC-CDCP-011-foo.md -> DEC-CDCP-011-foo
        m = DEC_FILENAME_RE.match(path.name)
        if not m:
            return None
        dec_id = path.stem
    amends = fm.get("amends")
    if isinstance(amends, str):
        amends_value: str | None = amends.strip() or None
    else:
        amends_value = None
    return {
        "id": dec_id.strip(),
        "bare_id": bare_id(dec_id),
        "amends": amends_value,
        "amends_bare": bare_id(amends_value) if amends_value else None,
        "status": str(fm.get("status", "")).strip() or "unknown",
        "owner": str(fm.get("owner", "")).strip() or "",
        "date": str(fm.get("date", "")).strip() or "",
        "filename": path.name,
    }


def collect_decs(repo_root: Path) -> list[dict[str, Any]]:
    """Walk `<repo_root>/decisions/` for `DEC-*.md`. Sorted by filename."""
    decisions_dir = repo_root / "decisions"
    if not decisions_dir.is_dir():
        return []
    decs: list[dict[str, Any]] = []
    for path in sorted(decisions_dir.glob("DEC-*.md")):
        if not path.is_file():
            continue
        parsed = parse_dec_file(path)
        if parsed is None:
            continue
        decs.append(parsed)
    return decs


# ---------------------------------------------------------------------------
# graph + chain construction
# ---------------------------------------------------------------------------


def build_edges(decs: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """Return (later, earlier) edges from `amends` references.

    Edges resolve to the slug-bearing id when the amendee is present in the
    DEC list; otherwise they fall back to the bare DEC-FAMILY-NNN form so a
    dangling reference still shows in the DOT.
    """
    by_bare: dict[str, str] = {d["bare_id"]: d["id"] for d in decs}
    edges: list[tuple[str, str]] = []
    for d in decs:
        target_bare = d["amends_bare"]
        if not target_bare:
            continue
        target_id = by_bare.get(target_bare, d["amends"] or target_bare)
        edges.append((d["id"], target_id))
    return edges


def build_chains(decs: list[dict[str, Any]]) -> list[list[str]]:
    """Render every amendment chain as a list of ids, oldest -> newest.

    A chain starts at a DEC with no `amends` pointer that nonetheless has
    descendants. Singletons (DECs with no parent and no children) are not
    rendered as chains; they show in the per-DEC table but the chain section
    only surfaces multi-DEC chains.
    """
    by_bare: dict[str, dict[str, Any]] = {d["bare_id"]: d for d in decs}
    # Reverse adjacency: earlier_bare_id -> [later_bare_id, ...]
    children: dict[str, list[str]] = {}
    has_parent: set[str] = set()
    for d in decs:
        parent_bare = d["amends_bare"]
        if parent_bare and parent_bare in by_bare:
            children.setdefault(parent_bare, []).append(d["bare_id"])
            has_parent.add(d["bare_id"])
    chains: list[list[str]] = []
    # Roots: DECs with no in-graph parent but at least one child.
    roots = [
        d["bare_id"]
        for d in decs
        if d["bare_id"] not in has_parent and children.get(d["bare_id"])
    ]
    for root in roots:
        # Depth-first walk; each leaf produces one chain.
        stack: list[tuple[str, list[str]]] = [(root, [root])]
        while stack:
            node, path = stack.pop()
            kids = children.get(node, [])
            if not kids:
                chains.append([by_bare[n]["id"] for n in path])
                continue
            for kid in kids:
                stack.append((kid, path + [kid]))
    return chains


def chain_depth(chains: list[list[str]]) -> int:
    """Max edges across all chains. Zero when no multi-DEC chain exists."""
    if not chains:
        return 0
    return max(len(c) - 1 for c in chains)


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------


def _safe_label(repo: str) -> str:
    """Sanitize a repo name for use inside a DOT graph identifier."""
    return re.sub(r"[^A-Za-z0-9_]", "_", repo)


def render_dot(repo: str, decs: list[dict[str, Any]], edges: list[tuple[str, str]]) -> str:
    """Emit a Graphviz DOT digraph of the amendment chains for one repo."""
    lines: list[str] = [f"digraph dec_chains_{_safe_label(repo)} {{", "  rankdir=LR;"]
    if not decs:
        lines.append("  // No DECs found.")
        lines.append("}")
        return "\n".join(lines) + "\n"
    # Nodes first so disconnected DECs still render.
    for d in decs:
        status = d["status"]
        # Approved decisions get a solid box; everything else is dashed.
        style = "solid" if status == "approved" else "dashed"
        lines.append(f'  "{d["id"]}" [shape=box, style={style}];')
    for later, earlier in edges:
        lines.append(f'  "{later}" -> "{earlier}" [label="amends"];')
    lines.append("}")
    return "\n".join(lines) + "\n"


def render_repo_markdown(repo: str, decs: list[dict[str, Any]], chains: list[list[str]]) -> str:
    """Per-repo Markdown summary: counts, chain text, table of every DEC."""
    out: list[str] = [
        f"# DEC dependency graph — {repo}",
        "",
        f"- Total DECs: **{len(decs)}**",
        f"- Amendment chains: **{len(chains)}**",
        f"- Deepest chain depth (edges): **{chain_depth(chains)}**",
        "",
        "## Chains",
        "",
    ]
    if chains:
        for chain in chains:
            out.append("- " + " -> ".join(chain))
    else:
        out.append("- No amendment chains. Every DEC stands alone.")
    out.append("")
    out.append("## DECs")
    out.append("")
    out.append("| id | status | amends | date |")
    out.append("|---|---|---|---|")
    for d in decs:
        amends_cell = d["amends"] if d["amends"] else "—"
        out.append(
            f"| `{d['id']}` | {d['status']} | {amends_cell} | {d['date'] or '—'} |"
        )
    out.append("")
    out.append(
        "Generated by `scripts/dec_dependency_graph.py`. DOT companion lives "
        "next to this file."
    )
    out.append("")
    return "\n".join(out)


def render_portfolio_rollup(stats: list[dict[str, Any]]) -> str:
    """Portfolio-wide rollup Markdown."""
    import datetime as dt

    today = dt.date.today().isoformat()
    out: list[str] = [
        f"# DEC dependency graph — portfolio rollup ({today})",
        "",
        "Generated by `scripts/dec_dependency_graph.py`. Per-repo DOT and "
        "Markdown sit alongside this file.",
        "",
        "| Repo | DECs | Chains | Deepest chain (edges) | Status |",
        "|---|---|---|---|---|",
    ]
    total_decs = 0
    for s in stats:
        if s["state"] == "ok":
            total_decs += s["dec_count"]
            out.append(
                f"| {s['repo']} | {s['dec_count']} | {s['chain_count']} | "
                f"{s['chain_depth']} | OK |"
            )
        else:
            out.append(f"| {s['repo']} | — | — | — | {s['state']} |")
    out.append("")
    out.append(f"- Repos indexed: **{sum(1 for s in stats if s['state'] == 'ok')} / {len(stats)}**")
    out.append(f"- Total DECs across portfolio: **{total_decs}**")
    out.append("")
    out.append("## Deepest chains")
    out.append("")
    any_chain = False
    for s in stats:
        if s["state"] != "ok" or not s["deepest_chain"]:
            continue
        any_chain = True
        out.append(f"- **{s['repo']}**: " + " -> ".join(s["deepest_chain"]))
    if not any_chain:
        out.append("- No multi-DEC chains across the portfolio yet.")
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# orchestration
# ---------------------------------------------------------------------------


def repo_root_for(name: str, local_root: Path | None) -> Path | None:
    """Resolve the on-disk path for a portfolio repo. None when not checked out."""
    if name == "athena-site":
        candidate = ROOT
    elif local_root is None:
        return None
    else:
        candidate = local_root / name
    return candidate if candidate.is_dir() else None


def process_repo(repo: str, repo_root: Path | None, output_dir: Path) -> dict[str, Any]:
    """Index one repo. Writes the DOT + per-repo MD when possible.

    Returns a stats dict the rollup consumes.
    """
    if repo_root is None:
        return {
            "repo": repo,
            "state": "not checked out",
            "dec_count": 0,
            "chain_count": 0,
            "chain_depth": 0,
            "deepest_chain": [],
        }
    decs = collect_decs(repo_root)
    edges = build_edges(decs)
    chains = build_chains(decs)
    depth = chain_depth(chains)
    deepest: list[str] = []
    if chains:
        # Stable: pick the first chain that ties for max length.
        deepest = max(chains, key=len)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{repo}.dot").write_text(
        render_dot(repo, decs, edges), encoding="utf-8"
    )
    (output_dir / f"{repo}.md").write_text(
        render_repo_markdown(repo, decs, chains), encoding="utf-8"
    )
    return {
        "repo": repo,
        "state": "ok",
        "dec_count": len(decs),
        "chain_count": len(chains),
        "chain_depth": depth,
        "deepest_chain": deepest,
    }


# ---------------------------------------------------------------------------
# self-test (smoke)
# ---------------------------------------------------------------------------


def self_test() -> int:
    """Smoke test: parse athena-site's own DECs and confirm the renderer works."""
    errors: list[str] = []
    decs = collect_decs(ROOT)
    if not decs:
        errors.append("expected at least one DEC under athena-site/decisions")
    ids = {d["bare_id"] for d in decs}
    for expected in ("DEC-CDCP-011", "DEC-CDCP-016"):
        if expected not in ids:
            errors.append(f"expected {expected} in athena-site decisions")
    edges = build_edges(decs)
    chains = build_chains(decs)
    dot = render_dot("athena-site", decs, edges)
    if "digraph dec_chains_athena_site" not in dot:
        errors.append("DOT header missing expected name")
    md = render_repo_markdown("athena-site", decs, chains)
    if "DEC dependency graph — athena-site" not in md:
        errors.append("per-repo Markdown header missing")

    # Synthetic chain check: build a fake portfolio and verify chain text.
    fake = [
        {
            "id": "DEC-AAA-001", "bare_id": "DEC-AAA-001",
            "amends": None, "amends_bare": None, "status": "approved",
            "owner": "", "date": "", "filename": "DEC-AAA-001.md",
        },
        {
            "id": "DEC-AAA-002", "bare_id": "DEC-AAA-002",
            "amends": "DEC-AAA-001", "amends_bare": "DEC-AAA-001",
            "status": "approved", "owner": "", "date": "",
            "filename": "DEC-AAA-002.md",
        },
        {
            "id": "DEC-AAA-003", "bare_id": "DEC-AAA-003",
            "amends": "DEC-AAA-002", "amends_bare": "DEC-AAA-002",
            "status": "approved", "owner": "", "date": "",
            "filename": "DEC-AAA-003.md",
        },
    ]
    fake_chains = build_chains(fake)
    if fake_chains != [["DEC-AAA-001", "DEC-AAA-002", "DEC-AAA-003"]]:
        errors.append(f"synthetic chain wrong: {fake_chains}")
    if chain_depth(fake_chains) != 2:
        errors.append(f"synthetic chain depth wrong: {chain_depth(fake_chains)}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print("self-test OK", file=sys.stderr)
    return 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run the smoke test (no file write) and exit.",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    manifest = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
    local_root = resolve_local_root(manifest)
    repos = active_cdcp_repos(manifest)

    args.output.mkdir(parents=True, exist_ok=True)

    stats: list[dict[str, Any]] = []
    for name in repos:
        repo_root = repo_root_for(name, local_root)
        stats.append(process_repo(name, repo_root, args.output))

    rollup = render_portfolio_rollup(stats)
    (args.output / "portfolio-rollup.md").write_text(rollup, encoding="utf-8")
    indexed = sum(1 for s in stats if s["state"] == "ok")
    total_decs = sum(s["dec_count"] for s in stats if s["state"] == "ok")
    print(
        f"Wrote {args.output} ({indexed}/{len(stats)} repos indexed, "
        f"{total_decs} DECs total)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
