#!/usr/bin/env python3
"""DEC test-coverage report generator.

Every CDCP repo carries a DEC ledger under `decisions/`. Each DEC names
one or more R-* requirements via the `requirement:` front-matter field.
A DEC is "covered" when at least one of its requirements is referenced
by a test file inside the same repo. This script walks each active
product repo plus `trace-to-eval-harness` and `mcp-security-lab`,
counts covered vs uncovered DECs, and writes a portfolio-wide Markdown
report to `ops/dec-coverage-report.md`.

The generator is deliberately on-disk: no GitHub API, no network. It
runs both locally (where every sibling repo is checked out under
`local_root`) and on CI (where only athena-site is checked out and the
siblings render as "not checked out"). The CI run still refreshes the
report header so the date stays current.

Probe contract per repo
-----------------------

1. Walk `<repo>/decisions/DEC-*.md`. Parse the YAML front-matter.
2. From the `requirement:` field, expand the requirement id set:
     * `R-FAM-NNN` -> {R-FAM-NNN}
     * `R-FAM-NNN..MMM` -> {R-FAM-NNN, R-FAM-NNN+1, ..., R-FAM-MMM}
     * `[R-A, R-B]` (YAML list) -> {R-A, R-B}
3. Read `<repo>/decisions/.spec-check-allowlist.yaml` when present. The
   allowlist's `deferred:` entries name R-* ids that ship without a
   per-id DEC; many of them are resolved by a collective DEC named in
   the `note:` field. For each allowlist entry whose note mentions a
   `DEC-FAM-NNN[-slug]`, attach the allowlisted R-* id to that DEC.
4. Discover test files: `<repo>/tests/` recursively (any `test_*.py` or
   `*.test.ts`/`*.spec.ts`), plus top-level `<repo>/scripts/test_*.py`.
5. For each DEC, mark it "covered" when at least one of its requirement
   ids appears as a substring in any discovered test file's contents.
6. Tally per-repo: total DECs, covered DECs, uncovered DECs, coverage
   %. Sum into a portfolio total.
7. Exit 0 when portfolio coverage % >= `--threshold` (default 70);
   exit 1 otherwise. Repos that are not checked out under `local_root`
   contribute zero DECs to the totals and render as "skipped" in the
   report, so missing siblings on CI do not skew the score downward.

Run:
    python scripts/dec_coverage_report.py
    python scripts/dec_coverage_report.py --threshold 80
    python scripts/dec_coverage_report.py --self-test
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "ops" / "portfolio-manifest.yml"
DEFAULT_OUTPUT = ROOT / "ops" / "dec-coverage-report.md"
DEFAULT_THRESHOLD = 70.0

# Pattern to match an R-* requirement id. Matches R-FAM-NNN with
# optional inner family segment (R-MCPSEC-DIFF-001). The trailing digit
# block is required.
R_ID_RE = re.compile(r"^R-[A-Z]+(?:-[A-Z]+)*-\d+$")
R_RANGE_RE = re.compile(r"^(R-[A-Z]+(?:-[A-Z]+)*-)(\d+)\.\.(\d+)$")
# Pattern to find a bare DEC id inside allowlist notes ("resolved by
# DEC-PUB-005 (collective)"). Anchors on the DEC- prefix.
DEC_REF_RE = re.compile(r"DEC-[A-Z0-9]+-\d+(?:-[A-Za-z0-9\-]+)?")
# DEC filename -> bare id.
DEC_BARE_RE = re.compile(r"^(DEC-[A-Z0-9]+-\d+)")

# Test file globs. Python tests live under tests/ and sometimes
# scripts/. TypeScript suites live next to source under src/. We
# deliberately exclude node_modules / dist / __pycache__ to avoid
# crawling vendor trees.
EXCLUDE_DIR_NAMES = {"node_modules", "dist", ".next", "__pycache__", ".venv", "venv", "build", "out"}

TEST_FILENAME_PATTERNS = (
    re.compile(r"^test_.*\.py$"),
    re.compile(r"^.*\.test\.(?:ts|tsx|js|jsx|mjs)$"),
    re.compile(r"^.*\.spec\.(?:ts|tsx|js|jsx|mjs)$"),
    re.compile(r"^.*_test\.py$"),
)


# ---------------------------------------------------------------------------
# manifest / root resolution (mirrors evidence_quorum_sentinel.py)
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
    """Active repos with a cdcp_status field, in manifest order."""
    out: list[str] = []
    for r in manifest.get("repos", []):
        if r.get("status") == "active" and r.get("cdcp_status") is not None:
            out.append(r["name"])
    return out


def repo_root_for(name: str, local_root: Path | None) -> Path | None:
    """Resolve a portfolio repo's on-disk root. None when not checked out."""
    if name == "athena-site":
        candidate = ROOT
    elif local_root is None:
        return None
    else:
        candidate = local_root / name
    return candidate if candidate.is_dir() else None


