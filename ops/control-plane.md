# Cognitive Delivery Control Plane

A charter for how athena-site and its sibling repos agree on what to record,
what to gate, and what to graduate.

## Why this exists

The load-bearing thesis: the durable system is specs, decisions, traces,
ledgers, tests, evals, and deployment evidence — not any agent framework.
Frameworks turn over every six months. The records survive. If the records
have shape, agents can write them, gates can check them, and humans can
audit them. If the records have no shape, every repo grows its own ad-hoc
folder and the portfolio drifts apart.

Athena-site owns the shape. Each product repo owns its own records.

## The six artifact types

**Specs** name what we're building. Each repo keeps a `specs/NNNN-<slug>/`
ledger with a requirements file, a plan, and a tests-and-evals file.
`scripts/spec_check.py` in each repo already gates the ledger format.

**Decisions** name why we chose this path. Each repo keeps a `decisions/`
directory of `DEC-*.md` (or `.json`) files. A decision points back at the
spec and requirement it resolves, lists the alternatives, names the
evidence, and writes down the rollback. See
`ops/schemas/decision.schema.json` for the contract.

**Artifacts** name what was made. Patches, PRs, eval reports, screenshots,
release notes, postmortems — each one is a typed record with provenance.
See `ops/schemas/artifact.schema.json`.

**Proof gates** name what's safe to ship. The existing `voice_lint.py`,
`spec_check.py`, and CI jobs in each repo are gates. They run on every PR
and on the weekly cron. A gate that fails blocks the merge or files an
issue.

**Dreams** name what we learned. A weekly offline-cognition job (per repo
or central) reads the last N days of runs, postmortems, and evals, then
proposes promotion candidates: memory updates, generated tests, skill
patches, backlog items. See `ops/schemas/dream-output.schema.json`. Every
candidate carries evidence and `human_review_required: true` by default.

**Skills** name what we'll reuse. A skill is an instructions file plus
optional scripts and evals, graduated from a pattern that recurred enough
to deserve a name. Skills are extracted from observed practice, never
invented from scratch. See `ops/schemas/skill.schema.json`.

## The operating model

Artifact types name what we record. The operating model names who records
it, in what order, under what permission rule, and which gate must pass
before the next step starts. Five more schemas in `ops/schemas/` carry this
layer: `role`, `tool`, `policy`, `workflow`, `state-machine`, `event`.

### The 22-step lifecycle

Every change in the portfolio travels the same 22 steps from signal to
retrospective: signal received, signal triaged, spec drafted, spec
reviewed, requirements frozen, decisions recorded, plan written, plan
approved, branch cut, code implemented, code self-reviewed, code peer
reviewed, tests run, evals run, security review, proof gates passed,
artifacts produced, PR merged, deploy executed, deploy verified, release
noted, retrospective filed. Not every change touches all 22; the workflow
declaration says which steps apply.

### The 12 guilds

Roles cluster into 12 guilds. Control coordinates. Product owns specs.
Research scouts. Design shapes interaction. Engineering implements.
Science runs evals. Security audits. Operations runs the platform. Domain
carries subject expertise. Learning runs the dream loop. Documentation
keeps the written record. A 12th guild slot stays reserved for whatever
the portfolio grows into next.

### The minimum-viable role set

A product repo ships six roles on day one, all defined in its `.agents/`
directory: `control.coordinator`, `product.spec-writer`,
`engineering.implementation`, `engineering.code-reviewer`,
`security.proof-gate-runner`, `learning.dream-orchestrator`. The rest of
the 50-role aspiration lands one role at a time, only when a workflow
needs it and a working example can ship with it. The ledger of pending
roles lives in each repo's `.agents/ROLES.md`; the ledger is the
authority, the count is a target.

### The four enforcement layers

Athena-site owns the contracts. Each product repo owns four executable
validators that fail the build on drift:

