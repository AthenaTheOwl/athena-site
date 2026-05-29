# Canonical event types

The append-only event ledger is governed by `ops/schemas/event.schema.json`.
Per `DEC-CDCP-013`, the schema now enforces typed payload contracts for
nine canonical event types via a top-level `oneOf` discriminator:
`pipeline.start`, `pipeline.complete`, `pipeline.done`,
`tool.call.started`, `tool.call.completed`, `gate.check.passed`,
`gate.check.failed`, `gate.run.evidence_recorded`, and
`run.evidence.replayed`. Any other event type passes envelope-only
validation via an escape-hatch branch so the ledger can still absorb new
event types without a schema bump. This file documents the canonical
event types every product repo should emit and consume; the entries
below are the contract the schema enforces for the nine typed types and
the documentation-only contract for everything else.

## Portable repo:// URI scheme (DEC-CDCP-014)

Run-evidence ref fields (e.g. `sandbox_image_ref`, `checkpoint_ref`,
evidence refs, packet refs) carry cross-repo references. Per
`DEC-CDCP-014`, the portfolio adopts two URI forms for those refs:
`repo://<repo-name>@<sha>/<rel-path>` for a file at a specific commit
in a portfolio repo, and `artifact://<repo-name>/<artifact-id>` for
logical artifact references that do not resolve to a fixed file path.

Producers SHOULD emit URIs going forward; consumers MUST accept both
URI forms and legacy local paths during the Round 6 migration window.
The event and run schemas in this repo keep their ref fields as opaque
strings; the URI grammar lives at the producer and consumer boundary.
See `DEC-CDCP-014` for the full grammar, resolution rules, and
migration notes.

Each entry below names:

- **When it fires** — the moment that produces the event.
- **Required payload fields** — fields the consumer expects to find. For
  the nine typed event types these are also enforced by the schema; for
  the rest they are documentation only.
- **Typical actor** — the most common `actor.kind` and `actor.id` shape.
- **Example JSON** — a minimal record that would validate.

Add new event types by appending to this file plus filing a DEC. Adding
a new event type to the typed set requires extending the `oneOf` block
in the schema. Removing an event type requires a deprecation window of
one quarter and a sweep of downstream consumers.

---

## `signal.received`

**When it fires.** A new external signal lands at the portfolio edge.
Examples: a webhook, a user message, a scheduled cron tick that carries
work.

**Required payload fields.** `source`, `signal_kind`, `body_ref`.

**Typical actor.** `{kind: "system", id: "<source-name>"}`.

**Example.**
```json
{
  "event_id": "9c2c4f7e-4f9a-4f0f-9e2b-1a2b3c4d5e6f",
  "type": "signal.received",
  "created_at": "2026-05-23T08:00:00Z",
  "actor": {"kind": "system", "id": "vercel-webhook"},
  "payload": {
    "source": "vercel-webhook",
    "signal_kind": "deploy_failed",
    "body_ref": "events/raw/vercel-2026-05-23T08-00-00Z.json"
  }
}
```

---

## `spec.created`

**When it fires.** A new `specs/NNNN-<slug>/` ledger is opened.

**Required payload fields.** `spec_id`, `slug`, `requirements_count`.

**Typical actor.** `{kind: "role", id: "product.spec-writer"}`.

**Example.**
```json
{
  "event_id": "1d2e3f40-aabb-4ccd-9eef-001122334455",
  "type": "spec.created",
  "created_at": "2026-05-23T09:14:22Z",
  "actor": {"kind": "role", "id": "product.spec-writer"},
  "spec_id": "specs/0007-supplier-onboarding/",
  "payload": {
    "spec_id": "specs/0007-supplier-onboarding/",
    "slug": "supplier-onboarding",
    "requirements_count": 12
  }
}
```

---

## `agent.run.started`

**When it fires.** An agent begins a run inside a workspace or sandbox.

**Required payload fields.** `runtime`, `workspace_id`, `agent_id`.

**Typical actor.** `{kind: "role", id: "<role-id>"}`.

