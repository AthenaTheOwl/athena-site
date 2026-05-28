// Filesystem walkers + parsers for the Athena MCP server.
//
// These are the read-only access layer. Each walker is defensive: missing
// directories return [], malformed files log to stderr and skip, and path
// resolution rejects traversal attempts (.. segments, absolute paths).

import * as fs from "node:fs";
import * as path from "node:path";
import * as readline from "node:readline";

const DEC_FRONTMATTER_BEGIN = /^---\s*$/;

export interface DecisionFrontmatter {
  id?: string;
  spec?: string;
  requirement?: string;
  date?: string;
  status?: string;
  reversible?: boolean;
  decision?: string;
  owner?: string;
}

export interface DecisionRecord {
  id: string;
  repo: string;
  prefix: string;
  status: string;
  owner_role: string | undefined;
  reversible: boolean | undefined;
  title: string;
  path: string;
  frontmatter: DecisionFrontmatter;
}

export interface RunRecord {
  id: string;
  repo: string;
  spec_id: string;
  agent_id: string;
  runtime: string;
  status: string;
  started_at: string;
  finished_at?: string;
  path: string;
}

export interface EventRecord {
  event_id: string;
  type: string;
  created_at: string;
  run_id?: string;
  spec_id?: string;
  artifact_id?: string;
  actor?: { kind: string; id: string };
  payload?: unknown;
  parent_event_id?: string;
  // For locating which file the event came from (useful for debugging).
  source_repo?: string;
  source_path?: string;
}

export function walkDecisions(
  portfolioRoot: string,
  productRepos: string[],
  filter?: { repo?: string; prefix?: string; status?: string },
): DecisionRecord[] {
  const repos = filter?.repo ? [filter.repo] : productRepos;
  const out: DecisionRecord[] = [];
  for (const repo of repos) {
    const decisionsDir = safeJoin(portfolioRoot, repo, "decisions");
    if (!decisionsDir || !fs.existsSync(decisionsDir)) continue;
    let entries: fs.Dirent[];
    try {
      entries = fs.readdirSync(decisionsDir, { withFileTypes: true });
    } catch (err) {
      logSkip(`readdir ${decisionsDir}`, err);
      continue;
    }
    for (const entry of entries) {
      if (!entry.isFile()) continue;
      if (!entry.name.startsWith("DEC-")) continue;
      if (!entry.name.endsWith(".md")) continue;
      const filePath = path.join(decisionsDir, entry.name);
      const parsed = parseDecisionFile(filePath, repo);
      if (!parsed) continue;
      if (filter?.prefix && parsed.prefix !== filter.prefix) continue;
      if (filter?.status && parsed.status !== filter.status) continue;
      out.push(parsed);
    }
  }
  out.sort((a, b) => a.id.localeCompare(b.id));
  return out;
}

export function readDecisionById(
  portfolioRoot: string,
  productRepos: string[],
  id: string,
): { record: DecisionRecord; body: string } | undefined {
  if (!isSafeId(id)) return undefined;
  for (const repo of productRepos) {
    const decisionsDir = safeJoin(portfolioRoot, repo, "decisions");
    if (!decisionsDir || !fs.existsSync(decisionsDir)) continue;
    let entries: fs.Dirent[];
    try {
      entries = fs.readdirSync(decisionsDir, { withFileTypes: true });
    } catch (err) {
      logSkip(`readdir ${decisionsDir}`, err);
      continue;
    }
    for (const entry of entries) {
      if (!entry.isFile()) continue;
      if (!entry.name.startsWith(`${id}`)) continue;
      if (!entry.name.endsWith(".md")) continue;
      const filePath = path.join(decisionsDir, entry.name);
      const parsed = parseDecisionFile(filePath, repo);
      if (!parsed) continue;
      const body = safeReadText(filePath);
      if (body === undefined) continue;
      return { record: parsed, body };
    }
  }
  return undefined;
}

