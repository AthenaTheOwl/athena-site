#!/usr/bin/env python3
"""Portfolio audit. Reads ops/portfolio-manifest.yml, runs checks, writes ops/portfolio-health.md.

Exits non-zero if any critical check fails. With --auto-issue, opens GitHub issues for
critical failures (requires gh CLI authenticated, e.g. via GITHUB_TOKEN in CI).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "ops" / "portfolio-manifest.yml"
DEFAULT_OUTPUT = ROOT / "ops" / "portfolio-health.md"
USER_AGENT = "AthenaTheOwl-portfolio-audit"
OWNER = "AthenaTheOwl"

# Markers each cdcp_status label expects to find in the repo. The check
# walks the local clone (resolved via local_root) and reports drift when
# a declared label has missing markers, or when markers exist for a label
# the manifest hasn't declared.
CDCP_LABEL_MARKERS: dict[str, list[str]] = {
    "cdcp-lite": ["has_specs", "has_decisions"],
    "installed": ["has_specs", "has_decisions", "has_agents_dir", "has_validators"],
    "operating-model": ["has_agents_roles", "has_ops_release_ledger"],
    "first-decs": ["has_decisions"],
    "dreams-promoted": ["has_dreams", "has_dream_output"],
    "skills-graduated": ["has_skills"],
    "decisions-ledger": ["has_decisions"],
    # markdown-only, markdown-only, meta-repo, cross-repo-schemas, contracts-owner
    # are scope declarations rather than installation markers; the check leaves
    # them alone.
}


def run_gh(*args: str) -> str:
    """Run `gh` CLI, return stdout (stripped). Empty string on failure."""
    result = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def http_status(url: str) -> int:
    """HEAD-then-GET fallback. Returns status code, or 0 on connection error."""
    headers = {"User-Agent": USER_AGENT}
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True, headers=headers) as c:
            r = c.head(url)
            if r.status_code in (405, 501):
                r = c.get(url)
            return r.status_code
    except httpx.HTTPError:
        return 0


def parse_iso(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def days_since(d: dt.datetime) -> int:
    now = dt.datetime.now(dt.timezone.utc)
    return (now - d).days


def repo_last_commit_date(repo: str) -> dt.datetime | None:
    out = run_gh("api", f"repos/{OWNER}/{repo}/commits", "--jq", ".[0].commit.author.date")
    return parse_iso(out) if out else None


def file_last_commit_date(repo: str, path: str) -> dt.datetime | None:
    out = run_gh(
        "api", f"repos/{OWNER}/{repo}/commits",
        "-X", "GET", "-f", f"path={path}", "-f", "per_page=1",
        "--jq", ".[0].commit.author.date",
    )
    return parse_iso(out) if out else None


def fork_count(repo: str) -> int:
    out = run_gh("api", f"repos/{OWNER}/{repo}/forks", "--jq", "length")
    try:
        return int(out)
    except (ValueError, TypeError):
        return -1


class Audit:
    def __init__(self, manifest: dict[str, Any]):
        self.manifest = manifest
        self.sections: list[tuple[str, str]] = []
        self.issues: list[tuple[str, str, str]] = []  # (repo, title, body)
        self.critical = False

    def add_section(self, heading: str, body: str) -> None:
        self.sections.append((heading, body))

    def flag_critical(self, repo: str, title: str, body: str) -> None:
        self.critical = True
        self.issues.append((repo, title, body))

    def render(self) -> str:
        today = dt.date.today().isoformat()
        out = [f"# Portfolio health — {today}", ""]
        for h, b in self.sections:
            out.append(h)
            out.append("")
            out.append(b)
            out.append("")
        if not self.critical:
            out.append("---")
            out.append("All critical checks passed.")
        else:
            out.append("---")
            out.append(f"**{len(self.issues)} critical issue(s) detected.** See sections above.")
        return "\n".join(out) + "\n"


def section_deploys(audit: Audit) -> None:
    rows = ["| Repo | URL | Status |", "|---|---|---|"]
    for r in audit.manifest["repos"]:
        url = r.get("deploy_url")
        if not url:
            continue
        if url == "<TBD>":
            rows.append(f"| {r['name']} | — | ⏳ pending deploy |")
            continue
        status = http_status(url)
        ok = 200 <= status < 400
        marker = "✅" if ok else "❌"
        rows.append(f"| {r['name']} | {url} | {marker} {status} |")
        if not ok:
            audit.flag_critical(
                "athena-site",
                f"Deploy down: {r['name']} returned {status}",
                f"Audit detected `{r['name']}` ({url}) returning HTTP `{status}`.\n\nFiled by `portfolio-audit` workflow.",
            )
    audit.add_section("## Deploys", "\n".join(rows))


def section_freshness(audit: Audit) -> None:
    rows = ["| Repo | Path | Age (days) | Threshold | Status |", "|---|---|---|---|---|"]
    any_rows = False
    for r in audit.manifest["repos"]:
        ff = r.get("file_freshness")
        if not ff:
            continue
        any_rows = True
        date = file_last_commit_date(r["name"], ff["path"])
        if date is None:
            rows.append(f"| {r['name']} | {ff['path']} | ? | {ff['threshold_days']} | ⚠️ no data |")
            continue
        age = days_since(date)
        threshold = ff["threshold_days"]
        marker = "✅" if age < threshold else "⚠️"
        rows.append(f"| {r['name']} | {ff['path']} | {age} | {threshold} | {marker} |")
        if age >= threshold:
            audit.flag_critical(
                r["name"],
                f"Stale data: {ff['path']} is {age} days old",
                f"`{ff['path']}` has not been touched in {age} days (threshold: {ff['threshold_days']}).\n\nReview, refresh, or extend the threshold in `portfolio-manifest.yml`.",
            )
    if any_rows:
        audit.add_section("## File freshness", "\n".join(rows))


def section_stale_active(audit: Audit) -> None:
    threshold = audit.manifest["stale_active_threshold_days"]
    rows = ["| Repo | Last commit (days ago) | Status |", "|---|---|---|"]
    for r in audit.manifest["repos"]:
        if r["status"] != "active":
            continue
        date = repo_last_commit_date(r["name"])
        if date is None:
            rows.append(f"| {r['name']} | ? | ⚠️ no data |")
            continue
        age = days_since(date)
        marker = "✅" if age < threshold else "⚠️"
        rows.append(f"| {r['name']} | {age} | {marker} |")
        if age >= threshold:
            audit.flag_critical(
                "athena-site",
                f"Stale active repo: {r['name']} ({age}d)",
                f"`{r['name']}` is labeled `status: active` but has no commits in {age} days (threshold: {threshold}).\n\nEither commit, or reconsider the status label in `portfolio-manifest.yml` and `doors.json`.",
            )
    audit.add_section(f"## Stale active repos (threshold: {threshold}d)", "\n".join(rows))


def section_forks(audit: Audit) -> None:
    rows = ["| Repo | Forks | Status |", "|---|---|---|"]
    any_rows = False
    for r in audit.manifest["repos"]:
        if not r.get("fork_check"):
            continue
        any_rows = True
        n = fork_count(r["name"])
        marker = "✅" if n == 0 else "⚠️"
        rows.append(f"| {r['name']} | {n} | {marker} |")
        if n != 0:
            audit.flag_critical(
                "athena-site",
                f"Starforge fork detected: {r['name']} has {n} fork(s)",
                f"`{r['name']}` is part of the Starforge cluster (history was force-rewritten to scrub later-act content). A new fork retains full pre-rewrite history.\n\nReview at: https://github.com/{OWNER}/{r['name']}/network/members",
            )
    if any_rows:
        audit.add_section("## Starforge cluster forks", "\n".join(rows))


def section_royal_road(audit: Audit) -> None:
    url = audit.manifest["royal_road"]["url"]
    status = http_status(url)
    if status == 0:
        body = f"- {url} — ❓ unreachable from CI"
    elif status in (403, 404, 429, 503):
        # Royal Road blocks non-browser User-Agents with various codes.
        # Treat all of these as "skipped, check manually" rather than failures.
        body = f"- {url} — ⏭️ skipped (HTTP {status}; likely anti-bot block; check manually)"
    else:
        marker = "✅" if 200 <= status < 400 else "⚠️"
        body = f"- {url} — {marker} {status}"
    audit.add_section("## Royal Road", body)


def section_drift(audit: Audit) -> None:
    """doors.json vs profile README drift check.

    Both must list the same door numbers + names.
    """
    body_lines: list[str] = []
    doors_json = ROOT / "src" / "content" / "doors.json"
    if not doors_json.exists():
        body_lines.append("- doors.json: not found ⚠️")
    else:
        try:
            doors = json.loads(doors_json.read_text(encoding="utf-8"))
            body_lines.append(f"- doors.json: {len(doors)} entries ✅")
        except json.JSONDecodeError as e:
            body_lines.append(f"- doors.json: parse error ⚠️ ({e})")
            audit.flag_critical(
                "athena-site",
                "doors.json fails to parse",
                f"```\n{e}\n```",
            )

    # Note: profile README cross-check would require a sibling clone or
    # gh api fetch. Skipped in v1 for simplicity. Add later if drift becomes
    # a real problem.

    audit.add_section("## Manifest drift", "\n".join(body_lines))


def resolve_local_root(manifest: dict[str, Any]) -> Path | None:
    """Resolve the workspace path where sibling product repos are checked out.

    Order of precedence: RANDOM_APPS_ROOT env var, then `local_root` in the
    manifest. Returns None if neither resolves to an existing directory.
    """
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


def walk_repo_markers(repo_root: Path) -> dict[str, bool]:
    """Probe filesystem for CDCP install markers. Cheap stat-only checks."""
    dreams_dir = repo_root / "dreams"
    skills_dir = repo_root / ".agents" / "skills"
    scripts_dir = repo_root / "scripts"
    return {
        "has_specs": (repo_root / "specs").is_dir(),
        "has_decisions": (repo_root / "decisions").is_dir(),
        "has_agents_dir": (repo_root / ".agents").is_dir(),
        "has_agents_roles": (repo_root / ".agents" / "roles").is_dir(),
        "has_dreams": dreams_dir.is_dir(),
        "has_dream_output": (
            any(dreams_dir.glob("[0-9][0-9][0-9][0-9]-W*/report.md"))
            if dreams_dir.is_dir() else False
        ),
        "has_skills": (
            skills_dir.is_dir()
            and any(
                p for p in skills_dir.iterdir()
                if p.name not in {"README.md", ".gitkeep"}
            )
        ),
        "has_ops_release_ledger": (repo_root / "ops" / "RELEASE_LEDGER.md").is_file(),
        "has_validators": all(
            (scripts_dir / f"validate_{x}.py").is_file()
            for x in ("decisions", "roles", "tools", "policies")
        ),
    }


def cdcp_drift(declared: list[str], markers: dict[str, bool]) -> list[str]:
    """Return human-readable drift items between declared labels and markers."""
    drift: list[str] = []
    declared_set = set(declared)
    for label in declared:
        expected = CDCP_LABEL_MARKERS.get(label)
        if not expected:
            continue
        missing = [m for m in expected if not markers.get(m, False)]
        if missing:
            drift.append(f"declares `{label}` but missing: {', '.join(missing)}")
    # Reverse direction: markers present that suggest an undeclared label.
    full_install = all(markers.get(m, False) for m in CDCP_LABEL_MARKERS["installed"])
    if full_install and "installed" not in declared_set and "markdown-only" not in declared_set:
        drift.append("repo has full install markers but `installed` not declared")
    if markers.get("has_dream_output") and "dreams-promoted" not in declared_set:
        drift.append("dream report present but `dreams-promoted` not declared")
    if markers.get("has_skills") and "skills-graduated" not in declared_set:
        drift.append("skill directory populated but `skills-graduated` not declared")
    return drift


def section_cdcp_status(audit: Audit, local_root: Path | None) -> None:
    """CDCP install status per repo. Walks the local clone to verify drift.

    The product repo's own gates prove the records work; this section
    cross-checks the manifest declaration against what's actually on disk
    so the throughline stays honest.
    """
    rows = ["| Repo | Door | CDCP status | Drift |", "|---|---|---|---|"]
    any_rows = False
    for r in audit.manifest["repos"]:
        cs = r.get("cdcp_status")
        if cs is None:
            continue
        any_rows = True
        declared = cs if isinstance(cs, list) else [str(cs)]
        value = ", ".join(declared)

        drift_text = "n/a"
        if local_root is None:
            drift_text = "⚠️ local_root unresolved"
        elif r["name"] == "athena-site":
            # athena-site is the meta-repo; markers don't apply here.
            drift_text = "—"
        else:
            repo_root = local_root / r["name"]
            if not repo_root.is_dir():
                drift_text = "⚠️ not checked out"
            else:
                markers = walk_repo_markers(repo_root)
                drift = cdcp_drift(declared, markers)
                if drift:
                    drift_text = "; ".join(drift)
                    audit.flag_critical(
                        r["name"],
                        f"CDCP drift: {r['name']}",
                        f"`portfolio-manifest.yml` declares `cdcp_status: {value}` "
                        f"but the local clone shows drift:\n\n- "
                        + "\n- ".join(drift)
                        + "\n\nEither update the manifest to match reality or "
                          "close the gap in the product repo.",
                    )
                else:
                    drift_text = "✅"
        rows.append(f"| {r['name']} | {r.get('door', '-')} | {value} | {drift_text} |")
    if any_rows:
        audit.add_section("## CDCP status", "\n".join(rows))


def section_anthropic(audit: Audit) -> None:
    if audit.manifest["anthropic"].get("manual_check_only"):
        body = (
            "Manual quarterly check required.\n\n"
            f"Required models: {', '.join(audit.manifest['anthropic']['required_models'])}\n\n"
            "Verify at: https://docs.anthropic.com/en/docs/about-claude/model-deprecations"
        )
        audit.add_section("## Anthropic models", body)


def maybe_create_issues(audit: Audit) -> None:
    seen: set[tuple[str, str]] = set()
    for repo, title, body in audit.issues:
        if (repo, title) in seen:
            continue
        seen.add((repo, title))
        # Look for an existing open issue with the same title to avoid duplicates.
        existing = run_gh(
            "issue", "list",
            "--repo", f"{OWNER}/{repo}",
            "--state", "open",
            "--search", f'"{title}" in:title',
            "--json", "number",
            "--jq", "length",
        )
        if existing and existing != "0":
            print(f"  (skipping duplicate) {repo}: {title}", file=sys.stderr)
            continue
        run_gh(
            "issue", "create",
            "--repo", f"{OWNER}/{repo}",
            "--title", title,
            "--body", body,
            "--label", "maintenance",
        )
        print(f"  (created) {repo}: {title}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--auto-issue", action="store_true")
    args = parser.parse_args()

    manifest = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
    audit = Audit(manifest)
    local_root = resolve_local_root(manifest)

    section_deploys(audit)
    section_freshness(audit)
    section_stale_active(audit)
    section_forks(audit)
    section_royal_road(audit)
    section_drift(audit)
    section_cdcp_status(audit, local_root)
    section_anthropic(audit)

    args.output.write_text(audit.render(), encoding="utf-8")
    print(f"Wrote {args.output}", file=sys.stderr)

    if args.auto_issue and audit.issues:
        maybe_create_issues(audit)

    return 1 if audit.critical else 0


if __name__ == "__main__":
    sys.exit(main())
