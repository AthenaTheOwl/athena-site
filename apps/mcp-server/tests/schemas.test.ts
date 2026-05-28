import { strict as assert } from "node:assert";
import { after, describe, it } from "node:test";

import {
  handleSchemasGet,
  handleSchemasList,
} from "../src/tools/schemas.js";
import { buildFixturePortfolio } from "./fixtures/setup.js";

const { config, cleanup } = buildFixturePortfolio();
after(() => cleanup());

describe("schemas_list", () => {
  it("lists every schema in the schemaDir", () => {
    const result = handleSchemasList(config) as { schemas: any[] };
    const names = result.schemas.map((s) => s.name).sort();
    assert.deepEqual(names, ["event", "run"]);
  });
});

describe("schemas_get", () => {
  it("returns the full schema document", () => {
    const result = handleSchemasGet(config, { name: "run" }) as { schema: any };
    assert.equal(result.schema.name, "run");
    assert.equal((result.schema.document as any).title, "Run");
  });

  it("throws on missing schema", () => {
    assert.throws(() => handleSchemasGet(config, { name: "nope" }));
  });

  it("rejects path-injection attempts", () => {
    assert.throws(() => handleSchemasGet(config, { name: "../package" }));
  });
});
