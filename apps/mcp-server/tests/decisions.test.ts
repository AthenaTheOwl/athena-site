import { strict as assert } from "node:assert";
import { after, describe, it } from "node:test";

import {
  handleDecisionsGet,
  handleDecisionsList,
} from "../src/tools/decisions.js";
import { buildFixturePortfolio } from "./fixtures/setup.js";

const { config, cleanup } = buildFixturePortfolio();
after(() => cleanup());

describe("decisions_list", () => {
  it("lists DECs from every product repo by default", () => {
    const result = handleDecisionsList(config, {}) as { decisions: any[] };
    assert.equal(result.decisions.length, 2);
    const ids = result.decisions.map((d) => d.id).sort();
    assert.deepEqual(ids, ["DEC-OTHER-002-second", "DEC-TEST-001-hello"]);
  });

  it("filters by repo", () => {
    const result = handleDecisionsList(config, { repo: "repo-a" }) as { decisions: any[] };
    assert.equal(result.decisions.length, 1);
    assert.equal(result.decisions[0].id, "DEC-TEST-001-hello");
  });

  it("filters by prefix", () => {
    const result = handleDecisionsList(config, { prefix: "OTHER" }) as { decisions: any[] };
    assert.equal(result.decisions.length, 1);
    assert.equal(result.decisions[0].prefix, "OTHER");
  });

  it("filters by status", () => {
    const result = handleDecisionsList(config, { status: "proposed" }) as { decisions: any[] };
    assert.equal(result.decisions.length, 1);
    assert.equal(result.decisions[0].status, "proposed");
  });
});

describe("decisions_get", () => {
  it("returns full body + parsed front-matter for a known id", () => {
    const result = handleDecisionsGet(config, {
      id: "DEC-TEST-001-hello",
    }) as { decision: any };
    assert.equal(result.decision.id, "DEC-TEST-001-hello");
    assert.equal(result.decision.status, "approved");
    assert.equal(result.decision.frontmatter.requirement, "R-TEST-001");
    assert.ok(typeof result.decision.body === "string");
    assert.ok(result.decision.body.includes("Body content"));
  });

  it("throws when id is missing", () => {
    assert.throws(() => handleDecisionsGet(config, { id: "" }));
  });

  it("throws when id does not match", () => {
    assert.throws(() =>
      handleDecisionsGet(config, { id: "DEC-NOPE-999-missing" }),
    );
  });

  it("rejects path-injection attempts", () => {
    assert.throws(() => handleDecisionsGet(config, { id: "../etc/passwd" }));
  });
});
