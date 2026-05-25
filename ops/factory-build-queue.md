# Factory build queue

Generated after the May 25 repo-by-repo scan. This is the working
queue for the software dev factory: each item names the repo, the
product move, and requirement-shaped acceptance criteria before any
implementation starts.

## Ranking rule

Work ranks higher when it makes the factory more inspectable, safer to
extend, or better at learning from failures. Domain depth matters when
the feature compounds an existing deployed app.

External signals behind the queue:

- Gartner's 2026 agentic AI coverage names governance, security, cost,
  and the agent development life cycle as adoption pressure points.
- MCP security guidance names consent, scope minimization, SSRF,
  token-passthrough, and local server compromise as concrete risks.
- SEC EDGAR's access guidance makes a declared user agent and bounded
  request behavior non-negotiable for live filing refresh.
- Recent AI software supply-chain research centers verifiability,
  versioning, observability, and traceability.

## Wave 0: parity and deploy hygiene

### ai-supply-chain-copilot-prd: CI workflow for markdown gates

Status: markdown-only PRD at `267fde5`; local scripts exist, CI does
not.

Requirements:

- R-PRD-CI-001: Run `python scripts/voice_lint.py` on every pull
  request and push.
- R-PRD-CI-002: Run `python scripts/check_no_bom.py` as a hard gate.
- R-PRD-CI-003: Keep the workflow dependency-free beyond Python and
  repository files.

First because it is a small parity gap and the repo is now an active
door.

### athena-site: close Dependabot preview failures

Status: major Astro and Tailwind preview PRs failed because peer
dependencies require a coordinated migration.

Requirements:

- R-ATH-DEP-001: Ignore semver-major Dependabot updates for Astro,
  Astro integrations, Tailwind, and Tailwind typography.
- R-ATH-DEP-002: Keep minor and patch updates flowing.
- R-ATH-DEP-003: Close existing failing major-version PRs with a
  comment pointing to the deliberate migration policy.

## Wave 1: the trilogy gets deeper

### athena-site: Factory Control Tower Q&A

Status: `/factory` reads a checked-in snapshot and shows counts,
deploys, validators, and recent events.

Requirements:

- R-FACT-QA-001: Build a static search index from
  `src/data/factory-snapshot.json`, `ops/portfolio-manifest.yml`,
  decision files, and event logs.
- R-FACT-QA-002: Answer only with cited repo/file evidence; uncited
  answers render as "not enough evidence".
- R-FACT-QA-003: Add a fixture gate that fails if a canned question
  returns an uncited answer.
- R-FACT-QA-004: Keep the public page read-only; no credentials needed
  for the static version.

First among meta work because the control tower is already visible,
but not yet interrogable.

### mcp-security-lab: policy evaluator

Status: CLI scores MCP configs and emits JSON/Markdown reports.

Requirements:

- R-MCPSEC-POL-001: Evaluate `.agents/policies` or a policy YAML file
  against each MCP server finding.
- R-MCPSEC-POL-002: Emit `allow`, `deny`, or `human_approval_required`
  per server and per tool.
- R-MCPSEC-POL-003: Include fixtures for local shell, broad filesystem,
  remote unauthenticated, and read-only resource servers.
- R-MCPSEC-POL-004: Fail CI on net-new critical risk when a baseline is
  supplied.

First because MCP risk scoring should become enforceable policy, not a
static warning.

### trace-to-eval-harness: formal schemas

Status: CLI ingests failed traces and runs deterministic checks.

Requirements:

- R-TTE-SCHEMA-001: Publish JSON Schemas for trace, eval case, and run
  report shapes.
- R-TTE-SCHEMA-002: Add `trace-to-eval validate` for schemas and
  fixtures.
- R-TTE-SCHEMA-003: Version schemas and include positive/negative
  fixtures.
- R-TTE-SCHEMA-004: Keep deterministic checks as the first gate before
  any LLM judge integration.

First because the harness becomes reusable only when the trace and eval
contract is stable.

## Wave 2: supply-chain product depth

### supplier-risk-rag-agent: investor rollup

Status: citation-faithful RAG with monthly EDGAR refresh path.

Requirements:

- R-SR-ROLL-001: Accept a holdings input of ticker/CIK plus portfolio
  weight.
- R-SR-ROLL-002: Return cited risk cards for export controls, customer
  concentration, Taiwan exposure, AI capacity, and supplier capacity.
- R-SR-ROLL-003: Aggregate risk by portfolio weight while preserving
  filing citations.
- R-SR-ROLL-004: Add rollup eval cases for missing evidence and
  citation faithfulness.

First because EDGAR refresh and citation verification already exist.

### chip-supply-chain-map: investor watchlist export

Status: graph includes AI accelerator nodes, scenarios, history mode,
and node-level investor sensitivity.

