/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      fontSize: {
        "print-xs": ["12px", { lineHeight: "1.4" }],
        "print-sm": ["14px", { lineHeight: "1.5" }],
        "print-base": ["16px", { lineHeight: "1.6" }],
        "print-lg": ["20px", { lineHeight: "1.4" }],
        "print-xl": ["24px", { lineHeight: "1.3" }],
        "print-2xl": ["32px", { lineHeight: "1.2" }],
      },
      colors: {
        brand: {
          50: "black",
          100: "black",
          500: "black",
          600: "black",
          700: "black",
          900: "black",
        },
      },
    },
  },
  plugins: [],
};
