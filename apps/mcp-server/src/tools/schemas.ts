// `schemas_list` and `schemas_get` tool definitions.

import type { PortfolioConfig } from "../config.js";
import { listSchemas, readSchemaByName } from "../fs/walk.js";

export const schemasListTool = {
  name: "schemas_list",
  description:
    "List the portfolio's authoritative JSON Schemas. Walks athena-site/ops/schemas/*.schema.json and returns name/title/description/path for each.",
  inputSchema: {
    type: "object",
    additionalProperties: false,
    properties: {},
  },
} as const;

export const schemasGetTool = {
  name: "schemas_get",
  description:
    "Return the full JSON Schema document for one named schema (e.g. 'run', 'event', 'decision', 'artifact', 'role', 'tool', 'policy', 'workflow', 'state-machine', 'skill', 'dream-output').",
  inputSchema: {
    type: "object",
    additionalProperties: false,
    required: ["name"],
    properties: {
      name: {
        type: "string",
        description:
          "Schema name without the .schema.json suffix. Must contain no path separators.",
      },
    },
  },
} as const;

export interface SchemasGetInput {
  name: string;
}

export function handleSchemasList(config: PortfolioConfig): { schemas: unknown[] } {
  const records = listSchemas(config.schemaDir);
  return {
    schemas: records.map((r) => ({
      name: r.name,
      title: r.title,
      description: r.description,
      path: r.path,
    })),
  };
}

export function handleSchemasGet(
  config: PortfolioConfig,
  input: SchemasGetInput,
): { schema: unknown } {
  if (typeof input.name !== "string" || input.name.length === 0) {
    throw new Error("schemas_get: 'name' is required and must be a non-empty string");
  }
  const found = readSchemaByName(config.schemaDir, input.name);
  if (!found) {
    throw new Error(`schemas_get: no schema found with name '${input.name}'`);
  }
  return {
    schema: {
      name: found.name,
      path: found.path,
      document: found.schema,
    },
  };
}
