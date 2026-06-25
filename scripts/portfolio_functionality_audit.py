#!/usr/bin/env python3
"""Audit whether portfolio repos have a concrete, runnable proof surface.

This is intentionally file-system based. It does not try to prove product
quality by reading marketing copy; it looks for the boring things that let a
reviewer verify a repo: entrypoint, test/build command, deploy target fit, and
documentation that tells a human what to run.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO_ROOT = ROOT.parent
PORTFOLIO_JSON = ROOT / "src" / "data" / "portfolio.json"
LIVE_URLS_JSON = ROOT / "src" / "data" / "live-urls.json"

README_NAMES = ("README.md", "readme.md", "README.rst")
PROFILE_REPOS = {"AthenaTheOwl", "AthenaTheOwl-profile"}
PLACEHOLDER_PATTERNS = (
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bcoming soon\b", re.IGNORECASE),
    re.compile(r"\bplaceholder\b", re.IGNORECASE),
    re.compile(r"\bscaffold\b", re.IGNORECASE),
    re.compile(r"\blorem ipsum\b", re.IGNORECASE),
)
RUNBOOK_PATTERNS = (
    re.compile(r"\bquick start\b", re.IGNORECASE),
    re.compile(r"\bverify\b", re.IGNORECASE),
    re.compile(r"\bverification\b", re.IGNORECASE),
    re.compile(r"\brun locally\b", re.IGNORECASE),
    re.compile(r"\bpytest\b", re.IGNORECASE),
    re.compile(r"\bnpm (run )?(test|build|install)\b", re.IGNORECASE),
    re.compile(r"\bstreamlit run\b", re.IGNORECASE),
    re.compile(r"\buv run\b", re.IGNORECASE),
)


@dataclass
class RepoAudit:
    name: str
    local_path: str
    in_portfolio: bool
    maturity: str | None = None
    domain: str | None = None
    deploy_target: str | None = None
    live_url: str | None = None
    demo_cmd: str | None = None
    exists: bool = False
    is_git_repo: bool = False
    entrypoints: list[str] = field(default_factory=list)
    proof_files: list[str] = field(default_factory=list)
    docs: list[str] = field(default_factory=list)
    package_scripts: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    score: int = 0
    verdict: str = "unknown"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(repo_root: Path, path: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def safe_text(path: Path, limit: int = 200_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def load_package_scripts(repo_root: Path) -> list[str]:
    package_json = repo_root / "package.json"
    if not package_json.exists():
        return []
    try:
        package = read_json(package_json)
    except (json.JSONDecodeError, OSError):
        return []
    scripts = package.get("scripts")
    if not isinstance(scripts, dict):
        return []
    useful = []
    for key in ("test", "build", "lint", "typecheck", "dev", "start", "preview"):
        if key in scripts:
            useful.append(f"npm:{key}")
    return useful


def first_existing(repo_root: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = repo_root / name
        if candidate.exists():
            return candidate
    return None


def discover_entrypoints(repo_root: Path) -> list[str]:
    candidates = [
        "streamlit_app.py",
        "app.py",
        "main.py",
        "cli.py",
        "apps/api/app/main.py",
        "src/app.py",
        "src/main.py",
        "src/cli.py",
        "index.html",
        "office_survivor.html",
        "vercel.json",
        "package.json",
        "pyproject.toml",
    ]
    found = [candidate for candidate in candidates if (repo_root / candidate).exists()]
    src_dir = repo_root / "src"
    if src_dir.exists():
        for path in sorted(src_dir.rglob("__main__.py")):
            found.append(rel(repo_root, path))
    for path in sorted(repo_root.glob("Lab*/tester.py")):
        found.append(rel(repo_root, path))
    for path in sorted(repo_root.glob("*.html")):
        found.append(rel(repo_root, path))
    return sorted(dict.fromkeys(found))


def discover_proof_files(repo_root: Path) -> list[str]:
    candidates = [
        "tests",
        "test",
        "pytest.ini",
        "tox.ini",
        "pyproject.toml",
        "package.json",
        "vitest.config.ts",
        "playwright.config.ts",
        "reports",
        "simulation_results.json",
        "examples",
        "fixtures",
        "data",
        "DEPLOY.md",
        "docs/deploy.md",
    ]
    found = [candidate for candidate in candidates if (repo_root / candidate).exists()]
    for pattern in ("*.ipynb", "validate.py", "scripts/validate*.py"):
        for path in sorted(repo_root.glob(pattern)):
            found.append(rel(repo_root, path))
    for pattern in ("*.js", "scripts/*.js"):
        for path in sorted(repo_root.glob(pattern)):
            found.append(rel(repo_root, path))
    for path in sorted(repo_root.glob("Lab*/tester.py")):
        found.append(rel(repo_root, path))
    for path in sorted(repo_root.glob("**/test_*.py")):
        if ".venv" not in path.parts and "node_modules" not in path.parts:
            found.append(rel(repo_root, path))
    return sorted(dict.fromkeys(found))


def discover_docs(repo_root: Path) -> list[str]:
    docs = []
    for name in README_NAMES:
        if (repo_root / name).exists():
            docs.append(name)
    docs_dir = repo_root / "docs"
    if docs_dir.exists():
        for path in sorted(docs_dir.glob("*.md")):
            docs.append(rel(repo_root, path))
    for name in ("DEPLOY.md", "STATUS.md", "CHANGELOG.md"):
        if (repo_root / name).exists():
            docs.append(name)
    return sorted(dict.fromkeys(docs))


def audit_readme(repo_root: Path, audit: RepoAudit) -> None:
    readme = first_existing(repo_root, README_NAMES)
    if readme is None:
        audit.findings.append("missing README")
        return
    text = safe_text(readme)
    if len(text.strip()) < 400:
        audit.findings.append("README is too thin to onboard a reviewer")
    if not any(pattern.search(text) for pattern in RUNBOOK_PATTERNS):
        audit.findings.append("README lacks explicit run/test verification")
    placeholder_hits = sorted({pattern.pattern for pattern in PLACEHOLDER_PATTERNS if pattern.search(text)})
    if placeholder_hits:
        audit.findings.append("README still contains scaffold/placeholder language")


def audit_deploy_fit(repo_root: Path, audit: RepoAudit) -> None:
    target = audit.deploy_target
    if not target or target == "none":
        return
    if target == "streamlit":
        if not (repo_root / "streamlit_app.py").exists():
            audit.findings.append("declares Streamlit deploy target but has no streamlit_app.py")
        if not ((repo_root / "requirements.txt").exists() or (repo_root / "pyproject.toml").exists()):
            audit.findings.append("Streamlit target lacks requirements.txt or pyproject.toml")
    elif target == "vercel":
        if not (repo_root / "package.json").exists():
            audit.findings.append("declares Vercel deploy target but has no package.json")
        if not ((repo_root / "vercel.json").exists() or (repo_root / "next.config.js").exists() or (repo_root / "astro.config.mjs").exists() or (repo_root / "vite.config.ts").exists()):
            audit.findings.append("Vercel target lacks obvious Vercel/Next/Astro/Vite config")


def score_repo(audit: RepoAudit) -> None:
    if audit.name in PROFILE_REPOS and audit.docs:
        audit.score = 70 if not audit.findings else 55
        audit.verdict = "profile-index"
        return
    if audit.deploy_target == "none" and audit.proof_files and audit.docs and not audit.findings:
        audit.score = 70
        audit.verdict = "archive-proof-ok"
        return
    score = 0
    if audit.exists:
        score += 10
    if audit.is_git_repo:
        score += 10
    if audit.entrypoints:
        score += 20
    if audit.proof_files:
        score += 20
    if audit.package_scripts:
        score += min(15, len(audit.package_scripts) * 5)
    if audit.docs:
        score += 10
    if audit.demo_cmd:
        score += 10
    if audit.live_url:
        score += 10
    score -= min(45, len(audit.findings) * 15)
    audit.score = max(score, 0)
    if not audit.exists:
        audit.verdict = "missing-local"
    elif audit.score >= 75 and not audit.findings:
        audit.verdict = "proof-surface-ok"
    elif audit.score >= 65:
        audit.verdict = "proof-surface-ok-doc-polish"
    elif audit.score >= 45:
        audit.verdict = "ambiguous"
    else:
        audit.verdict = "needs-work"


def audit_repo(repo_root: Path, item: dict[str, Any] | None, live_urls: dict[str, Any]) -> RepoAudit:
    name = item["name"] if item else repo_root.name
    live_entry = live_urls.get(name) if isinstance(live_urls, dict) else None
    live_url = live_entry.get("live") if isinstance(live_entry, dict) else None
    audit = RepoAudit(
        name=name,
        local_path=repo_root.name,
        in_portfolio=item is not None,
        maturity=item.get("maturity") if item else None,
        domain=item.get("domain") if item else None,
        deploy_target=(live_entry or {}).get("target") if isinstance(live_entry, dict) else item.get("deploy_target") if item else None,
        live_url=live_url,
        demo_cmd=item.get("demo_cmd") if item else None,
    )
    audit.exists = repo_root.exists()
    audit.is_git_repo = (repo_root / ".git").exists()
    if not audit.exists:
        audit.findings.append("local checkout missing")
        score_repo(audit)
        return audit
    audit.entrypoints = discover_entrypoints(repo_root)
    audit.proof_files = discover_proof_files(repo_root)
    audit.docs = discover_docs(repo_root)
    audit.package_scripts = load_package_scripts(repo_root)
    if not audit.entrypoints and not (audit.deploy_target == "none" and audit.proof_files):
        audit.findings.append("no obvious executable entrypoint")
    if not audit.proof_files and audit.deploy_target != "none":
        audit.findings.append("no obvious tests, fixtures, reports, examples, or validation files")
    audit_readme(repo_root, audit)
    audit_deploy_fit(repo_root, audit)
    score_repo(audit)
    return audit


def local_git_repos() -> list[Path]:
    repos = []
    for child in sorted(PORTFOLIO_ROOT.iterdir()):
        if not child.is_dir():
            continue
        if "-task-" in child.name:
            continue
        if (child / ".git").exists():
            repos.append(child)
    return repos


def render_markdown(audits: list[RepoAudit]) -> str:
    by_verdict: dict[str, list[RepoAudit]] = {}
    for audit in audits:
        by_verdict.setdefault(audit.verdict, []).append(audit)
    lines = [
        "# Portfolio functionality audit",
        "",
        "This report checks whether each repo has a concrete proof surface: entrypoint, run/test evidence, deploy-target fit, and reviewer-facing docs.",
        "",
        "## summary",
        "",
        "| Verdict | Count |",
        "|---|---:|",
    ]
    for verdict in ("proof-surface-ok", "archive-proof-ok", "profile-index", "proof-surface-ok-doc-polish", "ambiguous", "needs-work", "missing-local"):
        lines.append(f"| {verdict} | {len(by_verdict.get(verdict, []))} |")
    lines.extend(["", "## highest-priority gaps", "", "| Repo | Score | Target | Findings |", "|---|---:|---|---|"])
    gap_audits = sorted(
        [audit for audit in audits if audit.verdict in {"needs-work", "ambiguous", "missing-local"}],
        key=lambda audit: (audit.score, audit.name.lower()),
    )
    for audit in gap_audits[:30]:
        findings = "; ".join(audit.findings) if audit.findings else "score below threshold"
        lines.append(f"| {audit.name} | {audit.score} | {audit.deploy_target or 'n/a'} | {findings} |")
    lines.extend(["", "## all repos", "", "| Repo | Verdict | Score | Entrypoints | Proof | Findings |", "|---|---|---:|---|---|---|"])
    for audit in sorted(audits, key=lambda item: (item.verdict, item.name.lower())):
        entrypoints = ", ".join(audit.entrypoints[:4])
        proof = ", ".join(audit.proof_files[:4])
        findings = "; ".join(audit.findings)
        lines.append(f"| {audit.name} | {audit.verdict} | {audit.score} | {entrypoints} | {proof} | {findings} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--md-output", type=Path)
    parser.add_argument(
        "--include-local-extra",
        action="store_true",
        help="Include local Git repos that are not listed in src/data/portfolio.json. Intended for private local audits only.",
    )
    args = parser.parse_args()

    portfolio = read_json(PORTFOLIO_JSON)
    live_urls = read_json(LIVE_URLS_JSON) if LIVE_URLS_JSON.exists() else {}
    by_name = {item["name"]: item for item in portfolio}

    audits = [audit_repo(PORTFOLIO_ROOT / item["name"], item, live_urls) for item in portfolio]
    portfolio_names = set(by_name)
    if args.include_local_extra:
        for repo_root in local_git_repos():
            if repo_root.name not in portfolio_names:
                audits.append(audit_repo(repo_root, None, live_urls))

    payload = {
        "scope": "portfolio" if not args.include_local_extra else "portfolio-plus-local-extra",
        "counts": {
            verdict: sum(1 for audit in audits if audit.verdict == verdict)
            for verdict in sorted({audit.verdict for audit in audits})
        },
        "repos": [asdict(audit) for audit in sorted(audits, key=lambda item: item.name.lower())],
    }
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.json_output}")
    if args.md_output:
        args.md_output.parent.mkdir(parents=True, exist_ok=True)
        args.md_output.write_text(render_markdown(audits), encoding="utf-8")
        print(f"wrote {args.md_output}")
    for verdict, count in payload["counts"].items():
        print(f"{verdict}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
