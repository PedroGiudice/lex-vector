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
        // Dark tech aesthetic palette
        'bg-main': '#09090b',
        'bg-panel-1': '#0c0c0e',
        'bg-panel-2': '#18181b', // zinc-900
        'bg-input': '#18181b', // zinc-900 - input fields
        'bg-card': '#27272a',    // zinc-800
        'surface-elevated': '#0c0c0e', // Elevated surfaces
        'border-default': '#27272a', // zinc-800
        'border-light': '#3f3f46', // zinc-700
        'text-primary': '#d4d4d8', // zinc-300
        'text-secondary': '#a1a1aa', // zinc-400
        'text-muted': '#71717a',   // zinc-500
        'text-dark': '#52525b',    // zinc-600
        'accent-indigo': '#6366f1', // indigo-500
        'accent-indigo-light': '#818cf8', // indigo-400
        'accent-violet': '#7c3aed', // violet-600
        'accent-amber': '#f59e0b', // amber-500
        'status-red': '#ef4444', // red-500
        'status-emerald': '#10b981', // emerald-500
        'status-yellow': '#facc15', // yellow-400
        // CCui Legal AI Assistant - distinct identity
        'ccui': {
          'bg-primary': '#000000',
          'bg-secondary': '#050505',
          'bg-tertiary': '#0a0a0a',
          'bg-hover': '#1a1a1a',
          'bg-active': '#111111',
          'border-primary': '#1a1a1a',
          'border-secondary': '#222222',
          'border-tertiary': '#333333',
          'text-primary': '#e0e0e0',
          'text-secondary': '#888888',
          'text-muted': '#666666',
          'text-subtle': '#444444',
          'accent': '#d97757',
          'accent-glow': 'rgba(217, 119, 87, 0.2)',
        },
      },
      fontFamily: {
        // Trello Command Center Typography
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'xs': '0.75rem', // 12px
        'sm': '0.875rem', // 14px
        'base': '1rem', // 16px
        'lg': '1.125rem', // 18px
        'xl': '1.25rem', // 20px
        // Custom sizes from reference
        'xxs': '0.6875rem', // 11px
        'xxxs': '0.5625rem', // 9px
      },
      borderRadius: {
        'sm': '0.125rem', // 2px
        'md': '0.25rem', // 4px
        'lg': '0.5rem', // 8px
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-in-from-left': 'slideInFromLeft 0.2s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideInFromLeft: {
          '0%': { transform: 'translateX(-8px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
