---
id: DEC-CDCP-016-portfolio-status-dashboard
spec: specs/0010-cognitive-delivery-control-plane/
requirement: R-CDCP-016
date: 2026-05-29
status: approved
reversible: true
decision: |
  athena-site generates `ops/portfolio-status.md` aggregating per-repo
  state across the portfolio. The dashboard runs on the local checkout
  (no GitHub Actions API calls), reports recent commits, latest DECs,
  latest dreams, CI workflow count, schema cache freshness exit code,
  run-record count, and replay artifact count per active CDCP repo, and
  prepends a portfolio summary. The `Portfolio audit` workflow runs
  `scripts/portfolio_dashboard.py` weekly and commits the regenerated
  file when it changes.
alternatives:
  - label: keep cross-repo state-tracking manual; rely on weekly README review
    rejected_because: |
      Eight active repos each carry growing DEC, dream, run-record, and
      replay-artifact directories. Manual review across that surface
      misses drift within hours of landing. The maintainer's standard
      is at-a-glance visibility; a hand-curated README falls behind the
      moment a sub-agent lands a commit in auto mode.
  - label: query GitHub Actions API for per-repo CI state
    rejected_because: |
      The dashboard must work against committed state regardless of CI
      run scheduling, rate limits, or auth scopes. Probing the local
      checkout keeps the report deterministic: the same checkout
      produces the same dashboard. A future DEC can layer live CI
      status on top once an artifact resolver lands.
  - label: build a full web dashboard in athena-site under src/
    rejected_because: |
      A Markdown file under `ops/` is the right altitude for the first
      iteration. It renders in any editor, diffs cleanly in PRs, and
      keeps the generator a single Python file. A web UI raises the
      maintenance cost without adding any signal the Markdown table
      doesn't already carry.
  - label: emit one dashboard per repo, not one consolidated file
    rejected_because: |
      Per-repo dashboards re-create the problem the round was built to
      close: the user still has to cross-reference eight files. A
      single consolidated dashboard reduces eight scans to one.
rationale: |
  Portfolio scale forces this. Eight active CDCP repos each accumulate
  DECs, dreams, run records, and replay artifacts at a pace that
  manual cross-repo tracking cannot keep up with. Without a generated
  dashboard the maintainer's only options are walk each repo by hand
  or trust that nothing has drifted; both options fail at the rate
  CDCP records land.

  The dashboard is intentionally local-state-only. It walks the
  checked-out repos under `local_root` (the same root the portfolio
  audit script already resolves), counts files, reads mtimes, runs
  the schema cache freshness script via subprocess, and writes a
  Markdown report. No GitHub Actions API call, no auth, no rate
  limit. The same checkout always produces the same report; a CI
  regeneration is the canonical refresh.

  Wiring the generator into the existing `Portfolio audit` workflow
  costs one extra step and one extra git add path. The workflow
  already commits and pushes when a report changes; adding the
  status file to the same commit keeps the audit signal in one
  place.

  The format is human-skimmable on purpose: a portfolio summary
  table at the top for at-a-glance numbers, then a per-repo block
  with bullets for the seven probed fields. Markdown tables plus
  short prose. A future DEC can swap the renderer for a richer
  format (HTML page, dashboard tile in the Astro site) without
  changing the probe contract.
evidence:
  - kind: doc
    ref: ops/portfolio-manifest.yml
  - kind: doc
    ref: scripts/portfolio_dashboard.py
  - kind: doc
    ref: tests/test_portfolio_dashboard.py
  - kind: doc
    ref: .github/workflows/portfolio-audit.yml
  - kind: decision
    ref: DEC-CDCP-012-athena-mcp-server-exposes-portfolio-model.md
  - kind: decision
    ref: DEC-CDCP-015-ci-enforces-run-evidence-chain.md
rollback: |
  Delete `scripts/portfolio_dashboard.py`, `tests/test_portfolio_dashboard.py`,
  and `ops/portfolio-status.md`. Revert the `Run portfolio dashboard` step
  and the dashboard path in the commit step of `.github/workflows/portfolio-audit.yml`
  back to a single `git add ops/portfolio-health.md`. Mark this DEC
  reversed. The portfolio audit workflow continues to run health checks
  exactly as before.
