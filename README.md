# athena-site

Sixty-six public repositories do not fit in a row of GitHub pins. This site gives them a front door: 24 curated entry points for the strongest work, a complete `/labs` catalog, and a `/factory` view backed by the portfolio's checked-in control-plane evidence.

The home page also embeds two working systems. `procurement-negotiation-lab` turns mechanism-design choices into an interactive negotiation, while `chip-supply-chain-map` makes the semiconductor graph inspectable without opening a notebook.

**Live site:** https://athena-site-six.vercel.app

## What is here

- `/` - selected work, current writing, and the two embedded applications.
- `/labs` - all 66 public repositories, grouped by domain and labeled by maturity. Live-demo links appear only after the deployment is verified.
- `/factory` - a static snapshot of specs, requirements, decisions, roles, validators, and recent control-plane events across the active portfolio.
- `/essays` - long-form writing on AI product systems, mechanism design, semiconductors, and delivery control.
- `/pmt`, `/ai-systems`, and `/writer-engineer` - narrower routes through the same body of work.

## Run it locally

```powershell
npm install
npm run dev
```

The production check is the same one CI runs:

```powershell
npm run lint
npm run build
python -m pytest -q
```

## How public state is maintained

- `src/data/doors.json` owns the 24 curated entry points.
- `src/data/portfolio.json` and `src/data/connections.json` drive the full labs catalog and its cross-repo links.
- `src/data/live-urls.json` separates a deploy target from a verified live URL.
- `ops/portfolio-manifest.yml` defines the repos covered by the weekly health audit.
- `scripts/portfolio_audit.py` checks live deployments, content fingerprints, data freshness, stale active repos, and declared CDCP state.
- `scripts/factory_snapshot.py` and `scripts/factory_qa_index.py` rebuild the checked-in evidence used by `/factory`.

## Stack

Astro 7, MDX, Tailwind CSS 4, TypeScript, and Vercel.

## Repository map

- `src/pages/` - routes and long-form essays.
- `src/components/` - reusable page and evidence-view components.
- `src/data/` - public portfolio catalogs and generated factory snapshots.
- `ops/` - portfolio manifest, health reports, schemas, and control-plane records.
- `apps/mcp-server/` - seven read-only MCP tools for decisions, schemas, runs, and events.