| Validator | Schema | Job |
|---|---|---|
| `validate_decisions.py` | `decision.schema.json` | already shipped — gates `decisions/` |
| `validate_roles.py` | `role.schema.json` | gates `.agents/roles/*.yaml` |
| `validate_tools.py` | `tool.schema.json` | gates `.agents/tools/*.yaml` |
| `validate_policies.py` | `policy.schema.json` | gates `.agents/policies/*.yaml` |

State machines and workflows are declarative; the same generic walker
parses both and checks that every transition is legal and every step
points at a defined role.

### The honest rule

Ship six worked-example roles per pass. The 50-role aspiration is a TODO
ledger, never a one-shot build. Same rule for tools, policies, workflows,
and state machines: land the contract, land one working example,
backfill the rest as workflows ask for them. A repo with three roles and
two policies that all execute beats a repo with 50 roles on paper and a
broken CI.

## What lives where

| Owned by athena-site | Owned by each product repo |
|---|---|
| `ops/schemas/*.schema.json` (the contracts) | `specs/` ledger |
| `ops/control-plane.md` (this charter) | `decisions/DEC-*.md` |
| `ops/portfolio-manifest.yml` | `dreams/<week>/report.md` and outputs |
| `scripts/portfolio_audit.py` (cross-repo health) | `skills/<id>/` packages |
| `.github/workflows/portfolio-audit.yml` (weekly cron) | `scripts/spec_check.py`, `scripts/voice_lint.py`, `scripts/validate_decisions.py` |

Athena-site never reaches into a product repo to fix its records. The
portfolio audit reports drift; the product repo's own gates fix it.

## How a product repo onboards

Five steps. Each one is a separate commit in the product repo. Codex and
the human are doing this in parallel for ai-field-brief and one other repo.

1. **Add the spec ledger.** Create
   `specs/NNNN-cognitive-delivery-control-plane/` with `requirements.md`,
   `plan.md`, and `tests-and-evals.md`. Number it with whatever the repo's
   next free NNNN is.
2. **Add `.agents/AGENTS.md`.** A single file the human and the agents
   read first. It points at the spec ledger, the decisions directory, the
   gate scripts, and the dreams folder.
3. **Add the decisions directory.** Create `decisions/` with at least one
   backfilled DEC that captures a real past decision (a deploy target, a
   model pick, a vendored library). Backfilling proves the schema fits
   reality.
4. **Add `scripts/validate_decisions.py`.** Fetches
   `decision.schema.json` from this repo at the pinned ref, walks the
   local `decisions/` directory, and validates every record.
5. **Wire CI.** Extend `.github/workflows/` so a schema violation fails
   the build the same way `voice_lint.py` and `spec_check.py` already do.

Dreams and skills land later, once the repo has produced enough runs and
postmortems to feed them.

## What we explicitly don't build

The charter is small on purpose. Six things stay deferred until artifact
volume forces them:

- **A control-plane SaaS** with twelve screens for governance dashboards.
  The weekly cron + the per-repo gates do the job until they don't.
- **LangGraph / CrewAI / AutoGen / Strands / PydanticAI adoption.** The
  records are framework-neutral. Pick a framework the day a record shape
  asks for one, and write a DEC explaining why.
- **A cross-repo R-* requirement namespace migration.** Each repo keeps
  its own R-* numbering for now. Cross-repo joining waits until there's a
  query worth running across the join.
- **An OPA daemon.** `policy.schema.json` is OPA-shaped on purpose so a
  small Python evaluator inside each repo can read the rules. A daemon
  arrives the day the policy volume justifies one, not before.
- **A separate event-log database.** Events land as JSONL files inside
  each repo's `events/` directory; the portfolio audit walks the files.
  A database arrives the day the join queries justify it.
- **A workspace-manager service.** The Agent tool's worktree isolation
  plus per-repo factory scripts handle workspace setup. No long-running
  service.

The rule across all six: defer the build until the record volume names
the need.
