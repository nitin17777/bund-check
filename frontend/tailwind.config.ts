import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#090D16",
        surface: {
          base: "#0E1422",
          card: "#141C2E",
          overlay: "#1A243B",
          active: "#232F4C",
        },
        border: {
          subtle: "#1B253B",
          DEFAULT: "#263452",
          strong: "#3B4D75",
        },
        text: {
          primary: "#F8FAFC",
          secondary: "#94A3B8",
          muted: "#64748B",
        },
        accent: {
          DEFAULT: "#3B82F6",
          hover: "#2563EB",
          subtle: "rgba(59, 130, 246, 0.12)",
          foreground: "#FFFFFF",
        },
        semantic: {
          info: {
            DEFAULT: "#38BDF8",
            subtle: "rgba(56, 189, 248, 0.12)",
            border: "#0284C7",
          },
          success: {
            DEFAULT: "#10B981",
            subtle: "rgba(16, 185, 129, 0.12)",
            border: "#059669",
          },
          warning: {
            DEFAULT: "#F59E0B",
            subtle: "rgba(245, 158, 11, 0.12)",
            border: "#D97706",
          },
          critical: {
            DEFAULT: "#EF4444",
            subtle: "rgba(239, 68, 68, 0.12)",
            border: "#DC2626",
          },
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains)", "monospace"],
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "6px",
        md: "8px",
        lg: "12px",
        full: "9999px",
      },
      keyframes: {
        shimmer: {
          "100%": {
            transform: "translateX(100%)",
          },
        },
      },
    },
  },
  plugins: [],
};

export default config;
