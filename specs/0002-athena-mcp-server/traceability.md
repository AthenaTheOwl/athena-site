# Traceability: Athena MCP Server

| Requirement | Code or artifact | Decision coverage |
| --- | --- | --- |
| R-CDCP-MCP-001 | `apps/mcp-server/src/server.ts`, `apps/mcp-server/src/tools/decisions.ts`, `apps/mcp-server/src/tools/schemas.ts`, `apps/mcp-server/src/tools/runs.ts`, `apps/mcp-server/src/tools/events.ts`, `apps/mcp-server/tool-surface.snapshot.json` | DEC-CDCP-012-athena-mcp-server-exposes-portfolio-model |
| R-CDCP-MCP-002 | `apps/mcp-server/tool-surface.snapshot.json`, `apps/mcp-server/src/schemas/tool-surface.json`, `apps/mcp-server/scripts/snapshot-tool-surface.ts` | DEC-CDCP-012-athena-mcp-server-exposes-portfolio-model |
| R-CDCP-MCP-003 | `apps/mcp-server/tests/decisions.test.ts`, `apps/mcp-server/tests/schemas.test.ts`, `apps/mcp-server/tests/runs.test.ts`, `apps/mcp-server/tests/events.test.ts`, `apps/mcp-server/tests/integration.test.ts` | DEC-CDCP-012-athena-mcp-server-exposes-portfolio-model |
| R-CDCP-MCP-004 | `apps/mcp-server/src/fs/walk.ts` (logSkip + safeReadJson + readJsonlFile), `apps/mcp-server/tests/runs.test.ts` (skips malformed JSON), `apps/mcp-server/tests/events.test.ts` (skips malformed JSONL) | DEC-CDCP-012-athena-mcp-server-exposes-portfolio-model |
| R-CDCP-MCP-005 | `apps/mcp-server/src/config.ts` (env var + ~/.config override), `apps/mcp-server/README.md` (configure section) | DEC-CDCP-012-athena-mcp-server-exposes-portfolio-model |
| R-CDCP-MCP-006 | `apps/mcp-server/scripts/snapshot-tool-surface.ts` (canonicalJson + sorted tools), `apps/mcp-server/tests/integration.test.ts` ("snapshot regeneration is deterministic") | DEC-CDCP-012-athena-mcp-server-exposes-portfolio-model |
