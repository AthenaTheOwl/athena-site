// Shared test fixture: build an in-memory portfolio root with two product
// repos, each carrying a DEC, a Run record, and an event ledger.

import * as fs from "node:fs";
import * as path from "node:path";
import * as os from "node:os";

import type { PortfolioConfig } from "../../src/config.js";

export function buildFixturePortfolio(): { config: PortfolioConfig; cleanup: () => void } {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "athena-mcp-test-"));

  // athena-site/ops/schemas with two schemas.
  const schemaDir = path.join(root, "athena-site", "ops", "schemas");
  fs.mkdirSync(schemaDir, { recursive: true });
  fs.writeFileSync(
    path.join(schemaDir, "run.schema.json"),
    JSON.stringify(
      {
        $id: "https://athena.dev/ops/schemas/run.schema.json",
        title: "Run",
        description: "A run.",
        type: "object",
      },
      null,
      2,
    ),
  );
  fs.writeFileSync(
    path.join(schemaDir, "event.schema.json"),
    JSON.stringify(
      {
        $id: "https://athena.dev/ops/schemas/event.schema.json",
        title: "Event",
        description: "An event.",
        type: "object",
      },
      null,
      2,
    ),
  );

  // repo-a: one DEC, one Run, one event ledger.
  const repoADir = path.join(root, "repo-a");
  fs.mkdirSync(path.join(repoADir, "decisions"), { recursive: true });
  fs.mkdirSync(path.join(repoADir, "ops", "run-records"), { recursive: true });
  fs.mkdirSync(path.join(repoADir, "ops", "event-ledger"), { recursive: true });

  fs.writeFileSync(
    path.join(repoADir, "decisions", "DEC-TEST-001-hello.md"),
    [
      "---",
      "id: DEC-TEST-001-hello",
      "spec: specs/0001-fixture/",
      "requirement: R-TEST-001",
      "date: 2026-05-27",
      "status: approved",
      "reversible: true",
      "owner: editorial",
      "decision: |",
      "  Hello, fixture world.",
      "---",
      "",
      "# DEC-TEST-001",
      "",
      "Body content.",
      "",
    ].join("\n"),
  );

  fs.writeFileSync(
    path.join(repoADir, "ops", "run-records", "run-aaaaaaaa.json"),
    JSON.stringify(
      {
        id: "run-aaaaaaaa",
        spec_id: "specs/0001-fixture/",
        agent_id: "fixture@test",
        runtime: "test",
        workspace_id: "fixture",
        started_at: "2026-05-27T00:00:00Z",
        finished_at: "2026-05-27T00:00:01Z",
        status: "done",
      },
      null,
      2,
    ),
  );

  fs.writeFileSync(
    path.join(repoADir, "ops", "event-ledger", "run-aaaaaaaa.jsonl"),
    [
      JSON.stringify({
        event_id: "11111111-1111-1111-1111-111111111111",
        type: "pipeline.start",
        created_at: "2026-05-27T00:00:00Z",
        actor: { kind: "system", id: "fixture" },
        payload: { step: "start" },
        run_id: "run-aaaaaaaa",
      }),
      JSON.stringify({
        event_id: "22222222-2222-2222-2222-222222222222",
        type: "gate.check.passed",
        created_at: "2026-05-27T00:00:01Z",
        actor: { kind: "system", id: "fixture" },
        payload: { gate_name: "typecheck" },
        run_id: "run-aaaaaaaa",
      }),
      // Intentional malformed line to verify resilience.
      "{ not valid json",
      "",
    ].join("\n"),
  );

  // repo-b: separate DEC + a different run record.
  const repoBDir = path.join(root, "repo-b");
  fs.mkdirSync(path.join(repoBDir, "decisions"), { recursive: true });
  fs.mkdirSync(path.join(repoBDir, "ops", "run-records"), { recursive: true });
  fs.mkdirSync(path.join(repoBDir, "ops", "event-ledger"), { recursive: true });

  fs.writeFileSync(
    path.join(repoBDir, "decisions", "DEC-OTHER-002-second.md"),
    [
      "---",
      "id: DEC-OTHER-002-second",
      "spec: specs/0002-fixture-b/",
      "requirement: R-OTHER-002",
      "date: 2026-05-26",
      "status: proposed",
      "reversible: false",
      "owner: platform",
      "decision: |",
      "  Second DEC.",
      "---",
      "",
      "Body B.",
    ].join("\n"),
  );

  fs.writeFileSync(
    path.join(repoBDir, "ops", "run-records", "run-bbbbbbbb.json"),
    JSON.stringify(
      {
        id: "run-bbbbbbbb",
        spec_id: "specs/0002-fixture-b/",
        agent_id: "fixture@test",
        runtime: "test",
        workspace_id: "fixture-b",
        started_at: "2026-05-26T00:00:00Z",
        status: "running",
      },
      null,
      2,
    ),
  );

  // Intentionally malformed run record to verify resilience.
  fs.writeFileSync(
    path.join(repoBDir, "ops", "run-records", "run-malformed.json"),
    "{ not json",
  );

  const config: PortfolioConfig = {
    portfolioRoot: root,
    schemaDir,
    productRepos: ["athena-site", "repo-a", "repo-b"],
  };

  return {
    config,
    cleanup: () => {
      try {
        fs.rmSync(root, { recursive: true, force: true });
      } catch {
        /* best-effort cleanup */
      }
    },
  };
}
