#!/usr/bin/env python3
"""Evidence quorum sentinel.

The replay-equivalence claim in DEC-CDCP-011 only holds while replay
artifacts keep landing. A repo can pass every CI gate today, ship no
replays for a month, and silently fall out of the evidence chain. This
sentinel watches the floor: for each active product repo, count the
replay artifacts produced in the recent window and fail when any repo
falls below the quorum threshold.

For each active product repo declared in `ops/portfolio-manifest.yml`
that ships replays (chip-supply-chain-map, supplier-risk-rag-agent,
procurement-negotiation-lab, ai-field-brief), the sentinel:

    1. Globs `ops/replay-records/<run-id>/*.json` files
    2. Parses each file's timestamp from the first present field of
       `created_at`, `replay_timestamp`, `finished_at`, `started_at`,
       falling back to the file mtime when none are present
    3. Counts how many files land in the last `--window-days` window
    4. Compares to the per-repo quorum threshold (default 1)
    5. Writes a Markdown report to `ops/evidence-quorum-report.md`
    6. Exits 0 when every repo meets quorum; exits 1 otherwise

Run:
    python scripts/evidence_quorum_sentinel.py
    python scripts/evidence_quorum_sentinel.py --window-days 30 --threshold 1
    python scripts/evidence_quorum_sentinel.py --self-test
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "ops" / "portfolio-manifest.yml"
DEFAULT_OUTPUT = ROOT / "ops" / "evidence-quorum-report.md"

DEFAULT_WINDOW_DAYS = 30
DEFAULT_THRESHOLD = 1

# Repos that ship replay artifacts. The portfolio-manifest names that match
# the spec's short labels chip-map / supplier-risk / procurement-lab /
# ai-field-brief. athena-site itself is meta-repo and does not produce replays.
WATCHED_REPOS = (
    "chip-supply-chain-map",
    "supplier-risk-rag-agent",
    "procurement-negotiation-lab",
    "ai-field-brief",
)

TIMESTAMP_FIELDS = ("created_at", "replay_timestamp", "finished_at", "started_at")


# ---------------------------------------------------------------------------
# manifest / root resolution (mirrors portfolio_dashboard.py)
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


def watched_active_repos(manifest: dict[str, Any]) -> list[str]:
    """Intersect WATCHED_REPOS with active repos in the manifest, preserving manifest order."""
    active = {
        r["name"]
        for r in manifest.get("repos", [])
        if r.get("status") == "active" and r.get("name") in WATCHED_REPOS
    }
    return [name for name in WATCHED_REPOS if name in active]


# ---------------------------------------------------------------------------
# timestamp + count probe
# ---------------------------------------------------------------------------


def parse_iso_timestamp(value: str) -> dt.datetime | None:
    """Parse an ISO-8601 timestamp string. Accepts trailing Z. Returns None on failure."""
    if not isinstance(value, str) or not value:
        return None
    s = value.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return dt.datetime.fromisoformat(s)
    except ValueError:
        return None


def artifact_timestamp(path: Path) -> tuple[dt.datetime, str]:
    """Pick a timestamp for a replay artifact.

    Looks for the first present TIMESTAMP_FIELDS entry at the top of the JSON
    document. Falls back to the file mtime when no field is present or the file
    cannot be parsed. Returns the timestamp and the source label.
    """
    try:
        with path.open(encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, json.JSONDecodeError):
        doc = None

    if isinstance(doc, dict):
        for field in TIMESTAMP_FIELDS:
            ts = parse_iso_timestamp(doc.get(field, ""))
            if ts is not None:
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=dt.timezone.utc)
                return ts, field

    mtime = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc)
    return mtime, "mtime"


def count_recent_artifacts(
    repo_root: Path, window_days: int, now: dt.datetime | None = None
) -> dict[str, Any]:
    """Walk ops/replay-records/<run-id>/*.json under repo_root and bucket by recency."""
    if now is None:
        now = dt.datetime.now(tz=dt.timezone.utc)
    cutoff = now - dt.timedelta(days=window_days)

    replay_dir = repo_root / "ops" / "replay-records"
    result: dict[str, Any] = {
        "total": 0,
        "recent": 0,
        "latest_ts": None,
        "latest_path": None,
        "directory_present": replay_dir.is_dir(),
    }
    if not replay_dir.is_dir():
        return result

    latest_ts: dt.datetime | None = None
    latest_path: Path | None = None
    for path in replay_dir.glob("*/*.json"):
        if not path.is_file():
            continue
        result["total"] += 1
        ts, _src = artifact_timestamp(path)
        if ts >= cutoff:
            result["recent"] += 1
        if latest_ts is None or ts > latest_ts:
            latest_ts = ts
            latest_path = path

    if latest_ts is not None:
        result["latest_ts"] = latest_ts.isoformat()
    if latest_path is not None:
        result["latest_path"] = latest_path.relative_to(repo_root).as_posix()
    return result


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------


