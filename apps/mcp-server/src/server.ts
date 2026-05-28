// Server construction. Exported so tests can wire an InMemoryTransport and
// the `start()` entry point can wire the stdio transport.

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

import type { PortfolioConfig } from "./config.js";
import {
  decisionsGetTool,
  decisionsListTool,
  handleDecisionsGet,
  handleDecisionsList,
} from "./tools/decisions.js";
import {
  eventsQueryTool,
  handleEventsQuery,
} from "./tools/events.js";
import {
  handleRunsGet,
  handleRunsList,
  runsGetTool,
  runsListTool,
} from "./tools/runs.js";
import {
  handleSchemasGet,
  handleSchemasList,
  schemasGetTool,
  schemasListTool,
} from "./tools/schemas.js";

export interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
}

export const TOOL_DEFINITIONS: readonly ToolDefinition[] = [
  decisionsListTool,
  decisionsGetTool,
  schemasListTool,
  schemasGetTool,
  runsListTool,
  runsGetTool,
  eventsQueryTool,
] as const;

export const SERVER_NAME = "athena-mcp-server";
export const SERVER_VERSION = "0.1.0";

export function createServer(config: PortfolioConfig): Server {
  const server = new Server(
    { name: SERVER_NAME, version: SERVER_VERSION },
    { capabilities: { tools: {} } },
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: TOOL_DEFINITIONS.map((tool) => ({
      name: tool.name,
      description: tool.description,
      inputSchema: tool.inputSchema,
    })),
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const toolName = request.params.name;
    const args = (request.params.arguments ?? {}) as Record<string, unknown>;
    try {
      const payload = await dispatchTool(config, toolName, args);
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(payload, null, 2),
          },
        ],
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return {
        isError: true,
        content: [
          {
            type: "text",
            text: JSON.stringify({ error: message }, null, 2),
          },
        ],
      };
    }
  });

  return server;
}

export async function dispatchTool(
  config: PortfolioConfig,
  toolName: string,
  args: Record<string, unknown>,
): Promise<unknown> {
  switch (toolName) {
    case "decisions_list":
      return handleDecisionsList(config, {
        repo: stringOrUndef(args.repo),
        prefix: stringOrUndef(args.prefix),
        status: stringOrUndef(args.status),
      });
    case "decisions_get":
      return handleDecisionsGet(config, { id: stringRequired("id", args.id) });
    case "schemas_list":
      return handleSchemasList(config);
    case "schemas_get":
      return handleSchemasGet(config, {
        name: stringRequired("name", args.name),
      });
    case "runs_list":
      return handleRunsList(config, {
        repo: stringOrUndef(args.repo),
        limit: numberOrUndef(args.limit),
        since: stringOrUndef(args.since),
      });
    case "runs_get":
      return handleRunsGet(config, { id: stringRequired("id", args.id) });
    case "events_query":
      return handleEventsQuery(config, {
        run_id: stringOrUndef(args.run_id),
        type: stringOrUndef(args.type),
        since: stringOrUndef(args.since),
        until: stringOrUndef(args.until),
        limit: numberOrUndef(args.limit),
      });
    default:
      throw new Error(`Unknown tool: ${toolName}`);
  }
}

function stringOrUndef(value: unknown): string | undefined {
  if (typeof value === "string" && value.length > 0) return value;
  return undefined;
}

function numberOrUndef(value: unknown): number | undefined {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  return undefined;
}

function stringRequired(field: string, value: unknown): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new Error(`Missing required string argument: ${field}`);
  }
  return value;
}