**Example.**
```json
{
  "event_id": "2a2b2c2d-3e3f-4040-5151-626263636464",
  "type": "agent.run.started",
  "created_at": "2026-05-23T09:15:00Z",
  "actor": {"kind": "role", "id": "engineering.implementation"},
  "run_id": "run-2026-05-23-001",
  "spec_id": "specs/0007-supplier-onboarding/",
  "payload": {
    "runtime": "claude-code-cli",
    "workspace_id": "wt-supplier-onboarding-001",
    "agent_id": "claude-opus-4-7"
  }
}
```

---

## `agent.run.completed`

**When it fires.** The same run reaches a terminal status (`done`,
`failed`, `cancelled`, or `needs_review`).

**Required payload fields.** `status`, `duration_seconds`,
`outputs_count`.

**Typical actor.** `{kind: "role", id: "<role-id>"}`.

**Example.**
```json
{
  "event_id": "3b3c3d3e-4f4f-5050-6161-727273737474",
  "type": "agent.run.completed",
  "created_at": "2026-05-23T09:42:11Z",
  "actor": {"kind": "role", "id": "engineering.implementation"},
  "run_id": "run-2026-05-23-001",
  "parent_event_id": "2a2b2c2d-3e3f-4040-5151-626263636464",
  "cost_usd": 0.42,
  "tokens_input": 18034,
  "tokens_output": 6210,
  "payload": {
    "status": "done",
    "duration_seconds": 1631,
    "outputs_count": 3
  }
}
```

---

## `pipeline.start`

**When it fires.** A run-evidence-aware pipeline (factory, eval suite,
brief backfill, watchlist export) begins execution. Marks the moment a
run captures the preconditions a reviewer needs to verify replay
equivalence later.

**Required payload fields.** `prompt_snapshot_hash`,
`tool_schemas_snapshot_hash`. Both are SHA-256 hex digests (64 lowercase
hex chars) enforced by the schema.

**Typical actor.** `{kind: "system", id: "<runtime-or-pipeline-id>"}`.

**Example.**
```json
{
  "event_id": "7cc291dc-967f-44e6-b3d6-40c83e7bd552",
  "type": "pipeline.start",
  "created_at": "2026-05-28T01:40:15Z",
  "actor": {"kind": "system", "id": "procurement-lab-factory"},
  "run_id": "run-cb524eb06115",
  "payload": {
    "prompt_snapshot_hash": "eb599443822c3aa2abb21160bb3cb234e196ce768ad7072db99fc9be8f2293f5",
    "tool_schemas_snapshot_hash": "0051bdbb230ae794642e42a0033aca8e30f200c59c51a9f4899e6e90a6b42965"
  }
}
```

---

## `pipeline.complete`

**When it fires.** The same pipeline reaches a terminal state and a
gate-results summary is available. Used where the runtime distinguishes
`pipeline.complete` (run finished, gates summary attached) from a later
`pipeline.done` (process exited).

**Required payload fields.** `status` (one of `done`, `failed`,
`cancelled`). Optional `gate_results_summary` with `gates_passed`,
`gates_failed`, `all_passed`.

**Typical actor.** `{kind: "system", id: "<runtime-or-pipeline-id>"}`.

**Example.**
```json
{
  "event_id": "d8d6862e-6e6b-4597-9406-d72de4b5efba",
  "type": "pipeline.complete",
  "created_at": "2026-05-28T01:42:30Z",
  "actor": {"kind": "system", "id": "procurement-lab-factory"},
  "run_id": "run-cb524eb06115",
  "payload": {
    "status": "done",
    "gate_results_summary": {
      "gates_passed": ["typecheck", "vitest", "spec_check"],
      "gates_failed": [],
      "all_passed": true
    }
  }
}
```

---

## `pipeline.done`

**When it fires.** The pipeline process exits. Some runtimes emit
`pipeline.done` instead of (not in addition to) `pipeline.complete`;
others emit both. The schema treats `pipeline.done` as a sibling of
`pipeline.complete` with the same required payload contract.

**Required payload fields.** `status` (one of `done`, `failed`,
`cancelled`). Optional `gate_results_summary` as on `pipeline.complete`.

**Typical actor.** `{kind: "system", id: "<runtime-or-pipeline-id>"}`.

**Example.**
```json
{
  "event_id": "be4d546e-0753-4c90-b9e8-e890febcb440",
  "type": "pipeline.done",
  "created_at": "2026-05-28T02:30:03Z",
  "actor": {"kind": "system", "id": "chip-supply-chain-map-export"},
  "run_id": "run-efeb29900de3",
  "payload": {
    "status": "done"
  }
}
```

