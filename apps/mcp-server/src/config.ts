// Configuration for the Athena MCP server.
//
// The server walks the portfolio root for decisions, run records, and event
// ledgers, and reads schemas from athena-site's ops/schemas/ directory.
//
// Resolution order (first match wins):
//   1. Constructor argument (used by tests).
//   2. ~/.config/athena-mcp-server/config.json (user-level override).
//   3. PORTFOLIO_ROOT env var.
//   4. Walking up from process.cwd() to find a directory containing
//      both athena-site/ops/schemas and at least one product repo with
//      ops/run-records.
//   5. process.cwd() as a final fallback.

import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

export interface PortfolioConfig {
  // Absolute path to the directory holding all product repos (the portfolio root).
  portfolioRoot: string;
  // Absolute path to the JSON Schemas directory (lives inside athena-site).
  schemaDir: string;
  // Names of product-repo subdirectories that may contain decisions/, ops/run-records/, ops/event-ledger/.
  productRepos: string[];
}

const USER_CONFIG_PATH = path.join(
  os.homedir(),
  ".config",
  "athena-mcp-server",
  "config.json",
);

export function loadConfig(override?: Partial<PortfolioConfig>): PortfolioConfig {
  const userConfig = readUserConfig();
  const portfolioRoot = pickPortfolioRoot(override, userConfig);
  const schemaDir =
    override?.schemaDir ??
    userConfig?.schemaDir ??
    path.join(portfolioRoot, "athena-site", "ops", "schemas");
  const productRepos =
    override?.productRepos ??
    userConfig?.productRepos ??
    discoverProductRepos(portfolioRoot);
  return {
    portfolioRoot: path.resolve(portfolioRoot),
    schemaDir: path.resolve(schemaDir),
    productRepos: [...productRepos].sort(),
  };
}

function pickPortfolioRoot(
  override?: Partial<PortfolioConfig>,
  userConfig?: Partial<PortfolioConfig>,
): string {
  if (override?.portfolioRoot) return override.portfolioRoot;
  if (userConfig?.portfolioRoot) return userConfig.portfolioRoot;
  if (process.env.PORTFOLIO_ROOT) return process.env.PORTFOLIO_ROOT;
  const walked = walkForPortfolioRoot(process.cwd());
  if (walked) return walked;
  return process.cwd();
}

function readUserConfig(): Partial<PortfolioConfig> | undefined {
  try {
    if (!fs.existsSync(USER_CONFIG_PATH)) return undefined;
    const raw = fs.readFileSync(USER_CONFIG_PATH, "utf-8");
    const parsed = JSON.parse(raw) as Partial<PortfolioConfig>;
    return parsed;
  } catch {
    return undefined;
  }
}

function walkForPortfolioRoot(start: string): string | undefined {
  let current = path.resolve(start);
  // Walk up at most 6 levels to find a directory containing both
  // athena-site/ops/schemas and a sibling repo with ops/run-records.
  for (let i = 0; i < 6; i++) {
    const schemaDir = path.join(current, "athena-site", "ops", "schemas");
    if (fs.existsSync(schemaDir)) return current;
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return undefined;
}

function discoverProductRepos(portfolioRoot: string): string[] {
  try {
    const entries = fs.readdirSync(portfolioRoot, { withFileTypes: true });
    return entries
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name)
      .filter((name) => !name.startsWith("."))
      .filter((name) => {
        const opsRunRecords = path.join(portfolioRoot, name, "ops", "run-records");
        const opsEventLedger = path.join(portfolioRoot, name, "ops", "event-ledger");
        const decisionsDir = path.join(portfolioRoot, name, "decisions");
        return (
          fs.existsSync(opsRunRecords) ||
          fs.existsSync(opsEventLedger) ||
          fs.existsSync(decisionsDir)
        );
      });
  } catch {
    return [];
  }
}
