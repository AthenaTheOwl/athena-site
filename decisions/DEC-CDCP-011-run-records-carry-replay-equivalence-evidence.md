---
id: DEC-CDCP-011-run-records-carry-replay-equivalence-evidence
spec: specs/0010-cognitive-delivery-control-plane/
requirement: R-CDCP-011
date: 2026-05-27
status: approved
reversible: true
decision: |
  Run records SHOULD carry replay-equivalence evidence —
  prompt_snapshot_hash, tool_schemas_snapshot_hash, determinism,
  checkpoint_ref, sandbox_image_ref, gate_results_summary — populated
  where the runtime can derive them at run completion. All six fields
  land as optional properties on athena-site/ops/schemas/run.schema.json
  so existing runs validate unchanged and future runs gain replay
  evidence as runtimes learn to emit it.
alternatives:
  - label: keep run.schema.json minimal and put hashes in events[]
    rejected_because: |
      Hashes describe the run's preconditions, not a moment inside it.
      Burying them in the event timeline forces every reader to scan
      events to answer "were these two runs the same?" — which is a
      Run-level question. The fields belong at the Run root next to
      spec_id and agent_id.
  - label: require all six fields on every Run
    rejected_because: |
      Existing runtimes do not yet emit canonicalized prompt hashes or
      gate rollups. Making the fields required would break every Run
      record already written. Optional fields let the schema lead and
      runtimes catch up; a future DEC can promote any of them to
      required once portfolio-wide coverage is in place.
  - label: define the fields only in the trace-to-eval-harness packet schema
    rejected_because: |
      The packet schema is a review-time projection. If the source-of-
      truth Run record does not carry the underlying fields, the packet
      generator has nothing to read. The fields must live where the
      runtime can populate them as the run completes; the packet then
      derives from the Run plus its events and artifacts.
rationale: |
  The thesis: run evidence is the bridge between agents and
  engineering-grade trust. Without prompt and tool-schema hashes, two
  runs against the "same" prompt are not provably the same — and a
  reviewer cannot validate that a Run + Events + Artifacts bundle is
  genuinely replay-equivalent. Without a gate rollup at the Run root,
  the question "did this run pass its gates?" requires scanning every
  event of kind gate_check. Without checkpoint and sandbox refs,
  resuming a failed run or reproducing its environment is a manual
  archaeological dig.

  The six fields together let a reviewer answer four questions from a
  single Run record: were the prompt preconditions identical (hash
  match), was the tool surface identical (hash match), was the run
  pinned for determinism (knob presence), did the run pass its gates
  (rollup), and can the run be resumed or reproduced (refs). All four
  questions are load-bearing for engineering-grade trust; none are
  reliably answerable without the fields.

  The fields are SHOULD, not MUST, because the runtime emitters that
  populate them roll out in phases. Phase B lands emitters in
  procurement-negotiation-lab; phase D rolls the pattern across
  ai-field-brief, supplier-risk-rag-agent, chip-supply-chain-map.
  Until each runtime emits, the field is absent and validators stay
  green. The shape is fixed now so emitters have a target.
evidence:
  - kind: schema
    ref: ops/schemas/run.schema.json
  - kind: doc
    ref: ops/event-types.md
  - kind: decision
    ref: ../trace-to-eval-harness/decisions/DEC-TTE-007-run-evidence-packet-as-review-boundary.md
  - kind: schema
    ref: ../trace-to-eval-harness/schemas/run-evidence.schema.json
  - kind: code
    ref: ../trace-to-eval-harness/trace_to_eval/run_evidence.py
rollback: |
  Drop the six optional properties from run.schema.json and revert the
  top-level description to its prior wording. Drop the two new event
  types (gate.run.evidence_recorded, run.evidence.replayed) from
  ops/event-types.md. Refresh ops/schemas-cache/run.schema.json in
  each product repo via check_schema_cache_freshness. Existing Run
  records validate unchanged because the fields were optional. The
  trace-to-eval-harness packet generator loses the upstream fields it
  reads from but the packet schema in that repo remains untouched.
owner: editorial
---

## decision

