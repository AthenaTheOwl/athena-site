---
id: DEC-CDCP-013-event-schema-enforces-typed-payloads
spec: specs/0010-cognitive-delivery-control-plane/
requirement: R-CDCP-013
date: 2026-05-28
status: approved
reversible: true
decision: |
  ops/schemas/event.schema.json enforces typed payload schemas for nine
  canonical event types via a top-level oneOf discriminator on the type
  field: pipeline.start, pipeline.complete, pipeline.done,
  tool.call.started, tool.call.completed, gate.check.passed,
  gate.check.failed, gate.run.evidence_recorded, and
  run.evidence.replayed. A tenth escape-hatch branch passes envelope
  validation for any event type outside that set, preserving the v1
  contract that the ledger absorbs new event types without a schema
  bump. The schemas-cache copy in every product repo is refreshed
  byte-for-byte in the same round so validators across the portfolio
  see the same contract.
alternatives:
  - label: keep payload as an unconstrained type=object (v1 status quo)
    rejected_because: |
      Codex's independent review of v2 Round 1 confirmed the gap: a
      reviewer cannot verify that a pipeline.start event actually
      carries the prompt_snapshot_hash it claims to, because the
      schema does not constrain the inner shape. That breaks the
      engineering-grade-trust thesis behind DEC-CDCP-011. Typed
      payloads close the gap at the schema boundary, where every
      validator across the portfolio reads the same rules.
  - label: type every conceivable event payload, not just the canonical nine
    rejected_because: |
      Most event types in ops/event-types.md (signal.received,
      spec.created, agent.run.*, artifact.produced, proof.gate.*,
      decision.*, release.*, dream.*, memory.*, skill.*) are not yet
      on the engineering-grade-trust critical path. Typing them now
      would inflate the schema, slow down legitimate emitter
      evolution, and produce churn without buying replay-equivalence
      coverage. The nine typed types are the ones that show up in
      run-evidence audit trails; the rest can graduate later by
      adding branches.
  - label: gate the payload with a discriminator without an escape hatch
    rejected_because: |
      A strict oneOf with no escape-hatch branch turns every
      previously-validating event type (signal.received,
      agent.run.started, artifact.produced, decision.recorded, etc.)
      into a schema violation overnight. That contradicts the v1
      contract ("the ledger can absorb new event types without a
      schema bump") and would break every existing validator in the
      portfolio. The escape-hatch branch is the explicit trade-off:
      the nine typed types get enforcement; everything else keeps
      envelope-only validation.
rationale: |
  Codex's independent review of Round 1 named the gap precisely:
  event.schema.json currently only validates the envelope, not
  payloads. The maintainer's engineering-grade standard is that a
  third party should be able to verify what ran from the source-of-
  truth records alone. Without payload typing, that standard fails on
  three load-bearing checks:

  - Replay-equivalence verification reads pipeline.start payloads for
    prompt_snapshot_hash and tool_schemas_snapshot_hash. If the schema
    does not require those fields on pipeline.start, a malformed
    pipeline.start that omits the hashes still validates, and a
    downstream reviewer cannot tell whether the omission was the
    runtime's bug or expected.

  - Gate outcome reconstruction reads gate.check.* payloads for
    gate_name and reason. Without typing, two emitters might use
    gate_name versus check_name (or skip the reason on a failure),
    and the schema cannot catch it.

  - Run-evidence packet generation reads gate.run.evidence_recorded
    payloads for run_id and fields_populated (with the enum of valid
    field names). Without typing, fields_populated could carry any
    string, and the packet generator's enum check becomes the only
    enforcement — which is too late, because the event already
    landed in the ledger.

  Typed payloads via a oneOf discriminator on type close the gap at
  the schema boundary. Every validator that reads
  event.schema.json — from product-repo validate_run_evidence.py to
  the athena-site MCP server's events_query tool — enforces the same
  payload contract. The escape-hatch branch keeps the v1 absorb-new-
  types contract intact for everything outside the canonical nine.

  The nine typed types are the ones already in production ledgers
  across procurement-negotiation-lab, supplier-risk-rag-agent,
  ai-field-brief, and chip-supply-chain-map. Typing them now matches
  enforcement to where evidence already exists. Round 3 will land
  cross-checks in each repo's validate_run_evidence.py
  (Run.prompt_snapshot_hash == pipeline.start.payload.prompt_snapshot_hash,
  Run.gate_results_summary derived from gate.check.* events, etc.).
  Round 4 upgrades the trace-to-eval-harness packet schema to
  preserve producer identity through the review boundary.
evidence:
  - kind: schema
    ref: ops/schemas/event.schema.json
  - kind: doc
    ref: ops/event-types.md
  - kind: decision
    ref: DEC-CDCP-011-run-records-carry-replay-equivalence-evidence.md
  - kind: trace
    ref: ../procurement-negotiation-lab/ops/event-ledger/run-cb524eb06115.jsonl
  - kind: trace
    ref: ../supplier-risk-rag-agent/ops/event-ledger/run-13f2a48fe8bc.jsonl
  - kind: trace
    ref: ../ai-field-brief/ops/event-ledger/run-27338e664be4.jsonl
  - kind: trace
    ref: ../chip-supply-chain-map/ops/event-ledger/run-efeb29900de3.jsonl
rollback: |
  Remove the oneOf block, the $defs block, and the typed branches from
  ops/schemas/event.schema.json; revert the top-level description and
  the payload property description to their v1 wording. Refresh
  ops/schemas-cache/event.schema.json in each product repo. Existing
  events that fail the typed branches will validate again under the
  envelope-only contract. The doc changes in ops/event-types.md
  (added entries for pipeline.start, pipeline.complete, pipeline.done,
  gate.check.passed, gate.check.failed; tool.call.* migration notes)
  can stay as documentation even if the schema relaxes; they describe
  the contract emitters should still aim for.
owner: editorial
---

## decision

`ops/schemas/event.schema.json` enforces typed payload schemas for
nine canonical event types via a top-level `oneOf` discriminator on
the `type` field: `pipeline.start`, `pipeline.complete`,
`pipeline.done`, `tool.call.started`, `tool.call.completed`,
`gate.check.passed`, `gate.check.failed`, `gate.run.evidence_recorded`,
and `run.evidence.replayed`. A tenth escape-hatch branch passes
envelope validation for any event whose `type` is outside the
canonical nine, preserving the v1 contract that the ledger absorbs
new event types without a schema bump. The schemas-cache copy in
every product repo is refreshed in the same round.

## alternatives

- Keep `payload` unconstrained. Codex's review confirmed the gap;
  envelope-only validation breaks engineering-grade trust.
- Type every conceivable event payload. Inflates the schema without
  buying replay-equivalence coverage; the nine typed types are the
  ones on the critical path.
- Strict `oneOf` with no escape hatch. Breaks every previously-
  validating non-canonical event type and contradicts the v1
  absorb-new-types contract.

## rationale

The thesis: a reviewer should verify replay equivalence, gate
outcomes, and run-evidence completeness from the source-of-truth
records alone. Without typed payloads, the schema does not catch:

- `pipeline.start` events that omit `prompt_snapshot_hash` or
  `tool_schemas_snapshot_hash`.
- `gate.check.failed` events that omit `reason`.
- `gate.run.evidence_recorded` events whose `fields_populated`
  carries strings outside the enum.

Each gap forces a downstream consumer to repeat the validation that
should live at the schema boundary. Typed payloads via `oneOf` push
the contract to where every validator already reads. The escape-
hatch branch keeps the absorb-new-types contract intact for
everything outside the canonical nine.

## trade-off

The `oneOf` block adds schema complexity. The escape-hatch tenth
branch is the explicit trade-off: only the canonical nine types
get typed enforcement now; every other event type retains the v1
envelope-only contract. Future passes can add typed branches (or
relax the existing ones) as the portfolio's emitter discipline
matures.

## relationship to DEC-CDCP-011

`DEC-CDCP-011` added the six replay-equivalence fields to
`run.schema.json` so source-of-truth Run records carry the evidence
a reviewer needs. This DEC closes the matching event-side gap: now
the events that carry those fields into the ledger are themselves
typed. The two DECs together let a reviewer answer
"is this run replay-equivalent to that one" from the Run record plus
its event ledger with no manual re-walks.

## audit findings

Running the new schema against existing production ledgers surfaced
eleven non-conformant events across the four product repos with
ledgers — the audit is the round's evidence that the gap was real:

- `ai-field-brief`: three `pipeline.complete` events that use
  `outcome` instead of `status`.
- `procurement-negotiation-lab`: one `tool.call.started`, one
  `tool.call.completed`, and one `pipeline.done` event that use
  `tool_id` for tool name and omit `status` from `pipeline.done`.
- `supplier-risk-rag-agent`: one `tool.call.completed` using
  `tool_id` and one `gate.run.evidence_recorded` whose payload
  omits the required `run_id`.
- `chip-supply-chain-map`: two `tool.call.completed` events using
  `tool_id` and one `gate.run.evidence_recorded` using
  `populated_fields` instead of `fields_populated`.

The events are left in place on purpose. Round 3 lands the emitter
fixes; this round records the contract and surfaces the gaps.

## follow-on

- Round 3 adds cross-checks in each repo's
  `validate_run_evidence.py` (Run.prompt_snapshot_hash ==
  pipeline.start.payload.prompt_snapshot_hash,
  Run.gate_results_summary derivable from gate.check.* events) and
  fixes the eleven non-conformant events surfaced by this round's
  audit.
- Round 4 upgrades the trace-to-eval-harness packet schema to
  preserve producer identity through the review boundary.
- A future DEC may graduate additional event types
  (`signal.received`, `agent.run.*`, `artifact.produced`,
  `proof.gate.*`, `decision.*`, `release.*`, `dream.*`,
  `memory.*`, `skill.*`) into the typed set as portfolio-wide
  emitter coverage matures.

## rollback

Remove the `oneOf` block, the `$defs` block, and the typed branches
from `ops/schemas/event.schema.json`; revert the top-level
description and the `payload` property description to their v1
wording. Refresh `ops/schemas-cache/event.schema.json` in each
product repo. Existing events that fail the typed branches will
validate again under the envelope-only contract. The doc changes in
`ops/event-types.md` (added entries for `pipeline.start`,
`pipeline.complete`, `pipeline.done`, `gate.check.passed`,
`gate.check.failed`; `tool.call.*` migration notes) can stay as
documentation even if the schema relaxes; they describe the contract
emitters should still aim for.
