// tailwind.config.js
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gray: {
          750: 'rgba(55, 65, 81, 0.7)',
          850: '#1f2937',
          900: '#111827',
          950: '#0d1117',
        },
      },
      boxShadow: {
        'soft': '0 2px 10px 0 rgba(0, 0, 0, 0.2)',
      },
    },
  },
  plugins: [],
  darkMode: 'class',
}
