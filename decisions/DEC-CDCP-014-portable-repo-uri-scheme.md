---
id: DEC-CDCP-014-portable-repo-uri-scheme
spec: specs/0010-cognitive-delivery-control-plane/
requirement: R-CDCP-014
date: 2026-05-29
status: approved
reversible: true
decision: |
  The portfolio adopts a portable URI scheme for cross-repo refs in
  run-evidence artifacts. Two URI forms are defined: repo://<repo>@<sha>/<rel-path>
  for files at a specific commit in a portfolio repo, and
  artifact://<repo>/<artifact-id> for logical artifact references that
  do not resolve to a fixed file path. Producers SHOULD emit URIs in
  run-evidence ref fields (sandbox_image_ref, checkpoint_ref, evidence
  refs, packet refs) going forward. Consumers MUST accept both URI
  forms and legacy local paths during the Round 6 migration window.
alternatives:
  - label: keep absolute Windows paths in run-evidence refs
    rejected_because: |
      Codex's review of the v2 run-evidence rollout named the gap:
      sandbox_image_ref and similar fields currently emit values like
      E:/claude_code/random-apps/supplier-risk-rag-agent@<sha>, which a
      reviewer on Linux or macOS cannot open or verify. The engineering-
      grade-trust thesis is that a third party can verify what ran from
      the source-of-truth records alone; Windows-only paths break that
      property at the first cross-machine review.
  - label: normalise to POSIX absolute paths but keep filesystem semantics
    rejected_because: |
      Lowercasing the drive letter or rewriting to /e/claude_code/... is
      still machine-local. A reviewer who clones the portfolio under
      ~/work/random-apps still cannot follow the ref, and a CI runner
      with a different layout breaks the same way. The portability
      problem is the absolute prefix, not the slash direction.
  - label: emit git URLs (git+ssh://github.com/<org>/<repo>@<sha>) instead
    rejected_because: |
      Most portfolio repos are local-first and many are not yet pushed
      to a public remote. A git URL forces a network resolution step at
      review time and ties run-evidence to a hosting choice. The repo://
      scheme keeps refs symbolic against the portfolio model and lets
      the consumer resolve them against whatever portfolio_root it has
      locally. A future scheme (gh://) can layer on top without breaking
      repo://.
  - label: type one URI form (repo://) and treat artifacts as plain ids
    rejected_because: |
      Run-evidence packets already reference logical artifacts (an
      evaluation result, a generated bundle) that are not files at a
      stable path inside a repo. Without an artifact:// form, those
      refs either fall back to repo:// with a synthetic path (which
      lies about what the ref points at) or stay as untyped strings
      (which the grammar then cannot constrain). Two URI forms cover
      both shapes cleanly.
rationale: |
  Codex's independent review of the run-evidence rollout flagged
  "replace local paths with portable refs" as a load-bearing follow-up.
  The maintainer's engineering-grade standard is that a third party
  should be able to verify what ran from the source-of-truth records
  alone. Absolute Windows paths in sandbox_image_ref and adjacent fields
  fail that standard at the first cross-machine review: a reviewer on
  Linux cannot even open E:/claude_code/random-apps/<repo>@<sha>, let
  alone verify the commit it claims.

  A portable URI scheme closes the gap at the schema boundary. The
  repo:// form names a file by repo, commit, and relative path; the
  consumer resolves it against whatever portfolio_root it has locally.
  The <sha> is advisory metadata that lets replay commands verify the
  ref still points at the expected commit. The artifact:// form covers
  logical refs that do not map to a fixed file path; the consumer
  treats them as opaque ids unless it has an artifact resolver.

  Two URI forms beat one because run-evidence packets carry both
  shapes: filesystem refs (sandbox image, checkpoint, evidence files)
  and logical refs (eval results, generated bundles, packet outputs).
  Forcing every ref through repo:// would require synthetic paths for
  the logical refs, which lies about what the ref means. Two forms
  with one shared grammar is cheaper than one form that pretends.

  The migration is interop-tolerant on purpose. Round 6 lands emitters
  in the four product repos plus the trace-to-eval-harness packet
  generator; until every emitter has shipped, validators must keep
  accepting legacy local paths or the schema flip-day breaks every
  existing run-evidence sample at once. The interop contract is the
  explicit trade-off: producers SHOULD emit URIs going forward,
  consumers MUST accept both forms during and after migration. Future
  rounds may tighten the contract once portfolio-wide coverage is in.

  The run.schema.json and event.schema.json do not change. Their
  cross-repo refs are already opaque strings; the URI grammar is a
  string-shape contract that consumers and producers honour, not a
  schema-level constraint at the source. The pattern constraint lands
  in trace-to-eval-harness/run-evidence.schema.json in Phase 3 as an
  anyOf branch (URI pattern OR free-form path) so the packet schema
  documents the shape without breaking legacy packets.
evidence:
  - kind: doc
    ref: ops/event-types.md
  - kind: schema
    ref: ops/schemas/run.schema.json
  - kind: schema
    ref: ops/schemas/event.schema.json
  - kind: decision
    ref: DEC-CDCP-011-run-records-carry-replay-equivalence-evidence.md
  - kind: decision
    ref: DEC-CDCP-013-event-schema-enforces-typed-payloads.md
  - kind: schema
    ref: ../trace-to-eval-harness/schemas/run-evidence.schema.json
rollback: |
  Stop emitting URIs in run-evidence refs; revert producers to absolute
  local paths. Drop the URI pattern branch from the trace-to-eval-
  harness run-evidence.schema.json (Phase 3). The interop clause means
  consumers already accept both forms, so legacy local paths continue
  to validate with no schema change. Remove this DEC's mention from
  ops/event-types.md. Existing run-evidence packets that already emit
  URIs validate under the legacy free-form-path branch because the URI
  strings are themselves valid free-form path strings.
owner: editorial
---

## decision

The portfolio adopts a portable URI scheme for cross-repo refs in
run-evidence artifacts. Two URI forms are defined:

- `repo://<repo-name>@<sha>/<rel-path>` — a file at a specific commit
  in a portfolio repo.
- `artifact://<repo-name>/<artifact-id>` — a logical artifact
  reference that does not resolve to a fixed file path.

Producers SHOULD emit URIs in run-evidence ref fields
(`sandbox_image_ref`, `checkpoint_ref`, evidence refs, packet refs)
going forward. Consumers MUST accept both URI forms and legacy local
paths during the Round 6 migration window.

## alternatives

- Keep absolute Windows paths. Rejected: Windows-only paths break
  cross-machine review and contradict the engineering-grade-trust
  thesis.
- Normalise to POSIX absolute paths. Rejected: still machine-local;
  the portability problem is the absolute prefix, not the slash
  direction.
- Emit git URLs. Rejected: forces network resolution at review time
  and ties run-evidence to a hosting choice. Most portfolio repos are
  local-first.
- Type only `repo://` and leave artifacts as plain ids. Rejected:
  run-evidence already carries logical refs that do not map to a fixed
  file path; without `artifact://` those refs lose grammar coverage.

## grammar

Two URI schemes are defined for cross-repo references in run-evidence
artifacts.

`repo://<repo-name>@<sha>/<rel-path>` names a file at a specific
commit in a portfolio repo. Components:

- `<repo-name>`: lowercase kebab, matches `[a-z][a-z0-9-]*`.
- `<sha>`: full git SHA-1, matches `[a-f0-9]{40}`.
- `<rel-path>`: POSIX path relative to repo root, forward slashes, no
  leading slash.

`artifact://<repo-name>/<artifact-id>` names a logical artifact that
is not a file at a fixed path. Components:

- `<repo-name>`: same shape as above.
- `<artifact-id>`: opaque string (UUID, content hash, or scoped id).

The combined regex (Python) is:

```
^(?:repo://[a-z][a-z0-9-]*@[a-f0-9]{40}/[^\s]+|artifact://[a-z][a-z0-9-]*/[^\s]+)$
```

Examples:

```
repo://supplier-risk-rag-agent@7f0f2036e1fb4ce49dacb97c73868e937a4ce8b9/ops/runs/run-13f2a48fe8bc.json
repo://procurement-negotiation-lab@cb524eb06115a0033aca8e30f200c59c51a9f4eb/ops/event-ledger/run-cb524eb06115.jsonl
artifact://trace-to-eval-harness/eval-suite-2026-05-28-supplier-risk
```

## resolution rules

Given a URI and a `portfolio_root` (defaults to
`e:/claude_code/random-apps` on the maintainer's box; configurable on
other machines):

1. If the URI starts with `repo://`: parse `<repo>`, `<sha>`,
   `<rel-path>`. Return the local path
   `<portfolio_root>/<repo>/<rel-path>`. The `<sha>` is advisory
   metadata; the consumer may verify the current HEAD matches.
   Replay commands SHOULD verify strictly.
2. If the URI starts with `artifact://`: parse `<repo>` and
   `<artifact-id>`. Look the artifact up via an implementation-defined
   resolver. For now, consumers without a resolver treat the URI as
   opaque and do not attempt path resolution.
3. Otherwise: return the value as-is (legacy local path). This is the
   backward-compatibility branch.

## interop contract

- Consumers MUST accept both URI forms AND legacy local paths.
- Producers SHOULD emit URIs going forward (after Round 6).
- Round 6 is the migration window; later rounds may deprecate the
  legacy form once portfolio-wide emitter coverage is in place.

## migration notes

Round 6 migrates four product repos (`procurement-negotiation-lab`,
`supplier-risk-rag-agent`, `ai-field-brief`, `chip-supply-chain-map`)
plus `trace-to-eval-harness`. In each product repo, the run-evidence
emitter swaps absolute paths for `repo://` URIs and the validator
gains a URI-shape check that runs alongside the existing free-form
path check. In `trace-to-eval-harness`, the packet generator emits
URIs and the `run-evidence.schema.json` adds an `anyOf` branch
(URI pattern OR free-form path) so the packet schema documents the
shape without breaking legacy packets.

Existing run-evidence samples are regenerated under the new emitters.
Validators accept both forms during and after the migration so
samples committed before the round still validate.

`run.schema.json` and `event.schema.json` in this repo do not change.
Their cross-repo refs are opaque strings; the URI grammar lives at the
producer and consumer boundary, not at the source schema.

## follow-on

- Round 7 (CI as enforcement) adds CI checks that emitted URIs conform
  to the grammar in this DEC. The check runs against each product
  repo's recent run-evidence outputs and fails the build on a
  malformed URI.
- Round 8 (`ai-supply-chain-copilot-prd` install) adopts the URI
  scheme from day one — the new product repo ships with URI emitters
  and the validator gates on the URI grammar from its first run.
- A future DEC may tighten the producer contract from SHOULD to MUST
  and deprecate the legacy free-form-path branch once portfolio-wide
  emitter coverage is verified.

## rollback

Stop emitting URIs in run-evidence refs; revert producers to absolute
local paths. Drop the URI pattern branch from the trace-to-eval-
harness `run-evidence.schema.json` (Phase 3). The interop clause means
consumers already accept both forms, so legacy local paths continue to
validate with no schema change. Remove this DEC's mention from
`ops/event-types.md`. Existing run-evidence packets that already emit
URIs validate under the legacy free-form-path branch because the URI
strings are themselves valid free-form path strings.
