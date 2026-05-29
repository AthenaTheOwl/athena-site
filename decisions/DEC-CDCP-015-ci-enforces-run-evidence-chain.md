---
id: DEC-CDCP-015-ci-enforces-run-evidence-chain
spec: specs/0010-cognitive-delivery-control-plane/
requirement: R-CDCP-015
date: 2026-05-29
status: approved
reversible: true
decision: |
  Every CDCP repo's CI MUST gate on the run-evidence chain defined in
  this DEC. Failure of any listed gate blocks the build. The contract
  covers universal gates (schema cache freshness, voice lint, BOM
  check, spec check, decisions validation, typed event payload
  validation with Run/Event cross-checks, language test runner, packet
  generation from a canonical sample, packet validation, replay smoke)
  and repo-specific gates for trace-to-eval-harness, athena-site, and
  mcp-security-lab. The gates run on every pull_request targeting main
  and every push to main on a Linux runner with pinned Python and Node
  versions. continue-on-error and failure-tolerance escape hatches are
  forbidden on the listed gates.
alternatives:
  - label: keep CI advisory; rely on landing-time review to enforce the chain
    rejected_because: |
      Round 1-6 lands the producer + consumer + URI chain at write
      time, but subsequent drift can land via direct pushes to main
      and never trip a check. The maintainer's standard is that main
      cannot accept unverifiable work; "we reviewed it once" does not
      hold across months of direct pushes. CI is the only enforcement
      point that runs on every change without depending on reviewer
      attention.
  - label: enforce only the schema cache freshness check; treat the rest as nice-to-have
    rejected_because: |
      Schema freshness alone catches the contract drift case but
      misses the cases the v2 round was built for: typed event
      payload violations, Run/Event cross-check failures, broken
      packet generation from real ledger data, packet validation
      regressions, and replay-equivalence loss. Each of those gaps
      was named in Codex's review. Gating on the full chain is the
      point of the round.
  - label: write one monolithic CI workflow and copy it across product repos
    rejected_because: |
      Copy-paste workflows drift the moment one repo needs a slightly
      different runner version or an extra step. The contract lives
      here as a DEC; each product repo ships its own per-repo CI DEC
      that links back to this one. A shared composite action covers
      the universal gates without forcing per-repo workflow shape.
  - label: gate only on PRs, not on direct pushes to main
    rejected_because: |
      The maintainer authorizes direct pushes to main for sub-agents
      working in auto mode. A PR-only gate would let those pushes
      skip enforcement entirely, which is the exact drift case CI is
      supposed to close. Gating on both pull_request and push to main
      means the contract holds regardless of how a change lands.
rationale: |
  Codex's independent review of the v2 run-evidence rollout named the
  gap: the producer + consumer + portable-URI chain Rounds 1-6 shipped
  holds at landing time, but nothing prevents subsequent drift. A
  direct push to main can land a malformed event payload, a stale
  schema cache, a broken packet generator, or a replay regression and
  no automated check will catch it. The maintainer's framing was the
  decision driver: "main cannot accept unverifiable work."

  CI is the enforcement point. Every push and every PR runs the same
  set of gates against the same source-of-truth records, and any gate
  failure turns the build red. The gates are not new validators; they
  are the validators that already exist in the portfolio, wired up so
  they run on every change without depending on reviewer attention.
  Schema cache freshness catches schema drift between athena-site and
  the consumers. Typed event payload validation catches the cases
  DEC-CDCP-013 added the oneOf branches for. Run/Event cross-checks
  catch the cases DEC-CDCP-011's replay-equivalence fields exist for.
  Packet generation from a canonical sample catches the case where
  trace-to-eval-harness can no longer read the producer's output.
  Packet validation catches review-boundary schema regressions.
  Replay smoke catches the case where a sandbox image SHA stops
  producing the run it claims to.

  Together, the gates close the loop the v2 chain opened. Without CI
  the loop holds only at the moment of landing; with CI the loop
  holds every time a change touches main. That is the jump from "we
  have artifacts" to "main cannot accept unverifiable work."

  The contract lives in this DEC, not in a single workflow file,
  because product repos differ in language stack (Python-only, mixed
  Python + Node, etc.) and runner needs. Each product repo ships a
  per-repo CI DEC (Phase 2) that adopts this contract and a workflow
  file that implements it. A shared composite action in this repo
  covers the universal gates so per-repo workflows stay thin; repos
  that need extra steps wrap the composite action with their own
  steps before and after.
