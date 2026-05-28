// `decisions_list` and `decisions_get` tool definitions.

import type { PortfolioConfig } from "../config.js";
import { readDecisionById, walkDecisions } from "../fs/walk.js";

export const decisionsListTool = {
  name: "decisions_list",
  description:
    "List DEC-* decision records across the portfolio. Walks <portfolio>/<repo>/decisions/DEC-*.md, parses YAML front-matter, returns id/repo/prefix/status/owner_role/reversible/title/path for each. Filterable by repo, by DEC prefix (e.g. CDCP, MCPSEC), and by status.",
  inputSchema: {
    type: "object",
    additionalProperties: false,
    properties: {
      repo: {
        type: "string",
        description:
          "Optional product repo name to restrict the walk (e.g. 'athena-site', 'mcp-security-lab'). Omit to walk every repo.",
      },
      prefix: {
        type: "string",
        description:
          "Optional DEC prefix to filter by (e.g. 'CDCP', 'MCPSEC', 'EVL').",
      },
      status: {
        type: "string",
        description:
          "Optional status to filter by (e.g. 'approved', 'proposed', 'reversed', 'superseded').",
      },
    },
  },
} as const;

export const decisionsGetTool = {
  name: "decisions_get",
  description:
    "Return the full body plus parsed front-matter of a single DEC by id. Walks every product repo's decisions/ until the id is matched.",
  inputSchema: {
    type: "object",
    additionalProperties: false,
    required: ["id"],
    properties: {
      id: {
        type: "string",
        description:
          "Full DEC id, e.g. 'DEC-CDCP-011-run-records-carry-replay-equivalence-evidence'. Must contain no path separators.",
      },
    },
  },
} as const;

export interface DecisionsListInput {
  repo?: string;
  prefix?: string;
  status?: string;
}

export interface DecisionsGetInput {
  id: string;
}

export function handleDecisionsList(
  config: PortfolioConfig,
  input: DecisionsListInput,
): { decisions: unknown[] } {
  const records = walkDecisions(config.portfolioRoot, config.productRepos, {
    repo: input.repo,
    prefix: input.prefix,
    status: input.status,
  });
  return {
    decisions: records.map((r) => ({
      id: r.id,
      repo: r.repo,
      prefix: r.prefix,
      status: r.status,
      owner_role: r.owner_role ?? null,
      reversible: r.reversible ?? null,
      title: r.title,
      path: r.path,
    })),
  };
}

export function handleDecisionsGet(
  config: PortfolioConfig,
  input: DecisionsGetInput,
): { decision: unknown } {
  if (typeof input.id !== "string" || input.id.length === 0) {
    throw new Error("decisions_get: 'id' is required and must be a non-empty string");
  }
  const found = readDecisionById(
    config.portfolioRoot,
    config.productRepos,
    input.id,
  );
  if (!found) {
    throw new Error(`decisions_get: no DEC found with id '${input.id}'`);
  }
  return {
    decision: {
      id: found.record.id,
      repo: found.record.repo,
      prefix: found.record.prefix,
      status: found.record.status,
      owner_role: found.record.owner_role ?? null,
      reversible: found.record.reversible ?? null,
      title: found.record.title,
      path: found.record.path,
      frontmatter: found.record.frontmatter,
      body: found.body,
    },
  };
}
