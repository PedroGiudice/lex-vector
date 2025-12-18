/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'gh-bg-primary': '#0d1117',
        'gh-bg-secondary': '#161b22',
        'gh-bg-tertiary': '#21262d',
        'gh-text-primary': '#c9d1d9',
        'gh-text-secondary': '#8b949e',
        'gh-accent-primary': '#58a6ff',
        'gh-accent-success': '#3fb950',
        'gh-accent-danger': '#f85149',
        'gh-border-default': '#30363d',
        'gh-highlight-bg': '#388bfd33',
      },
    },
  },
  plugins: [],
}
