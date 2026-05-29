#!/usr/bin/env python3
"""Portfolio status dashboard.

Aggregates per-repo state across the eight active CDCP repos and writes a
human-skimmable Markdown report to `ops/portfolio-status.md`. Designed to
run against committed state on a local checkout (no GitHub Actions API calls):
the dashboard reflects what the repos look like on disk right now.

Source of truth for the active-repo list is `ops/portfolio-manifest.yml`; the
dashboard picks the subset with `status: active` AND a `cdcp_status` field, so
the workshop and drawer repos drop out automatically.

Per repo it reports:
    - recent commits (last 7 days), latest SHA + author + date
    - latest three DEC files by mtime
    - latest three dreams (week-stamped subdirectories under `dreams/`)
    - count of `.github/workflows/*.yml` files
    - schema cache freshness check exit code (when the script exists)
    - count of `ops/run-records/*.json` files
    - count of `ops/replay-records/*/*.json` files (one subdir per run)

Run:
    python scripts/portfolio_dashboard.py
    python scripts/portfolio_dashboard.py --output ops/portfolio-status.md
    python scripts/portfolio_dashboard.py --self-test
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "ops" / "portfolio-manifest.yml"
DEFAULT_OUTPUT = ROOT / "ops" / "portfolio-status.md"

RECENT_COMMITS_WINDOW_DAYS = 7
LATEST_DECS_COUNT = 3
LATEST_DREAMS_COUNT = 3


# ---------------------------------------------------------------------------
# repo probes
# ---------------------------------------------------------------------------


def run_git(repo_root: Path, *args: str) -> str:
    """Run a git command in repo_root. Returns stdout (stripped), or empty on failure."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def recent_commits(repo_root: Path, days: int = RECENT_COMMITS_WINDOW_DAYS) -> dict[str, Any]:
    """Count commits in the last `days` days and capture the latest SHA, author, date."""
    since = f"{days} days ago"
    count_out = run_git(repo_root, "rev-list", "--count", f"--since={since}", "HEAD")
    try:
        count = int(count_out) if count_out else 0
    except ValueError:
        count = 0
    head_out = run_git(repo_root, "log", "-1", "--format=%h%x09%an%x09%ad", "--date=short", "HEAD")
    latest_sha = ""
    latest_author = ""
    latest_date = ""
    if head_out:
        parts = head_out.split("\t")
        if len(parts) >= 3:
            latest_sha, latest_author, latest_date = parts[0], parts[1], parts[2]
    return {
        "count": count,
        "latest_sha": latest_sha,
        "latest_author": latest_author,
        "latest_date": latest_date,
    }


