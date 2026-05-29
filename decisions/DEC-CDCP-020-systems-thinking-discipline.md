---
id: DEC-CDCP-020-systems-thinking-discipline
spec: specs/0010-cognitive-delivery-control-plane/
requirement: R-CDCP-027..030
date: 2026-05-29
status: approved
reversible: true
decision: |
  The portfolio adopts a systems-thinking discipline for every
  substantial DEC, dream candidate, and Run record. Four new
  optional fields land on `ops/schemas/decision.schema.json`,
  `ops/schemas/dream-output.schema.json` (under each candidate),
  and `ops/schemas/run.schema.json`: `systems_map`,
  `transferable_principle`, `falsification_test`, and
  `adoption_ladder` (an object with `minimum_viable`,
  `mid_adoption`, `full_adoption`, `monitoring_signals`). All four
  are optional during the bootstrap window. Validators in each
  product repo emit a warning when a new DEC with `Status: approved`
  is missing any of the four fields; the warning does not fail the
  build. After 30 days, an amendment DEC switches the warning to a
  hard failure for new DECs. The discipline names the WHY at the
  systems level, what TRANSFERS, what would FALSIFY, and HOW to
  adopt incrementally — dimensions today's DEC ledger leaves
  implicit.
alternatives:
  - label: keep DECs as today and document the discipline in AGENTS.md only
    rejected_because: |
      AGENTS.md is read-once guidance; a schema field is enforced
      every time a DEC lands. The portfolio has spent six rounds
      teaching itself to treat schemas as the contract surface
      (DEC-CDCP-013 for events, DEC-CDCP-011 for run-evidence). A
      norm that lives only in prose drifts the moment the author
      forgets to read it. The schema + warning + ratchet sequence
      is the same shape every other CDCP norm has taken; doing it
      again here is the consistent move.
  - label: require the four fields from day one (no warning window)
    rejected_because: |
      A hard requirement on day one would bounce every in-flight DEC
      branch across the portfolio and force a backfill sweep across
      19 existing CDCP DECs before any new work could land. The
      bootstrap-warning-then-ratchet pattern (the same one
      DEC-CDCP-019 used for coverage) lets the discipline accumulate
      organically; new DECs populate at author's discretion first,
      then the 30-day amendment makes the contract real. Hard
      enforcement without the warning window is the brittle path.
  - label: add the fields only to the decision schema, skip dream-output and run
    rejected_because: |
      The discipline is portfolio-wide on purpose. Dream candidates
      are forward-looking decisions in waiting; if the four
      dimensions are right for DECs, they are right for the
      candidates that become DECs. Runs are the join key between
      decisions and artifacts (DEC-CDCP-011); a run that carries
      the four fields lets a downstream review packet reconstruct
      not just what happened but what the run was claiming
      systemically. Landing all three schemas in one DEC keeps the
      contract coherent across the artifact graph.
  - label: name a richer field set (e.g. add risk_vectors, second_order_effects)
    rejected_because: |
      Four fields is the smallest set that captures the
      systems-thinking move without becoming a fill-in-the-blanks
      form. Each of the four answers a distinct question:
      `systems_map` (what pattern), `transferable_principle` (what
      generalizes), `falsification_test` (what would disprove),
      `adoption_ladder` (how to roll out). Adding risk vectors or
      second-order effects would either duplicate the rationale
      block or pressure authors to invent content. A later DEC can
      widen the set if the discipline shows it needs more
      dimensions.
rationale: |
  The portfolio's existing artifacts capture WHAT was decided. The
  rationale block names WHY at the local level. Neither names the
  systemic pattern the decision exposes, the principle that would
  transfer to another repo, the observation that would falsify the
  decision, or the adoption ladder for landing it portfolio-wide.
  Those four dimensions are the difference between a recorded
  decision and an engineering-grade claim. The Matrix Plane and
  AI Brief OS chats both arrived at the same shape independently;
  the discipline crystallizes that convergence as a schema-level
  contract.

  The bootstrap-with-warning pattern matches DEC-CDCP-019's coverage
  threshold (5% floor with quarterly ratchet). Both decisions admit
  that the portfolio is not yet at the target state and refuse to
  pretend otherwise: validators emit a warning, the discipline
  diffuses through new DECs, the ledger records adoption rate, and
  the 30-day amendment ratchets the contract once the baseline is
  visible.

  Schema placement is deliberate. The decision schema is the primary
  surface. The dream-output schema mirrors the fields under each
  candidate because dreams are forward-looking decisions in waiting;
  a candidate that names its `systems_map` and `falsification_test`
  is one step closer to promotion. The run schema carries the same
  four fields because runs are the audit trail; a run that records
  what claim it was advancing systemically lets a downstream review
  packet (per DEC-CDCP-011) reconstruct the WHY, not just the WHAT.