---

## `gate.check.passed`

**When it fires.** A named gate inside a run returns clean. Distinct
from `proof.gate.passed`: this event is for the in-pipeline gate
sequence (typecheck, vitest, input_validation, packet_shape, etc.),
where `proof.gate.passed` is for the cross-cutting proof-gate runner.

**Required payload fields.** `gate_name`. Optional `details` (any
shape).

**Typical actor.** `{kind: "system", id: "<runtime-or-pipeline-id>"}`.

**Example.**
```json
{
  "event_id": "7f0f2036-e1fb-4ce4-9dac-b97c73868e93",
  "type": "gate.check.passed",
  "created_at": "2026-05-28T01:40:16Z",
  "actor": {"kind": "system", "id": "procurement-lab-factory"},
  "run_id": "run-cb524eb06115",
  "payload": {
    "gate_name": "typecheck",
    "details": {"cmd": "npx tsc --noEmit", "must_pass": true, "round": 0}
  }
}
```

---

## `gate.check.failed`

**When it fires.** A named in-pipeline gate returns non-zero. Mirrors
`gate.check.passed`; the schema requires a `reason` so the failure mode
is captured at the event boundary.

**Required payload fields.** `gate_name`, `reason`. Optional `details`.

**Typical actor.** `{kind: "system", id: "<runtime-or-pipeline-id>"}`.

**Example.**
```json
{
  "event_id": "a9b8c7d6-e5f4-4030-8201-021304050607",
  "type": "gate.check.failed",
  "created_at": "2026-05-28T01:40:16Z",
  "actor": {"kind": "system", "id": "procurement-lab-factory"},
  "run_id": "run-cb524eb06115",
  "payload": {
    "gate_name": "vitest",
    "reason": "1 test failed: src/lib/scoring.test.ts > floor-clamp",
    "details": {"cmd": "npm test -- --run", "must_pass": true, "round": 0}
  }
}
```

---

## `gate.run.evidence_recorded`

**When it fires.** A Run record is persisted with at least one of the
replay-equivalence fields populated (`prompt_snapshot_hash`,
`tool_schemas_snapshot_hash`, `determinism`, `checkpoint_ref`,
`sandbox_image_ref`, `gate_results_summary`). The event marks the moment
the source-of-truth Run carries enough evidence for a downstream packet
generator to assemble a review packet.

**Required payload fields.** `run_id`, `fields_populated`.

**Typical actor.** `{kind: "role", id: "engineering.implementation"}` or
`{kind: "system", id: "<runtime-id>"}`.

**Example.**
```json
{
  "event_id": "c4d5e6f7-0102-4304-8506-070809101112",
  "type": "gate.run.evidence_recorded",
  "created_at": "2026-05-27T20:31:00Z",
  "actor": {"kind": "system", "id": "claude-code-cli"},
  "run_id": "run-2026-05-27-007",
  "payload": {
    "run_id": "run-2026-05-27-007",
    "fields_populated": [
      "prompt_snapshot_hash",
      "tool_schemas_snapshot_hash",
      "determinism",
      "gate_results_summary"
    ]
  }
}
```

---

## `run.evidence.replayed`

**When it fires.** A consumer (`trace-to-eval-harness` or similar)
reconstructs a Run from its evidence packet and verifies
replay-equivalence against the recorded `prompt_snapshot_hash`,
`tool_schemas_snapshot_hash`, and determinism knobs.

**Required payload fields.** `run_id`, `packet_ref`, `replay_equivalent`.

**Typical actor.** `{kind: "system", id: "trace-to-eval-harness"}` or
`{kind: "role", id: "science.proof-gate-runner"}`.

**Example.**
```json
{
  "event_id": "d5e6f708-0203-4405-9607-181920212223",
  "type": "run.evidence.replayed",
  "created_at": "2026-05-27T20:42:11Z",
  "actor": {"kind": "system", "id": "trace-to-eval-harness"},
  "run_id": "run-2026-05-27-007",
  "payload": {
    "run_id": "run-2026-05-27-007",
    "packet_ref": "reports/run-evidence/run-2026-05-27-007.json",
    "replay_equivalent": true
  }
}
```

---

## `tool.call.started`

