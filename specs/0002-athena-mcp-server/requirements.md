# Requirements: Athena MCP Server

## Scope

athena-site ships a read-only MCP server at `apps/mcp-server/` that exposes
the portfolio's authoritative model — decisions, schemas, runs, events — to
any MCP client over stdio. The tool surface is snapshot-controlled and
drift-gated by `mcp-security-lab`.

## Requirements

| ID | Requirement | owner_role |
| --- | --- | --- |
| R-CDCP-MCP-001 | The server SHALL expose seven named read-only tools: `decisions_list`, `decisions_get`, `schemas_list`, `schemas_get`, `runs_list`, `runs_get`, `events_query`. | owner_role:implementation_agent |
| R-CDCP-MCP-002 | The committed `apps/mcp-server/tool-surface.snapshot.json` fingerprints every tool's name, description, and SHA-256 of its canonical input schema; the file changes only by deliberate snapshot regeneration. | owner_role:implementation_agent |
| R-CDCP-MCP-003 | Each tool implementation SHALL have a unit test against a fixture portfolio AND be exercised by an in-process integration test that wires an MCP client to the server. | owner_role:review_agent |
| R-CDCP-MCP-004 | The server SHALL be resilient to malformed JSON, missing files, and unreadable directories: it logs and skips, never crashes the process. | owner_role:implementation_agent |
| R-CDCP-MCP-005 | The server SHALL support overriding the portfolio root via the `PORTFOLIO_ROOT` env var AND via `~/.config/athena-mcp-server/config.json`, with env taking precedence. | owner_role:implementation_agent |
| R-CDCP-MCP-006 | Snapshot regeneration SHALL be reproducible: running the snapshot script twice in a row with no source changes produces byte-identical output (deterministic key ordering + canonical JSON hashing). | owner_role:review_agent |
