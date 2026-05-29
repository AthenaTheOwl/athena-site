---
id: DEC-CDCP-019-dec-test-coverage-report
spec: specs/0010-cognitive-delivery-control-plane/
requirement: R-CDCP-025..026
date: 2026-05-29
status: approved
reversible: true
decision: |
  athena-site emits a portfolio-wide DEC test-coverage report
  (`scripts/dec_coverage_report.py`) that walks each active CDCP
  repo's `decisions/` directory, extracts each DEC's `requirement:`
  ids (with range and list expansion), folds in any allowlisted ids
  that the spec-check allowlist notes as resolved by a named DEC,
  and searches that repo's test surface for any reference to those
  requirement ids. A DEC counts as covered when at least one of its
  requirement ids appears in any discovered test file. The report
  lands at `ops/dec-coverage-report.md` with per-repo totals plus an
  uncovered-DEC breakdown. The script exits 0 when portfolio
  coverage clears `--threshold` (default 5%, bootstrap) and exits 1
  otherwise. The `Portfolio audit` workflow runs the script weekly
  alongside the other portfolio audits with `continue-on-error:
  false` — the coverage gate is a real contract. The 5% floor
  ratchets up by 10pp per quarter via DEC amendment as repos add
  R-* references to test files.
alternatives:
  - label: skip the report and rely on per-repo spec_check.py
    rejected_because: |
      `spec_check.py` answers "does every R-* requirement have a
      DEC?" — the inverse question. It does not look at tests at
      all. Coverage is the gap the new report exists to close: a
      DEC can be approved and shipped without any test ever
      naming the requirement, and no existing check would notice.
      The portfolio audit is the right home for the cross-repo
      view; piggybacking one more report on the weekly run costs
      one step and one file.
  - label: parse the test files for DEC ids instead of R-* ids
    rejected_because: |
      DEC ids drift over time (slugs change, families are
      renamed); R-* ids are the stable contract. Searching by R-*
      gives the report a steady anchor across repos, and is
      consistent with the spec_check rule that R-* ids must
      resolve to DECs. A future amendment can widen the search to
      include DEC ids if the R-* coverage proves too narrow.
  - label: require every DEC to ship a test in the same commit
    rejected_because: |
      The portfolio includes governance DECs (cdcp-governance
      install, voice-lint contract, narrative decisions) where
      "the test" is a structural check or a manual review, not a
      Python unit test. A hard "test required" rule would either
      bounce legitimate governance DECs or force test-shaped
      placeholders that add no signal. The coverage report names
      the gaps; whether each gap warrants a test is a per-DEC
      review call.
  - label: keep the original 70% aspirational threshold with
      continue-on-error
    rejected_because: |
      A 70% target failing weekly with `continue-on-error: true`
      trains the maintainer to ignore the step. A real gate at a
      truthful floor (5%, just above today's ~1.7%) keeps the
      contract honest: the build fails when coverage regresses
      below floor, and the floor ratchets up by 10pp per quarter
      via DEC amendment. The contract gates real movement instead
      of advertising an unreachable goal.
  - label: ratchet automatically without DEC amendment
    rejected_because: |
      Each ratchet is a portfolio-wide governance change: it
      shortens slack for every active CDCP repo and may force test
      additions before a release. That belongs in a reviewed DEC,
      not in a cron-driven auto-bump. The amendment-per-quarter
      cadence forces a 30-second human read every three months
      and keeps the ledger honest about what changed and why.
rationale: |
  DEC-CDCP-002 records that decisions are validated against the
  schema. DEC-CDCP-016 records the portfolio dashboard. Neither
  asks the test-coverage question. A DEC can be approved, merged,
  and never touched by a test naming its requirement, and the
  portfolio has no visibility into that drift. The coverage report
  closes the loop: each repo's tests/, scripts/test_*.py, and
  co-located *.test.ts files are scanned for the R-* ids attached
  to each DEC, and the portfolio rollup reports the percentage.

  The probe is deliberately permissive: any substring match counts.
  R-* ids are sufficiently unique that incidental collisions are
  rare, and a stricter pattern (e.g. `# requires: R-X-001` magic
  comments) would force a portfolio-wide convention before any
  signal is visible. Starting with a low bar surfaces the real gap
  first; a follow-on DEC can tighten the contract once the
  baseline is known.

  The allowlist-aware step matters because many R-* ids resolve to
  a single collective DEC: the spec-check allowlist already names
  those pairings in its `note:` field. The coverage report mines
  the note to attach those ids to the right DEC, so the
  collective-coverage DECs do not show as uncovered just because
  their primary R-* lives in the allowlist.
trade_off: |
  The 5% bootstrap threshold sits just above today's portfolio
  coverage floor (~1.7%). It is honest about the current state and
  still acts as a real contract: the audit workflow runs the script
  with `continue-on-error: false`, so a regression below floor
  red-Xes the weekly run. The ratchet plan adds 10pp per quarter
  via DEC amendment as repos add R-* references to their tests
  (Workflow G Phase 2 is the first such lift). Each ratchet is a
  reviewed governance change, not an automatic bump, so the floor
  only rises when the portfolio has the slack to absorb it. A naive
  substring search may also produce false positives (an R-* id that
  appears in a comment unrelated to a real test of that
  requirement). Across the portfolio R-* ids are unique enough that
  this risk is small, and the alternative — a stricter contract —
  would force a convention nobody has agreed to yet.
evidence:
  - kind: doc
    ref: scripts/dec_coverage_report.py
  - kind: doc
    ref: tests/test_dec_coverage_report.py
  - kind: doc
    ref: .github/workflows/portfolio-audit.yml
  - kind: doc
    ref: ops/dec-coverage-report.md
  - kind: decision
    ref: DEC-CDCP-016-portfolio-status-dashboard.md
  - kind: decision
    ref: DEC-CDCP-017-dec-dependency-graph-generator.md
  - kind: decision
    ref: DEC-CDCP-018-evidence-quorum-sentinel.md
coverage:
  - R-CDCP-025
  - R-CDCP-026
rollback: |
  Delete `scripts/dec_coverage_report.py`,
  `tests/test_dec_coverage_report.py`, and
  `ops/dec-coverage-report.md`. Revert the
  `Run DEC coverage report` step in
  `.github/workflows/portfolio-audit.yml` and drop the report from
  the commit step. Mark this DEC reversed. The other audit
  artifacts continue to run exactly as before.
owner: governance.cdcp-curator
---

## decision

athena-site runs a DEC test-coverage report
(`scripts/dec_coverage_report.py`) that walks every active CDCP
repo's `decisions/` ledger, extracts each DEC's `requirement:` ids
(supporting `R-FAM-NNN`, `R-FAM-NNN..MMM` ranges, and YAML lists),
folds in any allowlist-deferred ids whose note text names the DEC
collectively responsible for them, and searches the repo's test
files (`tests/` recursively, top-level `scripts/test_*.py`, and
co-located `*.test.ts`/`*.spec.ts` under `src/`) for any reference
to those ids. A DEC counts as covered when at least one of its
requirement ids appears in any discovered test. The script writes
`ops/dec-coverage-report.md` with per-repo totals plus an
uncovered-DEC breakdown, and exits 0 when portfolio coverage clears
`--threshold` (default 5%, bootstrap). The bootstrap floor ratchets
up by 10pp per quarter via DEC amendment as portfolio coverage
climbs.

## why

DEC-CDCP-016 records the portfolio status dashboard; DEC-CDCP-017
the DEC dependency graph; DEC-CDCP-018 the evidence quorum
sentinel. None of those answers "does each shipped DEC have a test
that names its requirement?". A DEC can be approved and merged
without ever being touched by a test, and today there is no probe
that surfaces the gap. The coverage report closes that loop and
ships the result alongside the other portfolio audits.

## alternatives

- Skip the report and rely on per-repo `spec_check.py`. Rejected:
  spec_check answers the inverse question (every R-* has a DEC)
  and never looks at tests.
- Search for DEC ids instead of R-* ids. Rejected: R-* ids are the
  stable contract; DEC slugs drift.
- Require every DEC to ship a test in the same commit. Rejected:
  governance DECs do not always have a Python test surface; a
  hard rule would force placeholder tests.
- Keep the 70% aspirational threshold with `continue-on-error:
  true`. Rejected: a permanently failing step trains the
  maintainer to ignore the alert. A truthful 5% floor with a
  quarterly 10pp ratchet keeps the gate real and the goal
  reachable.
- Ratchet automatically without a DEC amendment. Rejected: each
  ratchet shortens slack across every active CDCP repo and
  belongs in a reviewed governance change, not a cron-driven
  auto-bump.

## probe contract

For each active CDCP repo declared in `ops/portfolio-manifest.yml`
(plus the two named in the task — `trace-to-eval-harness` and
`mcp-security-lab` — even when they fall outside the manifest's
active set):

1. Walk `<repo>/decisions/DEC-*.md` and parse the YAML
   front-matter.
2. Extract the `requirement:` value and expand it into one or
   more R-* ids (`R-FAM-NNN`, `R-FAM-NNN..MMM`, or list).
3. Read `<repo>/decisions/.spec-check-allowlist.yaml`; for every
   `deferred:` entry whose `note:` text names a `DEC-FAM-NNN[-slug]`
   that is present in the repo, attach the allowlisted R-* id to
   that DEC.
4. Discover test files under `<repo>/tests/` (recursive),
   `<repo>/scripts/test_*.py`, and co-located `*.test.ts` /
   `*.spec.ts` / `*_test.py` under `<repo>/src/`. Skip
   `node_modules`, `dist`, `__pycache__`, `.venv`, `build`.
5. For each DEC, mark covered when at least one of its
   requirement ids appears as a substring in any discovered test
   file's contents.
6. Tally per-repo: total / covered / uncovered / coverage %.
   Portfolio coverage is the sum of per-repo covered over total.
7. Exit 0 when portfolio coverage clears `--threshold` (default
   5%, bootstrap); exit 1 otherwise. Repos not checked out under
   `local_root` contribute zero DECs and render as `skipped`.

## trade-offs

The 5% bootstrap threshold sits just above today's portfolio
coverage floor (~1.7%). It is truthful about the current state
and still acts as a real contract: the audit workflow runs the
script with `continue-on-error: false`, so a regression below
floor red-Xes the weekly run. The ratchet plan adds 10pp per
quarter via DEC amendment as repos add R-* references to their
tests; each ratchet is a reviewed governance change rather than
an automatic bump, so the floor only rises when the portfolio has
slack to absorb it. A naive substring match can yield false
positives; R-* ids are unique enough across the portfolio that
this risk is small, and a stricter contract (magic comments,
structured annotations) would force a portfolio-wide convention
before any signal is visible.

## ratchet plan

The threshold lives in three places (script default,
`portfolio-audit.yml` step argument, this DEC's trade-off and
decision blocks). Each quarterly ratchet is one DEC amendment
that updates all three together:

- Q3 2026 (after Workflow G Phase 2 lifts coverage): 15%
- Q4 2026: 25%
- Q1 2027: 35%
- onward: +10pp per quarter until the portfolio sustains 70%

An amendment may skip or compress steps when coverage outruns the
schedule, or pause when a repo onboards a large new DEC family.
The amendment is the reviewed signal; the cron is not allowed to
ratchet on its own.

## CI wiring

`.github/workflows/portfolio-audit.yml` runs the script after the
DEC dependency graph step. The job uses `continue-on-error:
false` so the gate is a real contract: a regression below the
current floor fails the weekly run. The commit step adds
`ops/dec-coverage-report.md` to its `git add` list so the
regenerated report lands with the other audit outputs. On CI only
athena-site is checked out, so sibling repos render as
`skipped`; the portfolio coverage figure in the CI run reflects
athena-site alone.

## coverage

R-CDCP-025 portfolio DEC coverage report exists,
R-CDCP-026 audit workflow regenerates the report weekly.

## rollback

Delete `scripts/dec_coverage_report.py`,
`tests/test_dec_coverage_report.py`, and
`ops/dec-coverage-report.md`. Revert the `Run DEC coverage report`
step in `.github/workflows/portfolio-audit.yml` and drop the
report from the commit step. Mark this DEC reversed. The other
audit artifacts continue to run exactly as before.
