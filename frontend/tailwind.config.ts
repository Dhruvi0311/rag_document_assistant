import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./app/components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        black: "#0F172A",
        white: "#FFFFFF",
        "gray-50": "#F8FAFC",
        "gray-100": "#F1F5F9",
        "gray-200": "#E2E8F0",
        "gray-300": "#CBD5E1",
        "gray-400": "#94A3B8",
        "gray-600": "#475569",
        "gray-800": "#1E293B",
      },

      fontFamily: {
        display: ["'Playfair Display'", "Georgia", "serif"],
        body: ["'Source Serif 4'", "Georgia", "serif"],
        sans: ["'Inter'", "-apple-system", "BlinkMacSystemFont", "'Segoe UI'", "Roboto", "sans-serif"],
        mono: ["'JetBrains Mono'", "Menlo", "monospace"],
      },

      fontSize: {
        "display-2xl": ["clamp(3rem, 6vw, 5rem)", { lineHeight: "1.05", letterSpacing: "-0.04em" }],
        "display-xl":  ["clamp(2rem, 4vw, 3.5rem)", { lineHeight: "1.08", letterSpacing: "-0.03em" }],
        "display-lg":  ["clamp(1.5rem, 3vw, 2.25rem)", { lineHeight: "1.15", letterSpacing: "-0.02em" }],
        "body-lg": ["1.125rem", { lineHeight: "1.7" }],
        "body-md": ["1rem",     { lineHeight: "1.7" }],
        "body-sm": ["0.875rem", { lineHeight: "1.6" }],
        "label-lg": ["0.75rem",  { lineHeight: "1.4", letterSpacing: "0.12em" }],
        "label-sm": ["0.625rem", { lineHeight: "1.4", letterSpacing: "0.14em" }],
      },

      transitionDuration: {
        DEFAULT: "150ms",
        100: "100ms",
        150: "150ms",
      },
      transitionTimingFunction: {
        DEFAULT: "cubic-bezier(0.4, 0, 0.2, 1)",
      },

      spacing: {
        "page-x": "clamp(1.5rem, 4vw, 3rem)",
      },
      gridTemplateColumns: {
        "12": "repeat(12, minmax(0, 1fr))",
        "layout": "3fr 9fr",
      },
    },
  },
  plugins: [],
};

export default config;

