#!/usr/bin/env python3
"""Build the static Factory Q&A evidence index."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "src/data/factory-qa-index.json"

SOURCE_PATHS = [
    "src/data/factory-snapshot.json",
    "ops/portfolio-manifest.yml",
    "ops/factory-build-queue.md",
    "ops/control-plane.md",
    "ops/portfolio-health.md",
    "src/content/doors.json",
]

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "have",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "our",
    "should",
    "the",
    "to",
    "we",
    "what",
    "where",
    "which",
    "who",
    "why",
    "with",
}

QUERY_EXPANSIONS = {
    "blocked": ["blocker", "blockers", "credential", "credentials", "secret"],
    "build": ["queue", "wave", "requirements", "first"],
    "cdcp": ["cognitive", "delivery", "control", "plane", "cdcp"],
    "credential": ["credentials", "blocker", "blockers", "secret", "key"],
    "credentials": ["credential", "blocker", "blockers", "secret", "key"],
    "factory": ["factory", "control", "tower", "repo", "repos"],
    "mcp": ["mcp", "mcp-security-lab", "security", "lab"],
    "new": ["19", "20", "mcp", "trace", "eval", "harness", "door"],
    "next": ["queue", "wave", "requirements", "first"],
    "repos": ["repo", "repos"],
    "repo": ["repo", "repos"],
}

TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def rel_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\r\n", "\n")).strip()


def tokenize(text: str, *, drop_stopwords: bool = False) -> list[str]:
    tokens: list[str] = []
    for match in TOKEN_RE.findall(text.lower()):
        normalized = match.replace("_", "-")
        candidates = [normalized]
        if "-" in normalized:
            candidates.extend(part for part in normalized.split("-") if part)
        for candidate in candidates:
            if drop_stopwords and candidate in STOPWORDS:
                continue
            tokens.append(candidate)
            if len(candidate) > 3 and candidate.endswith("s"):
                singular = candidate[:-1]
                if not drop_stopwords or singular not in STOPWORDS:
                    tokens.append(singular)
    return tokens


def expanded_query_tokens(question: str) -> list[str]:
    tokens = tokenize(question, drop_stopwords=True)
    expanded = set(tokens)
    for token in tokens:
        expanded.update(QUERY_EXPANSIONS.get(token, []))
    return sorted(expanded)


def snippet(text: str, limit: int = 950) -> str:
    cleaned = clean_text(text)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def make_chunk(path: str, title: str, locator: str, body: str) -> dict[str, Any]:
    body_snippet = snippet(body)
    token_text = " ".join([path, title, locator, body_snippet])
    return {
        "id": hashlib.sha1(token_text.encode("utf-8")).hexdigest()[:12],
        "path": path,
        "title": title,
        "locator": locator,
        "snippet": body_snippet,
        "tokens": sorted(set(tokenize(token_text))),
    }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot_chunks(path: Path) -> list[dict[str, Any]]:
    data = read_json(path)
    path_text = rel_path(path)
    totals = data.get("totals", {})
    repos = data.get("repos", [])
    chunks = [
        make_chunk(
            path_text,
            "Factory snapshot totals",
            "totals",
            (
                f"Generated at {data.get('generated_at', 'unknown')}. "
                f"Repos: {totals.get('repos', 0)}. Specs: {totals.get('specs', 0)}. "
                f"Requirements: {totals.get('requirements', 0)}. "
                f"Decisions: {totals.get('decisions', 0)}. Roles: {totals.get('roles', 0)}. "
                f"Skills: {totals.get('skills', 0)}. Dreams: {totals.get('dreams', 0)}."
            ),
        )
    ]

    for index, repo in enumerate(repos):
        events = repo.get("events") or []
        event_text = "; ".join(
            f"{event.get('type', '')} {event.get('label', '')}".strip()
            for event in events[:5]
            if event.get("type") or event.get("label")
        )
        body = (
            f"Repo {repo.get('name')}. Door {repo.get('door', '--')}. "
            f"Status {repo.get('status', 'unknown')}. "
            f"Deploy URL {repo.get('deploy_url') or 'none'}. "
            f"CDCP status {', '.join(repo.get('cdcp_status') or ['none'])}. "
            f"Exists local {repo.get('exists_local')}. "
            f"Specs {repo.get('specs', 0)}. Requirements {repo.get('requirements', 0)}. "
            f"Decisions {repo.get('decisions', 0)}. Roles {repo.get('roles', 0)}. "
            f"Skills {repo.get('skills', 0)}. Dreams {repo.get('dreams', 0)}. "
            f"Validators {', '.join(repo.get('validators') or ['none'])}. "
            f"Recent events {event_text or 'none'}."
        )
        chunks.append(
            make_chunk(
                path_text,
                f"Factory snapshot repo: {repo.get('name')}",
                f"repos[{index}]",
                body,
            )
        )
    return chunks


def doors_chunks(path: Path) -> list[dict[str, Any]]:
    doors = read_json(path)
    path_text = rel_path(path)
    chunks: list[dict[str, Any]] = []
    for index, door in enumerate(doors):
        audience = door.get("for") or {}
        audience_text = " ".join(
            f"For {key}: {value}." for key, value in sorted(audience.items())
        )
        body = (
            f"Door {door.get('n')}: {door.get('name')}. "
            f"Status {door.get('status')}. URL {door.get('url')}. "
            f"Hook: {door.get('hook')}. {audience_text}"
        )
        chunks.append(
            make_chunk(
                path_text,
                f"Portfolio door {door.get('n')}: {door.get('name')}",
                f"[{index}]",
                body,
            )
        )
    return chunks


def text_chunks(path: Path) -> list[dict[str, Any]]:
    path_text = rel_path(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    chunks: list[dict[str, Any]] = []
    headings: list[tuple[int, str]] = []
    block: list[str] = []
    block_start = 1

    def current_title() -> str:
        if not headings:
            return path_text
        return " > ".join(title for _, title in headings[-3:])

    def flush(end_line: int) -> None:
        nonlocal block, block_start
        body = "\n".join(line for line in block if line.strip())
        if clean_text(body):
            chunks.append(
                make_chunk(
                    path_text,
                    current_title(),
                    f"lines {block_start}-{end_line}",
                    body,
                )
            )
        block = []

    for line_no, line in enumerate(lines, start=1):
        heading_match = HEADING_RE.match(line)
        if heading_match:
            flush(line_no - 1)
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            headings = [(h_level, h_title) for h_level, h_title in headings if h_level < level]
            headings.append((level, title))
            block_start = line_no
            continue
        if not line.strip():
            flush(line_no - 1)
            block_start = line_no + 1
            continue
        if not block:
            block_start = line_no
        block.append(line)

    flush(len(lines))
    return chunks


def source_chunks(path: Path) -> list[dict[str, Any]]:
    path_text = rel_path(path)
    if path_text == "src/data/factory-snapshot.json":
        return snapshot_chunks(path)
    if path_text == "src/content/doors.json":
        return doors_chunks(path)
    return text_chunks(path)


def build_index() -> dict[str, Any]:
    chunks: list[dict[str, Any]] = []
    source_hash = hashlib.sha256()
    snapshot_generated_at = "unknown"

    for source in SOURCE_PATHS:
        path = ROOT / source
        if not path.exists():
            raise FileNotFoundError(source)
        raw = path.read_bytes()
        source_hash.update(source.encode("utf-8"))
        source_hash.update(raw)
        if source == "src/data/factory-snapshot.json":
            snapshot_generated_at = json.loads(raw.decode("utf-8")).get(
                "generated_at", "unknown"
            )
        chunks.extend(source_chunks(path))

    for order, chunk in enumerate(chunks):
        chunk["order"] = order

    return {
        "schema_version": 1,
        "source": "scripts/factory_qa_index.py",
        "generated_at": snapshot_generated_at,
        "source_hash": source_hash.hexdigest(),
        "answer_policy": {
            "mode": "snippet_citations_only",
            "fallback": "Not enough evidence in the static index.",
        },
        "sources": SOURCE_PATHS,
        "chunks": chunks,
    }


def score_chunk(chunk: dict[str, Any], question: str, query_tokens: list[str]) -> int:
    chunk_tokens = set(chunk.get("tokens", []))
    search_text = " ".join(
        [
            chunk.get("path", ""),
            chunk.get("title", ""),
            chunk.get("locator", ""),
            chunk.get("snippet", ""),
        ]
    ).lower()
    score = 0
    for token in query_tokens:
        if token in chunk_tokens:
            score += 3
        if token and token in search_text:
            score += 1

    raw_tokens = tokenize(question, drop_stopwords=True)
    raw_set = set(raw_tokens)
    for left, right in zip(raw_tokens, raw_tokens[1:]):
        phrase = f"{left} {right}"
        hyphen_phrase = f"{left}-{right}"
        if phrase in search_text or hyphen_phrase in search_text:
            score += 5

    path = chunk.get("path", "")
    title = chunk.get("title", "").lower()
    snippet_text = chunk.get("snippet", "")
    if {"build", "next"} & raw_set and path == "ops/factory-build-queue.md":
        score += 8
    if {"credential", "credentials", "blocked"} & raw_set:
        if path == "ops/factory-build-queue.md":
            score += 5
        if "credential blockers" in search_text:
            score += 12
    if "cdcp" in raw_set and {"repo", "repos"} & raw_set:
        if path == "ops/portfolio-health.md" and "cdcp status" in title:
            score += 18
        if path == "src/data/factory-snapshot.json" and "CDCP status" in snippet_text:
            score += 8
    if {"mcp", "security", "lab"}.issubset(raw_set):
        if path == "src/content/doors.json":
            score += 16
        if "mcp-security-lab" in search_text:
            score += 5
    if "new" in raw_set and "factory" in raw_set and {"repo", "repos"} & raw_set:
        if path in {"src/data/factory-snapshot.json", "src/content/doors.json"}:
            if "Door 19" in snippet_text or "Door 20" in snippet_text:
                score += 16
    return score


def answer_question(
    question: str, index: dict[str, Any], *, limit: int = 5, min_score: int = 6
) -> dict[str, Any]:
    query_tokens = expanded_query_tokens(question)
    if not query_tokens:
        return {
            "question": question,
            "status": "not_enough_evidence",
            "message": index.get("answer_policy", {}).get(
                "fallback", "Not enough evidence in the static index."
            ),
            "results": [],
        }

    ranked = []
    for chunk in index.get("chunks", []):
        score = score_chunk(chunk, question, query_tokens)
        if score >= min_score:
            ranked.append((score, chunk))
    ranked.sort(
        key=lambda item: (-item[0], item[1].get("order", 0))
    )
    results = [
        {
            "score": score,
            "path": chunk.get("path", ""),
            "title": chunk.get("title", ""),
            "locator": chunk.get("locator", ""),
            "snippet": chunk.get("snippet", ""),
        }
        for score, chunk in ranked[:limit]
    ]
    if not results:
        return {
            "question": question,
            "status": "not_enough_evidence",
            "message": index.get("answer_policy", {}).get(
                "fallback", "Not enough evidence in the static index."
            ),
            "results": [],
        }
    return {
        "question": question,
        "status": "cited",
        "message": "Cited snippets from the static index.",
        "results": results,
    }


def write_index(index: dict[str, Any], path: Path = INDEX_PATH) -> None:
    path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Factory Q&A static index")
    parser.add_argument("--check", action="store_true", help="fail if the index is stale")
    args = parser.parse_args(argv)

    index = build_index()
    if args.check:
        if not INDEX_PATH.exists():
            print(f"{rel_path(INDEX_PATH)} is missing", file=sys.stderr)
            return 1
        current = INDEX_PATH.read_text(encoding="utf-8")
        expected = json.dumps(index, indent=2, sort_keys=True) + "\n"
        if current != expected:
            print(f"{rel_path(INDEX_PATH)} is stale; run python scripts/factory_qa_index.py", file=sys.stderr)
            return 1
        print(f"{rel_path(INDEX_PATH)} is current")
        return 0

    write_index(index)
    print(f"wrote {rel_path(INDEX_PATH)} with {len(index['chunks'])} chunks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
