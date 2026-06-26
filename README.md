# athena-site

The front door. Every other repo in the portfolio is a room off this hallway —
athena-site is the personal site that links the portfolio doors, hosts the
long-form writing, and embeds chip-supply-chain-map as a live interactive demo.

Deployed at https://athena-site-six.vercel.app.

## Local dev

    npm install
    npm run dev

## Stack

astro 4, mdx, tailwind 3, vercel.

## Structure

- `src/data/doors.json` — the single source of truth for the portfolio grid
- `src/pages/essays/` — long-form writing (MDX)
- `src/components/` — page primitives
- `ops/factory-build-queue.md` — the repo-by-repo build queue for the software factory
