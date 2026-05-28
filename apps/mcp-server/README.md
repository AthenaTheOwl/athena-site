# athena-mcp-server

A read-only Model Context Protocol server that exposes the athena-site
portfolio's authoritative model — decisions, schemas, runs, events — to any
MCP client (Claude Code, Codex CLI, Claude desktop, automation).

This is the "protocol standardization" layer of the portfolio's
five-point framework. Phases A through D built the source-of-truth model in
the file system. This server turns that source-of-truth model into a
queryable surface other agents can reason against.

## Tools

Seven read-only tools, snapshotted in `tool-surface.snapshot.json` and
gated by the `mcp-security-lab` surface-diff check.

### `decisions_list({ repo?, prefix?, status? })`

Walks `<portfolioRoot>/<repo>/decisions/DEC-*.md`, parses YAML
front-matter, and returns one row per DEC with id, repo, prefix, status,
owner_role, reversible, title, and path.

### `decisions_get({ id })`

Returns the full body plus parsed front-matter for one DEC by id.

### `schemas_list()`

Walks `athena-site/ops/schemas/*.schema.json` and returns name, title,
description, and path for each.

### `schemas_get({ name })`

Returns the full JSON Schema document for one named schema (e.g. `run`,
`event`, `decision`, `artifact`).

### `runs_list({ repo?, limit?, since? })`

Walks `<portfolioRoot>/<repo>/ops/run-records/run-*.json` and returns a
summary row per run (id, repo, spec_id, agent_id, runtime, status,
started_at, finished_at, path). Most-recent-first; default limit 50.

### `runs_get({ id })`

Returns the full Run record JSON document for one run by id.

### `events_query({ run_id?, type?, since?, until?, limit? })`

Walks `<portfolioRoot>/<repo>/ops/event-ledger/*.jsonl`, parses each line,
filters by run id, event type (exact or dotted-namespace prefix), and
time range. Default limit 100.

## Install

This package lives inside the athena-site repo under
`apps/mcp-server/`. It is a standalone npm package (not a workspace member
yet).

```sh
cd apps/mcp-server
npm install
npm run build
```

## Configure

The server resolves the portfolio root in this order:

1. `PORTFOLIO_ROOT` environment variable.
2. `~/.config/athena-mcp-server/config.json`, shaped as:
   ```json
   {
     "portfolioRoot": "/abs/path/to/random-apps",
     "schemaDir": "/abs/path/to/random-apps/athena-site/ops/schemas",
     "productRepos": ["athena-site", "supplier-risk-rag-agent", "..."]
   }
   ```
3. A walk upward from the current working directory, looking for a
   directory containing `athena-site/ops/schemas`.
4. `process.cwd()` as a final fallback.

`schemaDir` defaults to `<portfolioRoot>/athena-site/ops/schemas`.
`productRepos` defaults to every direct subdirectory of `portfolioRoot`
containing a `decisions/`, `ops/run-records/`, or `ops/event-ledger/`
folder.

## Connect from an MCP client

The server speaks the standard MCP protocol over stdio. From any MCP
client:

```sh
# After `npm run build`, the entry point is at dist/index.js.
node /abs/path/to/athena-site/apps/mcp-server/dist/index.js
```

Example Claude Code MCP config snippet:

```json
{
  "mcpServers": {
    "athena": {
      "command": "node",
      "args": ["/abs/path/to/athena-site/apps/mcp-server/dist/index.js"],
      "env": { "PORTFOLIO_ROOT": "/abs/path/to/random-apps" }
    }
  }
}
```

## Snapshot the tool surface

The server's tool surface is fingerprinted in
`tool-surface.snapshot.json`. Regenerate it whenever a tool is added,
removed, or its input schema changes:

```sh
npm run snapshot
```

The snapshot is byte-identical across runs when the source has not
changed. `mcp-security-lab` runs a gate (`validate_athena_mcp_surface`)
that fails CI when the live server's surface drifts from the committed
snapshot.

## Tests

```sh
npm test
```

Runs the unit tests for each tool against an in-process fixture
portfolio and an integration test that wires an in-process MCP client
to the server.

## See also

- DEC-CDCP-012-athena-mcp-server-exposes-portfolio-model: the decision
  record that authorizes this server.
- `../../specs/0002-athena-mcp-server/`: the spec ledger covering the
  R-CDCP-MCP-001..006 requirements this server satisfies.
- `../../../mcp-security-lab` and its `validate_athena_mcp_surface` gate:
  the drift check enforcing the snapshot.
