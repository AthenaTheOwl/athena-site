# No. 11 | athena-site

personal site + essays. central hub linking portfolio doors,
hosts long-form writing, and embeds the chip-supply-chain-map
as a flagship interactive demo.

deployed at: https://athena-site-six.vercel.app

## local dev

    npm install
    npm run dev

## stack

astro 4 | mdx | tailwind 3 | vercel

## structure

- `src/content/doors.json` - single source of truth for the portfolio grid
- `src/pages/essays/` - long-form writing (MDX)
- `src/components/` - page primitives
- `ops/factory-build-queue.md` - repo-by-repo build queue for the software factory