# ---------------------------------------------------------------------------
# front-matter parsing
# ---------------------------------------------------------------------------


def parse_front_matter(text: str) -> dict[str, Any]:
    """Extract the YAML front-matter block. Returns {} on miss."""
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


def expand_requirement_value(value: Any) -> list[str]:
    """Normalize a front-matter `requirement:` value into a list of R-* ids.

    Accepted shapes:
      * "R-CDCP-011"
      * "R-CDCP-022..024"  (inclusive range)
      * ["R-CDCP-011", "R-CDCP-012"]
      * "R-CDCP-022..024, R-CDCP-026" (comma-separated mix)

    Unknown / unparseable tokens are dropped silently; the caller can
    decide whether to flag the DEC.
    """
    out: list[str] = []
    if value is None:
        return out

    def add_token(token: str) -> None:
        token = token.strip()
        if not token:
            return
        m = R_RANGE_RE.match(token)
        if m:
            prefix, start_s, end_s = m.groups()
            start, end = int(start_s), int(end_s)
            if end < start:
                start, end = end, start
            # Preserve the original digit width when the start has a
            # leading zero (R-FOO-007..009 -> R-FOO-007, R-FOO-008, ...).
            width = len(start_s)
            for n in range(start, end + 1):
                out.append(f"{prefix}{n:0{width}d}")
            return
        if R_ID_RE.match(token):
            out.append(token)
            return
        # Unknown shape; skip.

    if isinstance(value, list):
        for v in value:
            if isinstance(v, str):
                for part in v.split(","):
                    add_token(part)
    elif isinstance(value, str):
        for part in value.split(","):
            add_token(part)
    return out


def parse_dec_file(path: Path) -> dict[str, Any] | None:
    """Parse one DEC file. Returns the bare id, slug id, and requirement ids."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    fm = parse_front_matter(text)
    dec_id = fm.get("id")
    if not isinstance(dec_id, str) or not dec_id.strip():
        # Fall back to filename id.
        dec_id = path.stem
    dec_id = dec_id.strip()
    m = DEC_BARE_RE.match(dec_id)
    bare = m.group(1) if m else dec_id
    reqs = expand_requirement_value(fm.get("requirement"))
    return {
        "id": dec_id,
        "bare_id": bare,
        "filename": path.name,
        "requirement_ids": reqs,
        "status": str(fm.get("status", "")).strip() or "unknown",
    }


def collect_decs(repo_root: Path) -> list[dict[str, Any]]:
    """Walk <repo_root>/decisions/DEC-*.md. Sorted by filename."""
    decisions_dir = repo_root / "decisions"
    if not decisions_dir.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(decisions_dir.glob("DEC-*.md")):
        if not path.is_file():
            continue
        parsed = parse_dec_file(path)
        if parsed is None:
            continue
        out.append(parsed)
    return out


# ---------------------------------------------------------------------------
# allowlist parsing
# ---------------------------------------------------------------------------


def collect_allowlist_extras(repo_root: Path, decs: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Attach allowlisted R-* ids to DECs named in their note text.

    The spec-check allowlist lists deferred R-* ids. Some of those carry
    a note like "resolved by DEC-PUB-005 (collective coverage)". For
    every such pairing we attach the R-* id to the named DEC's
    requirement set, so the coverage probe sees the full picture.

    Returns a dict {dec_bare_id -> [extra R ids]} for legibility; the
    caller folds these into each DEC's requirement_ids.
    """
    path = repo_root / "decisions" / ".spec-check-allowlist.yaml"
    extras: dict[str, list[str]] = {}
    if not path.is_file():
        return extras
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return extras
    if not isinstance(data, dict):
        return extras
    deferred = data.get("deferred")
    if not isinstance(deferred, list):
        return extras

    bare_index = {d["bare_id"] for d in decs}
    for entry in deferred:
        if not isinstance(entry, dict):
            continue
        rid = entry.get("id")
        if not isinstance(rid, str) or not R_ID_RE.match(rid.strip()):
            continue
        rid = rid.strip()
        note = entry.get("note") or ""
        if not isinstance(note, str):
            continue
        for match in DEC_REF_RE.findall(note):
            bare_m = DEC_BARE_RE.match(match)
            if not bare_m:
                continue
            target_bare = bare_m.group(1)
            if target_bare in bare_index:
                extras.setdefault(target_bare, []).append(rid)
    # Dedupe each list.
    for k, v in extras.items():
        extras[k] = sorted(set(v))
    return extras


