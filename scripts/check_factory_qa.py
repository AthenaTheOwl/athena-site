#!/usr/bin/env python3
"""Gate canned Factory Q&A questions against the static evidence index."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from factory_qa_index import INDEX_PATH, answer_question

CANNED_QUESTIONS = [
    "what should we build next",
    "which repos have CDCP",
    "what are the new factory repos",
    "what credentials are blocked",
    "what is MCP Security Lab",
]


def load_index() -> dict:
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def main() -> int:
    if not INDEX_PATH.exists():
        print("factory QA index is missing; run python scripts/factory_qa_index.py", file=sys.stderr)
        return 1

    index = load_index()
    failures: list[str] = []
    for question in CANNED_QUESTIONS:
        answer = answer_question(question, index)
        citations = [
            f"{result.get('path')} {result.get('locator')}".strip()
            for result in answer.get("results", [])
            if result.get("path") and result.get("snippet")
        ]
        if answer.get("status") == "not_enough_evidence" or not citations:
            failures.append(question)
            print(f"FAIL | {question} | not enough evidence")
            continue
        print(f"PASS | {question} | {', '.join(citations[:3])}")

    if failures:
        print("\ncheck_factory_qa: failed questions:", file=sys.stderr)
        for question in failures:
            print(f"  - {question}", file=sys.stderr)
        return 1

    print(f"\ncheck_factory_qa OK ({len(CANNED_QUESTIONS)} questions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
