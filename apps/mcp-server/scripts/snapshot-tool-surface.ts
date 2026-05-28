#!/usr/bin/env node
// Generate a snapshot of the MCP server's tool surface.
//
// What "snapshot" means: for every tool the server registers, record the
// tool's name, description, and a SHA-256 hash of its canonical (sorted-keys,
// no-whitespace) input schema. The result lands at
// apps/mcp-server/tool-surface.snapshot.json and is the contract the
// mcp-security-lab gate enforces.
//
// Determinism: tools are sorted by name; the canonical-JSON encoder sorts
// object keys at every level. Running this script twice in a row with no
// source changes MUST produce byte-identical output.

import { createHash } from "node:crypto";
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

import { SERVER_VERSION, TOOL_DEFINITIONS } from "../src/server.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const OUTPUT_PATH = path.resolve(__dirname, "..", "tool-surface.snapshot.json");

function canonicalJson(value: unknown): string {
  if (value === null || typeof value !== "object") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((v) => canonicalJson(v)).join(",")}]`;
  }
  const obj = value as Record<string, unknown>;
  const keys = Object.keys(obj).sort();
  const parts = keys.map((k) => `${JSON.stringify(k)}:${canonicalJson(obj[k])}`);
  return `{${parts.join(",")}}`;
}

function sha256Hex(input: string): string {
  return createHash("sha256").update(input, "utf-8").digest("hex");
}

interface ToolSurfaceEntry {
  name: string;
  description: string;
  input_schema_hash: string;
}

export interface ToolSurfaceSnapshot {
  version: string;
  tools: ToolSurfaceEntry[];
}

export function buildSnapshot(): ToolSurfaceSnapshot {
  const tools: ToolSurfaceEntry[] = TOOL_DEFINITIONS.map((tool) => ({
    name: tool.name,
    description: tool.description,
    input_schema_hash: sha256Hex(canonicalJson(tool.inputSchema)),
  })).sort((a, b) => a.name.localeCompare(b.name));
  return { version: SERVER_VERSION, tools };
}

export function serializeSnapshot(snapshot: ToolSurfaceSnapshot): string {
  // Pretty-print with 2-space indent and a trailing newline so the file is
  // diff-friendly and matches the rest of the repo's JSON conventions.
  return `${JSON.stringify(snapshot, null, 2)}\n`;
}

function main(): void {
  const snapshot = buildSnapshot();
  const serialized = serializeSnapshot(snapshot);
  fs.writeFileSync(OUTPUT_PATH, serialized, { encoding: "utf-8" });
  process.stdout.write(
    `snapshot-tool-surface: wrote ${snapshot.tools.length} tools to ${OUTPUT_PATH}\n`,
  );
}

const invokedDirectly = process.argv[1]
  ? path.resolve(process.argv[1]) === __filename
  : false;
if (invokedDirectly) {
  main();
}