# ---------------------------------------------------------------------------
# test discovery + coverage probe
# ---------------------------------------------------------------------------


def discover_test_files(repo_root: Path) -> list[Path]:
    """List candidate test files inside the repo.

    Walks tests/ recursively and the top-level scripts/ for test_*.py.
    Also picks up co-located *.test.ts under src/ for TypeScript repos.
    Skips node_modules / __pycache__ / dist trees.
    """
    out: list[Path] = []

    def walk(start: Path) -> None:
        if not start.is_dir():
            return
        for path in start.rglob("*"):
            # Skip excluded subtrees.
            parts = set(path.parts)
            if parts & EXCLUDE_DIR_NAMES:
                continue
            if not path.is_file():
                continue
            name = path.name
            for pat in TEST_FILENAME_PATTERNS:
                if pat.match(name):
                    out.append(path)
                    break

    walk(repo_root / "tests")
    walk(repo_root / "scripts")
    walk(repo_root / "src")
    # Dedupe + stable order.
    return sorted({p for p in out})


def search_requirement_in_files(req_ids: set[str], files: Iterable[Path]) -> dict[str, list[str]]:
    """Return a {req_id: [test files referencing it]} map.

    Each file is read once and scanned for any of the requirement ids.
    Files that fail to decode as UTF-8 are skipped.
    """
    matches: dict[str, list[str]] = {rid: [] for rid in req_ids}
    if not req_ids:
        return matches
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for rid in req_ids:
            if rid in text:
                matches[rid].append(path.as_posix())
    return matches


# ---------------------------------------------------------------------------
# per-repo orchestration
# ---------------------------------------------------------------------------


def index_repo(name: str, repo_root: Path | None) -> dict[str, Any]:
    """Build a per-repo coverage record.

    Returns:
        {
          "name": repo,
          "state": "ok" | "not checked out",
          "total": int,
          "covered": int,
          "uncovered": int,
          "coverage_pct": float | None,
          "decs": [
            {"id", "bare_id", "requirement_ids", "covered", "matches"}
          ],
        }
    """
    if repo_root is None:
        return {
            "name": name,
            "state": "not checked out",
            "total": 0,
            "covered": 0,
            "uncovered": 0,
            "coverage_pct": None,
            "decs": [],
        }
    decs = collect_decs(repo_root)
    extras = collect_allowlist_extras(repo_root, decs)
    for d in decs:
        more = extras.get(d["bare_id"], [])
        if more:
            merged = list(d["requirement_ids"]) + [r for r in more if r not in d["requirement_ids"]]
            d["requirement_ids"] = merged

    test_files = discover_test_files(repo_root)
    all_req_ids: set[str] = set()
    for d in decs:
        all_req_ids.update(d["requirement_ids"])
    matches = search_requirement_in_files(all_req_ids, test_files)

    covered = 0
    out_decs: list[dict[str, Any]] = []
    for d in decs:
        hits: list[str] = []
        for rid in d["requirement_ids"]:
            if matches.get(rid):
                hits.append(rid)
        is_covered = bool(hits)
        if is_covered:
            covered += 1
        out_decs.append(
            {
                "id": d["id"],
                "bare_id": d["bare_id"],
                "requirement_ids": d["requirement_ids"],
                "covered": is_covered,
                "matched_ids": hits,
            }
        )

    total = len(decs)
    pct = (covered / total * 100.0) if total else None
    return {
        "name": name,
        "state": "ok",
        "total": total,
        "covered": covered,
        "uncovered": total - covered,
        "coverage_pct": pct,
        "decs": out_decs,
    }


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------