owner: governance.cdcp-curator
---

## decision

athena-site generates `ops/portfolio-status.md` aggregating per-repo
state across the eight active CDCP repos. The generator
(`scripts/portfolio_dashboard.py`) runs against the local checkout,
no GitHub API call, and writes a Markdown report with a portfolio
summary table plus a per-repo block. The `Portfolio audit` workflow
regenerates the file weekly and commits it when it changes.

## alternatives

- Keep cross-repo tracking manual. Rejected: portfolio scale (8 repos
  × growing artifact directories) defeats manual review within hours.
- Query the GitHub Actions API for live CI state. Rejected: the
  dashboard must work against committed state regardless of CI
  scheduling, rate limits, or auth scopes. A future DEC can layer
  live status on top.
- Build a full web dashboard under `src/`. Rejected: Markdown is the
  right altitude for the first iteration; a web UI adds maintenance
  cost without adding signal.
- One dashboard per repo. Rejected: re-creates the cross-reference
  problem the round was built to close.

## per-repo probes

Each active repo with a `cdcp_status` declaration in
`ops/portfolio-manifest.yml` gets probed for:

1. **Recent commits**: count in the last 7 days from `git rev-list`;
   latest SHA, author, date from `git log -1`.
2. **Latest DECs**: top 3 `decisions/DEC-*.md` files by mtime.
3. **Latest dreams**: top 3 subdirectories under `ops/dreams/` (or
   `dreams/` as fallback) by mtime.
4. **CI workflow files**: count of `.yml`/`.yaml` files under
   `.github/workflows/`.
5. **Schema cache freshness**: exit code of
   `scripts/check_schema_cache_freshness.py` when present; `n/a`
   when the script is absent.
6. **Run records**: count of `ops/run-records/*.json` files.
7. **Replay artifacts**: count of `ops/replay-records/*/*.json`
   files (one subdirectory per run).

## output format

A Markdown file at `ops/portfolio-status.md`. Top: a generation
header and a portfolio summary table (repos indexed, summed
commits, summed run records, summed replay artifacts, summed
workflow files). Then a `## Per-repo detail` section with one
`### <repo>` block per repo, each carrying the seven probe
results as bullets. Repos that are not checked out under
`local_root` render as `Not checked out. Skipped.` and drop out
of the summary totals. This format is the contract for Phase 1C;
later DECs can swap the renderer.

## CI wiring

`.github/workflows/portfolio-audit.yml` already runs weekly on
Monday 09:00 UTC and on workflow_dispatch. The dashboard runs as
a second step after the audit, writes to
`ops/portfolio-status.md`, and is committed alongside
`ops/portfolio-health.md` when either file changes. The
dashboard step uses `continue-on-error: true` because a probe
failure in one repo should not block the report for the others;
the workflow's failure mode is the audit step itself, not the
dashboard.

In CI, only `athena-site` is checked out, so per-repo sections
for siblings render as `Not checked out`. That is the expected
CI behavior. The dashboard is most useful when regenerated from
a maintainer workstation with all eight repos checked out under
`local_root`; the CI regeneration provides an audit trail and a
baseline header refresh.

## trade-offs

The dashboard reports committed state, not live CI state. A repo
that has a green local checkout and a red GitHub Actions run
will look healthy in the dashboard. That trade-off is
deliberate: a deterministic report is more useful as a baseline
than a flaky live probe. Live CI status is a separate concern
that a later DEC can layer on once an artifact resolver lands.

The `latest 3` cap on DECs and dreams keeps the per-repo block
short. A repo with a high decision velocity will lose the
older-than-3 entries from view, but those entries are still
discoverable via `decisions/` directly. The cap is a presentation
choice, not a contract violation.

## coverage

R-CDCP-016 dashboard exists, R-CDCP-017 dashboard regenerates on
portfolio-audit run, R-CDCP-018 output format stable across
regeneration. The format contract is the bullet list above; a
later DEC may extend or replace it.

## rollback

Delete `scripts/portfolio_dashboard.py`,
`tests/test_portfolio_dashboard.py`, and
`ops/portfolio-status.md`. Revert the dashboard step and commit
path in `.github/workflows/portfolio-audit.yml`. Mark this DEC
reversed. The audit workflow continues to run health checks
exactly as before.
