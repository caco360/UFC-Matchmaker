import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bone: "#f5f1ea",
        ember: "#b72821",
        charcoal: "#1c1b19",
        ash: "#746d66",
        line: "#d7cec2",
      },
      fontFamily: {
        display: ["var(--font-source-sans)", "sans-serif"],
        body: ["var(--font-source-sans)", "sans-serif"],
      },
      boxShadow: {
        soft: "0 20px 80px rgba(28, 27, 25, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
