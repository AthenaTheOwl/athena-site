#!/usr/bin/env node
// Entry point for the Athena MCP server. Connects to a stdio transport so the
// process can be launched by an MCP client (Claude Code, Codex CLI, Claude
// desktop, etc.) over its standard input and output.

import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

import { loadConfig } from "./config.js";
import { createServer, SERVER_NAME, SERVER_VERSION } from "./server.js";

async function main(): Promise<void> {
  const config = loadConfig();
  const server = createServer(config);
  const transport = new StdioServerTransport();
  await server.connect(transport);
  process.stderr.write(
    `[${SERVER_NAME} ${SERVER_VERSION}] connected; portfolio_root=${config.portfolioRoot} repos=${config.productRepos.length}\n`,
  );
}

main().catch((err) => {
  process.stderr.write(
    `[athena-mcp-server] fatal: ${err instanceof Error ? err.stack ?? err.message : String(err)}\n`,
  );
  process.exit(1);
});
