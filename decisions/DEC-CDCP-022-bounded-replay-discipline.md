---
id: DEC-CDCP-022-bounded-replay-discipline
spec: specs/0010-cognitive-delivery-control-plane/
requirement: R-CDCP-035..038
date: 2026-05-30
status: approved
reversible: true
amends: DEC-CDCP-011-run-records-carry-replay-equivalence-evidence
decision: |
  The portfolio adopts "bounded replay with evidence capture" as the
  canonical framing for run-evidence work — replacing "deterministic
  replay" and "replay-equivalence" in any new artifact. Two new
  policies land under `ops/policies/`:
  `replay-acceptance-v1.yaml` names the required fields, checks,
  warnings, and three-state verdict set (PASS / INVESTIGATE / BLOCK)
  for accepting a replay; `runtime-lockin-v1.yaml` names the guard
  that keeps the evidence contract owned by the control plane while
  vendor runtimes supply execution substrate. This DEC amends
  DEC-CDCP-011 by sharpening the wording, not by changing the
  underlying run-evidence shape; the six fields landed there remain
  the source of truth. New artifacts cite the policies; existing
  artifacts can keep their wording until they are otherwise touched.
alternatives:
  - label: keep "deterministic replay" wording and add nothing
    rejected_because: |
      "Deterministic" implies a guarantee the substrate does not
      provide. Exact determinism requires frozen prompts, frozen
      model and version, frozen sandbox image, frozen dependency
      versions, mounted files preserved, network state pinned,
      random seeds pinned, and tool side effects reproducible. The
      OpenAI Agents SDK substrate (and any analog) emits capture +
      resume evidence; the control plane decides whether the
      captured evidence is valid enough for CI. Calling that
      "deterministic" overclaims; calling it "bounded replay with
      evidence capture" names what actually holds.
  - label: rewrite DEC-CDCP-011 in place to use the new framing
    rejected_because: |
      DEC-CDCP-011 is an approved decision in the ledger. Editing
      its body would erase the record of how the framing evolved
      and break the audit trail other DECs cite. The amendment
      pattern (a sibling DEC with `amends:`) is the contract every
      other DEC in the portfolio follows; doing it again here is
      the consistent move. The wording in DEC-CDCP-011 stands as
      written; this DEC names the sharper framing for new work.
  - label: encode the acceptance policy as an OPA-shaped permission rule
    rejected_because: |
      The existing `ops/schemas/policy.schema.json` shape is
      OPA-style — applies_to / decision / conditions / priority —
      built for runtime permission evaluation. Replay acceptance is
      a verdict over an evidence bundle, not a permission check on
      a request. Forcing the acceptance criteria into the OPA shape
      would distort both the schema and the policy. The two YAMLs
      here stand as advisory documents; a later DEC can extend or
      add a sibling schema once the acceptance verdict has a
      validator script reading it.
  - label: skip the runtime-lockin policy and rely on per-adapter review
    rejected_because: |
      Per-adapter review is one author noticing one bad copy at a
      time. The lockin risk is structural: a vendor SDK ships an
      evidence-shaped object, an author serializes it directly into
      a Run record to save work, and the evidence schema quietly
      becomes a function of that vendor's API. A written policy
      with named guards turns the structural risk into a checkable
      item at review time and at the quarterly audit.
rationale: |
  The ChatGPT chat on 2026-05-30 distilled the OpenAI Agents SDK
  substrate plus its sandbox semantics into a precise wording
  correction: avoid "deterministic replay"; prefer "bounded replay
  with evidence capture" or "replayable evidence package." Exact
  determinism requires too many frozen inputs to be a contract the
  substrate can keep. The control plane can, however, contract on
  the shape of captured evidence and the verdict over that shape.

  The wording change is precision, not retreat. The original
  DEC-CDCP-011 framing ("replay-equivalence evidence") was a
  reasonable first cut; six rounds of substrate work since then
  surfaced gotchas the original wording papers over. The most
  load-bearing of those: mounted paths may not be copied into
  workspace snapshots — the sandbox client treats them as
  ephemeral entries — so a captured "snapshot" of a run that
  mounted remote storage does not contain that storage. A reviewer
  who reads "deterministic replay" and assumes the snapshot is
  self-contained will be wrong; a reviewer who reads "bounded
  replay with evidence capture" knows to check what the bound is.

  The runtime-lockin policy is the structural complement. Vendor
  runtimes (OpenAI Agents SDK today, Anthropic / Claude Code /
  local stub tomorrow) supply execution substrate. The evidence
  shape — what a Run record carries, what the manifest schema
  requires, what the event ledger emits — is owned by the control
  plane. If the evidence schema drifts to track a vendor's SDK
  vocabulary, the contract becomes a function of that vendor's
  release notes. The policy names three guards that surface that
  drift at review time and at quarterly audit.
