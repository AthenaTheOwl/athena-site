---
id: DEC-CDCP-018-evidence-quorum-sentinel
spec: specs/0010-cognitive-delivery-control-plane/
requirement: R-CDCP-022..024
date: 2026-05-29
status: approved
reversible: true
decision: |
  athena-site runs an evidence quorum sentinel
  (`scripts/evidence_quorum_sentinel.py`) that fails the
  `Portfolio audit` workflow when any active product repo has fewer
  than N replay artifacts in the last 30 days. The default quorum is
  N=1 per repo per 30-day window. The watched product repos are
  `chip-supply-chain-map`, `supplier-risk-rag-agent`,
  `procurement-negotiation-lab`, and `ai-field-brief`. The sentinel
  writes `ops/evidence-quorum-report.md` with per-repo counts and a
  pass/fail status, and the audit workflow commits the report
  alongside the other audit outputs.
alternatives:
  - label: skip the sentinel and trust that replay tooling will be re-run when needed
    rejected_because: |
      The replay-equivalence claim in DEC-CDCP-011 only holds while
      replay records keep landing. A repo can pass every CI gate
      today, ship no replays for a month, and silently drop out of
      the evidence chain. No existing check looks for that drift. The
      audit workflow already runs weekly; piggybacking a sentinel on
      it costs one step and one report file.
  - label: enforce a stricter quorum, such as N=5 in 7 days
    rejected_because: |
      The product repos do not yet ship replays on a steady weekly
      cadence; a stricter quorum would fail the workflow during
      ordinary quiet weeks and train the maintainer to ignore the
      alert. N=1 in 30 days is the floor: a repo that ships zero
      replays in a month has effectively dropped its replay habit
      and the audit should say so. The threshold and window are CLI
      flags so a later DEC can ratchet them up once the cadence is
      established.
  - label: write per-repo sentinels inside each product repo
    rejected_because: |
      Per-repo sentinels solve a different problem: they catch
      regressions within one repo. Quorum spans repos. The sentinel
      must see all four product repos at once to answer whether the
      portfolio still has a live replay-equivalence chain. A central
      sentinel in athena-site is the right home; it already owns the
      cross-repo manifest and the audit workflow.
  - label: gate the workflow only on PRs, not on the weekly cron
    rejected_because: |
      The drift case the sentinel watches for unfolds across weeks
      of quiet activity, not across single PRs. A PR-only gate
      would never trip on the drift mode it is built to catch. The
      weekly cron is the right surface; workflow_dispatch lets the
      maintainer run it on demand.
rationale: |
  DEC-CDCP-011 records that every run carries replay-equivalence
  evidence. DEC-CDCP-015 wires that evidence into per-repo CI. The
  remaining gap is cross-repo and time-bound: a repo that stops
  shipping replays does not fail any CI gate, because no CI gate
  asks "did this repo ship a replay recently?". The portfolio audit
  workflow is the right home for that question; it already runs
  weekly, already touches every active repo via the manifest, and
  already commits its own audit reports back to athena-site.

  The sentinel deliberately keeps a low bar. N=1 in 30 days is
  forgiving on purpose: the audit must not become a noisy alarm
  during ordinary quiet weeks. A repo that goes a full month with
  zero replays has stopped exercising its replay path, and that is
  the drift the sentinel exists to surface. Once the cadence
  settles into a steadier rhythm a follow-on DEC can ratchet the
  threshold up.

  The sentinel reads on-disk state under each repo's
  `ops/replay-records/<run-id>/*.json`. It accepts the first present
  timestamp field of `created_at`, `replay_timestamp`,
  `finished_at`, `started_at`, then falls back to the file mtime.
  This matches the field shapes the existing replay tooling emits
  across the four product repos without forcing a schema migration.

  On the GitHub Actions runner only athena-site is checked out; the
  sentinel renders sibling repos as SKIPPED and exits 0. The local
  maintainer workstation is where the sentinel reads all four
  product repos and reports a meaningful PASS/FAIL. The CI run
  still regenerates the report header so the file dates stay
  current, and `workflow_dispatch` lets the maintainer trigger a
  fresh report when needed.
trade_off: |
  The weekly cron may produce a false positive during a quiet week
  when one product repo happens to ship zero replays for 30 days
  without an underlying regression. The default N=1 is forgiving
  enough that this should be rare, and the report makes the failure
  legible: the audit lists the failing repo, its count, and the
  threshold. The remediation is to land one fresh replay and re-run
  the audit. The cost of one occasional false positive is lower
  than the cost of an undetected drift.
evidence:
  - kind: doc
    ref: scripts/evidence_quorum_sentinel.py
  - kind: doc
    ref: .github/workflows/portfolio-audit.yml
  - kind: doc
    ref: ops/evidence-quorum-report.md
  - kind: doc
    ref: ops/portfolio-manifest.yml
  - kind: decision
    ref: DEC-CDCP-011-run-records-carry-replay-equivalence-evidence.md
  - kind: decision
    ref: DEC-CDCP-015-ci-enforces-run-evidence-chain.md
  - kind: decision
    ref: DEC-CDCP-016-portfolio-status-dashboard.md