export function listSchemas(schemaDir: string): {
  name: string;
  title: string;
  description: string;
  path: string;
}[] {
  if (!fs.existsSync(schemaDir)) return [];
  let entries: fs.Dirent[];
  try {
    entries = fs.readdirSync(schemaDir, { withFileTypes: true });
  } catch (err) {
    logSkip(`readdir ${schemaDir}`, err);
    return [];
  }
  const out = [];
  for (const entry of entries) {
    if (!entry.isFile()) continue;
    if (!entry.name.endsWith(".schema.json")) continue;
    const filePath = path.join(schemaDir, entry.name);
    const raw = safeReadJson(filePath);
    if (!raw || typeof raw !== "object") continue;
    const name = entry.name.replace(/\.schema\.json$/, "");
    out.push({
      name,
      title: (raw as { title?: string }).title ?? name,
      description: (raw as { description?: string }).description ?? "",
      path: filePath,
    });
  }
  out.sort((a, b) => a.name.localeCompare(b.name));
  return out;
}

export function readSchemaByName(
  schemaDir: string,
  name: string,
): { name: string; path: string; schema: unknown } | undefined {
  if (!isSafeId(name)) return undefined;
  const filePath = path.join(schemaDir, `${name}.schema.json`);
  if (!filePath.startsWith(path.resolve(schemaDir))) return undefined;
  if (!fs.existsSync(filePath)) return undefined;
  const schema = safeReadJson(filePath);
  if (!schema) return undefined;
  return { name, path: filePath, schema };
}

export function walkRuns(
  portfolioRoot: string,
  productRepos: string[],
  filter?: { repo?: string; limit?: number; since?: string },
): RunRecord[] {
  const repos = filter?.repo ? [filter.repo] : productRepos;
  const limit = filter?.limit ?? 50;
  const sinceMs = filter?.since ? Date.parse(filter.since) : Number.NEGATIVE_INFINITY;
  const out: RunRecord[] = [];
  for (const repo of repos) {
    const runDir = safeJoin(portfolioRoot, repo, "ops", "run-records");
    if (!runDir || !fs.existsSync(runDir)) continue;
    let entries: fs.Dirent[];
    try {
      entries = fs.readdirSync(runDir, { withFileTypes: true });
    } catch (err) {
      logSkip(`readdir ${runDir}`, err);
      continue;
    }
    for (const entry of entries) {
      if (!entry.isFile()) continue;
      if (!entry.name.startsWith("run-")) continue;
      if (!entry.name.endsWith(".json")) continue;
      const filePath = path.join(runDir, entry.name);
      const raw = safeReadJson(filePath) as Record<string, unknown> | undefined;
      if (!raw) continue;
      const startedAt = typeof raw.started_at === "string" ? raw.started_at : "";
      if (startedAt && !Number.isNaN(sinceMs) && Number.isFinite(sinceMs)) {
        const ts = Date.parse(startedAt);
        if (!Number.isNaN(ts) && ts < sinceMs) continue;
      }
      out.push({
        id: stringOr(raw.id, entry.name.replace(/\.json$/, "")),
        repo,
        spec_id: stringOr(raw.spec_id, ""),
        agent_id: stringOr(raw.agent_id, ""),
        runtime: stringOr(raw.runtime, ""),
        status: stringOr(raw.status, ""),
        started_at: startedAt,
        finished_at:
          typeof raw.finished_at === "string" ? raw.finished_at : undefined,
        path: filePath,
      });
    }
  }
  // Most recent first.
  out.sort((a, b) => b.started_at.localeCompare(a.started_at));
  return out.slice(0, limit);
}

export function readRunById(
  portfolioRoot: string,
  productRepos: string[],
  id: string,
): { record: RunRecord; full: unknown } | undefined {
  if (!isSafeId(id)) return undefined;
  for (const repo of productRepos) {
    const runDir = safeJoin(portfolioRoot, repo, "ops", "run-records");
    if (!runDir) continue;
    const filePath = path.join(runDir, `${id}.json`);
    if (!filePath.startsWith(path.resolve(runDir))) continue;
    if (!fs.existsSync(filePath)) continue;
    const raw = safeReadJson(filePath) as Record<string, unknown> | undefined;
    if (!raw) continue;
    const record: RunRecord = {
      id: stringOr(raw.id, id),
      repo,
      spec_id: stringOr(raw.spec_id, ""),
      agent_id: stringOr(raw.agent_id, ""),
      runtime: stringOr(raw.runtime, ""),
      status: stringOr(raw.status, ""),
      started_at: stringOr(raw.started_at, ""),
      finished_at:
        typeof raw.finished_at === "string" ? raw.finished_at : undefined,
      path: filePath,
    };
    return { record, full: raw };
  }
  return undefined;
}

