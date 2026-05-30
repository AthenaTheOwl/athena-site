---
id: DEC-CDCP-021-sandbox-manifest-and-agent-runtime-adapter
spec: specs/0010-cognitive-delivery-control-plane/
requirement: R-CDCP-031..034
date: 2026-05-30
status: approved
reversible: true
decision: |
  The portfolio adds a `sandbox_manifest_ref` optional field to
  `ops/schemas/run.schema.json` and a new
  `ops/schemas/sandbox-manifest.schema.json` that names the manifest
  body shape (manifest_version, runtime_provider, model, adapter_ids,
  mounts, env_refs, tool_surface, determinism, created_at). Two new
  event types land in `ops/event-types.md`:
  `sandbox.manifest.recorded` (fired when a manifest is written for a
  run) and `runstate.checkpoint.persisted` (fired when a RunState
  snapshot is persisted at a pause point). Runtime adapters — starting
  with the procurement-lab Agents-SDK adapter scaffolded in Phase 3 —
  emit conformant manifests, persist RunState checkpoints, and emit
  the two new event types into the existing event ledger so the
  validator and replay paths keep working unchanged.
alternatives:
  - label: keep the existing checkpoint_ref + sandbox_image_ref pair and add nothing
    rejected_because: |
      `sandbox_image_ref` names a frozen image; `checkpoint_ref` names
      a serialized RunState. Neither field captures the workspace
      contract — which files were mounted, which env vars the adapter
      expected, which tools were on the surface at run start, and
      which model + adapter ids were loaded. A reviewer who wants to
      replay a run on a fresh LLM needs the workspace contract, not
      just the image hash or the runner state. The Agents SDK's
      Manifest concept is the right shape; landing it as a typed
      cross-runtime contract is the consistent move.
  - label: inline the manifest body inside the Run record under a sandbox object
    rejected_because: |
      Inlining the manifest body would bloat every Run record and
      couple the run schema to one runtime's workspace model. The
      ref-plus-sibling-schema pattern matches how `checkpoint_ref`
      and `sandbox_image_ref` already work, and matches how the event
      schema separates envelope from payload. A separate schema also
      lets non-Agents-SDK adapters (Anthropic, Claude Code, local
      stub) target the same contract without renegotiating the Run
      shape.
  - label: emit traces to a new ops/traces/ directory instead of reusing the event ledger
    rejected_because: |
      A second trace surface would fork the source of truth and
      defeat the single-ledger discipline the portfolio has built
      across six rounds. The existing event ledger already carries
      `tool.call.started` / `tool.call.completed` / `gate.check.*` and
      the validator + replay scripts read it. Adapter implementations
      wrap each SDK tool invocation and emit the same event types;
      manifest + checkpoint events join the ledger via the two new
      types defined here. One source of truth, one validator path.
  - label: require live OPENAI_API_KEY for any Agents-SDK adapter use
    rejected_because: |
      A hard live-mode requirement would bounce CI and any offline
      author from touching the adapter at all. The Phase 1 design
      already specifies a three-layer graceful degradation — package
      missing, package present without key (stub mode emits manifest
      + initial checkpoint), package and key present (live). Stub mode
      lets the artifact wiring run in CI and proves the contract
      before any paid call lands. A future amendment can tighten the
      contract once stub mode is the well-trodden path.
rationale: |
  The Codex analysis on 2026-05-30 identifies the missing
  runtime-adapter layer between the control plane and the data
  substrate. Today's Run + Event evidence captures WHAT ran but not
  the workspace state needed to resume or replay-with-fresh-LLM. The
  Agents SDK's Manifest + RunState concepts fill that gap when
  wrapped as the producer side; the schema is the durable contract
  that survives any single runtime.

  The split is deliberate. The Run record carries a ref, not a body.
  The manifest body lives in a sibling schema, so a future runtime
  adapter (Anthropic, Claude Code, local stub) targets the same
  contract without renegotiating the Run shape. The two event types
  ride the existing ledger and the existing validator so no second
  trace surface forks the source of truth.

  Phase 3 implementation lives in `procurement-negotiation-lab` under
  `src/procurement_lab/runtime/openai_agents_runtime.py`. Manifests
  land at `ops/sandbox-manifests/<run-id>.json`; checkpoints land at
  `ops/checkpoints/<run-id>.runstate.json`; trace events ride the
  existing `ops/event-ledger/<run-id>.jsonl`. The `--mode agents-sdk`
  flag on `scripts/factory/run.py` and `scripts/replay_run.py` gates
  the adapter path; the default dry-run/stub-worker path remains the
  committed evidence shape so existing tests stay green.
