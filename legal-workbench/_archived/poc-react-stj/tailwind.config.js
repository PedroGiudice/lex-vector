/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        terminal: {
          bg: '#0a0f1a',
          text: '#e2e8f0',
          accent: '#f59e0b',
          danger: '#dc2626',
          success: '#22c55e',
          warning: '#eab308',
          muted: '#64748b',
          border: '#1e293b',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Consolas', 'Monaco', 'Courier New', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'terminal': '0 0 20px rgba(245, 158, 11, 0.1)',
        'terminal-lg': '0 0 40px rgba(245, 158, 11, 0.2)',
      }
    },
  },
  plugins: [],
}