trade_off: |
  Adding a fourth framing term to the portfolio (after
  "replay-equivalence" in DEC-CDCP-011 and "sandbox manifest" in
  DEC-CDCP-021) costs author attention. New DECs must reach for the
  right vocabulary; cross-references must use the term the cited
  DEC actually used. The amendment pattern does not erase the
  older wording; readers will see both phrasings in the ledger
  until older artifacts are touched for other reasons. The
  mitigation: the two policies are short, the DEC names the
  preferred wording explicitly, and the wording lives in writing
  rather than in tacit author memory.

  The policy files are advisory text rather than schema-validated
  documents. The existing `ops/policies/` directory does not exist
  before this DEC, and no validator reads the YAMLs at commit
  time. A later DEC can land a `replay-acceptance.schema.json`
  sibling that turns the verdict set into a typed contract; until
  then, the policies stand as documentation a human reviewer
  consults, and the warning shape (mounted paths, bitwise drift,
  runtime lockin) is the operative content even without an
  enforcer.
evidence:
  - kind: decision
    ref: DEC-CDCP-011-run-records-carry-replay-equivalence-evidence.md
  - kind: decision
    ref: DEC-CDCP-021-sandbox-manifest-and-agent-runtime-adapter.md
  - kind: doc
    ref: ops/policies/replay-acceptance-v1.yaml
  - kind: doc
    ref: ops/policies/runtime-lockin-v1.yaml
  - kind: doc
    ref: ops/schemas/sandbox-manifest.schema.json
  - kind: doc
    ref: ops/schemas/run.schema.json
coverage:
  - R-CDCP-035
  - R-CDCP-036
  - R-CDCP-037
  - R-CDCP-038
rollback: |
  Delete `ops/policies/replay-acceptance-v1.yaml`. Delete
  `ops/policies/runtime-lockin-v1.yaml`. Remove the
  `ops/policies/` directory if no other policy has landed.
  Mark this DEC reversed. DEC-CDCP-011 is unaffected by the
  reversal because the amendment never altered its body —
  the older wording ("replay-equivalence") becomes the
  canonical phrasing again. No Run record, no manifest, and
  no event-ledger entry is invalidated by the rollback; the
  policies are advisory and have no validator dependency.
owner: governance.cdcp-curator
systems_map: |
  Wording is part of the contract. "Deterministic" implies a
  guarantee the substrate does not provide; "bounded replay with
  evidence capture" names the actual property — sufficient
  evidence to validate-and-accept, not byte-for-byte reproduction.
  The control plane owns the evidence shape and the verdict over
  it; the vendor runtime supplies execution substrate. The two
  policies land that separation as written guards at review and
  audit boundaries.
transferable_principle: |
  When the substrate cannot guarantee a property, the contract
  should claim what is actually emitted (evidence) rather than
  what the substrate hopes for (determinism). This generalizes to
  any multi-vendor portfolio where a single vendor's runtime
  semantics could otherwise become the source of truth; the
  evidence-shape contract is the cross-vendor boundary.
falsification_test: |
  If four weeks of portfolio replays produce zero INVESTIGATE
  verdicts and 100% PASS, the policy is either trivial (warnings
  never fire) or the bar is too low. A healthy distribution has
  some INVESTIGATE verdicts surfacing mounted-path drift,
  bitwise non-determinism, or runtime-specific semantics. A
  flatter signal than that means the policy is decorative and
  needs sharpening.
adoption_ladder:
  minimum_viable: |
    Policies committed under `ops/policies/`; this DEC published
    with `amends: DEC-CDCP-011`; new artifacts that touch
    run-evidence use the "bounded replay" framing.
  mid_adoption: |
    Existing artifacts amended to cite `replay-acceptance-v1`
    when they touch replay; validators in product repos emit
    INVESTIGATE verdicts where applicable; portfolio-status
    surfaces the verdict mix.
  full_adoption: |
    Every run-evidence producer emits a verdict aligned to
    `replay-acceptance-v1`; the mounted-path warning fires on
    any run that mounts remote storage; the runtime-lockin
    guard is checked at quarterly audit and on any new runtime
    adapter landing.
  monitoring_signals:
    - "% of new DECs using the 'bounded replay' framing"
    - INVESTIGATE verdict rate per week across portfolio replays
    - mounted-path warning frequency on runs that mount remote storage
    - count of vendor-specific evidence fields surfaced by the lockin guard
---

## decision

