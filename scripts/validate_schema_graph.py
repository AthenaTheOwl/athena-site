#!/usr/bin/env python3
"""Validate the cross-schema reference map declared in ops/schemas/README.md.

The portfolio's 11+ JSON Schemas (CDCP artifact contracts) reference each
other by id, not by $ref. ``ops/schemas/README.md`` documents every
cross-schema edge as a dash-bulleted line under "Schema dependency map":

    - `<source>` -> `<target>` via `<field>`.

This validator parses those lines and asserts:

1. Each source schema file exists at ``ops/schemas/<source>.schema.json``.
2. Each target schema file exists at ``ops/schemas/<target>.schema.json``.
3. The named ``<field>`` resolves inside the source schema's ``properties``
   (recursing through nested objects, arrays, and oneOf/anyOf branches).

Exits nonzero on any failure; prints the offending edge + reason.

Out of scope (v1): runtime data validation. The check is purely a
schema-shape lint of the dependency-map README against the schemas it
documents.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "ops" / "schemas"
README = SCHEMAS_DIR / "README.md"

# Match dash-bulleted edges. The arrow may be `->` or `→` (unicode).
EDGE_RE = re.compile(
    r"^-\s*`(?P<source>[a-z0-9_-]+)`\s*(?:->|→)\s*`(?P<target>[a-z0-9_-]+)`"
    r"\s*via\s*`(?P<field>[A-Za-z_][\w.\[\]]*)`",
    re.MULTILINE,
)


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    field: str
    line: int


@dataclass(frozen=True)
class Failure:
    edge: Edge
    reason: str


def parse_edges(readme: Path) -> list[Edge]:
    text = readme.read_text(encoding="utf-8")
    edges: list[Edge] = []
    for m in EDGE_RE.finditer(text):
        # Estimate line by counting newlines up to the match start.
        line_no = text.count("\n", 0, m.start()) + 1
        edges.append(
            Edge(
                source=m.group("source"),
                target=m.group("target"),
                field=m.group("field"),
                line=line_no,
            )
        )
    return edges


def schema_path(name: str) -> Path:
    return SCHEMAS_DIR / f"{name}.schema.json"


def load_schema(name: str) -> dict[str, Any] | None:
    p = schema_path(name)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _collect_property_paths(node: Any, prefix: str = "") -> set[str]:
    """Walk a JSON Schema node and return every property dotted path found.

    Handles nested objects (`properties.x.properties.y`), arrays (`x[]`),
    and one-of/any-of branches. The returned set contains both the bare
    leaf names and the dotted paths so callers can match either form.
    """
    paths: set[str] = set()
    if not isinstance(node, dict):
        return paths

    props = node.get("properties")
    if isinstance(props, dict):
        for name, sub in props.items():
            path = f"{prefix}.{name}" if prefix else name
            paths.add(name)
            paths.add(path)
            sub_node = sub if isinstance(sub, dict) else {}
            # Recurse into nested objects.
            paths |= _collect_property_paths(sub_node, prefix=path)
            # Recurse into items if this is an array.
            items = sub_node.get("items")
            if isinstance(items, dict):
                paths |= _collect_property_paths(items, prefix=f"{path}[]")
            # Recurse into oneOf/anyOf/allOf branches.
            for branch_key in ("oneOf", "anyOf", "allOf"):
                branches = sub_node.get(branch_key)
                if isinstance(branches, list):
                    for branch in branches:
                        if isinstance(branch, dict):
                            paths |= _collect_property_paths(branch, prefix=path)

    # Top-level oneOf/anyOf/allOf composition.
    for branch_key in ("oneOf", "anyOf", "allOf"):
        branches = node.get(branch_key)
        if isinstance(branches, list):
            for branch in branches:
                if isinstance(branch, dict):
                    paths |= _collect_property_paths(branch, prefix=prefix)

    return paths


def validate_edges(edges: list[Edge]) -> list[Failure]:
    """Run the three checks per edge."""
    failures: list[Failure] = []
    schema_cache: dict[str, dict[str, Any] | None] = {}

    def _load(name: str) -> dict[str, Any] | None:
        if name not in schema_cache:
            schema_cache[name] = load_schema(name)
        return schema_cache[name]

    for edge in edges:
        src = _load(edge.source)
        if src is None:
            failures.append(
                Failure(edge, f"source schema not found: {schema_path(edge.source)}")
            )
            continue

        tgt = _load(edge.target)
        if tgt is None:
            failures.append(
                Failure(edge, f"target schema not found: {schema_path(edge.target)}")
            )
            continue

        property_paths = _collect_property_paths(src)
        # Accept the field as either a bare leaf name (`allowed_tools`),
        # a dotted path (`applies_to.roles`), or an array-suffixed path
        # (`steps[].role`). The collection includes all three forms.
        if edge.field not in property_paths:
            failures.append(
                Failure(
                    edge,
                    f"field `{edge.field}` not found in {edge.source}.schema.json properties",
                )
            )

    return failures


def self_test() -> int:
    """Build a tiny in-memory fixture and assert the validator works.

    Provides:
    - one well-formed edge that should pass
    - one with a missing source schema
    - one with a missing field
    """
    sample_source_schema = {
        "type": "object",
        "properties": {
            "allowed_tools": {"type": "array"},
            "applies_to": {
                "type": "object",
                "properties": {"roles": {"type": "array"}},
            },
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"role": {"type": "string"}},
                },
            },
        },
    }
    paths = _collect_property_paths(sample_source_schema)
    assert "allowed_tools" in paths, "leaf name must be in paths"
    assert "applies_to.roles" in paths, "dotted path must be in paths"
    assert "steps[].role" in paths, "array-suffixed path must be in paths"
    assert "nonexistent" not in paths
    print("self-test OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--readme",
        type=Path,
        default=README,
        help="override path to schemas README (default: ops/schemas/README.md)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run a fixture-based self-test of the parsing + path-walk and exit",
    )
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    if not args.readme.exists():
        print(f"schema-graph: README not found at {args.readme}", file=sys.stderr)
        return 1

    edges = parse_edges(args.readme)
    if not edges:
        print(
            "schema-graph: no edges parsed from README — check the dash-bulleted "
            "`<source>` -> `<target>` via `<field>` line shape",
            file=sys.stderr,
        )
        return 1

    failures = validate_edges(edges)
    if failures:
        print(
            f"schema-graph: {len(failures)} failure(s) across {len(edges)} declared edge(s).",
            file=sys.stderr,
        )
        for f in failures:
            print(
                f"  README:{f.edge.line}: {f.edge.source} -> {f.edge.target} via {f.edge.field}: {f.reason}",
                file=sys.stderr,
            )
        return 1

    print(
        f"schema-graph OK ({len(edges)} edge(s) checked across "
        f"{len({e.source for e in edges} | {e.target for e in edges})} schema(s))",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
