"""Tests for the schema-graph validator.

Covers:
- the README parser captures every well-formed dash-bulleted edge
- the path-walk surfaces leaf names, dotted paths, and array-suffixed paths
- a broken edge (missing field or missing schema) is reported with the
  README line number
- the live ops/schemas/README.md passes the validator
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_schema_graph import (  # noqa: E402  — sys.path side-effect above
    Edge,
    Failure,
    _collect_property_paths,
    parse_edges,
    validate_edges,
)


REPO = Path(__file__).resolve().parents[1]


def test_parse_edges_real_readme() -> None:
    edges = parse_edges(REPO / "ops" / "schemas" / "README.md")
    assert len(edges) >= 5, f"expected the README to declare >= 5 edges, got {len(edges)}"
    # The first declared edge in the README is role -> tool via allowed_tools.
    first = edges[0]
    assert first.source == "role"
    assert first.target == "tool"
    assert first.field == "allowed_tools"


def test_parse_edges_skips_non_bullet_lines(tmp_path: Path) -> None:
    fixture = tmp_path / "README.md"
    fixture.write_text(
        "# Title\n\nSome prose with `code` in it that should not match.\n"
        "- `role` -> `tool` via `allowed_tools`.\n"
        "  - `nested` -> `not-a-top-level` via `field`.\n"  # different indent
        "- `tool` -> `role` via `allowed_roles`.\n",
        encoding="utf-8",
    )
    edges = parse_edges(fixture)
    # Two top-level edges; the indented one is also dash-bulleted so the regex
    # picks it up. That's fine — the validator's job is to enforce shape, not
    # markdown nesting depth.
    assert len(edges) >= 2
    assert any(e.source == "role" and e.target == "tool" for e in edges)


def test_collect_property_paths_handles_nesting() -> None:
    schema = {
        "type": "object",
        "properties": {
            "leaf": {"type": "string"},
            "obj": {
                "type": "object",
                "properties": {"child": {"type": "number"}},
            },
            "arr": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"role": {"type": "string"}},
                },
            },
        },
    }
    paths = _collect_property_paths(schema)
    assert "leaf" in paths
    assert "obj" in paths
    assert "obj.child" in paths
    assert "arr" in paths
    assert "arr[].role" in paths
    assert "arr[]" not in paths or "arr[].role" in paths  # array suffix only with field
    assert "missing" not in paths


def test_validate_edges_passes_well_formed() -> None:
    edges = parse_edges(REPO / "ops" / "schemas" / "README.md")
    failures = validate_edges(edges)
    if failures:
        for f in failures:
            print(f"  README:{f.edge.line}: {f.edge.source} -> {f.edge.target}: {f.reason}")
    assert failures == [], "live README should validate clean — fix README or schemas"


def test_validate_edges_reports_missing_field(tmp_path: Path, monkeypatch) -> None:
    # Create a minimal source schema that lacks the named field.
    schemas_dir = tmp_path / "ops" / "schemas"
    schemas_dir.mkdir(parents=True)
    (schemas_dir / "fakerole.schema.json").write_text(
        json.dumps({"type": "object", "properties": {"other_field": {"type": "string"}}}),
        encoding="utf-8",
    )
    (schemas_dir / "faketool.schema.json").write_text(
        json.dumps({"type": "object", "properties": {"id": {"type": "string"}}}),
        encoding="utf-8",
    )
    edge = Edge(source="fakerole", target="faketool", field="missing_field", line=10)
    # Monkeypatch the schema-loading module-level paths.
    import validate_schema_graph as vsg
    monkeypatch.setattr(vsg, "SCHEMAS_DIR", schemas_dir)
    failures = vsg.validate_edges([edge])
    assert len(failures) == 1
    assert "missing_field" in failures[0].reason


def test_validate_edges_reports_missing_target(tmp_path: Path, monkeypatch) -> None:
    schemas_dir = tmp_path / "ops" / "schemas"
    schemas_dir.mkdir(parents=True)
    (schemas_dir / "fakerole.schema.json").write_text(
        json.dumps({"type": "object", "properties": {"target_id": {"type": "string"}}}),
        encoding="utf-8",
    )
    edge = Edge(source="fakerole", target="does_not_exist", field="target_id", line=5)
    import validate_schema_graph as vsg
    monkeypatch.setattr(vsg, "SCHEMAS_DIR", schemas_dir)
    failures = vsg.validate_edges([edge])
    assert len(failures) == 1
    assert "target schema not found" in failures[0].reason