export async function queryEvents(
  portfolioRoot: string,
  productRepos: string[],
  filter: {
    run_id?: string;
    type?: string;
    since?: string;
    until?: string;
    limit?: number;
  },
): Promise<EventRecord[]> {
  const limit = filter.limit ?? 100;
  const sinceMs = filter.since ? Date.parse(filter.since) : Number.NEGATIVE_INFINITY;
  const untilMs = filter.until ? Date.parse(filter.until) : Number.POSITIVE_INFINITY;
  const out: EventRecord[] = [];
  for (const repo of productRepos) {
    const ledgerDir = safeJoin(portfolioRoot, repo, "ops", "event-ledger");
    if (!ledgerDir || !fs.existsSync(ledgerDir)) continue;
    let entries: fs.Dirent[];
    try {
      entries = fs.readdirSync(ledgerDir, { withFileTypes: true });
    } catch (err) {
      logSkip(`readdir ${ledgerDir}`, err);
      continue;
    }
    for (const entry of entries) {
      if (!entry.isFile()) continue;
      if (!entry.name.endsWith(".jsonl")) continue;
      // Cheap filter: if run_id filter is set and file name encodes a run id, skip mismatches.
      if (filter.run_id) {
        const base = entry.name.replace(/\.jsonl$/, "");
        if (base.startsWith("run-") && base !== filter.run_id) continue;
      }
      const filePath = path.join(ledgerDir, entry.name);
      const events = await readJsonlFile(filePath);
      for (const event of events) {
        if (filter.run_id && event.run_id !== filter.run_id) continue;
        if (filter.type && !eventTypeMatches(event.type, filter.type)) continue;
        const ts = Date.parse(event.created_at ?? "");
        if (!Number.isNaN(ts)) {
          if (ts < sinceMs) continue;
          if (ts > untilMs) continue;
        }
        event.source_repo = repo;
        event.source_path = filePath;
        out.push(event);
        if (out.length >= limit * productRepos.length * 4) break;
      }
      if (out.length >= limit * productRepos.length * 4) break;
    }
  }
  out.sort((a, b) => (a.created_at ?? "").localeCompare(b.created_at ?? ""));
  return out.slice(0, limit);
}

async function readJsonlFile(filePath: string): Promise<EventRecord[]> {
  const out: EventRecord[] = [];
  let stream: fs.ReadStream;
  try {
    stream = fs.createReadStream(filePath, { encoding: "utf-8" });
  } catch (err) {
    logSkip(`open ${filePath}`, err);
    return out;
  }
  const rl = readline.createInterface({ input: stream, crlfDelay: Infinity });
  let lineNumber = 0;
  for await (const line of rl) {
    lineNumber += 1;
    const trimmed = line.trim();
    if (!trimmed) continue;
    try {
      const parsed = JSON.parse(trimmed) as EventRecord;
      out.push(parsed);
    } catch (err) {
      logSkip(`parse ${filePath}:${lineNumber}`, err);
      continue;
    }
  }
  return out;
}

function parseDecisionFile(
  filePath: string,
  repo: string,
): DecisionRecord | undefined {
  const text = safeReadText(filePath);
  if (text === undefined) return undefined;
  const lines = text.split(/\r?\n/);
  if (!DEC_FRONTMATTER_BEGIN.test(lines[0] ?? "")) {
    return undefined;
  }
  // Collect frontmatter until next ---
  let end = -1;
  for (let i = 1; i < lines.length; i++) {
    if (DEC_FRONTMATTER_BEGIN.test(lines[i] ?? "")) {
      end = i;
      break;
    }
  }
  if (end === -1) return undefined;
  const frontmatter = parseYamlFrontmatter(lines.slice(1, end));
  const id = frontmatter.id ?? path.basename(filePath, ".md");
  const prefix = extractPrefix(id);
  const status = frontmatter.status ?? "unknown";
  const title = deriveTitle(id, lines.slice(end + 1));
  return {
    id,
    repo,
    prefix,
    status,
    owner_role: frontmatter.owner,
    reversible: frontmatter.reversible,
    title,
    path: filePath,
    frontmatter,
  };
}