Requirements:

- R-CM-WATCH-001: Let a reader create a watchlist of public-company
  nodes.
- R-CM-WATCH-002: Show scenario-level summary when no node is selected.
- R-CM-WATCH-003: Export a markdown risk packet with node, scenario,
  sensitivity band, and source ids.
- R-CM-WATCH-004: Keep static data sourced; no live market prices.

First because the last overlay is useful but still node-by-node.

### procurement-negotiation-lab: factory console

Status: simulator plus reusable mechanism SDK and factory subsystem.

Requirements:

- R-PN-FAC-001: Render factory tasks, artifacts, checkpoints, and gate
  states in a web view.
- R-PN-FAC-002: Link each task to replayable run reports.
- R-PN-FAC-003: Show human-approval checkpoints before any action that
  changes generated artifacts.
- R-PN-FAC-004: Keep the console read-only for the first version.

First because it makes the factory subsystem inspectable.

### ai-supply-chain-copilot-prd: runnable prototype

Status: markdown PRD with a build plan.

Requirements:

- R-PRD-APP-001: Add a Vercel prototype with a synthetic exception
  queue.
- R-PRD-APP-002: Generate cited action briefs from seeded evidence.
- R-PRD-APP-003: Require human approval before any supplier-facing
  action.
- R-PRD-APP-004: Add eval cases for unsafe recommendations and missing
  citations.

First app step when the portfolio needs a single end-to-end
supply-chain workflow.

## Wave 3: subscriber and operations surfaces

### ai-field-brief: subscriber ops cockpit

Status: feeds, subscription form, and Resend weekly digest cron exist.

Requirements:

- R-AFB-SUB-001: Show subscriber segment status, digest config state,
  and latest dry-run result.
- R-AFB-SUB-002: Log digest dry-runs, sends, provider errors, and
  skipped sends.
- R-AFB-SUB-003: Add a manual dry-run readiness endpoint with no send
  side effect.
- R-AFB-SUB-004: Keep credentials server-only.

Credential blockers: `RESEND_API_KEY`, `RESEND_SEGMENT_ID`,
`DIGEST_FROM_EMAIL`, `CRON_SECRET`.

### ai-field-brief: source ops queue

Requirements:

- R-AFB-SRC-001: Show registry freshness and connector failures.
- R-AFB-SRC-002: Promote captured items into brief candidates with
  source ids.
- R-AFB-SRC-003: Gate promotion on duplicate and source-quality checks.

### ai-field-brief: ask briefs

Requirements:

- R-AFB-QA-001: Retrieve only published briefs.
- R-AFB-QA-002: Cite exact week, section, and source id in every answer.
- R-AFB-QA-003: Refuse questions not grounded in the archive.

## Wave 4: Starforge workshop, only if the cluster becomes public-facing

### starforge-narrative-tools: cross-engine manifest

Requirements:

- R-SF-NT-001: Produce a source-hash manifest consumed by Twine and
  ChoiceScript demos.
- R-SF-NT-002: Validate downstream repos consume the same source hash.
- R-SF-NT-003: Scan file text for spoiler tokens, not just paths.
- R-SF-NT-004: Fail on bytecode/cache artifacts.

### starforge-twine-demo: publishable factory exhibit

Requirements:

- R-SF-TW-001: Build a CI artifact for the playable HTML.
- R-SF-TW-002: Store smoke screenshots.
- R-SF-TW-003: Add a release ledger.
- R-SF-TW-004: Show source prose to passage mapping.

### starforge-choicescript-demo: route coverage dashboard

Requirements:

- R-SF-CS-001: Emit branch coverage JSON.
- R-SF-CS-002: Gate minimum scene coverage.
- R-SF-CS-003: Diff generated scenes against committed source.

## Keep historical unless a specific story needs them

- `facility-location`: add scenario packs and screenshots only if it
  becomes part of the AI data-center/site-selection story.
- `semiconductor-wafer-robust-optimization`: add CI and an AI
  accelerator bottleneck planner only if it becomes the wafer-capacity
  companion to chip-map.
- `food-relief-fund`: keep solved; add CI smoke only before promoting.
- `robust-knapsack` and `server-load-optimizer`: keep drawer; do not
  publish while they contain textbook/PDF material.
- `starforge-renpy-demo` and `starforge-rpg-prototype`: keep workshop
  unless a public playable export becomes the goal.

## Current external blockers

- ai-field-brief Vercel env: `RESEND_API_KEY`, `RESEND_SEGMENT_ID`,
  `DIGEST_FROM_EMAIL`, `CRON_SECRET`.
- supplier-risk-rag-agent GitHub repo variable: `SEC_USER_AGENT`.
- Factory Q&A live refresh: optional GitHub token if the static index is
  not enough.
