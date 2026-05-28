---
id: DEC-CDCP-012-athena-mcp-server-exposes-portfolio-model
spec: specs/0002-athena-mcp-server/
requirement: R-CDCP-MCP-001
date: 2026-05-27
status: approved
reversible: true
decision: |
  athena-site ships an MCP server (apps/mcp-server/) that exposes seven
  read-only tools over the portfolio's authoritative model — decisions,
  schemas, runs, events. The server speaks the Model Context Protocol
  over stdio so any MCP client (Claude Code, Codex CLI, Claude desktop,
  automation) can query the source-of-truth records without re-walking
  the file system itself. The tool surface is fingerprinted in
  apps/mcp-server/tool-surface.snapshot.json; mcp-security-lab gates
  against drift.
alternatives:
  - label: ship a REST API instead of an MCP server
    rejected_because: |
      The portfolio's consumers are agents, not browsers. MCP is the
      protocol every agent runtime in this portfolio already speaks
      (Claude Code, Codex CLI). A REST API would force each agent to
      learn a second transport for the same data and ship per-client
      adapter code.
  - label: ship one MCP tool per record kind with full CRUD
    rejected_because: |
      Writes need policy, gates, and provenance — none of which the
      source-of-truth files yet enforce at the protocol boundary. The
      portfolio's discipline is "the file system is the model";
      adding write tools would require a second policy plane on top.
      Read-only ships now and unblocks the consumers without
      introducing that second plane.
  - label: expose the model as MCP resources rather than tools
    rejected_because: |
      Resources are pull-by-URI and assume the client knows the URI
      space ahead of time. Tools are queryable with structured filters
      (repo, prefix, status, time range), which is how every consuming
      agent will actually use this server. Tools also fit the
      snapshot-the-surface gate model naturally: a tool surface has a
      stable name and input schema; a resource URI space drifts on
      every new file.
rationale: |
  Phases A through D built the authoritative model layer — cross-repo
  schemas, DECs, Run records with replay-equivalence evidence, event
  ledgers across procurement-negotiation-lab, supplier-risk-rag-agent,
  ai-field-brief, and chip-supply-chain-map. That model is the load-
  bearing artifact of the Cognitive Delivery Control Plane. But until
  Phase E, the model was readable only by the maintainer's eyes and by
  whatever ad-hoc script each agent ran against the file system.

  Other agents need a standard query interface or the CDCP discipline
  stays invisible to consumers. The Model Context Protocol is the
  portfolio-wide answer: it is the protocol Claude Code, Codex CLI,
  Claude desktop, and every automation framework already speaks. An
  athena-site MCP server lets any of them ask "which DECs landed this
  week", "show me the run records for the supplier-risk eval suite",
  "what does the run schema look like" without learning the file
  layout. The server reads; the file system stays the source of truth.

  The surface is intentionally small (seven tools) and read-only.
  Small means the snapshot fits on one page and reviewers can audit
  every change. Read-only means the server cannot violate the file
  system's existing gates: a write surface would need its own policy
  plane and provenance, which is a separate decision.

  The surface is contracted via tool-surface.snapshot.json. The
  snapshot lists every tool name plus the SHA-256 hash of its
  canonicalized input schema. mcp-security-lab runs the
  validate_athena_mcp_surface gate on each CI build and fails when the
  live server's surface diverges from the snapshot. The snapshot is
  the contract; drift is detected, never silent.
evidence:
  - kind: code
    ref: apps/mcp-server/src/server.ts
  - kind: code
    ref: apps/mcp-server/src/tools/decisions.ts
  - kind: code
    ref: apps/mcp-server/src/tools/schemas.ts
  - kind: code
    ref: apps/mcp-server/src/tools/runs.ts
  - kind: code
    ref: apps/mcp-server/src/tools/events.ts
  - kind: schema
    ref: apps/mcp-server/src/schemas/tool-surface.json
  - kind: schema
    ref: apps/mcp-server/tool-surface.snapshot.json
  - kind: spec
    ref: specs/0002-athena-mcp-server/requirements.md
  - kind: decision
    ref: ../mcp-security-lab/decisions/DEC-MCPSEC-007-athena-mcp-surface-drift-gate.md
rollback: |
  Disable or unpublish the MCP server by removing the apps/mcp-server/
  bin entry from its package.json and stopping any client config that
  launched it. The source-of-truth records under decisions/, ops/, and
  ops/schemas/ are untouched by this server and remain readable
  directly. The mcp-security-lab gate becomes a no-op once the
  snapshot file is removed from athena-site, which is the same revert
  step. Existing run records, schemas, and event ledgers continue to
  validate against their schemas with no further action.
