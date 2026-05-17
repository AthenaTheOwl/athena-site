import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import tailwind from "@astrojs/tailwind";

export default defineConfig({
  site: "https://athena-site-six.vercel.app",
  integrations: [mdx(), tailwind(), sitemap()]
});