def render_report(
    rows: list[dict[str, Any]],
    threshold: float,
    local_root: Path | None,
    now: dt.datetime,
) -> tuple[str, dict[str, Any]]:
    """Render the Markdown report and return (text, portfolio_totals)."""
    today = now.date().isoformat()
    total = sum(r["total"] for r in rows if r["state"] == "ok")
    covered = sum(r["covered"] for r in rows if r["state"] == "ok")
    uncovered = total - covered
    overall_pct = (covered / total * 100.0) if total else 0.0
    gate = "PASS" if overall_pct >= threshold else "FAIL"

    lines: list[str] = [
        f"# DEC test-coverage report - {today}",
        "",
        (
            "Generated by `scripts/dec_coverage_report.py`. For each active "
            "CDCP repo this report counts DECs whose `requirement:` ids are "
            "referenced from a test file. A DEC counts as covered when at "
            "least one of its requirement ids appears in any discovered "
            "test under `tests/`, `scripts/test_*.py`, or co-located "
            "`*.test.ts` under `src/`."
        ),
        "",
        f"- Local root: `{local_root if local_root else 'unresolved'}`",
        f"- Threshold: **{threshold:.1f}%**",
        f"- Portfolio coverage: **{overall_pct:.1f}%** ({covered}/{total})",
        f"- Gate: **{gate}**",
        "",
        "## Per-repo coverage",
        "",
        "| Repo | DECs | Covered | Uncovered | Coverage | State |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        if row["state"] != "ok":
            lines.append(f"| {row['name']} | - | - | - | - | {row['state']} |")
            continue
        pct = row["coverage_pct"]
        pct_cell = f"{pct:.1f}%" if pct is not None else "-"
        lines.append(
            f"| {row['name']} | {row['total']} | {row['covered']} | "
            f"{row['uncovered']} | {pct_cell} | OK |"
        )
    lines.append("")

    # Uncovered DECs per repo. Skipped repos are not listed here; they
    # surface in the "Skipped" block below.
    lines.append("## Uncovered DECs")
    lines.append("")
    any_uncovered = False
    for row in rows:
        if row["state"] != "ok":
            continue
        uncov = [d for d in row["decs"] if not d["covered"]]
        if not uncov:
            continue
        any_uncovered = True
        lines.append(f"### {row['name']} ({len(uncov)} uncovered)")
        lines.append("")
        for d in uncov:
            reqs = ", ".join(f"`{r}`" for r in d["requirement_ids"]) or "(no requirement ids)"
            lines.append(f"- `{d['id']}` -> {reqs}")
        lines.append("")
    if not any_uncovered:
        lines.append("Every DEC in every checked-out repo has at least one")
        lines.append("requirement id referenced from a test file.")
        lines.append("")

    skipped = [r for r in rows if r["state"] != "ok"]
    if skipped:
        lines.append("## Skipped repos")
        lines.append("")
        for r in skipped:
            lines.append(
                f"- `{r['name']}`: not checked out under `local_root`; "
                "skipped so missing siblings on CI do not skew the totals."
            )
        lines.append("")

    lines.append("---")
    lines.append(
        "Regenerated by the `Portfolio audit` workflow. Refresh locally with "
        "`python scripts/dec_coverage_report.py`."
    )
    lines.append("")
    totals = {
        "total_decs": total,
        "decs_with_tests": covered,
        "decs_without_tests": uncovered,
        "coverage_pct": round(overall_pct, 1),
        "gate_pass": overall_pct >= threshold,
    }
    return "\n".join(lines), totals


# ---------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------


def self_test() -> int:
    """Smoke test: synthetic fixture + renderer + range expansion."""
    import tempfile

    errors: list[str] = []

    # Range expansion.
    expanded = expand_requirement_value("R-CDCP-022..024")
    if expanded != ["R-CDCP-022", "R-CDCP-023", "R-CDCP-024"]:
        errors.append(f"range expansion wrong: {expanded}")

    single = expand_requirement_value("R-CDCP-011")
    if single != ["R-CDCP-011"]:
        errors.append(f"single id expansion wrong: {single}")

    list_form = expand_requirement_value(["R-A-001", "R-A-002"])
    if list_form != ["R-A-001", "R-A-002"]:
        errors.append(f"list expansion wrong: {list_form}")

    multi_family = expand_requirement_value("R-TTE-SCHEMA-001")
    if multi_family != ["R-TTE-SCHEMA-001"]:
        errors.append(f"multi-family id wrong: {multi_family}")

    # Synthetic fixture: one covered DEC, one uncovered DEC.
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        decisions = repo / "decisions"
        decisions.mkdir()
        (decisions / "DEC-FOO-001-covered.md").write_text(
            "---\nid: DEC-FOO-001-covered\nrequirement: R-FOO-001\n"
            "status: approved\nreversible: true\n---\n## decision\n",
            encoding="utf-8",
        )
        (decisions / "DEC-FOO-002-uncovered.md").write_text(
            "---\nid: DEC-FOO-002-uncovered\nrequirement: R-FOO-002..003\n"
            "status: approved\nreversible: true\n---\n## decision\n",
            encoding="utf-8",
        )
        tests = repo / "tests"
        tests.mkdir()
        (tests / "test_a.py").write_text(
            "def test_x():\n    # references R-FOO-001 in a comment\n    pass\n",
            encoding="utf-8",
        )

        record = index_repo("fake", repo)
        if record["total"] != 2:
            errors.append(f"expected 2 DECs, got {record['total']}")
        if record["covered"] != 1:
            errors.append(f"expected 1 covered DEC, got {record['covered']}")
        if record["uncovered"] != 1:
            errors.append(f"expected 1 uncovered DEC, got {record['uncovered']}")

        # Allowlist credit: deferred R-FOO-002 noted as covered by
        # DEC-FOO-001 should not flip the second DEC; it should add
        # R-FOO-002 to the first DEC's requirement set and keep the
        # first DEC covered.
        (decisions / ".spec-check-allowlist.yaml").write_text(
            "deferred:\n"
            "  - id: R-FOO-099\n"
            "    note: resolved by DEC-FOO-001 (collective coverage)\n",
            encoding="utf-8",
        )
        record2 = index_repo("fake", repo)
        first = next(d for d in record2["decs"] if d["bare_id"] == "DEC-FOO-001")
        if "R-FOO-099" not in first["requirement_ids"]:
            errors.append("allowlist note did not attach R-FOO-099 to DEC-FOO-001")

        # Renderer.
        now = dt.datetime(2026, 5, 29, tzinfo=dt.timezone.utc)
        rendered, totals = render_report([record2], 50.0, repo.parent, now)
        for needle in (
            "DEC test-coverage report",
            "Per-repo coverage",
            "Uncovered DECs",
            "Portfolio coverage:",
        ):
            if needle not in rendered:
                errors.append(f"rendered output missing {needle!r}")
        if totals["total_decs"] != 2:
            errors.append(f"totals.total_decs wrong: {totals}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print("self-test OK", file=sys.stderr)
    return 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


# Default set of repos the report considers. Pulled from manifest +
# explicit task spec (trace-to-eval-harness + mcp-security-lab are
# active CDCP repos and already appear in the manifest with
# cdcp_status). athena-site itself is included because it ships its own
# DECs.
def repos_to_scan(manifest: dict[str, Any]) -> list[str]:
    """Active CDCP repos in manifest order; ensures the two named in
    the task are present even if the manifest tags change later."""
    out = active_cdcp_repos(manifest)
    for name in ("trace-to-eval-harness", "mcp-security-lab"):
        if name not in out:
            out.append(name)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="portfolio coverage %% required for exit 0 (default 70)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run the smoke test and exit",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    manifest = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
    local_root = resolve_local_root(manifest)
    names = repos_to_scan(manifest)
    now = dt.datetime.now(tz=dt.timezone.utc)

    rows: list[dict[str, Any]] = []
    for name in names:
        repo_root = repo_root_for(name, local_root)
        rows.append(index_repo(name, repo_root))

    rendered, totals = render_report(rows, args.threshold, local_root, now)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(
        f"Wrote {args.output} (portfolio coverage "
        f"{totals['coverage_pct']:.1f}%, {totals['decs_with_tests']}/"
        f"{totals['total_decs']})",
        file=sys.stderr,
    )

    return 0 if totals["gate_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