owner: editorial
---

## decision

athena-site ships an MCP server under `apps/mcp-server/` that exposes
seven read-only tools over the portfolio's authoritative model —
`decisions_list`, `decisions_get`, `schemas_list`, `schemas_get`,
`runs_list`, `runs_get`, `events_query`. The server speaks the Model
Context Protocol over stdio. The tool surface is fingerprinted in
`apps/mcp-server/tool-surface.snapshot.json`; `mcp-security-lab`
gates against drift via `validate_athena_mcp_surface`.

## alternatives

- Ship a REST API. Rejected: the portfolio's consumers are agents that
  already speak MCP; a second transport would force per-client adapter
  code.
- Ship one tool per record kind with full CRUD. Rejected: writes need
  policy and provenance the source-of-truth files do not yet enforce
  at the protocol boundary. Read-only ships now without introducing a
  second policy plane.
- Expose the model as MCP resources. Rejected: resources are pull-by-
  URI and assume a stable URI space; tools support structured filters
  (repo, prefix, status, time range) and fit the snapshot-the-surface
  gate model.

## rationale

Phases A through D built the authoritative model layer. Until Phase E
that model was readable only by the maintainer's eyes and ad-hoc
scripts. Other agents need a standard query interface or the CDCP
discipline stays invisible to consumers.

The Model Context Protocol is the portfolio-wide answer because it is
the protocol every agent runtime in this portfolio already speaks. An
MCP server lets any client ask "which DECs landed this week", "show me
the run records for the supplier-risk eval suite", "what does the run
schema look like" without learning the file layout. The server reads;
the file system stays the source of truth.

Seven tools, read-only, snapshotted, drift-gated. The surface is
small enough to audit; the snapshot is the contract.

## evidence

- `apps/mcp-server/src/server.ts` — the Server class and request
  handlers for `tools/list` and `tools/call`.
- `apps/mcp-server/src/tools/*.ts` — one file per tool family
  (decisions, schemas, runs, events) declaring input schemas and
  pure-function handlers.
- `apps/mcp-server/src/schemas/tool-surface.json` — the JSON Schema
  describing what a snapshot file looks like.
- `apps/mcp-server/tool-surface.snapshot.json` — the current snapshot
  (seven tools, version 0.1.0).
- `specs/0002-athena-mcp-server/requirements.md` — R-CDCP-MCP-001..006
  the server satisfies.
- `../mcp-security-lab/decisions/DEC-MCPSEC-007-athena-mcp-surface-drift-gate.md`
  — the complementary gate that fails CI on surface drift.

## relationship to mcp-security-lab

`mcp-security-lab` already scans MCP servers from a security angle
(config diff gate, policy verdicts). This DEC adds a second
relationship: `mcp-security-lab` is the gatekeeper for athena-site's
own MCP server surface. The `validate_athena_mcp_surface` gate reads
this server's `tool-surface.snapshot.json` and compares it against the
live tool surface; drift fails the build. The snapshot is the
contract.

## requirement coverage

R-CDCP-MCP-001..006 land in `specs/0002-athena-mcp-server/` in this
phase:

- R-CDCP-MCP-001: server exposes seven named read-only tools per the
  public surface.
- R-CDCP-MCP-002: tool-surface.snapshot.json is committed and updated
  only by deliberate snapshot regeneration.
- R-CDCP-MCP-003: each tool implementation is unit-tested plus covered
  by an end-to-end integration test.
- R-CDCP-MCP-004: server is resilient to malformed JSON or missing
  files (logs and skips).
- R-CDCP-MCP-005: server config supports portfolio-root override via
  env var or config file.
- R-CDCP-MCP-006: snapshot regeneration is reproducible — running the
  snapshot script twice in a row with no source changes produces
  byte-identical output.

## rollback

Disable or unpublish the MCP server by removing the `apps/mcp-server/`
`bin` entry from its package.json and stopping any client config that
launched it. The source-of-truth records under `decisions/`, `ops/`,
and `ops/schemas/` are untouched by this server and remain readable
directly. The `mcp-security-lab` gate becomes a no-op once the
snapshot file is removed from athena-site, which is the same revert
step. Existing run records, schemas, and event ledgers continue to
validate against their schemas with no further action.
