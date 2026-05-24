# Canonical event types

The append-only event ledger is governed by `ops/schemas/event.schema.json`.
The schema does not constrain the inner `payload` shape so the ledger can
absorb new event types without a schema bump. This file documents the
canonical event types every product repo should emit and consume.

Each entry below names:

- **When it fires** — the moment that produces the event.
- **Required payload fields** — fields the consumer expects to find.
- **Typical actor** — the most common `actor.kind` and `actor.id` shape.
- **Example JSON** — a minimal record that would validate.

Add new event types by appending to this file plus filing a DEC. Removing
an event type requires a deprecation window of one quarter and a sweep of
downstream consumers.

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

## `tool.call.started`

**When it fires.** A role invokes a tool from the registry.

**Required payload fields.** `tool_id`, `arguments_digest`.

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
    "tool_id": "repo.apply_patch",
    "arguments_digest": "sha256:6f1c..."
  }
}
```

---

## `tool.call.completed`

**When it fires.** The same tool call returns or errors out.

**Required payload fields.** `tool_id`, `status`, `duration_ms`.

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
    "tool_id": "repo.apply_patch",
    "status": "ok",
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
