const defaultTheme = require("tailwindcss/defaultTheme");
const typography = require("@tailwindcss/typography");

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", ...defaultTheme.fontFamily.sans],
        mono: ["IBM Plex Mono", ...defaultTheme.fontFamily.mono]
      },
      colors: {
        ink: "#141414",
        paper: "#fbfaf7",
        line: "#ded8cc",
        accent: "#0f766e"
      }
    }
  },
  plugins: [typography]
};