Run records SHOULD carry replay-equivalence evidence —
`prompt_snapshot_hash`, `tool_schemas_snapshot_hash`, `determinism`,
`checkpoint_ref`, `sandbox_image_ref`, `gate_results_summary` —
populated where the runtime can derive them at run completion. The six
fields land as optional properties on
`athena-site/ops/schemas/run.schema.json` so existing runs validate
unchanged and future runs gain replay evidence as runtimes learn to
emit it.

## alternatives

- Put the hashes in `events[]` instead of at the Run root. Hashes
  describe preconditions, not events; the question "were these two
  runs the same?" belongs at the Run root.
- Require all six fields on every Run. Existing runtimes do not emit
  canonicalized hashes or gate rollups yet; required would break every
  Run already written. Optional lets the schema lead.
- Define the fields only in the trace-to-eval-harness packet schema.
  The packet is a review-time projection; if the source Run record
  does not carry the fields, the packet generator has nothing to read.

## rationale

The thesis: run evidence is the bridge between agents and
engineering-grade trust. Without prompt and tool-schema hashes, two
runs against the "same" prompt are not provably the same — and a
reviewer cannot validate that a Run + Events + Artifacts bundle is
genuinely replay-equivalent. Without a gate rollup at the Run root,
the question "did this run pass its gates?" requires scanning every
gate_check event. Without checkpoint and sandbox refs, resuming a
failed run or reproducing its environment is a manual archaeological
dig.

The six fields together let a reviewer answer four questions from one
Run record: were the prompt preconditions identical, was the tool
surface identical, was the run pinned for determinism, did the run
pass its gates, and can the run be resumed or reproduced. All four
are load-bearing for engineering-grade trust; none are reliably
answerable without the fields.

## relationship to trace-to-eval-harness

Two complementary schemas, one source-of-truth and one review packet:

- `athena-site/ops/schemas/run.schema.json` (amended here) — the
  source-of-truth Run record, written as the run executes. Fields here
  are populated by the runtime at run completion.
- `trace-to-eval-harness/schemas/run-evidence.schema.json` (Codex's
  `bfd1d48`) — the review packet derived from the Run plus its events
  and artifacts. The `trace-to-eval evidence from-cdcp-events` CLI
  reads CDCP event logs and assembles the packet for review.

The packet generator depends on these source fields. Without
`prompt_snapshot_hash` and `tool_schemas_snapshot_hash` populated on
the Run, the packet cannot prove replay-equivalence. Without
`gate_results_summary`, the packet must reconstruct the rollup from
events on every read. The two schemas do not compete; the source
records, the packet reviews.

## requirement coverage

This DEC resolves a new requirement, R-CDCP-011 (run records carry
replay-equivalence evidence at the schema level), to be added to the
CDCP spec ledger in a follow-on. The requirement is named here so the
DEC stands; the spec entry follows in the same phase. R-CDCP-010
(cross-repo schemas live in athena-site) covers the schema-cache
discipline that propagates this amendment to product repos.

## evidence

- `ops/schemas/run.schema.json` — the amended schema with the six new
  optional properties.
- `ops/event-types.md` — two new event types
  (`gate.run.evidence_recorded`, `run.evidence.replayed`) that name
  the moments the evidence is recorded and verified.
- `../trace-to-eval-harness/decisions/DEC-TTE-007-run-evidence-packet-as-review-boundary.md`
  — the complementary review-packet DEC.
- `../trace-to-eval-harness/schemas/run-evidence.schema.json` — the
  review packet schema that derives from these source fields.
- `../trace-to-eval-harness/trace_to_eval/run_evidence.py` — the
  packet generator that reads the source fields.

## follow-on

- Phase B lands runtime emitters in procurement-negotiation-lab so the
  first Run records carry populated evidence fields.
- Phase D rolls the emitter pattern across ai-field-brief,
  supplier-risk-rag-agent, and chip-supply-chain-map.
- A future DEC adds R-CDCP-011 to the CDCP spec ledger and may
  promote individual fields from SHOULD to MUST once portfolio-wide
  emitter coverage is in place.

## rollback

Drop the six optional properties from `run.schema.json` and revert the
top-level description to its prior wording. Drop the two new event
types from `ops/event-types.md`. Refresh
`ops/schemas-cache/run.schema.json` in each product repo via
`check_schema_cache_freshness`. Existing Run records validate
unchanged because the fields were optional. The
trace-to-eval-harness packet generator loses the upstream fields it
reads from but the packet schema in that repo remains untouched.
