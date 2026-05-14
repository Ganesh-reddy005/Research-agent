import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        mistral: {
          orange: "#ff511c",
          black: "#000000",
          white: "#ffffff",
          beige: "#f5f2ed",
          grey: "#1a1a1a",
          border: "#e5e1da",
        },
        workspace: {
          ink: "#000000",
          accent: "#ff511c",
          "accent-soft": "#fff3f0",
          border: "#e5e1da",
          bg: "#ffffff",
          parchment: "#f5f2ed",
          "muted": "#666666",
        }
      },
      fontFamily: {
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        retro: ["var(--font-retro)", "serif"],
      },
    },
  },
  plugins: [
    require("@tailwindcss/typography"),
  ],
};
export default config;