def latest_decisions(repo_root: Path, n: int = LATEST_DECS_COUNT) -> list[dict[str, Any]]:
    """Latest n DEC-*.md files in `decisions/`, sorted by mtime descending."""
    decisions_dir = repo_root / "decisions"
    if not decisions_dir.is_dir():
        return []
    files = sorted(
        (p for p in decisions_dir.glob("DEC-*.md") if p.is_file()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    out: list[dict[str, Any]] = []
    for p in files[:n]:
        out.append({
            "name": p.name,
            "mtime": dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d"),
        })
    return out


def latest_dreams(repo_root: Path, n: int = LATEST_DREAMS_COUNT) -> list[dict[str, Any]]:
    """Latest n dream entries. Looks at `ops/dreams/` first, then `dreams/`.

    A dream is a subdirectory; we report the subdirectory name and mtime.
    """
    for candidate in (repo_root / "ops" / "dreams", repo_root / "dreams"):
        if candidate.is_dir():
            subdirs = [p for p in candidate.iterdir() if p.is_dir()]
            subdirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            return [
                {
                    "name": p.name,
                    "mtime": dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d"),
                }
                for p in subdirs[:n]
            ]
    return []


def workflow_count(repo_root: Path) -> int:
    """Count `.github/workflows/*.yml` (and `.yaml`) files."""
    wf_dir = repo_root / ".github" / "workflows"
    if not wf_dir.is_dir():
        return 0
    return sum(1 for p in wf_dir.iterdir() if p.is_file() and p.suffix in (".yml", ".yaml"))


def schema_cache_freshness_exit(repo_root: Path) -> int | None:
    """Run `scripts/check_schema_cache_freshness.py` if present. Return exit code, or None if absent."""
    script = repo_root / "scripts" / "check_schema_cache_freshness.py"
    if not script.is_file():
        return None
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        return result.returncode
    except (subprocess.TimeoutExpired, OSError):
        return -1


def run_record_count(repo_root: Path) -> int:
    """Count `ops/run-records/*.json` files."""
    run_dir = repo_root / "ops" / "run-records"
    if not run_dir.is_dir():
        return 0
    return sum(1 for p in run_dir.glob("*.json") if p.is_file())


def replay_artifact_count(repo_root: Path) -> int:
    """Count `ops/replay-records/*/*.json` files (one subdir per run)."""
    replay_dir = repo_root / "ops" / "replay-records"
    if not replay_dir.is_dir():
        return 0
    return sum(1 for p in replay_dir.glob("*/*.json") if p.is_file())


# ---------------------------------------------------------------------------
# manifest / root resolution
# ---------------------------------------------------------------------------


def resolve_local_root(manifest: dict[str, Any]) -> Path | None:
    """Workspace path where sibling repos live. Mirrors portfolio_audit.py."""
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
    """Active repos that carry a `cdcp_status` field. Order preserved from the manifest."""
    out: list[str] = []
    for r in manifest.get("repos", []):
        if r.get("status") == "active" and r.get("cdcp_status") is not None:
            out.append(r["name"])
    return out


# ---------------------------------------------------------------------------
# probe + render
# ---------------------------------------------------------------------------


def probe_repo(repo_root: Path) -> dict[str, Any]:
    """Run every probe against repo_root and return the aggregated dict."""
    return {
        "commits": recent_commits(repo_root),
        "decisions": latest_decisions(repo_root),
        "dreams": latest_dreams(repo_root),
        "workflow_count": workflow_count(repo_root),
        "schema_cache_exit": schema_cache_freshness_exit(repo_root),
        "run_records": run_record_count(repo_root),
        "replay_artifacts": replay_artifact_count(repo_root),
    }


def render_repo_section(name: str, data: dict[str, Any] | None) -> str:
    """Render one repo block. data is None when the repo is not checked out."""
    lines: list[str] = [f"### {name}", ""]
    if data is None:
        lines.append("Not checked out under local_root. Skipped.")
        lines.append("")
        return "\n".join(lines)

    c = data["commits"]
    if c["count"] > 0 and c["latest_sha"]:
        lines.append(
            f"- Commits in last {RECENT_COMMITS_WINDOW_DAYS} days: **{c['count']}** "
            f"(latest `{c['latest_sha']}` by {c['latest_author']} on {c['latest_date']})"
        )
    elif c["latest_sha"]:
        lines.append(
            f"- Commits in last {RECENT_COMMITS_WINDOW_DAYS} days: **0** "
            f"(HEAD `{c['latest_sha']}` by {c['latest_author']} on {c['latest_date']})"
        )
    else:
        lines.append(f"- Commits in last {RECENT_COMMITS_WINDOW_DAYS} days: no git data")

    decs = data["decisions"]
    if decs:
        lines.append(f"- Latest DECs ({len(decs)}):")
        for d in decs:
            lines.append(f"  - `{d['name']}` ({d['mtime']})")
    else:
        lines.append("- Latest DECs: none")

    dreams = data["dreams"]
    if dreams:
        lines.append(f"- Latest dreams ({len(dreams)}):")
        for d in dreams:
            lines.append(f"  - `{d['name']}` ({d['mtime']})")
    else:
        lines.append("- Latest dreams: none")

    lines.append(f"- CI workflow files: **{data['workflow_count']}**")

    sce = data["schema_cache_exit"]
    if sce is None:
        sc_text = "n/a (script absent)"
    elif sce == 0:
        sc_text = "fresh (exit 0)"
    elif sce == -1:
        sc_text = "errored (timeout or OS error)"
    else:
        sc_text = f"stale (exit {sce})"
    lines.append(f"- Schema cache freshness: {sc_text}")

    lines.append(f"- Run records: **{data['run_records']}**")
    lines.append(f"- Replay artifacts: **{data['replay_artifacts']}**")
    lines.append("")
    return "\n".join(lines)


def render_dashboard(
    repos: list[str], probes: dict[str, dict[str, Any] | None], local_root: Path | None
) -> str:
    today = dt.date.today().isoformat()
    out: list[str] = [
        f"# Portfolio status dashboard — {today}",
        "",
        (
            f"Generated by `scripts/portfolio_dashboard.py` from the local checkout at "
            f"`{local_root if local_root else 'unresolved'}`. Reflects committed state only — "
            "no GitHub Actions API call."
        ),
        "",
        "## Portfolio summary",
        "",
    ]

    # Aggregate totals across repos that probed cleanly.
    total_commits = 0
    total_decs_dir = 0
    total_dreams_dir = 0
    total_run_records = 0
    total_replay_artifacts = 0
    total_workflows = 0
    probed = 0
    for name in repos:
        data = probes.get(name)
        if data is None:
            continue
        probed += 1
        total_commits += data["commits"]["count"]
        total_decs_dir += len(data["decisions"])  # latest-3 count, not all-time
        total_dreams_dir += len(data["dreams"])
        total_run_records += data["run_records"]
        total_replay_artifacts += data["replay_artifacts"]
        total_workflows += data["workflow_count"]

    summary_rows = [
        "| Metric | Value |",
        "|---|---|",
        f"| Repos indexed | {probed} / {len(repos)} |",
        f"| Commits (last {RECENT_COMMITS_WINDOW_DAYS} days, summed) | {total_commits} |",
        f"| Latest-DEC entries shown (sum of per-repo top 3) | {total_decs_dir} |",
        f"| Latest-dream entries shown (sum of per-repo top 3) | {total_dreams_dir} |",
        f"| Run records (sum) | {total_run_records} |",
        f"| Replay artifacts (sum) | {total_replay_artifacts} |",
        f"| CI workflow files (sum) | {total_workflows} |",
    ]
    out.extend(summary_rows)
    out.append("")
    out.append("## Per-repo detail")
    out.append("")
    for name in repos:
        out.append(render_repo_section(name, probes.get(name)))
    out.append("---")
    out.append(
        "Regenerated weekly by the `Portfolio audit` workflow. To refresh locally, run "
        "`python scripts/portfolio_dashboard.py`."
    )
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# self-test (smoke)
# ---------------------------------------------------------------------------


def self_test() -> int:
    """Smoke test: probe athena-site itself + render a tiny dashboard. Exit 0 on success."""
    errors: list[str] = []
    manifest = yaml.safe_load(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
    repos = active_cdcp_repos(manifest)
    if len(repos) < 1:
        errors.append("expected at least 1 active CDCP repo from the manifest")
    if "athena-site" not in repos:
        errors.append("expected athena-site to be among the active CDCP repos")

    data = probe_repo(ROOT)
    if data["commits"]["latest_sha"] == "":
        errors.append("expected a HEAD SHA from athena-site git")
    if data["workflow_count"] < 1:
        errors.append("expected at least one workflow file under .github/workflows/")
    decs = data["decisions"]
    if not decs:
        errors.append("expected at least one DEC under decisions/")

    rendered = render_dashboard(["athena-site"], {"athena-site": data}, ROOT.parent)
    if "Portfolio status dashboard" not in rendered:
        errors.append("rendered output missing dashboard header")
    if "athena-site" not in rendered:
        errors.append("rendered output missing athena-site section")
    if "Portfolio summary" not in rendered:
        errors.append("rendered output missing portfolio summary block")

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
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
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

    probes: dict[str, dict[str, Any] | None] = {}
    for name in repos:
        if name == "athena-site":
            repo_root = ROOT
        elif local_root is None:
            probes[name] = None
            continue
        else:
            repo_root = local_root / name
        if not repo_root.is_dir():
            probes[name] = None
            continue
        probes[name] = probe_repo(repo_root)

    rendered = render_dashboard(repos, probes, local_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Wrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
