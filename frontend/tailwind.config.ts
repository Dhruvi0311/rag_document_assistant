import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      // ── Palette: Pure Black / White only ─────────────────────────────
      colors: {
        black: "#000000",
        white: "#FFFFFF",
        // Grays are ONLY for secondary text and structural borders
        "gray-100": "#F5F5F5",
        "gray-200": "#E0E0E0",
        "gray-400": "#9E9E9E",
        "gray-600": "#616161",
        "gray-800": "#212121",
      },

      // ── Typography ────────────────────────────────────────────────────
      fontFamily: {
        display: ["'Playfair Display'", "Georgia", "serif"],
        body: ["'Source Serif 4'", "Georgia", "serif"],
        mono: ["'JetBrains Mono'", "Menlo", "monospace"],
      },

      fontSize: {
        // Display scale for oversized headlines
        "display-2xl": ["clamp(3rem, 6vw, 5rem)", { lineHeight: "1.05", letterSpacing: "-0.04em" }],
        "display-xl":  ["clamp(2rem, 4vw, 3.5rem)", { lineHeight: "1.08", letterSpacing: "-0.03em" }],
        "display-lg":  ["clamp(1.5rem, 3vw, 2.25rem)", { lineHeight: "1.15", letterSpacing: "-0.02em" }],
        // Body scale
        "body-lg": ["1.125rem", { lineHeight: "1.7" }],
        "body-md": ["1rem",     { lineHeight: "1.7" }],
        "body-sm": ["0.875rem", { lineHeight: "1.6" }],
        // Mono/label scale
        "label-lg": ["0.75rem",  { lineHeight: "1.4", letterSpacing: "0.12em" }],
        "label-sm": ["0.625rem", { lineHeight: "1.4", letterSpacing: "0.14em" }],
      },

      // ── Border radius: ZERO everywhere ───────────────────────────────
      borderRadius: {
        none:    "0px",
        DEFAULT: "0px",
        sm:      "0px",
        md:      "0px",
        lg:      "0px",
        xl:      "0px",
        "2xl":   "0px",
        full:    "0px",
      },

      // ── Box shadow: NONE — depth via color inversion ──────────────────
      boxShadow: {
        none:    "none",
        DEFAULT: "none",
        sm:      "none",
        md:      "none",
        lg:      "none",
        xl:      "none",
        "2xl":   "none",
        inner:   "none",
      },

      // ── Transitions: max 100ms ────────────────────────────────────────
      transitionDuration: {
        DEFAULT: "100ms",
        75:  "75ms",
        100: "100ms",
      },
      transitionTimingFunction: {
        DEFAULT: "linear",
      },

      // ── Spacing ───────────────────────────────────────────────────────
      spacing: {
        "page-x": "clamp(1.5rem, 4vw, 3rem)",
      },

      // ── Grid ──────────────────────────────────────────────────────────
      gridTemplateColumns: {
        "12": "repeat(12, minmax(0, 1fr))",
        "layout": "3fr 9fr",
      },
    },
  },
  plugins: [],
};

export default config;
