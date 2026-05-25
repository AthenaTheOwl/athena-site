#!/usr/bin/env python3
"""Generate the static factory snapshot used by /factory.

The portfolio repos live beside athena-site on the maintainer machine.
Vercel only builds athena-site, so the public page reads a checked-in JSON
snapshot rather than walking sibling repos at build time.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "ops" / "portfolio-manifest.yml"
OUTPUT_PATH = ROOT / "src" / "data" / "factory-snapshot.json"


def resolve_local_root(manifest: dict[str, Any]) -> Path:
    configured = os.environ.get("RANDOM_APPS_ROOT") or manifest.get("local_root")
    if not configured:
        raise SystemExit("factory_snapshot: RANDOM_APPS_ROOT or local_root required")
    path = Path(str(configured)).expanduser()
    if not path.is_dir():
        raise SystemExit(f"factory_snapshot: local root not found: {path}")
    return path.resolve()


def count_dirs(path: Path, pattern: str = "*") -> int:
    if not path.is_dir():
        return 0
    return sum(1 for item in path.glob(pattern) if item.is_dir())


def count_files(path: Path, pattern: str = "*") -> int:
    if not path.is_dir():
        return 0
    return sum(1 for item in path.glob(pattern) if item.is_file())


def count_requirement_tokens(repo_root: Path) -> int:
    total = 0
    for req_path in repo_root.glob("specs/*/requirements.md"):
        text = req_path.read_text(encoding="utf-8", errors="ignore")
        total += len(re.findall(r"^###\s+R-[A-Z0-9-]+:", text, flags=re.MULTILINE))
    return total


def list_validators(repo_root: Path) -> list[str]:
    scripts = repo_root / "scripts"
    names = [
        "spec_check.py",
        "voice_lint.py",
        "validate_decisions.py",
        "validate_roles.py",
        "validate_tools.py",
        "validate_policies.py",
        "validate_skills.py",
        "validate_dreams.py",
        "check_schema_cache_freshness.py",
        "check_data_freshness.py",
        "validate_schemas.py",
        "validate_registry.py",
    ]
    return [name for name in names if (scripts / name).is_file()]


def recent_events(repo_root: Path, limit: int = 5) -> list[dict[str, str]]:
    event_dir = repo_root / "ops" / "event-log"
    if not event_dir.is_dir():
        return []
    events: list[dict[str, str]] = []
    for path in sorted(event_dir.glob("*.jsonl"), reverse=True):
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            payload = data.get("payload", {})
            label = (
                payload.get("decision_id")
                or payload.get("role_id")
                or payload.get("spec")
                or payload.get("kind")
                or ""
            )
            events.append(
                {
                    "created_at": str(data.get("created_at", "")),
                    "type": str(data.get("type", "")),
                    "label": str(label),
                }
            )
    events.sort(key=lambda item: item["created_at"], reverse=True)
    return events[:limit]


def repo_snapshot(local_root: Path, item: dict[str, Any]) -> dict[str, Any]:
    name = item["name"]
    repo_root = local_root / name
    exists = repo_root.is_dir()
    data: dict[str, Any] = {
        "name": name,
        "door": item.get("door"),
        "status": item.get("status"),
        "deploy_url": item.get("deploy_url"),
        "cdcp_status": item.get("cdcp_status", []),
        "exists_local": exists,
    }
    if not exists:
        data.update(
            {
                "specs": 0,
                "requirements": 0,
                "decisions": 0,
                "roles": 0,
                "skills": 0,
                "dreams": 0,
                "validators": [],
                "events": [],
            }
        )
        return data

    data.update(
        {
            "specs": count_dirs(repo_root / "specs", "[0-9][0-9][0-9][0-9]-*"),
            "requirements": count_requirement_tokens(repo_root),
            "decisions": count_files(repo_root / "decisions", "DEC-*.md"),
            "roles": count_dirs(repo_root / ".agents" / "roles"),
            "skills": count_files(repo_root / ".agents" / "skills", "*/SKILL.md"),
            "dreams": count_dirs(repo_root / "dreams", "[0-9][0-9][0-9][0-9]-W*"),
            "validators": list_validators(repo_root),
            "events": recent_events(repo_root),
        }
    )
    return data


def main() -> int:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    local_root = resolve_local_root(manifest)
    repos = [
        repo_snapshot(local_root, item)
        for item in manifest["repos"]
        if item.get("status") in {"active", "workshop"}
    ]
    snapshot = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "scripts/factory_snapshot.py",
        "repos": repos,
        "totals": {
            "repos": len(repos),
            "specs": sum(repo["specs"] for repo in repos),
            "requirements": sum(repo["requirements"] for repo in repos),
            "decisions": sum(repo["decisions"] for repo in repos),
            "roles": sum(repo["roles"] for repo in repos),
            "skills": sum(repo["skills"] for repo in repos),
            "dreams": sum(repo["dreams"] for repo in repos),
        },
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