evidence:
  - kind: doc
    ref: ops/event-types.md
  - kind: schema
    ref: ops/schemas/event.schema.json
  - kind: schema
    ref: ops/schemas/run.schema.json
  - kind: decision
    ref: DEC-CDCP-011-run-records-carry-replay-equivalence-evidence.md
  - kind: decision
    ref: DEC-CDCP-013-event-schema-enforces-typed-payloads.md
  - kind: decision
    ref: DEC-CDCP-014-portable-repo-uri-scheme.md
  - kind: schema
    ref: ../trace-to-eval-harness/schemas/run-evidence.schema.json
rollback: |
  Relax the contract by issuing an amending DEC that downgrades any
  blocking gate to advisory (continue-on-error: true) or removes it
  outright. Existing product-repo workflows continue to run; the gates
  that get downgraded stop blocking the build but still surface
  findings. To roll back entirely, mark this DEC superseded by a
  later DEC and drop the shared composite action from
  .github/actions/run-evidence-gates/. Per-repo CI DECs in product
  repos can stay as documentation of the historical contract.
owner: editorial
---

## decision

Every CDCP repo's CI MUST gate on the run-evidence chain defined in
this DEC. Failure of any listed gate blocks the build. The gates run
on every `pull_request` targeting `main` and every `push` to `main`
on a Linux runner with pinned Python and Node versions.
`continue-on-error: true` and `if: ${{ failure() }}` escape hatches
on the listed gates are forbidden.

## alternatives

- Keep CI advisory and rely on landing-time review. Rejected: direct
  pushes to main bypass review entirely; the maintainer's standard is
  that main cannot accept unverifiable work.
- Enforce only schema cache freshness. Rejected: misses typed event
  payload validation, Run/Event cross-checks, packet generation,
  packet validation, and replay smoke — the cases Codex's review
  flagged.
- Copy one monolithic workflow across repos. Rejected: copy-paste
  drift. The contract lives here; each product repo ships a per-repo
  CI DEC and workflow that adopts it.
- Gate only on PRs. Rejected: sub-agents in auto mode push directly
  to main; PR-only gating would let those pushes skip enforcement.

## the CI contract

### universal gates (apply to every repo with run-evidence)

1. **schema-cache-freshness** — `python scripts/check_schema_cache_freshness.py`
   exits 0. Catches schema drift between athena-site and the
   consumers' `ops/schemas-cache/` copies.
2. **voice-lint** — `python scripts/voice_lint.py` clean. Public-facing
   copy stays within the editorial voice contract.
3. **bom-check** — `python scripts/check_no_bom.py` OK. No UTF-8 BOM
   in tracked text files.
4. **spec-check** — `python scripts/spec_check.py` OK. Spec ledger
   shape holds.
5. **decisions-validation** — `python scripts/validate_decisions.py` OK
   (where the script is present). Every DEC's frontmatter validates
   against `ops/schemas/decision.schema.json`.
6. **typed-event-payload-validation** — `python scripts/validate_run_evidence.py`
   exits 0. Validates the JSONL ledger entries against the typed
   `event.schema.json` (the DEC-CDCP-013 oneOf discriminator) AND
   runs the Round 3 Run/Event cross-checks (hash agreement,
   `fields_populated` agreement, `gate_results_summary` scan).
7. **language-test-runner** — `pytest` (Python) or `npm test`
   (TypeScript) exits 0.
8. **packet-generation-from-canonical-sample** (product repos only) —
   the workflow checks out `trace-to-eval-harness` as a sibling,
   pip-installs it, then runs
   `python -m trace_to_eval evidence from-cdcp-events ops/event-ledger/<canonical-sample>.jsonl --out /tmp/packet.json`.
   Must exit 0.