trade_off: |
  The bootstrap warning trains authors to ignore the prompt if the
  ratchet never lands. The 30-day amendment is the load-bearing
  half of the contract; without it, the discipline degrades into a
  decorative field set. A future DEC must close the loop. The
  field-count choice (four) is also a bet — too few and the
  discipline underspecifies engineering-grade trust; too many and
  authors fill in placeholder content to clear the warning. Four is
  the smallest set the source chats converged on, but a later
  amendment may widen or narrow it once the adoption signal is
  visible. The voluntary-during-bootstrap stance also means the
  first 30 days produce a noisy signal: some new DECs populate all
  four fields, some populate none, and the portfolio-status
  dashboard must distinguish authentic adoption from
  warning-clearing copy-paste.
evidence:
  - kind: doc
    ref: ops/schemas/decision.schema.json
  - kind: doc
    ref: ops/schemas/dream-output.schema.json
  - kind: doc
    ref: ops/schemas/run.schema.json
  - kind: doc
    ref: ops/event-types.md
  - kind: decision
    ref: DEC-CDCP-011-run-records-carry-replay-equivalence-evidence.md
  - kind: decision
    ref: DEC-CDCP-013-event-schema-enforces-typed-payloads.md
  - kind: decision
    ref: DEC-CDCP-019-dec-test-coverage-report.md
coverage:
  - R-CDCP-027
  - R-CDCP-028
  - R-CDCP-029
  - R-CDCP-030
rollback: |
  Revert the four-field additions in
  `ops/schemas/decision.schema.json`,
  `ops/schemas/dream-output.schema.json`, and
  `ops/schemas/run.schema.json`. Drop the systems-thinking
  discipline note from `ops/event-types.md`. Mark this DEC reversed.
  Any product-repo validator extensions wired in Workflow K Phase 2
  must be reverted in their own follow-on amendment per repo. New
  DECs continue to validate against the older schema shape; no
  existing DEC carrying the four fields is invalidated by the
  rollback because the fields are optional from day one.
owner: governance.cdcp-curator
systems_map: |
  Portfolio-wide artifact discipline — every DEC and dream becomes a
  systems claim with explicit transferability, falsifiability, and
  adoption ladder, not just a local decision. The schema is the
  contract surface; the validators are the enforcement boundary;
  the 30-day amendment ratchet is the cadence by which a voluntary
  norm becomes a structural requirement.
transferable_principle: |
  Any control-plane artifact (decision, action, evaluation,
  forward-looking candidate) should declare its four dimensions:
  what systemic pattern it touches, what generalizes, what would
  falsify, and how to adopt incrementally. This generalizes to any
  multi-repo portfolio where decisions accrue and the ledger
  outlives the authors. The pattern also generalizes to single-repo
  decision logs once the four-field discipline is part of the
  team's review checklist.
falsification_test: |
  If a population of DECs with all four fields populated leads to
  worse engineering outcomes than a matched population without —
  measured via downstream amendment rate, time-to-rollback, or
  rework hours over a 90-day window — the discipline is falsified.
  A weaker but earlier signal: if authors consistently leave the
  fields blank or fill them with copy-paste placeholders, the
  discipline is not yet adding value and the warning-to-failure
  ratchet should pause until the underlying signal recovers.
adoption_ladder:
  minimum_viable: |
    Schemas amended with the four optional fields; AGENTS.md per
    repo names the discipline as expected for new DECs; new DECs
    populate at author's discretion; no validator change.
  mid_adoption: |
    Validators emit a warning when a new DEC with Status: approved
    is missing any of the four fields; portfolio-status.md tracks
    the % of new DECs with all four fields populated; ~30% of new
    DECs populate all four within 60 days of the amendment.
  full_adoption: |
    Validators fail on missing fields for any new DEC with Status:
    approved; >=80% of all DECs across the portfolio carry the four
    fields; the discipline is referenced in onboarding docs and PR
    review templates.
  monitoring_signals:
    - "% of new DECs with all four fields populated (tracked weekly by dec_coverage_report.py companion check)"
    - downstream amendment rate per DEC (DEC-CDCP-017 dependency graph signal)
    - transfer of principles across repos (tracked via cross-repo amends references)
    - author feedback during PR review (qualitative; surfaced via portfolio retrospectives)
---

## decision