**When it fires.** A role invokes a tool from the registry.

**Required payload fields.** `tool_name`. Optional `args` (any object).

**Note.** Earlier emitters used `tool_id` for the same field. The
schema source-of-truth is `tool_name`; emitter migration is tracked in
the Round 3 follow-on to DEC-CDCP-013.

**Typical actor.** `{kind: "role", id: "<role-id>"}`.

**Example.**
```json
{
  "event_id": "4c4d4e4f-5050-6161-7272-838384848585",
  "type": "tool.call.started",
  "created_at": "2026-05-23T09:20:01Z",
  "actor": {"kind": "role", "id": "engineering.implementation"},
  "run_id": "run-2026-05-23-001",
  "payload": {
    "tool_name": "repo.apply_patch",
    "args": {"arguments_digest": "sha256:6f1c..."}
  }
}
```

---

## `tool.call.completed`

**When it fires.** The same tool call returns or errors out.

**Required payload fields.** `tool_name`. Optional `result` (any),
`duration_ms` (non-negative integer), `error` (string).

**Note.** Earlier emitters used `tool_id` for the same field and
carried `status` / `duration_ms` at the payload root. The schema
source-of-truth is `tool_name`; emitters migrate in Round 3.

**Typical actor.** `{kind: "role", id: "<role-id>"}`.

**Example.**
```json
{
  "event_id": "5d5e5f60-6161-7272-8383-949495959696",
  "type": "tool.call.completed",
  "created_at": "2026-05-23T09:20:03Z",
  "actor": {"kind": "role", "id": "engineering.implementation"},
  "run_id": "run-2026-05-23-001",
  "parent_event_id": "4c4d4e4f-5050-6161-7272-838384848585",
  "payload": {
    "tool_name": "repo.apply_patch",
    "duration_ms": 1820
  }
}
```

---

## `artifact.produced`

**When it fires.** A run writes a typed artifact and registers it.

**Required payload fields.** `artifact_type`, `artifact_path`, `status`.

**Typical actor.** `{kind: "role", id: "<role-id>"}`.

**Example.**
```json
{
  "event_id": "6e6f7071-7272-8383-9494-a5a5b6b6c7c7",
  "type": "artifact.produced",
  "created_at": "2026-05-23T09:24:14Z",
  "actor": {"kind": "role", "id": "engineering.implementation"},
  "run_id": "run-2026-05-23-001",
  "artifact_id": "art-2026-05-23-pr-0042",
  "payload": {
    "artifact_type": "pr",
    "artifact_path": "https://github.com/example/repo/pull/42",
    "status": "proposed"
  }
}
```

---

## `proof.gate.passed`

**When it fires.** A proof gate (lint, spec_check, tests, evals,
security_review) returns clean.

**Required payload fields.** `gate_name`, `target_ref`, `duration_ms`.

**Typical actor.** `{kind: "system", id: "<gate-runner>"}`.

**Example.**
```json
{
  "event_id": "7f808182-8383-9494-a5a5-b6b6c7c7d8d8",
  "type": "proof.gate.passed",
  "created_at": "2026-05-23T09:25:00Z",
  "actor": {"kind": "system", "id": "github-actions"},
  "run_id": "run-2026-05-23-001",
  "payload": {
    "gate_name": "voice_lint",
    "target_ref": "sha:abc1234",
    "duration_ms": 412
  }
}
```

---

## `proof.gate.failed`

**When it fires.** The same gate returns non-zero.

**Required payload fields.** `gate_name`, `target_ref`, `failure_count`,
`failure_digest_ref`.

**Typical actor.** `{kind: "system", id: "<gate-runner>"}`.

**Example.**
```json
{
  "event_id": "8081828384-9494-a5a5-b6b6-c7c7d8d8e9e9",
  "type": "proof.gate.failed",
  "created_at": "2026-05-23T09:25:01Z",
  "actor": {"kind": "system", "id": "github-actions"},
  "run_id": "run-2026-05-23-001",
  "payload": {
    "gate_name": "spec_check",
    "target_ref": "sha:abc1234",
    "failure_count": 3,
    "failure_digest_ref": "events/raw/spec_check-2026-05-23.log"
  }
}
```

---

## `decision.recorded`

**When it fires.** A new DEC-* record lands in `decisions/`.

