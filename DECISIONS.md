# Decisions

- Kept the implementation static and content-first. The brief does not need a backend, CMS, analytics, or client framework.
- Use `https://athena-site-six.vercel.app` as the Astro `site` value because that is the active Vercel production domain for this project.
- Rendered door statuses with a small inline filter script instead of a framework component. This keeps all 13 doors in the HTML and lets the `status` field control filtering.
- Added a static chip-map preview fallback under `public/screenshots/` and a timeout-based iframe fallback. Cross-origin iframe failure is not always detectable, so the open-in-new-tab link remains visible.
