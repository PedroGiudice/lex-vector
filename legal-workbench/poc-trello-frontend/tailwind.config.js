/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0d1117',
        surface: '#161b22',
        border: '#30363d',
        'text-primary': '#e6edf3',
        'text-secondary': '#8b949e',
        accent: '#58a6ff',
        success: '#3fb950',
        warning: '#d29922',
        'data-highlight': '#1f6feb',
      },
      fontFamily: {
        data: ['"JetBrains Mono"', '"Fira Code"', 'Consolas', 'monospace'],
        label: ['"JetBrains Mono"', '"Fira Code"', 'Consolas', 'monospace'],
        heading: ['"JetBrains Mono"', '"Fira Code"', 'Consolas', 'monospace'],
      },
      fontSize: {
        data: '13px',
        label: '11px',
        heading: '14px',
      },
      lineHeight: {
        'dense': '1.4',
      }
    },
  },
  plugins: [],
}