**Required payload fields.** `decision_id`, `spec_id`, `requirement`,
`reversible`.

**Typical actor.** `{kind: "human", id: "<handle>"}` or
`{kind: "role", id: "product.spec-writer"}`.

**Example.**
```json
{
  "event_id": "90919293-9494-a5a5-b6b6-c7c7d8d8e9ea",
  "type": "decision.recorded",
  "created_at": "2026-05-23T09:30:00Z",
  "actor": {"kind": "human", "id": "vigneshthegreat"},
  "spec_id": "specs/0007-supplier-onboarding/",
  "payload": {
    "decision_id": "DEC-AFB-0007-storage-backend",
    "spec_id": "specs/0007-supplier-onboarding/",
    "requirement": "R-AFB-0007-3",
    "reversible": true
  }
}
```

---

## `decision.amended`

**When it fires.** A new DEC amends an existing DEC. The new DEC's
`amends:` field carries the prior DEC's id. Use when refining a decision
without overwriting it. The prior DEC is not changed; the new DEC is a
sibling artifact that documents the amendment.

**Required payload fields.** `amending_decision_id`,
`amended_decision_id`, `reason`.

**Typical actor.** `{kind: "role", id: "product.spec-writer"}`.

**Example.**
```json
{
  "event_id": "a0a1a2a3-a4a5-4a6a-8a7a-a8a9aaabacad",
  "type": "decision.amended",
  "created_at": "2026-05-23T11:00:00Z",
  "actor": {"kind": "role", "id": "product.spec-writer"},
  "payload": {
    "amending_decision_id": "DEC-CIT-002-amendment-reversibility-mitigation",
    "amended_decision_id": "DEC-CIT-002-original",
    "reason": "Capture forward-looking mitigation without changing original."
  }
}
```

---

## `approval.granted`

**When it fires.** A human or higher-privileged role approves a request
that was held in `require_approval`.

**Required payload fields.** `request_kind`, `target_ref`, `approver_id`.

**Typical actor.** `{kind: "human", id: "<handle>"}`.

**Example.**
```json
{
  "event_id": "a1a2a3a4-a5a5-b6b6-c7c7-d8d8e9eafafa",
  "type": "approval.granted",
  "created_at": "2026-05-23T09:35:00Z",
  "actor": {"kind": "human", "id": "vigneshthegreat"},
  "payload": {
    "request_kind": "deploy_to_production",
    "target_ref": "release-2026-05-23-001",
    "approver_id": "vigneshthegreat"
  }
}
```

---

## `release.shipped`

**When it fires.** A deploy finishes and the deploy verification gate
passes.

**Required payload fields.** `release_id`, `environment`, `commit_sha`,
`deploy_url`.

**Typical actor.** `{kind: "role", id: "operations.release-driver"}` or
`{kind: "system", id: "vercel"}`.

**Example.**
```json
{
  "event_id": "b2b3b4b5-b6b6-c7c7-d8d8-e9eafafa0b0b",
  "type": "release.shipped",
  "created_at": "2026-05-23T09:45:00Z",
  "actor": {"kind": "system", "id": "vercel"},
  "payload": {
    "release_id": "release-2026-05-23-001",
    "environment": "production",
    "commit_sha": "abc1234",
    "deploy_url": "https://athena-site-six.vercel.app"
  }
}
```

---

## `runtime.signal.received`

**When it fires.** A long-running agent or service receives an
out-of-band runtime signal (pause, resume, cancel, budget warning).

**Required payload fields.** `signal_kind`, `target_run_id`.

**Typical actor.** `{kind: "human", id: "<handle>"}` or
`{kind: "system", id: "budget-watchdog"}`.

**Example.**
```json
{
  "event_id": "c3c4c5c6-c7c7-d8d8-e9ea-fafa0b0b1c1c",
  "type": "runtime.signal.received",
  "created_at": "2026-05-23T09:50:00Z",
  "actor": {"kind": "system", "id": "budget-watchdog"},
  "run_id": "run-2026-05-23-001",
  "payload": {
    "signal_kind": "budget_warning",
    "target_run_id": "run-2026-05-23-001"
  }
}
```

---

## `dream.job.started`

**When it fires.** A weekly dream job begins.

**Required payload fields.** `dream_id`, `week`, `lookback_days`.