trade_off: |
  The schema-first approach lands the contract before any runtime
  adapter exists. That means the first 30 days produce a manifest
  schema without a production emitter — the procurement-lab adapter
  scaffolds in stub mode and only proves live-mode wiring once an
  OPENAI_API_KEY run lands. The risk is a schema field set that
  reads well on paper but discovers gaps once the adapter writes a
  real manifest. Mitigation: the Phase 1 verification cross-checks
  the Agents SDK source-of-truth (Agent, Runner, SandboxAgent,
  Manifest, SandboxRunConfig, RunState, client.deserialize_session_state)
  so the field set tracks the SDK's vocabulary. A follow-on
  amendment can widen or rename fields once the first live run
  exposes a gap. Reversibility is preserved by keeping
  `sandbox_manifest_ref` optional — no existing Run record is
  invalidated by the schema change.
evidence:
  - kind: doc
    ref: ops/schemas/run.schema.json
  - kind: doc
    ref: ops/schemas/sandbox-manifest.schema.json
  - kind: doc
    ref: ops/event-types.md
  - kind: decision
    ref: DEC-CDCP-011-run-records-carry-replay-equivalence-evidence.md
  - kind: decision
    ref: DEC-CDCP-013-event-schema-enforces-typed-payloads.md
  - kind: decision
    ref: DEC-CDCP-014-portable-repo-uri-scheme.md
coverage:
  - R-CDCP-031
  - R-CDCP-032
  - R-CDCP-033
  - R-CDCP-034
rollback: |
  Drop the `sandbox_manifest_ref` field from
  `ops/schemas/run.schema.json`. Delete
  `ops/schemas/sandbox-manifest.schema.json`. Remove the two new
  event-type entries (`sandbox.manifest.recorded`,
  `runstate.checkpoint.persisted`) from `ops/event-types.md`. Mark
  this DEC reversed. The procurement-lab adapter implementation (if
  landed by then) reverts in its own follow-on amendment within
  procurement-negotiation-lab. Existing Run records continue to
  validate because the new field is optional from day one; no
  artifact in the portfolio is invalidated by the rollback.
owner: governance.cdcp-curator
systems_map: |
  Three-layer separation made explicit — control-plane (DECs +
  schemas) declares the contract, runtime (Agents SDK adapter)
  executes against it, data-substrate (manifests + checkpoints +
  traces) preserves the workspace state for resume/replay. The
  schema is the cross-runtime boundary; the adapter is the per-repo
  producer; the event ledger is the single audit trail consumers
  read.
transferable_principle: |
  Any agent runtime adapter (Anthropic, Claude Code, local stub,
  Agents SDK) should emit a conformant Sandbox Manifest + checkpoint
  + trace triad. The schema is the cross-runtime contract; the
  adapter is the per-runtime producer. This generalizes to any
  multi-runtime portfolio where the same Run + Event vocabulary
  must hold across vendors.
falsification_test: |
  If a captured manifest + checkpoint pair cannot rehydrate a run
  and reach byte-equivalent (deterministic) or hash-equivalent
  (equivalence) state, the contract is falsified for that runtime.
  A weaker but earlier signal: if the first live procurement-lab
  Agents-SDK run produces a manifest that the schema fails to
  validate, the field set is wrong and the DEC needs an amendment
  before any second adapter targets it.
adoption_ladder:
  minimum_viable: |
    Schemas amended; procurement-lab adapter scaffolded in stub
    mode (no OPENAI_API_KEY required); manifest + initial
    checkpoint artifact wiring proven offline and in CI.
  mid_adoption: |
    Live procurement-lab adapter run with OPENAI_API_KEY produces a
    conformant manifest + checkpoint + trace triad; replay_run.py
    --mode agents-sdk rehydrates and verifies; second adapter
    (Anthropic or Claude Code) targets the same schema.
  full_adoption: |
    All product repos with agent-runtime workloads (procurement,
    supplier-risk if it gains long-running runs, others) ship
    runtime adapters; chaos suite mutation classes cover manifest
    and checkpoint tampering; the schema is referenced from
    onboarding docs and from each repo's AGENTS.md.
  monitoring_signals:
    - "% of Run records carrying sandbox_manifest_ref + checkpoint_ref"
    - "replay --mode agents-sdk pass rate across runs"
    - "manifest schema drift over time (additions, deprecations)"
    - "count of distinct runtime_provider values in committed manifests"
