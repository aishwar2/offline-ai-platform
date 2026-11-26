/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          500: "#10a37f",
          600: "#0d8a6a",
        },
      },
    },
  },
  plugins: [],
};
