/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "odoo-primary": "var(--odoo-primary)",
        ink: "#161616",
        paper: "#f8f7f2",
        line: "#d7d2c6",
        moss: "#44624a",
        clay: "#a5533d",
        signal: "#275efe",
        warn: "#b42318"
      },
      boxShadow: {
        panel: "0 1px 0 rgba(22,22,22,0.08), 0 18px 40px rgba(22,22,22,0.08)"
      }
    }
  },
  plugins: []
}