The portfolio adopts "bounded replay with evidence capture" as the
canonical framing for run-evidence work, replacing "deterministic
replay" and "replay-equivalence" in any new artifact. Two new
policies land under `ops/policies/`:
`replay-acceptance-v1.yaml` names the required fields, checks,
warnings, and three-state verdict set (PASS / INVESTIGATE / BLOCK)
for accepting a replay; `runtime-lockin-v1.yaml` names the guard
that keeps the evidence contract owned by the control plane while
vendor runtimes supply execution substrate. This DEC amends
DEC-CDCP-011 by sharpening the wording; the six run-evidence
fields landed there remain the source of truth.

## why

The ChatGPT chat on 2026-05-30 distilled the OpenAI Agents SDK
substrate plus its sandbox semantics into a precise wording
correction. Exact determinism requires frozen prompts, frozen
model and version, frozen sandbox image, frozen dependency
versions, mounted files preserved, network state pinned, random
seeds pinned, and tool side effects reproducible — too many
inputs for the substrate to contract on. The substrate emits
capture + resume evidence; the control plane decides whether the
captured evidence is valid enough for CI. "Bounded replay with
evidence capture" names what actually holds; "deterministic
replay" overclaims.

The wording change is precision, not retreat. DEC-CDCP-011's
"replay-equivalence" framing was a reasonable first cut; six
rounds of substrate work since then surfaced gotchas the original
wording papers over.

## the most load-bearing gotcha

Mounted paths may not be copied into workspace snapshots. The
sandbox client docs note that mounted paths can be treated as
ephemeral workspace entries; snapshot and persistence flows may
detach or skip mounted remote storage rather than copying it into
the saved workspace. A captured snapshot of a run that mounted
remote storage does not, then, contain that storage. The warning
is named explicitly in `replay-acceptance-v1.yaml`
(`mounted_remote_paths_may_not_be_copied_into_snapshots`) so a
reviewer reading a replay verdict knows to check what the bound
is.

## the two policies

`replay-acceptance-v1.yaml` names seven required fields
(`run_state_ref`, `source_registry_version`, `prompt_lens_versions`,
`artifact_hashes`, `tool_call_log`, `validation_result`,
`source_refs_for_published_claims`), seven checks, three
warnings, and a three-state verdict set:

- PASS: all required fields present AND all checks pass
- INVESTIGATE: any check yields a warning OR any optional field absent that would aid replay
- BLOCK: any required field missing OR any check fails

`runtime-lockin-v1.yaml` names the principle (the control plane
owns the evidence schema; the vendor runtime supplies execution
substrate), three guards
(`vendor_specific_run_state_must_be_wrapped_in_portable_evidence`,
`non_OAI_runtimes_must_produce_the_same_evidence_shape_as_OAI`,
`sandbox_session_state_is_metadata_not_authority`), and two
review triggers (quarterly audit; on-new-runtime-adapter parity
check).

## scope

`replay-acceptance-v1` applies to agent runs producing
committable artifacts (briefs, code patches, packets, review
bundles). It does not apply to ephemeral chat sessions where no
artifact lands in a repo. `runtime-lockin-v1` applies any time a
runtime adapter is added or modified, and at quarterly portfolio
audit.

## relationship to DEC-CDCP-011 and DEC-CDCP-021

DEC-CDCP-011 named the six run-evidence fields on
`run.schema.json` (`prompt_snapshot_hash`,
`tool_schemas_snapshot_hash`, `determinism`, `checkpoint_ref`,
`sandbox_image_ref`, `gate_results_summary`). DEC-CDCP-021 added
`sandbox_manifest_ref` and a sibling
`sandbox-manifest.schema.json`. This DEC sharpens the framing
those fields advance — the fields are what is captured; the
acceptance policy is the verdict over the capture — and adds the
runtime-lockin guard so the evidence shape does not drift to
track a vendor's SDK.

## coverage

R-CDCP-035 bounded-replay framing adopted as canonical wording;
R-CDCP-036 `replay-acceptance-v1.yaml` lands the required fields,
checks, warnings, and three-state verdict set; R-CDCP-037
`runtime-lockin-v1.yaml` lands the control-plane-owns-evidence
guard; R-CDCP-038 DEC-CDCP-022 records the framing change with
all four systems-thinking fields populated.

## rollback

Delete `ops/policies/replay-acceptance-v1.yaml`. Delete
`ops/policies/runtime-lockin-v1.yaml`. Remove the `ops/policies/`
directory if no other policy has landed. Mark this DEC reversed.
DEC-CDCP-011 is unaffected by the reversal because the amendment
never altered its body — the older wording ("replay-equivalence")
becomes the canonical phrasing again. No Run record, no manifest,
and no event-ledger entry is invalidated by the rollback; the
policies are advisory and have no validator dependency.
