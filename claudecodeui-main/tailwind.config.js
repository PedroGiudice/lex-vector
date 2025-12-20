/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        // CCui Design System
        ccui: {
          bg: {
            primary: '#000000',
            secondary: '#050505',
            tertiary: '#0a0a0a',
            hover: '#1a1a1a',
            active: '#111111',
          },
          border: {
            primary: '#1a1a1a',
            secondary: '#222222',
            tertiary: '#333333',
          },
          text: {
            primary: '#e0e0e0',
            secondary: '#888888',
            muted: '#666666',
            subtle: '#444444',
          },
          accent: {
            DEFAULT: '#d97757',
            glow: 'rgba(217, 119, 87, 0.2)',
          },
        },
        // Keep existing for backwards compatibility
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      spacing: {
        'safe-area-inset-bottom': 'env(safe-area-inset-bottom)',
        'mobile-nav': 'var(--mobile-nav-total)',
        'icon-rail': '48px',
        'sidebar': '240px',
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'SF Mono', 'Menlo', 'Consolas', 'Liberation Mono', 'monospace'],
      },
      fontSize: {
        'xxs': ['10px', '14px'],
        'xs': ['11px', '16px'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out forwards',
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(5px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
      // Claude Code UI Design Tokens (legacy - backwards compatible)
      backgroundColor: {
        'chat-primary': '#09090b',
        'chat-secondary': '#18181b',
        'chat-tertiary': '#27272a',
      },
      textColor: {
        'chat-primary': '#fafafa',
        'chat-secondary': '#a1a1aa',
        'chat-tertiary': '#71717a',
      },
      borderColor: {
        'chat-primary': '#27272a',
        'chat-secondary': '#3f3f46',
      },
      accentColor: {
        'claude': '#d97757',
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
}