import { strict as assert } from "node:assert";
import { after, describe, it } from "node:test";

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";

import { createServer, TOOL_DEFINITIONS } from "../src/server.js";
import { buildSnapshot } from "../scripts/snapshot-tool-surface.js";
import { buildFixturePortfolio } from "./fixtures/setup.js";

const { config, cleanup } = buildFixturePortfolio();
after(() => cleanup());

async function withClient<T>(
  fn: (client: Client) => Promise<T>,
): Promise<T> {
  const server = createServer(config);
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  const client = new Client({ name: "test-client", version: "0.0.0" });
  await Promise.all([
    server.connect(serverTransport),
    client.connect(clientTransport),
  ]);
  try {
    return await fn(client);
  } finally {
    await client.close();
    await server.close();
  }
}

describe("integration", () => {
  it("exposes seven tools via tools/list", async () => {
    await withClient(async (client) => {
      const result = await client.listTools();
      assert.equal(result.tools.length, 7);
      const names = result.tools.map((t) => t.name).sort();
      assert.deepEqual(names, [
        "decisions_get",
        "decisions_list",
        "events_query",
        "runs_get",
        "runs_list",
        "schemas_get",
        "schemas_list",
      ]);
    });
  });

  it("calls decisions_list end to end", async () => {
    await withClient(async (client) => {
      const result = await client.callTool({
        name: "decisions_list",
        arguments: {},
      });
      assert.ok(Array.isArray(result.content));
      const text = (result.content as any[])[0].text as string;
      const parsed = JSON.parse(text) as { decisions: any[] };
      assert.equal(parsed.decisions.length, 2);
    });
  });

  it("calls schemas_get end to end", async () => {
    await withClient(async (client) => {
      const result = await client.callTool({
        name: "schemas_get",
        arguments: { name: "run" },
      });
      const text = (result.content as any[])[0].text as string;
      const parsed = JSON.parse(text) as { schema: any };
      assert.equal(parsed.schema.name, "run");
    });
  });

  it("calls events_query end to end", async () => {
    await withClient(async (client) => {
      const result = await client.callTool({
        name: "events_query",
        arguments: { type: "gate" },
      });
      const text = (result.content as any[])[0].text as string;
      const parsed = JSON.parse(text) as { events: any[] };
      assert.equal(parsed.events.length, 1);
    });
  });

  it("returns an error result when a tool argument is invalid", async () => {
    await withClient(async (client) => {
      const result = await client.callTool({
        name: "decisions_get",
        arguments: { id: "" },
      });
      assert.equal(result.isError, true);
    });
  });

  it("the snapshot generator's tool list matches the declared TOOL_DEFINITIONS", () => {
    const snapshot = buildSnapshot();
    const declared = TOOL_DEFINITIONS.map((t) => t.name).sort();
    const snapshotNames = snapshot.tools.map((t) => t.name).sort();
    assert.deepEqual(snapshotNames, declared);
  });

  it("snapshot regeneration is deterministic", () => {
    const a = buildSnapshot();
    const b = buildSnapshot();
    assert.deepEqual(a, b);
  });
});
