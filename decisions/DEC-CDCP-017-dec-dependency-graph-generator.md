---
id: DEC-CDCP-017-dec-dependency-graph-generator
spec: specs/0010-cognitive-delivery-control-plane/
requirement: R-CDCP-019..021
date: 2026-05-29
status: approved
reversible: true
decision: |
  athena-site emits a DEC dependency graph per active CDCP repo, plus a
  portfolio-wide rollup, regenerated weekly by the `Portfolio audit`
  workflow. The generator (`scripts/dec_dependency_graph.py`) walks each
  repo's `decisions/` directory, parses front-matter to extract `id`,
  `amends`, `status`, `owner`, and `date`, builds a directed graph with
  an edge from each amending DEC to its parent, and writes three files
  per run: `ops/dec-graphs/<repo>.dot` (Graphviz DOT), `ops/dec-graphs/
  <repo>.md` (per-repo summary table + chain text), and
  `ops/dec-graphs/portfolio-rollup.md` (cross-repo counts and deepest
  chains).
alternatives:
  - label: read amendment chains by hand at review time
    rejected_because: |
      The portfolio carries 168 DECs across 8 active product repos
      with chain depths up to six edges. A reviewer who has to
      reconstruct each chain by grepping `amends:` across eight
      `decisions/` directories falls behind the moment a new
      amendment lands. The generator turns the chain structure into
      a stable artifact a reviewer can read in seconds.
  - label: render the graph as a PNG via a graphviz binary in CI
    rejected_because: |
      The DOT file is the durable contract: it diffs cleanly in PRs,
      stays under version control, and renders in any Graphviz
      viewer the reviewer prefers. A PNG locks the format choice
      into the build pipeline, adds a binary dependency, and forces
      a binary diff in the audit commit. A future DEC can layer a
      rendered image on top once the chain count justifies the
      build-step cost.
  - label: store the chain graph inside the per-repo DEC files
    rejected_because: |
      A DEC describes one decision. Encoding the global chain
      structure inside each DEC duplicates state the source-of-truth
      `amends` pointer already carries, and the chain shape
      shifts whenever a new DEC lands. The graph belongs in a
      derived artifact that regenerates from the DEC front-matter,
      not in the DECs themselves.
  - label: emit one consolidated DOT for the whole portfolio
    rejected_because: |
      A single 168-node DOT mixes chains that have nothing in common
      across repos (chip-supply-chain-map's FIN chain, supplier-risk-
      rag-agent's EVL chain, ai-field-brief's PUB chain). The reviewer
      almost always asks "what does this repo's amendment history
      look like?" — a per-repo DOT answers that question directly.
      The portfolio rollup carries the cross-repo summary as a
      Markdown table; that is the right altitude for the aggregate
      view.
rationale: |
  Portfolio scale forces this. Eight active product repos carry deep
  amendment chains: chip-supply-chain-map, supplier-risk-rag-agent,
  and procurement-negotiation-lab each have a six-edge chain;
  ai-field-brief carries two chains with a four-edge maximum;
  trace-to-eval-harness carries a four-edge chain. Without a
  generated graph, a reviewer asking "how did this decision get
  here?" has to walk each `decisions/` directory, parse front-matter
  by eye, and reconstruct the chain. The cost of that walk grows
  with every amendment.

  The generator runs against committed state on a local checkout —
  no GitHub API call, no auth, no rate limit. The same checkout
  always produces the same graph; a CI regeneration is the
  canonical refresh. The local maintainer workstation regenerates
  with all eight repos checked out under `local_root`; in CI only
  athena-site is checked out, so sibling repos render as `not
  checked out` in the rollup. The CI run keeps the file dates
  current and provides an audit trail.

  The per-repo DOT carries every DEC as a node, with `solid` shape
  for `status: approved` and `dashed` for everything else. Edges
  are labeled `amends` and run from the later DEC to the earlier
  DEC. The per-repo Markdown carries the chain rendered as
  arrow-joined ids ("DEC-CDCP-011 -> DEC-CDCP-012 -> ...") plus a
  table of every DEC with status, amends target, and date. The
  portfolio rollup carries a summary row per repo plus the deepest
  chain across the portfolio.

  Wiring the generator into the existing `Portfolio audit`
  workflow costs one extra step and one extra `git add` path. The
  workflow already commits and pushes when an audit report
  changes; adding the dec-graphs directory to the same commit
  keeps the audit signal in one place.
trade_off: |
  The graph reports committed state, not in-flight DECs. A draft
  amendment open in a PR will not appear in the graph until it
  merges. That trade-off is deliberate: the graph is a baseline
  for shipped state, and PR review surfaces the draft already. The
  graph does not lay claim to live PR state.

  Per-repo chain text in the Markdown summary lists every chain
  including branching ones; a root with three children renders as
  three separate lines. That reads cleanly for the shallow trees
  the portfolio carries today. A future DEC can swap the renderer
  for a denser format if chain branching outgrows the line-based
  layout.
evidence:
  - kind: doc
    ref: scripts/dec_dependency_graph.py
  - kind: doc
    ref: tests/test_dec_dependency_graph.py
  - kind: doc
    ref: .github/workflows/portfolio-audit.yml
  - kind: doc
    ref: ops/dec-graphs/portfolio-rollup.md
  - kind: decision
    ref: DEC-CDCP-016-portfolio-status-dashboard.md
  - kind: decision
    ref: DEC-CDCP-018-evidence-quorum-sentinel.md