function parseYamlFrontmatter(lines: string[]): DecisionFrontmatter {
  // Minimal YAML reader limited to scalar key: value pairs and block-scalar
  // blocks (decision: |). Robust against the DEC files in this repo; not a
  // full YAML parser. Multi-line blocks (lines starting with whitespace
  // after a `|` indicator) are collected into the parent key.
  const out: Record<string, unknown> = {};
  let currentKey: string | undefined;
  let block: string[] = [];
  let blockIndent = 0;
  let inBlock = false;

  const commitBlock = () => {
    if (inBlock && currentKey) {
      out[currentKey] = block.join("\n").trim();
      block = [];
      inBlock = false;
    }
  };

  for (const raw of lines) {
    const line = raw.replace(/\t/g, "  ");
    if (inBlock) {
      if (line.trim() === "") {
        block.push("");
        continue;
      }
      const leading = line.length - line.trimStart().length;
      if (leading >= blockIndent && blockIndent > 0) {
        block.push(line.slice(blockIndent));
        continue;
      }
      commitBlock();
      // Fall through to handle this line as a new key.
    }
    const m = line.match(/^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)$/);
    if (!m) continue;
    const key = m[1] ?? "";
    const valueRaw = (m[2] ?? "").trim();
    if (valueRaw === "|" || valueRaw === ">" || valueRaw === "|-" || valueRaw === ">-") {
      currentKey = key;
      inBlock = true;
      block = [];
      // Indent is one more than the key's column. We use 2 as a sensible default.
      blockIndent = 2;
      continue;
    }
    currentKey = key;
    out[key] = coerceScalar(valueRaw);
  }
  commitBlock();
  return out as DecisionFrontmatter;
}

function coerceScalar(raw: string): unknown {
  if (raw === "") return "";
  if (raw === "true") return true;
  if (raw === "false") return false;
  if (/^-?\d+$/.test(raw)) return Number(raw);
  if (raw.startsWith("\"") && raw.endsWith("\"")) return raw.slice(1, -1);
  if (raw.startsWith("'") && raw.endsWith("'")) return raw.slice(1, -1);
  return raw;
}

function extractPrefix(id: string): string {
  // DEC-CDCP-011-foo -> CDCP. DEC-MCPSEC-006-bar -> MCPSEC.
  const m = id.match(/^DEC-([A-Z]+)-/);
  return m?.[1] ?? "";
}

function deriveTitle(id: string, bodyLines: string[]): string {
  // Title = id minus the DEC-PREFIX-NNN-, transformed back to spaces. Fall
  // back to the first non-empty body line if a heading exists.
  for (const line of bodyLines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("# ")) return trimmed.slice(2).trim();
  }
  const m = id.match(/^DEC-[A-Z]+-\d+-(.*)$/);
  if (m && m[1]) return m[1].replace(/-/g, " ");
  return id;
}

function safeReadText(p: string): string | undefined {
  try {
    return fs.readFileSync(p, "utf-8");
  } catch (err) {
    logSkip(`read ${p}`, err);
    return undefined;
  }
}

function safeReadJson(p: string): unknown {
  const text = safeReadText(p);
  if (text === undefined) return undefined;
  try {
    return JSON.parse(text);
  } catch (err) {
    logSkip(`parse ${p}`, err);
    return undefined;
  }
}

function safeJoin(root: string, ...parts: string[]): string | undefined {
  const candidate = path.resolve(root, ...parts);
  if (!candidate.startsWith(path.resolve(root))) return undefined;
  return candidate;
}

function isSafeId(value: string): boolean {
  // No path separators, no .. segments, no NULs.
  if (!value) return false;
  if (value.includes("\0")) return false;
  if (value.includes("/") || value.includes("\\")) return false;
  if (value === "." || value === "..") return false;
  if (!/^[A-Za-z0-9_.-]+$/.test(value)) return false;
  return true;
}

function stringOr(value: unknown, fallback: string): string {
  return typeof value === "string" ? value : fallback;
}

function eventTypeMatches(type: string | undefined, filter: string): boolean {
  if (!type) return false;
  if (type === filter) return true;
  // Dotted-namespace prefix match: "gate" matches "gate.check.passed".
  return type.startsWith(`${filter}.`);
}

function logSkip(label: string, err: unknown): void {
  const msg = err instanceof Error ? err.message : String(err);
  process.stderr.write(`[athena-mcp-server] skip: ${label}: ${msg}\n`);
}
