#!/usr/bin/env python3
"""Voice lint. Greps for banned phrases against the voice spec.

Advisory: prints offenses, exits non-zero on hits. Wire into CI as a check, not a gate.
Voice spec: C:/Users/Vignesh/.claude/plans/codex-briefs/voice-spec.md (private)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Banned phrases. Word-boundary, case-insensitive.
# Drawn from the voice spec's "what to avoid" list.
BANNED = [
    "leverage",
    "leverages",
    "leveraging",
    "demonstrates",
    "demonstrate",
    "production-grade",
    "comprehensive",
    "portfolio-grade",
    "synergy",
    "enables",
    "enabling",
    "best-in-class",
    "state-of-the-art",
    "seamlessly",
    "cutting-edge",
    "robust solution",
    "industry-leading",
    "world-class",
    "next-generation",
]

# Files to scan.
TARGETS = [
    "src/pages/**/*.mdx",
    "src/pages/**/*.astro",
    "src/components/**/*.astro",
    "src/layouts/**/*.astro",
    "src/content/**/*.json",
    "README.md",
]

# Skip directories. Astro generates dist/ and node_modules/ — don't scan.
SKIP_DIRS = {"node_modules", "dist", ".astro", ".git"}


def iter_files() -> list[Path]:
    files: list[Path] = []
    for pattern in TARGETS:
        for p in ROOT.glob(pattern):
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if p.is_file():
                files.append(p)
    return sorted(set(files))


def scan(path: Path, patterns: list[re.Pattern[str]]) -> list[tuple[int, str, str]]:
    """Return list of (line_no, phrase, line_text)."""
    offenses: list[tuple[int, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return offenses
    for i, line in enumerate(text.splitlines(), start=1):
        for pat in patterns:
            m = pat.search(line)
            if m:
                offenses.append((i, m.group(0), line.strip()))
    return offenses


def main() -> int:
    patterns = [re.compile(rf"\b{re.escape(p)}\b", re.IGNORECASE) for p in BANNED]
    files = iter_files()
    total = 0
    for f in files:
        offenses = scan(f, patterns)
        for line_no, phrase, line_text in offenses:
            rel = f.relative_to(ROOT).as_posix()
            print(f"{rel}:{line_no}: {phrase!r} -> {line_text}")
            total += 1
    if total:
        print(f"\nvoice-lint: {total} offense(s) across {len(files)} file(s) scanned.", file=sys.stderr)
        return 1
    print(f"voice-lint: clean. {len(files)} file(s) scanned.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
