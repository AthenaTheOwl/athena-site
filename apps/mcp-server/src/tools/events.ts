// `events_query` tool definition.

import type { PortfolioConfig } from "../config.js";
import { queryEvents } from "../fs/walk.js";

export const eventsQueryTool = {
  name: "events_query",
  description:
    "Query the portfolio's event ledger. Walks <portfolio>/<repo>/ops/event-ledger/*.jsonl, parses each line, filters by run_id, type (exact or dotted-namespace prefix, e.g. 'gate' matches 'gate.check.passed'), and time range. Returns sorted-by-time event objects, capped by limit (default 100).",
  inputSchema: {
    type: "object",
    additionalProperties: false,
    properties: {
      run_id: {
        type: "string",
        description: "Optional run id to filter on. Matches event.run_id exactly.",
      },
      type: {
        type: "string",
        description:
          "Optional event type or dotted-namespace prefix. 'gate' matches 'gate.check.passed' and 'gate.run.evidence_recorded'.",
      },
      since: {
        type: "string",
        description: "Optional ISO 8601 timestamp lower bound (inclusive).",
      },
      until: {
        type: "string",
        description: "Optional ISO 8601 timestamp upper bound (inclusive).",
      },
      limit: {
        type: "integer",
        minimum: 1,
        maximum: 10000,
        description: "Maximum number of events to return. Default 100.",
      },
    },
  },
} as const;

export interface EventsQueryInput {
  run_id?: string;
  type?: string;
  since?: string;
  until?: string;
  limit?: number;
}

export async function handleEventsQuery(
  config: PortfolioConfig,
  input: EventsQueryInput,
): Promise<{ events: unknown[] }> {
  const events = await queryEvents(config.portfolioRoot, config.productRepos, input);
  return {
    events: events.map((e) => ({
      event_id: e.event_id,
      type: e.type,
      created_at: e.created_at,
      run_id: e.run_id ?? null,
      spec_id: e.spec_id ?? null,
      artifact_id: e.artifact_id ?? null,
      actor: e.actor ?? null,
      payload: e.payload ?? null,
      parent_event_id: e.parent_event_id ?? null,
      source_repo: e.source_repo ?? null,
      source_path: e.source_path ?? null,
    })),
  };
}
