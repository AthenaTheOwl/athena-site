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

## What we don't build yet

The charter is small on purpose. Three things stay deferred until artifact
volume forces them:

- **A control-plane SaaS** with twelve screens for governance dashboards.
  The weekly cron + the per-repo gates do the job until they don't.
- **LangGraph / CrewAI / AutoGen / Strands / PydanticAI adoption.** The
  records are framework-neutral. Pick a framework the day a record shape
  asks for one, and write a DEC explaining why.
- **A cross-repo R-* requirement namespace migration.** Each repo keeps
  its own R-* numbering for now. Cross-repo joining waits until there's a
  query worth running across the join.

The rule across all three: defer the build until the record volume names
the need.
