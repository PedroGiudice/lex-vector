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
        // CCui Design System - Brighter version
        ccui: {
          bg: {
            primary: '#0c0c0c',      // Lighter black
            secondary: '#141414',    // Lighter sidebar/header
            tertiary: '#1c1c1c',     // Lighter input bg
            hover: '#262626',        // More visible hover
            active: '#1e1e1e',       // More visible active
          },
          border: {
            primary: '#2a2a2a',      // More visible borders
            secondary: '#363636',
            tertiary: '#444444',
          },
          text: {
            primary: '#f5f5f5',      // Brighter main text
            secondary: '#a0a0a0',    // Brighter secondary
            muted: '#808080',        // Brighter muted
            subtle: '#606060',       // Brighter subtle
          },
          accent: {
            DEFAULT: '#e07e5f',      // Slightly brighter coral
            glow: 'rgba(224, 126, 95, 0.25)',
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
        'xxs': ['11px', '15px'],    // Was 10px, now 11px
        'xs': ['12px', '17px'],     // Was 11px, now 12px
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