coverage:
  - R-CDCP-019
  - R-CDCP-020
  - R-CDCP-021
rollback: |
  Delete `scripts/dec_dependency_graph.py`,
  `tests/test_dec_dependency_graph.py`, and the
  `ops/dec-graphs/` directory. Revert the
  `Run DEC dependency graph generator` step in
  `.github/workflows/portfolio-audit.yml` and drop
  `ops/dec-graphs` from the commit step. Mark this DEC reversed.
  The audit workflow continues to run the health check, the
  dashboard, and the evidence quorum sentinel exactly as before.
owner: governance.cdcp-curator
---

## decision

athena-site emits per-repo DEC dependency graphs (DOT + Markdown) and
a portfolio rollup, regenerated weekly via the `Portfolio audit`
workflow. The generator (`scripts/dec_dependency_graph.py`) walks
each active CDCP repo's `decisions/` directory, parses front-matter,
and writes `ops/dec-graphs/<repo>.dot`, `ops/dec-graphs/<repo>.md`,
and `ops/dec-graphs/portfolio-rollup.md`.

## why

Portfolio scale forces this. The eight active product repos carry
168 DECs with amendment chains up to six edges deep. A reviewer
asking "how did this decision get here?" should not have to grep
`amends:` across eight `decisions/` directories. The generator
turns the chain structure into a stable artifact the reviewer
reads in seconds.

## alternatives

- Read amendment chains by hand at review time. Rejected: 168 DECs
  across 8 repos defeats hand review the moment a new amendment
  lands.
- Render the DOT as a PNG via graphviz in CI. Rejected: the DOT
  file is the durable contract; a PNG adds a binary dependency and
  forces a binary diff in the audit commit. A future DEC can layer
  a rendered image on top.
- Encode the chain graph inside the per-repo DEC files. Rejected:
  duplicates state the source-of-truth `amends` pointer already
  carries.
- Emit one consolidated DOT for the whole portfolio. Rejected: a
  single 168-node DOT mixes chains that have nothing in common
  across repos. The per-repo DOT plus a portfolio rollup answers
  both the per-repo and the cross-repo question.

## probe contract

For each active product repo declared in
`ops/portfolio-manifest.yml` with a `cdcp_status` field:

1. Glob `decisions/DEC-*.md` under the repo root.
2. Parse the YAML front-matter for `id`, `amends`, `status`,
   `owner`, `date`.
3. Build a directed edge from each amending DEC to its parent.
4. Walk the reverse adjacency from each root DEC (one that has
   descendants but no in-graph parent) to render every chain as
   an ordered list of ids, oldest to newest.
5. Write `ops/dec-graphs/<repo>.dot` (Graphviz DOT digraph),
   `ops/dec-graphs/<repo>.md` (counts, chains, per-DEC table),
   and `ops/dec-graphs/portfolio-rollup.md` (cross-repo summary +
   deepest chains).

Repos not checked out under `local_root` render as `not checked
out` in the rollup and do not get a per-repo DOT or Markdown.

## output format

`ops/dec-graphs/<repo>.dot`:

```dot
digraph dec_chains_<repo> {
  rankdir=LR;
  "DEC-CDCP-011-..." [shape=box, style=solid];
  ...
  "DEC-CDCP-012-..." -> "DEC-CDCP-011-..." [label="amends"];
  ...
}
```

`ops/dec-graphs/<repo>.md`: header with the repo name, totals
(DEC count, chain count, deepest chain depth), a `## Chains`
block with arrow-joined ids, and a `## DECs` table with every
DEC and its `amends` target.

`ops/dec-graphs/portfolio-rollup.md`: header with the run date,
a summary table (repo, DEC count, chain count, deepest chain
depth, status), totals, and a `## Deepest chains` block.

## CI wiring

`.github/workflows/portfolio-audit.yml` runs weekly on Monday
09:00 UTC and on workflow_dispatch. The dec-graph step runs
after the health check, the dashboard, and the evidence quorum
sentinel. The commit step adds `ops/dec-graphs` to its `git add`
list and runs under `if: always()` so the artifacts still land
when the evidence quorum sentinel fails on a maintainer-
triggered run.

In CI, only athena-site is checked out, so per-repo files for
siblings do not regenerate; the rollup renders sibling rows as
`not checked out`. That is the expected CI behavior. The
generator is most useful when regenerated from a maintainer
workstation with all eight repos checked out under `local_root`;
the CI regeneration provides an audit trail.

## coverage

R-CDCP-019 per-repo DEC dependency graph exists,
R-CDCP-020 portfolio rollup exists,
R-CDCP-021 the graph regenerates on the weekly portfolio-audit
run and the workflow commits the artifacts when they change.

## rollback

Delete `scripts/dec_dependency_graph.py`,
`tests/test_dec_dependency_graph.py`, and the
`ops/dec-graphs/` directory. Revert the
`Run DEC dependency graph generator` step in
`.github/workflows/portfolio-audit.yml` and drop
`ops/dec-graphs` from the commit step. Mark this DEC reversed.
The audit workflow continues to run the health check, the
dashboard, and the evidence quorum sentinel exactly as before.