**Typical actor.** `{kind: "role", id: "learning.dream-orchestrator"}`.

**Example.**
```json
{
  "event_id": "d4d5d6d7-d8d8-e9ea-fafa-0b0b1c1c2d2d",
  "type": "dream.job.started",
  "created_at": "2026-05-23T03:00:00Z",
  "actor": {"kind": "role", "id": "learning.dream-orchestrator"},
  "payload": {
    "dream_id": "dream-2026-W21",
    "week": "2026-W21",
    "lookback_days": 7
  }
}
```

---

## `dream.candidate.generated`

**When it fires.** A dream job produces a promotion candidate (memory
update, generated test, skill patch, backlog item).

**Required payload fields.** `dream_id`, `candidate_kind`,
`human_review_required`.

**Typical actor.** `{kind: "role", id: "learning.dream-orchestrator"}`.

**Example.**
```json
{
  "event_id": "e5e6e7e8-e9ea-fafa-0b0b-1c1c2d2d3e3e",
  "type": "dream.candidate.generated",
  "created_at": "2026-05-23T03:21:14Z",
  "actor": {"kind": "role", "id": "learning.dream-orchestrator"},
  "payload": {
    "dream_id": "dream-2026-W21",
    "candidate_kind": "memory_update",
    "human_review_required": true
  }
}
```

---

## `memory.promoted`

**When it fires.** A reviewer promotes a dream candidate into long-term
memory (a memory file, a guard, a system-prompt patch).

**Required payload fields.** `target_path`, `candidate_event_id`,
`approver_id`.

**Typical actor.** `{kind: "human", id: "<handle>"}`.

**Example.**
```json
{
  "event_id": "f6f7f8f9-fafa-0b0b-1c1c-2d2d3e3e4f4f",
  "type": "memory.promoted",
  "created_at": "2026-05-23T10:05:00Z",
  "actor": {"kind": "human", "id": "vigneshthegreat"},
  "parent_event_id": "e5e6e7e8-e9ea-fafa-0b0b-1c1c2d2d3e3e",
  "payload": {
    "target_path": ".agents/memory/lessons.md",
    "candidate_event_id": "e5e6e7e8-e9ea-fafa-0b0b-1c1c2d2d3e3e",
    "approver_id": "vigneshthegreat"
  }
}
```

---

## `skill.promoted`

**When it fires.** A pattern that recurred enough across runs is packaged
as a skill and added to `skills/<id>/`.

**Required payload fields.** `skill_id`, `version`, `approver_id`.

**Typical actor.** `{kind: "human", id: "<handle>"}`.

**Example.**
```json
{
  "event_id": "07181920-2122-2324-2526-272829303132",
  "type": "skill.promoted",
  "created_at": "2026-05-23T10:30:00Z",
  "actor": {"kind": "human", "id": "vigneshthegreat"},
  "payload": {
    "skill_id": "weekly-portfolio-audit",
    "version": "1.0.0",
    "approver_id": "vigneshthegreat"
  }
}
```

---

## Schema evolution notes

A small log of field-shape decisions that aren't worth their own DEC but
should be visible to anyone writing emitters or validators.

### `dream-output.candidate.kind` → `target_kind` (2026-05-24)

The four candidate sub-schemas in `ops/schemas/dream-output.schema.json`
(`memory_update`, `test_generation`, `skill_patch`, `backlog_item`)
discriminate on `target_kind`. Earlier emissions across the product
repos used `kind:` for the same field; validators in
ai-field-brief, procurement-negotiation-lab, and supplier-risk-rag-agent
tolerate both during the transition.

**The canonical form is `target_kind`.** Reason: `kind` is a generic
field name and already appears on `actor.kind` and on evidence items
(`evidence[].kind`); a more specific name keeps the discriminator
from getting confused with adjacent fields during reads.

**Migration plan.** A future cleanup pass renames `kind:` to
`target_kind:` in candidate front-matter across the existing
`dreams/<week>/candidates/*.yaml` files, then tightens the per-repo
validators to reject `kind:` alone. Until then, dual-acceptance stays.

**Affected files.** `ops/schemas/dream-output.schema.json` (canonical
contract). Product-repo validators read this schema at a pinned ref and
add a tolerance layer that rewrites `kind` to `target_kind` before
validation.
