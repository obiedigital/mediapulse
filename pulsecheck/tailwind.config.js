/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0A0A0F",
        ink2: "#12121A",
        surface: "#1C1C28",
        s2: "#252534",
        s3: "#2E2E42",
        line: "rgba(255,255,255,0.08)",
        or: "#FF5C1A",
        or2: "#FF8150",
        teal: "#00D4C8",
        cream: "#F5F2EC",
      },
      fontFamily: {
        display: ["Syne", "sans-serif"],
        sans: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