The portfolio adopts a systems-thinking discipline for every
substantial DEC, dream candidate, and Run record. Four optional
fields — `systems_map`, `transferable_principle`,
`falsification_test`, `adoption_ladder` — land on
`ops/schemas/decision.schema.json`,
`ops/schemas/dream-output.schema.json` (under each candidate), and
`ops/schemas/run.schema.json`. The fields are optional during the
bootstrap window. Validators in each product repo emit a warning
when a new DEC with `Status: approved` is missing any of the four
fields; the warning does not fail the build. After 30 days, an
amendment DEC switches the warning to a hard failure for new DECs.

## why

The portfolio's existing artifacts capture WHAT was decided. The
rationale block names WHY at the local level. Neither names the
systemic pattern the decision exposes, the principle that would
transfer to another repo, the observation that would falsify the
decision, or the adoption ladder for landing it portfolio-wide.
The Matrix Plane and AI Brief OS chats converged independently on
this four-field shape; the discipline crystallizes that
convergence as a schema-level contract. Engineering-grade trust
depends on these dimensions being explicit, not implicit in the
rationale.

## alternatives

- Keep DECs as today and document the discipline in AGENTS.md only.
  Rejected: AGENTS.md is read-once guidance; a schema field is
  enforced every time a DEC lands. Norms that live only in prose
  drift.
- Require the four fields from day one with no warning window.
  Rejected: a hard requirement bounces every in-flight DEC branch
  and forces a backfill sweep across 19 existing CDCP DECs. The
  bootstrap-warning-then-ratchet pattern matches DEC-CDCP-019.
- Add the fields only to the decision schema and skip dream-output
  and run. Rejected: the discipline is portfolio-wide; dream
  candidates are forward-looking decisions in waiting and runs are
  the audit trail. Landing all three schemas in one DEC keeps the
  contract coherent.
- Name a richer field set (e.g. add risk_vectors or
  second_order_effects). Rejected: four fields is the smallest set
  the source chats converged on. A later DEC can widen the set
  once the discipline shows it needs more dimensions.

## the four fields

`systems_map` names the underlying system or mechanism the decision
exposes or changes. It names the systemic pattern, not just the
local concern. Example for a hypothetical factory-emits-evidence
DEC: "Producer-consumer separation in agentic pipelines — emitter
writes typed evidence, consumer reads + transforms into review
packets. Same pattern applies to any pipeline where evidence is the
join key."

`transferable_principle` names what generalizes beyond the specific
decision — the principle that applies in other contexts or repos.
Example: "Every agent-driven pipeline should emit a typed run
record + event ledger; consumers operate on the ledger, not the
raw pipeline state."

`falsification_test` names the observation or experiment that would
prove the decision wrong — the empirical condition that would
invalidate the decision. Example: "If the chaos test suite finds a
mutation class the validator does NOT catch, the typed-event-payload
claim is falsified for that class."

`adoption_ladder` is an object with four sub-fields:
`minimum_viable` (smallest useful adoption), `mid_adoption`
(incremental expansion), `full_adoption` (complete enrollment), and
`monitoring_signals` (an array of strings naming what to watch at
each step). Each rung names a concrete state the portfolio can be
in; the monitoring signals are how a future reviewer knows which
rung the portfolio currently occupies.

## ratchet plan

The four fields are optional from day one. The validator changes
land in Workflow K Phase 2 (per-repo): each product repo's DEC
validator gains a warning step that emits to stderr when a new DEC
with `Status: approved` is missing any of the four fields. The
warning step does not fail the build during the 30-day window.

After 30 days (target: 2026-06-28), an amendment DEC switches the
warning to a hard failure for new DECs. The amendment is reviewed
content, not a cron-driven auto-bump: it lands with the
portfolio-status snapshot of the actual adoption rate and any
known reasons to delay the ratchet (in-flight branches, large
backfill required, signal too noisy to call adoption real).

## coverage

R-CDCP-027 decision/dream-output/run schemas carry four optional
systems-thinking fields, R-CDCP-028 event-types.md documents the
discipline at the event-payload boundary, R-CDCP-029 DEC-CDCP-020
records the discipline contract and the 30-day amendment plan,
R-CDCP-030 adoption ladder and monitoring signals are explicit on
this DEC.

## rollback

Revert the four-field additions in `ops/schemas/decision.schema.json`,
`ops/schemas/dream-output.schema.json`, and
`ops/schemas/run.schema.json`. Drop the systems-thinking discipline
note from `ops/event-types.md`. Mark this DEC reversed. Any
product-repo validator extensions wired in Workflow K Phase 2 must
be reverted in their own follow-on amendment per repo. New DECs
continue to validate against the older schema shape; no existing
DEC carrying the four fields is invalidated by the rollback because
the fields are optional from day one.