coverage:
  - R-CDCP-022
  - R-CDCP-023
  - R-CDCP-024
rollback: |
  Delete `scripts/evidence_quorum_sentinel.py` and
  `ops/evidence-quorum-report.md`. Revert the
  `Run evidence quorum sentinel` step in
  `.github/workflows/portfolio-audit.yml` and drop
  `ops/evidence-quorum-report.md` from the commit step. Mark this
  DEC reversed. The audit workflow continues to run the health
  check and the dashboard exactly as before.
owner: governance.cdcp-curator
---

## decision

athena-site runs an evidence quorum sentinel
(`scripts/evidence_quorum_sentinel.py`) that fails the
`Portfolio audit` workflow when any active product repo has fewer
than N replay artifacts in the last 30 days. Default N is 1 per
repo per 30-day window. The watched repos are
`chip-supply-chain-map`, `supplier-risk-rag-agent`,
`procurement-negotiation-lab`, and `ai-field-brief`. The sentinel
writes `ops/evidence-quorum-report.md` and the audit workflow
commits it alongside the other audit reports.

## why

DEC-CDCP-011 records that every run carries replay-equivalence
evidence. DEC-CDCP-015 wires that evidence into per-repo CI.
Neither check answers the cross-repo, time-bound question: did
this repo ship a replay recently? A repo can pass every CI gate
today, stop shipping replays for a month, and never trip a
warning. The sentinel closes that gap.

## alternatives

- Skip the sentinel and trust that replay tooling will be re-run
  on demand. Rejected: the replay-equivalence claim depends on
  ongoing evidence, and no other check looks at recency.
- Stricter quorum (for example N=5 in 7 days). Rejected: the
  product repos do not yet ship replays on a steady weekly
  cadence; a strict quorum would fire during ordinary quiet weeks
  and train the maintainer to ignore the alert. N=1 in 30 days is
  the floor.
- Per-repo sentinels inside each product repo. Rejected: that
  solves a different problem. Quorum spans repos; the sentinel
  must see all four product repos at once.
- Gate only on PRs. Rejected: the drift case unfolds across weeks
  of quiet activity, not across single PRs. The weekly cron is the
  right surface; `workflow_dispatch` covers ad-hoc runs.

## probe contract

For each watched active product repo declared in
`ops/portfolio-manifest.yml`:

1. Glob `ops/replay-records/<run-id>/*.json` under the repo root.
2. Parse a timestamp from each file: first present of
   `created_at`, `replay_timestamp`, `finished_at`, `started_at`;
   fall back to the file mtime.
3. Count the files whose timestamp lands in the last
   `--window-days` window (default 30).
4. Compare to `--threshold` (default 1).
5. Emit `ops/evidence-quorum-report.md` with a summary header, a
   per-repo table, and a failing-repos block.
6. Exit 0 when every checked-out repo meets quorum; exit 1
   otherwise.

Repos that are not checked out under `local_root` render as
SKIPPED and do not contribute to the exit code. On the CI runner
only athena-site is checked out, so the sentinel exits 0 there;
the report still regenerates so the date header stays current.
The local maintainer run is where the sentinel reads all four
product repos and produces a meaningful pass/fail.

## trade-offs

The weekly cron may flag a false positive during a quiet week
when one product repo ships zero replays for 30 days without an
underlying regression. The default N=1 is forgiving enough that
this should be rare, and the report names the failing repo, its
count, and the threshold so the cause is legible. The remediation
is to land one fresh replay and re-run the audit. One occasional
false positive costs less than an undetected drift across the
portfolio.

The 30-day window is a fixed-floor window, not a sliding-rate
metric. A repo that ships one replay on day 30 and then zero for
the next 30 days will pass once and fail the next run. That is
the intended behavior: the sentinel asks "is there fresh
evidence?", not "is the replay rate steady?". A future DEC can
add a separate rate metric on top if the portfolio outgrows the
floor.

## CI wiring

`.github/workflows/portfolio-audit.yml` runs weekly on Monday
09:00 UTC and on workflow_dispatch. The sentinel runs as a third
step after the audit and the dashboard. The commit step now
includes `ops/evidence-quorum-report.md` in its `git add` list
and runs under `if: always()` so the report still commits when
the sentinel exits non-zero on a future maintainer-triggered
run. The sentinel step itself has no `continue-on-error`: a
quorum failure should fail the workflow on the cron run where it
matters.

## coverage

R-CDCP-022 sentinel exists, R-CDCP-023 sentinel runs in the
portfolio-audit workflow on a weekly cron, R-CDCP-024 sentinel
fails the workflow when any watched repo falls below quorum.

## rollback

Delete `scripts/evidence_quorum_sentinel.py` and
`ops/evidence-quorum-report.md`. Revert the
`Run evidence quorum sentinel` step in
`.github/workflows/portfolio-audit.yml` and drop the report from
the commit step. Mark this DEC reversed. The audit workflow
continues to run the health check and the dashboard exactly as
before.
