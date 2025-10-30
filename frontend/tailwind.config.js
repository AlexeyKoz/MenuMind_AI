/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
        '88': '22rem',
      },
      minHeight: {
        '44': '44px',
        '56': '56px',
      },
      minWidth: {
        '44': '44px',
        '56': '56px',
      },
    },
  },
  plugins: [],
}

