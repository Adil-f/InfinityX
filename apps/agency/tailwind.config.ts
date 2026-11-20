import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f1419",
        paper: "#f4f1ea",
        accent: "#1f6f5b",
      },
    },
  },
  plugins: [],
} satisfies Config;