def render_report(
    rows: list[dict[str, Any]],
    window_days: int,
    threshold: int,
    local_root: Path | None,
    now: dt.datetime,
) -> str:
    today = now.date().isoformat()
    all_pass = all(row["pass"] for row in rows) if rows else False
    overall = "PASS" if all_pass else "FAIL"

    lines: list[str] = [
        f"# Evidence quorum sentinel report - {today}",
        "",
        (
            "Generated by `scripts/evidence_quorum_sentinel.py`. Counts replay "
            f"artifacts under `ops/replay-records/<run-id>/*.json` per repo in "
            f"the last {window_days} days against a per-repo quorum of "
            f"{threshold}."
        ),
        "",
        f"- Local root: `{local_root if local_root else 'unresolved'}`",
        f"- Window: {window_days} days",
        f"- Per-repo quorum threshold: {threshold}",
        f"- Overall: **{overall}**",
        "",
        "## Per-repo counts",
        "",
        "| Repo | Recent | Total | Threshold | Status | Latest artifact |",
        "|---|---:|---:|---:|---|---|",
    ]
    for row in rows:
        status = "PASS" if row["pass"] else "FAIL"
        latest = row.get("latest_path") or "-"
        if row["checked_out"]:
            lines.append(
                f"| {row['name']} | {row['recent']} | {row['total']} | "
                f"{threshold} | {status} | `{latest}` |"
            )
        else:
            lines.append(
                f"| {row['name']} | - | - | {threshold} | SKIPPED | not checked out |"
            )
    lines.append("")

    failing = [row for row in rows if row["checked_out"] and not row["pass"]]
    if failing:
        lines.append("## Failing repos")
        lines.append("")
        for row in failing:
            lines.append(
                f"- **{row['name']}**: {row['recent']} replay artifact(s) in "
                f"the last {window_days} days; quorum is {threshold}. "
                f"Latest artifact: `{row.get('latest_path') or 'none'}` "
                f"({row.get('latest_ts') or 'no timestamp'})."
            )
        lines.append("")
    else:
        lines.append("## Failing repos")
        lines.append("")
        lines.append("None. Every watched repo meets the quorum.")
        lines.append("")

    skipped = [row for row in rows if not row["checked_out"]]
    if skipped:
        lines.append("## Skipped repos")
        lines.append("")
        for row in skipped:
            lines.append(
                f"- `{row['name']}`: not checked out under `local_root`; "
                "sentinel cannot read its replay-records on this host."
            )
        lines.append("")

    lines.append("---")
    lines.append(
        "Regenerated by the `Portfolio audit` workflow. Refresh locally with "
        "`python scripts/evidence_quorum_sentinel.py`."
    )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------


def self_test() -> int:
    """Smoke test: parse a synthetic artifact and render a minimal report."""
    errors: list[str] = []

    # Timestamp parsing.
    ts = parse_iso_timestamp("2026-05-29T12:00:00Z")
    if ts is None or ts.year != 2026:
        errors.append("expected to parse trailing-Z ISO timestamp")
    if parse_iso_timestamp("not-a-date") is not None:
        errors.append("expected None for invalid timestamp")

    # Manifest reads cleanly and yields at least one watched repo.
    manifest = yaml.safe_load(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
    watched = watched_active_repos(manifest)
    if not watched:
        errors.append("expected at least one watched repo from the manifest")

    # Renderer produces a report with the headline blocks.
    now = dt.datetime(2026, 5, 29, tzinfo=dt.timezone.utc)
    fake_rows = [
        {
            "name": "chip-supply-chain-map",
            "recent": 2,
            "total": 5,
            "pass": True,
            "checked_out": True,
            "latest_path": "ops/replay-records/run-abc/artifact.json",
            "latest_ts": "2026-05-28T12:00:00+00:00",
        },
        {
            "name": "supplier-risk-rag-agent",
            "recent": 0,
            "total": 0,
            "pass": False,
            "checked_out": True,
            "latest_path": None,
            "latest_ts": None,
        },
    ]
    rendered = render_report(fake_rows, 30, 1, ROOT.parent, now)
    for needle in (
        "Evidence quorum sentinel report",
        "Per-repo counts",
        "Failing repos",
        "supplier-risk-rag-agent",
        "chip-supply-chain-map",
    ):
        if needle not in rendered:
            errors.append(f"rendered output missing {needle!r}")

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
        "--window-days",
        type=int,
        default=DEFAULT_WINDOW_DAYS,
        help="recency window in days (default 30)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD,
        help="per-repo quorum threshold (default 1)",
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
    repos = watched_active_repos(manifest)
    now = dt.datetime.now(tz=dt.timezone.utc)

    rows: list[dict[str, Any]] = []
    for name in repos:
        if local_root is None:
            rows.append(
                {
                    "name": name,
                    "recent": 0,
                    "total": 0,
                    "pass": False,
                    "checked_out": False,
                    "latest_path": None,
                    "latest_ts": None,
                }
            )
            continue
        repo_root = local_root / name
        if not repo_root.is_dir():
            rows.append(
                {
                    "name": name,
                    "recent": 0,
                    "total": 0,
                    "pass": False,
                    "checked_out": False,
                    "latest_path": None,
                    "latest_ts": None,
                }
            )
            continue
        counts = count_recent_artifacts(repo_root, args.window_days, now=now)
        rows.append(
            {
                "name": name,
                "recent": counts["recent"],
                "total": counts["total"],
                "pass": counts["recent"] >= args.threshold,
                "checked_out": True,
                "latest_path": counts["latest_path"],
                "latest_ts": counts["latest_ts"],
            }
        )

    rendered = render_report(rows, args.window_days, args.threshold, local_root, now)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Wrote {args.output}", file=sys.stderr)

    # Fail when any checked-out repo falls below quorum. Repos that are not
    # checked out cannot be evaluated on this host; they render as SKIPPED and
    # do not contribute to the exit code so that CI (where siblings are absent)
    # does not always fail. The portfolio-audit workflow runs all sentinels
    # with continue-on-error so one sentinel failing does not mask the others.
    failing = [r for r in rows if r["checked_out"] and not r["pass"]]
    if failing:
        names = ", ".join(r["name"] for r in failing)
        print(f"evidence-quorum: FAIL ({names})", file=sys.stderr)
        return 1
    print(
        f"evidence-quorum: OK ({len([r for r in rows if r['checked_out']])} repo(s) checked)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
