import { strict as assert } from "node:assert";
import { after, describe, it } from "node:test";

import { handleEventsQuery } from "../src/tools/events.js";
import { buildFixturePortfolio } from "./fixtures/setup.js";

const { config, cleanup } = buildFixturePortfolio();
after(() => cleanup());

describe("events_query", () => {
  it("returns events across the portfolio", async () => {
    const result = (await handleEventsQuery(config, {})) as { events: any[] };
    assert.equal(result.events.length, 2);
  });

  it("filters by run_id", async () => {
    const result = (await handleEventsQuery(config, {
      run_id: "run-aaaaaaaa",
    })) as { events: any[] };
    assert.equal(result.events.length, 2);
  });

  it("filters by exact event type", async () => {
    const result = (await handleEventsQuery(config, {
      type: "gate.check.passed",
    })) as { events: any[] };
    assert.equal(result.events.length, 1);
    assert.equal(result.events[0].type, "gate.check.passed");
  });

  it("filters by dotted-namespace prefix", async () => {
    const result = (await handleEventsQuery(config, { type: "gate" })) as {
      events: any[];
    };
    assert.equal(result.events.length, 1);
  });

  it("filters by time range", async () => {
    const result = (await handleEventsQuery(config, {
      since: "2026-05-27T00:00:01Z",
    })) as { events: any[] };
    assert.equal(result.events.length, 1);
    assert.equal(result.events[0].type, "gate.check.passed");
  });

  it("honors limit", async () => {
    const result = (await handleEventsQuery(config, { limit: 1 })) as {
      events: any[];
    };
    assert.equal(result.events.length, 1);
  });

  it("skips malformed JSONL lines without crashing", async () => {
    // The fixture has '{ not valid json' as one line; we should still get the
    // two good events.
    const result = (await handleEventsQuery(config, {})) as { events: any[] };
    assert.equal(result.events.length, 2);
  });
});