9. **packet-validation** (product repos only) —
   `python -m trace_to_eval evidence validate /tmp/packet.json` exits 0.
10. **replay-smoke** (product repos only) — extract the sandbox SHA
    from the canonical sample's Run record
    (`jq -r .sandbox_image_ref ops/run-records/<sample>.json` plus
    a `[a-f0-9]{40}` regex extract). Run
    `git checkout <sandbox-sha>` and
    `python scripts/replay_run.py --run-id <sample>`. Must exit 0
    with `replay_equivalent: true`.

### trace-to-eval-harness-specific gates

11. **all-example-packets-validate** — for each
    `examples/run_evidence/*.packet.json`, run
    `python -m trace_to_eval evidence validate <path>`. All exit 0.
12. **uri-resolver-tests** — `pytest tests/test_uri.py
    tests/test_run_evidence.py` covering the Round 6 URI handling.

### athena-site-specific gates

13. **dec-frontmatter-validation** — every DEC's frontmatter matches
    `ops/schemas/decision.schema.json`.
14. **ops-doc-link-integrity** — `ops/event-types.md` references
    valid DEC files.

### mcp-security-lab-specific gates

15. **mcp-surface-drift** — `python scripts/validate_athena_mcp_surface.py`
    exits 0. Requires a sibling `athena-site` checkout; the workflow
    sets that up.

### CI environment expectations

- Linux runner (`ubuntu-latest`). Products MUST work on Linux
  regardless of dev OS.
- Python 3.11+ (specify the minor version explicitly in the
  workflow).
- Node 20+ where needed (`chip-supply-chain-map`, `ai-field-brief`,
  `trace-to-eval-harness`).
- All gates run on `pull_request` events targeting `main` AND
  `push` events to the `main` branch.
- Optional: a cron schedule for a daily smoke run.

### forbidden patterns

- `continue-on-error: true` on any gate listed above. Defeats the
  point of CI as the enforcement gate.
- `if: ${{ failure() }}` to mark a gate as informational. Gates
  must block.
- Path filters that skip a gate run when files outside the filter
  change but the gate would still catch a real failure.

## migration notes

Phase 2 of Round 7 rolls the contract across the four product repos
(`procurement-negotiation-lab`, `supplier-risk-rag-agent`,
`ai-field-brief`, `chip-supply-chain-map`) plus
`trace-to-eval-harness`. Each repo gets its own per-repo CI DEC that
links back to `DEC-CDCP-015` and a workflow file that implements the
contract. Per-repo DECs name the canonical sample the workflow runs
gates 8-10 against and any repo-specific extensions.

A shared composite action lives at
`.github/actions/run-evidence-gates/action.yml` in this repo. Product
repos can reference it as
`uses: AthenaTheOwl/athena-site/.github/actions/run-evidence-gates@main`
with `canonical-sample` and `python-version` inputs. Repos that need
extra steps wrap the composite action with their own steps before
and after.

## trade-offs

CI runs cost wall-clock minutes per push, and some gates (packet
generation from a sample, replay smoke) require checking out a
sibling repo and possibly pip-installing it. That cost is the price
of engineering-grade trust: the alternative is letting drift land
silently because no human reviewed it. The composite action keeps
per-repo workflows thin so the cost is in CI runtime, not in
maintenance burden.

## follow-on

- Phase 2 lands the per-repo CI DECs and workflows in the four
  product repos and `trace-to-eval-harness`.
- Round 8 brings `ai-supply-chain-copilot-prd` onto the grid; the
  same CI contract installs there from day one.
- A future DEC may add gates as new validators ship (e.g., a
  cross-repo evidence trail check once an artifact resolver lands).

## rollback

Issue an amending DEC that downgrades any blocking gate to advisory
or removes it. Existing product-repo workflows continue to run; the
downgraded gates surface findings without blocking. To roll back
entirely, mark this DEC superseded by a later DEC and drop the
shared composite action from `.github/actions/run-evidence-gates/`.
Per-repo CI DECs in product repos can stay as documentation of the
historical contract.
