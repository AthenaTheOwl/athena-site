// `runs_list` and `runs_get` tool definitions.

import type { PortfolioConfig } from "../config.js";
import { readRunById, walkRuns } from "../fs/walk.js";

export const runsListTool = {
  name: "runs_list",
  description:
    "List Run records across the portfolio. Walks <portfolio>/<repo>/ops/run-records/run-*.json and returns id/repo/spec_id/agent_id/runtime/status/started_at/finished_at/path. Filterable by repo, since (ISO 8601), and limit (default 50). Returned most-recent-first.",
  inputSchema: {
    type: "object",
    additionalProperties: false,
    properties: {
      repo: {
        type: "string",
        description:
          "Optional product repo name to restrict the walk. Omit to walk every repo.",
      },
      limit: {
        type: "integer",
        minimum: 1,
        maximum: 1000,
        description: "Maximum number of records to return. Default 50.",
      },
      since: {
        type: "string",
        description:
          "Optional ISO 8601 timestamp. Only runs with started_at >= this value are returned.",
      },
    },
  },
} as const;

export const runsGetTool = {
  name: "runs_get",
  description:
    "Return the full Run record JSON document for one run by id. Walks every product repo's ops/run-records/ until matched.",
  inputSchema: {
    type: "object",
    additionalProperties: false,
    required: ["id"],
    properties: {
      id: {
        type: "string",
        description:
          "Run id (typically 'run-<hex>'). Must contain no path separators.",
      },
    },
  },
} as const;

export interface RunsListInput {
  repo?: string;
  limit?: number;
  since?: string;
}

export interface RunsGetInput {
  id: string;
}

export function handleRunsList(
  config: PortfolioConfig,
  input: RunsListInput,
): { runs: unknown[] } {
  const records = walkRuns(config.portfolioRoot, config.productRepos, {
    repo: input.repo,
    limit: input.limit,
    since: input.since,
  });
  return {
    runs: records.map((r) => ({
      id: r.id,
      repo: r.repo,
      spec_id: r.spec_id,
      agent_id: r.agent_id,
      runtime: r.runtime,
      status: r.status,
      started_at: r.started_at,
      finished_at: r.finished_at ?? null,
      path: r.path,
    })),
  };
}

export function handleRunsGet(
  config: PortfolioConfig,
  input: RunsGetInput,
): { run: unknown } {
  if (typeof input.id !== "string" || input.id.length === 0) {
    throw new Error("runs_get: 'id' is required and must be a non-empty string");
  }
  const found = readRunById(config.portfolioRoot, config.productRepos, input.id);
  if (!found) {
    throw new Error(`runs_get: no run found with id '${input.id}'`);
  }
  return {
    run: {
      id: found.record.id,
      repo: found.record.repo,
      path: found.record.path,
      record: found.full,
    },
  };
}