---

## decision

The portfolio adds a `sandbox_manifest_ref` optional field to
`ops/schemas/run.schema.json`, lands a new
`ops/schemas/sandbox-manifest.schema.json` that names the manifest
body shape, and adds two new event types
(`sandbox.manifest.recorded`, `runstate.checkpoint.persisted`) to
`ops/event-types.md`. Runtime adapters — starting with the
procurement-lab Agents-SDK adapter scaffolded in Phase 3 — emit
conformant manifests, persist RunState checkpoints, and emit the two
new event types into the existing event ledger.

## why

Codex's 2026-05-30 analysis identifies the missing runtime-adapter
layer between the control plane and the data substrate. Today's Run
and Event evidence captures WHAT ran but not the workspace state
needed to resume a run or replay it on a fresh LLM. The Agents SDK
Manifest and RunState concepts fill that gap when wrapped as the
producer side; the schema is the durable contract that survives any
single runtime.

The Run record carries a ref, not the manifest body. The body lives
in a sibling schema, so a future runtime adapter (Anthropic, Claude
Code, local stub) targets the same contract without renegotiating
the Run shape. The two new event types ride the existing ledger and
the existing validator path, so no second trace surface forks the
source of truth.

## alternatives

- Keep the existing `checkpoint_ref` + `sandbox_image_ref` pair and
  add nothing. Rejected: neither field captures the workspace
  contract (mounts, env_refs, tool_surface, model + adapter ids) a
  reviewer needs to replay on a fresh LLM.
- Inline the manifest body inside the Run record under a sandbox
  object. Rejected: would bloat Run records and couple the run
  schema to one runtime's workspace model.
- Emit traces to a new `ops/traces/` directory instead of reusing
  the event ledger. Rejected: forks the single source of truth.
- Require live `OPENAI_API_KEY` for any Agents-SDK adapter use.
  Rejected: bounces CI and offline authors; stub-mode degradation
  is the well-trodden path the Phase 1 design already specifies.

## the new schema shape

`sandbox-manifest.schema.json` requires five fields:
`manifest_version` (SemVer), `runtime_provider` (e.g.
`openai-agents-sdk`), `model` (vendor:name:version), `mounts` (array
of `{src, dst, mode}`), and `tool_surface` (array of
`{tool_name, schema_hash}`). Optional fields are `adapter_ids`,
`env_refs` (names only, values not inlined), `determinism` (seed,
temperature, top_p), and `created_at` (ISO 8601). The Run record
gains one optional field, `sandbox_manifest_ref`, alongside the
existing `checkpoint_ref` and `sandbox_image_ref`.

## the new event types

`sandbox.manifest.recorded` fires when a runtime adapter writes a
manifest for a run. Payload: `{run_id, manifest_ref}`. Typical actor:
`{kind: "system", id: "<runtime-adapter-id>"}`.

`runstate.checkpoint.persisted` fires when a runtime adapter persists
a RunState snapshot at a named pause point. Payload:
`{run_id, checkpoint_ref, step_label}`. Step labels for the
procurement-lab factory are `plan_review`, `diff_review`, `pre_pr`;
other adapters MAY use their own labels.

Per `DEC-CDCP-013`, these two new types pass envelope-only validation
on the event schema during the bootstrap window. A future amendment
adds them to the `oneOf` discriminator block once two adapters have
emitted real instances.

## coverage

R-CDCP-031 schemas/run.schema.json carries the new
`sandbox_manifest_ref` optional field, R-CDCP-032
schemas/sandbox-manifest.schema.json names the manifest body shape,
R-CDCP-033 event-types.md documents the two new event types,
R-CDCP-034 DEC-CDCP-021 records the contract with all four
systems-thinking fields populated.

## rollback

Drop the `sandbox_manifest_ref` field from
`ops/schemas/run.schema.json`. Delete
`ops/schemas/sandbox-manifest.schema.json`. Remove the two new
event-type entries from `ops/event-types.md`. Mark this DEC reversed.
The procurement-lab adapter implementation (if landed by then)
reverts in its own follow-on amendment within
procurement-negotiation-lab. Existing Run records continue to
validate because the new field is optional from day one.
