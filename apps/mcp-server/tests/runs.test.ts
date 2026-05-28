import { strict as assert } from "node:assert";
import { after, describe, it } from "node:test";

import { handleRunsGet, handleRunsList } from "../src/tools/runs.js";
import { buildFixturePortfolio } from "./fixtures/setup.js";

const { config, cleanup } = buildFixturePortfolio();
after(() => cleanup());

describe("runs_list", () => {
  it("lists runs from every product repo by default, most recent first", () => {
    const result = handleRunsList(config, {}) as { runs: any[] };
    assert.equal(result.runs.length, 2);
    assert.equal(result.runs[0].id, "run-aaaaaaaa");
    assert.equal(result.runs[1].id, "run-bbbbbbbb");
  });

  it("filters by repo", () => {
    const result = handleRunsList(config, { repo: "repo-b" }) as { runs: any[] };
    assert.equal(result.runs.length, 1);
    assert.equal(result.runs[0].id, "run-bbbbbbbb");
  });

  it("honors limit", () => {
    const result = handleRunsList(config, { limit: 1 }) as { runs: any[] };
    assert.equal(result.runs.length, 1);
  });

  it("filters by since", () => {
    const result = handleRunsList(config, {
      since: "2026-05-27T00:00:00Z",
    }) as { runs: any[] };
    assert.equal(result.runs.length, 1);
    assert.equal(result.runs[0].id, "run-aaaaaaaa");
  });

  it("skips malformed JSON files without crashing", () => {
    // repo-b has run-malformed.json; the list should still return repo-b's good run.
    const result = handleRunsList(config, { repo: "repo-b" }) as { runs: any[] };
    assert.equal(result.runs.length, 1);
  });
});

describe("runs_get", () => {
  it("returns the full Run record", () => {
    const result = handleRunsGet(config, { id: "run-aaaaaaaa" }) as { run: any };
    assert.equal(result.run.id, "run-aaaaaaaa");
    assert.equal((result.run.record as any).status, "done");
  });

  it("throws on unknown id", () => {
    assert.throws(() => handleRunsGet(config, { id: "run-zzzzzzzz" }));
  });

  it("rejects path-injection attempts", () => {
    assert.throws(() => handleRunsGet(config, { id: "../etc/passwd" }));
  });
});
