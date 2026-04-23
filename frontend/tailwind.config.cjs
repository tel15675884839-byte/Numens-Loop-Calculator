/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{vue,ts}"],
  theme: {
    extend: {
      boxShadow: {
        panel: "0 1px 0 rgba(15, 23, 42, 0.04)"
      }
    }
  },
  plugins: []
};
