"""
PREMIUM PRODUCTION DESIGN SYSTEM FOR STJ MODULE
Inspired by Vercel, Linear, and Notion - Legal Tech Edition
Version: 2.0 (2025)
"""

# ============================================================================
# COLOR PALETTE - Premium Legal Tech Aesthetic
# ============================================================================

COLORS = {
    # Background System (Deep Navy with subtle warmth)
    'bg_primary': '#0B0F19',        # Main background - not pure black for comfort
    'bg_secondary': '#141825',      # Card/elevated surfaces
    'bg_tertiary': '#1A1F2E',       # Hover states, inputs
    'bg_elevated': '#1E2433',       # Modal overlays, dropdowns
    'bg_glass': 'rgba(26, 31, 46, 0.7)',  # Glassmorphism overlays

    # Text Hierarchy
    'text_primary': '#F8FAFC',      # High contrast white (not pure)
    'text_secondary': '#CBD5E1',    # Secondary text
    'text_tertiary': '#94A3B8',     # Muted text, labels
    'text_disabled': '#64748B',     # Disabled states

    # Accent System - Professional Blues & Gold
    'accent_primary': '#3B82F6',    # Primary actions (trust blue)
    'accent_primary_hover': '#2563EB',
    'accent_secondary': '#F59E0B',  # Highlights, warnings (refined amber)
    'accent_secondary_hover': '#D97706',

    # Semantic Colors (Legal Context)
    'success': '#10B981',           # PROVIDO decisions
    'success_dim': 'rgba(16, 185, 129, 0.15)',
    'error': '#EF4444',             # DESPROVIDO decisions
    'error_dim': 'rgba(239, 68, 68, 0.15)',
    'warning': '#F59E0B',           # PARCIAL decisions
    'warning_dim': 'rgba(245, 158, 11, 0.15)',
    'info': '#3B82F6',              # Information states
    'info_dim': 'rgba(59, 130, 246, 0.15)',

    # Borders & Dividers
    'border_subtle': '#1E293B',     # Subtle dividers
    'border_medium': '#334155',     # Standard borders
    'border_strong': '#475569',     # Emphasis borders
    'border_glow': 'rgba(59, 130, 246, 0.3)',  # Focus glow

    # Overlays & Shadows
    'overlay_light': 'rgba(11, 15, 25, 0.5)',
    'overlay_heavy': 'rgba(11, 15, 25, 0.8)',
    'shadow_sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    'shadow_md': '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    'shadow_lg': '0 10px 15px -3px rgba(0, 0, 0, 0.2)',
    'shadow_xl': '0 20px 25px -5px rgba(0, 0, 0, 0.3)',
    'shadow_glow_blue': '0 0 20px rgba(59, 130, 246, 0.3)',
    'shadow_glow_amber': '0 0 20px rgba(245, 158, 11, 0.3)',
}

# ============================================================================
# TYPOGRAPHY SYSTEM
# ============================================================================

FONTS = {
    'sans': '-apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", "Roboto", sans-serif',
    'mono': '"JetBrains Mono", "Fira Code", "Courier New", monospace',
    'display': '"Cal Sans", "Inter", -apple-system, sans-serif',
}

FONT_SIZES = {
    'xs': '0.75rem',      # 12px - Captions, badges
    'sm': '0.875rem',     # 14px - Small text
    'base': '1rem',       # 16px - Body text
    'lg': '1.125rem',     # 18px - Large body
    'xl': '1.25rem',      # 20px - H3
    '2xl': '1.5rem',      # 24px - H2
    '3xl': '1.875rem',    # 30px - H1
    '4xl': '2.25rem',     # 36px - Display
}

# ============================================================================
# SPACING SYSTEM (8px grid)
# ============================================================================

SPACING = {
    'xs': '0.25rem',   # 4px
    'sm': '0.5rem',    # 8px
    'md': '1rem',      # 16px
    'lg': '1.5rem',    # 24px
    'xl': '2rem',      # 32px
    '2xl': '3rem',     # 48px
    '3xl': '4rem',     # 64px
}

# ============================================================================
# CDN IMPORTS
# ============================================================================

TAILWIND_CDN = "https://cdn.tailwindcss.com"
ICONIFY_CDN = "https://code.iconify.design/3/3.1.0/iconify.min.js"  # Modern icon library

# ============================================================================
# PREMIUM CSS - Production Grade Styling
# ============================================================================

PREMIUM_STYLE = """
<style>
    /* ===================================================================
       BASE SETUP & RESET
    =================================================================== */

    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }

    html {
        scroll-behavior: smooth;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    body {
        background: linear-gradient(135deg, #0B0F19 0%, #141825 100%);
        background-attachment: fixed;
        color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
        font-size: 16px;
        line-height: 1.6;
        min-height: 100vh;
    }

    /* Subtle background grid pattern */
    body::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image:
            linear-gradient(rgba(59, 130, 246, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px);
        background-size: 50px 50px;
        pointer-events: none;
        z-index: 0;
    }

    /* ===================================================================
       CUSTOM SCROLLBAR (Premium)
    =================================================================== */

    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }

    ::-webkit-scrollbar-track {
        background: #141825;
        border-radius: 5px;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #3B82F6 0%, #2563EB 100%);
        border-radius: 5px;
        border: 2px solid #141825;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #2563EB 0%, #1D4ED8 100%);
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
    }

    /* ===================================================================
       TYPOGRAPHY ENHANCEMENTS
    =================================================================== */

    h1, h2, h3, h4, h5, h6 {
        font-weight: 600;
        letter-spacing: -0.02em;
        line-height: 1.2;
        color: #F8FAFC;
    }

    .font-display {
        font-family: "Cal Sans", "Inter", -apple-system, sans-serif;
        font-weight: 700;
        letter-spacing: -0.03em;
    }

    .font-mono {
        font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
        font-variant-ligatures: normal;
    }

    /* Text gradients for premium feel */
    .text-gradient-blue {
        background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .text-gradient-amber {
        background: linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* ===================================================================
       CARD SYSTEM - Glassmorphism + Depth
    =================================================================== */

    .card {
        background: rgba(26, 31, 46, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(59, 130, 246, 0.1);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow:
            0 4px 6px rgba(0, 0, 0, 0.1),
            0 1px 3px rgba(0, 0, 0, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    /* Subtle gradient border effect */
    .card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        border-radius: 16px;
        padding: 1px;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(245, 158, 11, 0.1));
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .card:hover::before {
        opacity: 1;
    }

    .card:hover {
        transform: translateY(-2px);
        border-color: rgba(59, 130, 246, 0.2);
        box-shadow:
            0 10px 15px rgba(0, 0, 0, 0.2),
            0 4px 6px rgba(0, 0, 0, 0.1),
            0 0 0 1px rgba(59, 130, 246, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }

    .card-header {
        font-size: 1.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(59, 130, 246, 0.2);
        position: relative;
    }

    /* Animated glow on header */
    .card-header::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        width: 0;
        height: 2px;
        background: linear-gradient(90deg, #3B82F6, #60A5FA);
        transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .card:hover .card-header::after {
        width: 100%;
    }

    /* ===================================================================
       FORM INPUTS - Premium Focus States
    =================================================================== */

    .input-field {
        background: rgba(11, 15, 25, 0.6);
        border: 1px solid #1E293B;
        color: #F8FAFC;
        padding: 0.75rem 1rem;
        border-radius: 10px;
        width: 100%;
        font-size: 0.875rem;
        font-family: inherit;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        outline: none;
    }

    .input-field::placeholder {
        color: #64748B;
    }

    .input-field:hover {
        border-color: #334155;
        background: rgba(20, 24, 37, 0.8);
    }

    .input-field:focus {
        border-color: #3B82F6;
        background: rgba(20, 24, 37, 0.9);
        box-shadow:
            0 0 0 3px rgba(59, 130, 246, 0.1),
            0 1px 2px rgba(0, 0, 0, 0.1);
    }

    /* Select dropdown styling */
    select.input-field {
        appearance: none;
        background-image: url("data:image/svg+xml,%3Csvg width='12' height='8' viewBox='0 0 12 8' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1.5L6 6.5L11 1.5' stroke='%233B82F6' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: right 1rem center;
        padding-right: 3rem;
    }

    /* ===================================================================
       BUTTONS - Modern, Tactile, Premium
    =================================================================== */

    .btn {
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.875rem;
        cursor: pointer;
        border: none;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        text-decoration: none;
        white-space: nowrap;
    }

    /* Primary button - Blue gradient */
    .btn-primary {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        color: #FFFFFF;
        box-shadow:
            0 4px 6px rgba(0, 0, 0, 0.1),
            0 1px 3px rgba(0, 0, 0, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }

    .btn-primary::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        opacity: 0;
        transition: opacity 0.2s;
    }

    .btn-primary:hover::before {
        opacity: 1;
    }

    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow:
            0 10px 15px rgba(59, 130, 246, 0.3),
            0 4px 6px rgba(0, 0, 0, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }

    .btn-primary:active {
        transform: translateY(0);
    }

    /* Secondary button - Subtle ghost */
    .btn-secondary {
        background: rgba(30, 41, 59, 0.6);
        color: #CBD5E1;
        border: 1px solid #334155;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }

    .btn-secondary:hover {
        background: rgba(51, 65, 85, 0.8);
        border-color: #475569;
        transform: translateY(-1px);
        box-shadow:
            0 4px 6px rgba(0, 0, 0, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }

    /* Template button - Amber accent */
    .btn-template {
        background: rgba(245, 158, 11, 0.1);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.3);
        padding: 0.5rem 1rem;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .btn-template:hover {
        background: rgba(245, 158, 11, 0.2);
        border-color: #F59E0B;
        box-shadow: 0 0 15px rgba(245, 158, 11, 0.2);
    }

    /* Disabled state */
    .btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
        transform: none !important;
    }

    /* ===================================================================
       BADGES & PILLS - Status Indicators
    =================================================================== */

    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        padding: 0.375rem 0.875rem;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        border-radius: 8px;
        letter-spacing: 0.05em;
        border: 1px solid;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }

    .badge-provido {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border-color: rgba(16, 185, 129, 0.3);
    }

    .badge-desprovido {
        background: rgba(239, 68, 68, 0.15);
        color: #EF4444;
        border-color: rgba(239, 68, 68, 0.3);
    }

    .badge-parcial {
        background: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
        border-color: rgba(245, 158, 11, 0.3);
    }

    .badge-warning {
        background: rgba(239, 68, 68, 0.1);
        color: #EF4444;
        border-color: #EF4444;
        animation: pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }

    @keyframes pulse-glow {
        0%, 100% {
            box-shadow: 0 0 5px rgba(239, 68, 68, 0.5);
            border-color: #EF4444;
        }
        50% {
            box-shadow: 0 0 15px rgba(239, 68, 68, 0.8);
            border-color: #F87171;
        }
    }

    /* Interactive pills for multi-select */
    .pill {
        display: inline-flex;
        align-items: center;
        background: rgba(59, 130, 246, 0.1);
        color: #60A5FA;
        border: 1px solid rgba(59, 130, 246, 0.3);
        padding: 0.5rem 1rem;
        border-radius: 999px;
        font-size: 0.8125rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        user-select: none;
    }

    .pill:hover {
        background: rgba(59, 130, 246, 0.2);
        border-color: #3B82F6;
        transform: translateY(-1px) scale(1.02);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
    }

    .pill.selected {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        color: #FFFFFF;
        border-color: transparent;
        box-shadow:
            0 4px 12px rgba(59, 130, 246, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }

    .pill.selected:hover {
        transform: translateY(-2px) scale(1.05);
        box-shadow: 0 8px 16px rgba(59, 130, 246, 0.5);
    }

    /* ===================================================================
       TOGGLE SWITCH - Modern, Smooth
    =================================================================== */

    .toggle-switch {
        position: relative;
        display: inline-block;
        width: 52px;
        height: 28px;
    }

    .toggle-switch input {
        opacity: 0;
        width: 0;
        height: 0;
    }

    .toggle-slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid #334155;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border-radius: 28px;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
    }

    .toggle-slider:before {
        position: absolute;
        content: "";
        height: 20px;
        width: 20px;
        left: 4px;
        bottom: 3px;
        background: linear-gradient(135deg, #64748B 0%, #475569 100%);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border-radius: 50%;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }

    input:checked + .toggle-slider {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        border-color: transparent;
        box-shadow:
            inset 0 2px 4px rgba(0, 0, 0, 0.1),
            0 0 12px rgba(59, 130, 246, 0.5);
    }

    input:checked + .toggle-slider:before {
        transform: translateX(24px);
        background: linear-gradient(135deg, #FFFFFF 0%, #F1F5F9 100%);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }

    input:focus + .toggle-slider {
        box-shadow:
            0 0 0 3px rgba(59, 130, 246, 0.2),
            inset 0 2px 4px rgba(0, 0, 0, 0.2);
    }

    /* ===================================================================
       SQL PREVIEW & TERMINAL - Code Display
    =================================================================== */

    .sql-preview {
        background: linear-gradient(135deg, rgba(11, 15, 25, 0.9) 0%, rgba(14, 18, 27, 0.9) 100%);
        border: 1px solid #1E293B;
        border-radius: 12px;
        padding: 1.25rem;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 0.8125rem;
        color: #60A5FA;
        white-space: pre-wrap;
        word-wrap: break-word;
        line-height: 1.7;
        overflow-x: auto;
        box-shadow:
            inset 0 2px 8px rgba(0, 0, 0, 0.3),
            0 1px 3px rgba(0, 0, 0, 0.1);
        position: relative;
    }

    .sql-preview::before {
        content: 'SQL';
        position: absolute;
        top: 0.75rem;
        right: 1rem;
        font-size: 0.625rem;
        color: #475569;
        font-weight: 700;
        letter-spacing: 0.1em;
    }

    .sql-keyword {
        color: #60A5FA;
        font-weight: 700;
    }

    .sql-table {
        color: #10B981;
        font-weight: 600;
    }

    .sql-string {
        color: #FBBF24;
    }

    .sql-comment {
        color: #64748B;
        font-style: italic;
    }

    /* Terminal output */
    .terminal {
        background: linear-gradient(135deg, #0B0F19 0%, #0E121B 100%);
        border: 1px solid #1E293B;
        border-radius: 12px;
        padding: 1.25rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8125rem;
        color: #10B981;
        overflow-x: auto;
        max-height: 500px;
        overflow-y: auto;
        box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.3);
        position: relative;
    }

    /* Terminal header with dots */
    .terminal::before {
        content: '';
        position: absolute;
        top: 0.75rem;
        left: 1rem;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #EF4444;
        box-shadow:
            18px 0 0 #F59E0B,
            36px 0 0 #10B981;
    }

    .terminal-line {
        color: #10B981;
        margin: 0.375rem 0;
        line-height: 1.6;
        padding-left: 1rem;
        position: relative;
    }

    .terminal-line::before {
        content: '›';
        position: absolute;
        left: 0;
        color: #3B82F6;
        font-weight: 700;
    }

    .terminal-error {
        color: #EF4444;
    }

    .terminal-warning {
        color: #F59E0B;
    }

    .terminal-info {
        color: #3B82F6;
    }

    /* Typing animation for terminal */
    @keyframes typing {
        from { width: 0; }
        to { width: 100%; }
    }

    .terminal-typing {
        display: inline-block;
        overflow: hidden;
        white-space: nowrap;
        animation: typing 0.8s steps(40, end);
    }

    /* ===================================================================
       TABLES - Data Grid with Hover States
    =================================================================== */

    .results-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin-top: 1rem;
        overflow: hidden;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .results-table thead {
        position: sticky;
        top: 0;
        z-index: 10;
    }

    .results-table th {
        background: linear-gradient(180deg, rgba(26, 31, 46, 0.95) 0%, rgba(20, 24, 37, 0.95) 100%);
        backdrop-filter: blur(8px);
        color: #60A5FA;
        padding: 1rem 1.25rem;
        text-align: left;
        font-weight: 700;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        border-bottom: 2px solid rgba(59, 130, 246, 0.3);
    }

    .results-table td {
        padding: 1rem 1.25rem;
        border-bottom: 1px solid rgba(30, 41, 59, 0.5);
        font-size: 0.875rem;
        color: #CBD5E1;
        background: rgba(20, 24, 37, 0.3);
        transition: all 0.2s ease;
    }

    .results-table tr {
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .results-table tbody tr:hover {
        background: rgba(59, 130, 246, 0.08);
        transform: scale(1.01);
        box-shadow:
            0 4px 12px rgba(0, 0, 0, 0.15),
            inset 0 0 0 1px rgba(59, 130, 246, 0.2);
    }

    .results-table tbody tr:hover td {
        color: #F8FAFC;
        border-color: rgba(59, 130, 246, 0.3);
    }

    /* Skeleton loading for table rows */
    .skeleton-row {
        background: linear-gradient(
            90deg,
            rgba(30, 41, 59, 0.5) 25%,
            rgba(51, 65, 85, 0.5) 50%,
            rgba(30, 41, 59, 0.5) 75%
        );
        background-size: 200% 100%;
        animation: skeleton-loading 1.5s ease-in-out infinite;
        height: 20px;
        border-radius: 4px;
    }

    @keyframes skeleton-loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }

    /* ===================================================================
       LOADING STATES & ANIMATIONS
    =================================================================== */

    .loading {
        display: inline-block;
        width: 18px;
        height: 18px;
        border: 2px solid rgba(59, 130, 246, 0.2);
        border-top-color: #3B82F6;
        border-radius: 50%;
        animation: spin 0.6s linear infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    /* Larger loading spinner for full-page states */
    .loading-lg {
        width: 48px;
        height: 48px;
        border-width: 4px;
    }

    /* Pulsing dot indicator */
    .loading-dots {
        display: inline-flex;
        gap: 0.5rem;
    }

    .loading-dots span {
        width: 8px;
        height: 8px;
        background: #3B82F6;
        border-radius: 50%;
        animation: pulse-dot 1.4s ease-in-out infinite;
    }

    .loading-dots span:nth-child(2) {
        animation-delay: 0.2s;
    }

    .loading-dots span:nth-child(3) {
        animation-delay: 0.4s;
    }

    @keyframes pulse-dot {
        0%, 80%, 100% {
            opacity: 0.3;
            transform: scale(1);
        }
        40% {
            opacity: 1;
            transform: scale(1.3);
        }
    }

    /* Progress bar with glow */
    .progress-bar {
        width: 100%;
        height: 8px;
        background: rgba(30, 41, 59, 0.5);
        border-radius: 999px;
        overflow: hidden;
        position: relative;
    }

    .progress-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 100%);
        border-radius: 999px;
        transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 0 12px rgba(59, 130, 246, 0.6);
        position: relative;
        overflow: hidden;
    }

    .progress-bar-fill::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 255, 255, 0.3),
            transparent
        );
        animation: shimmer 2s infinite;
    }

    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }

    /* ===================================================================
       HTMX INDICATORS & STATES
    =================================================================== */

    .htmx-indicator {
        display: none;
    }

    .htmx-request .htmx-indicator {
        display: inline-block;
    }

    .htmx-request.htmx-indicator {
        display: inline-block;
    }

    /* Smooth fade-in for swapped content */
    .htmx-swapping {
        opacity: 0;
        transition: opacity 0.2s ease-out;
    }

    .htmx-settling {
        opacity: 1;
    }

    /* ===================================================================
       TOAST NOTIFICATIONS
    =================================================================== */

    .toast {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        background: rgba(26, 31, 46, 0.95);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        min-width: 300px;
        max-width: 500px;
        box-shadow:
            0 10px 25px rgba(0, 0, 0, 0.3),
            0 0 0 1px rgba(255, 255, 255, 0.05);
        animation: slide-in-right 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        z-index: 1000;
    }

    @keyframes slide-in-right {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    .toast-success {
        border-left: 4px solid #10B981;
    }

    .toast-error {
        border-left: 4px solid #EF4444;
    }

    .toast-warning {
        border-left: 4px solid #F59E0B;
    }

    .toast-info {
        border-left: 4px solid #3B82F6;
    }

    /* ===================================================================
       LAYOUT UTILITIES
    =================================================================== */

    .container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 2rem;
        position: relative;
        z-index: 1;
    }

    .grid-2 {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 2rem;
    }

    .grid-3 {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.5rem;
    }

    @media (max-width: 1024px) {
        .grid-2, .grid-3 {
            grid-template-columns: 1fr;
        }
    }

    /* ===================================================================
       HEADER - Premium App Title
    =================================================================== */

    .app-header {
        background: linear-gradient(135deg, rgba(26, 31, 46, 0.9) 0%, rgba(20, 24, 37, 0.9) 100%);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(59, 130, 246, 0.2);
        padding: 1.5rem 2rem;
        margin-bottom: 2rem;
        box-shadow:
            0 4px 6px rgba(0, 0, 0, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
        position: sticky;
        top: 0;
        z-index: 100;
    }

    .app-title {
        font-size: 1.875rem;
        font-weight: 800;
        background: linear-gradient(135deg, #3B82F6 0%, #60A5FA 50%, #F59E0B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: -0.02em;
        display: inline-block;
    }

    .app-subtitle {
        font-size: 0.875rem;
        color: #94A3B8;
        margin-top: 0.375rem;
        font-weight: 400;
        letter-spacing: 0.02em;
    }

    /* ===================================================================
       EMPTY STATES
    =================================================================== */

    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: #64748B;
    }

    .empty-state-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        opacity: 0.3;
    }

    .empty-state-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #94A3B8;
        margin-bottom: 0.5rem;
    }

    .empty-state-description {
        font-size: 0.875rem;
        color: #64748B;
    }

    /* ===================================================================
       UTILITY CLASSES
    =================================================================== */

    .flex { display: flex; }
    .flex-col { flex-direction: column; }
    .items-center { align-items: center; }
    .justify-center { justify-content: center; }
    .justify-between { justify-content: space-between; }
    .gap-1 { gap: 0.25rem; }
    .gap-2 { gap: 0.5rem; }
    .gap-3 { gap: 0.75rem; }
    .gap-4 { gap: 1rem; }

    .w-full { width: 100%; }
    .h-full { height: 100%; }

    .text-xs { font-size: 0.75rem; }
    .text-sm { font-size: 0.875rem; }
    .text-base { font-size: 1rem; }
    .text-lg { font-size: 1.125rem; }
    .text-xl { font-size: 1.25rem; }

    .font-normal { font-weight: 400; }
    .font-medium { font-weight: 500; }
    .font-semibold { font-weight: 600; }
    .font-bold { font-weight: 700; }

    .mb-2 { margin-bottom: 0.5rem; }
    .mb-4 { margin-bottom: 1rem; }
    .mb-6 { margin-bottom: 1.5rem; }
    .mb-8 { margin-bottom: 2rem; }

    .mt-2 { margin-top: 0.5rem; }
    .mt-4 { margin-top: 1rem; }
    .mt-6 { margin-top: 1.5rem; }

    .p-4 { padding: 1rem; }
    .p-6 { padding: 1.5rem; }
    .py-3 { padding-top: 0.75rem; padding-bottom: 0.75rem; }

    .rounded { border-radius: 0.375rem; }
    .rounded-lg { border-radius: 0.5rem; }
    .rounded-xl { border-radius: 0.75rem; }
    .rounded-full { border-radius: 9999px; }

    .shadow-sm { box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
    .shadow { box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1); }
    .shadow-lg { box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }

    .cursor-pointer { cursor: pointer; }
    .select-none { user-select: none; }

    .transition { transition: all 0.2s; }
    .transition-colors { transition: color 0.2s, background-color 0.2s, border-color 0.2s; }

    .opacity-50 { opacity: 0.5; }
    .opacity-70 { opacity: 0.7; }

    .hover\:opacity-100:hover { opacity: 1; }

    /* Text colors */
    .text-white { color: #F8FAFC; }
    .text-gray-400 { color: #94A3B8; }
    .text-gray-500 { color: #64748B; }
    .text-blue-400 { color: #60A5FA; }
    .text-amber-400 { color: #FBBF24; }
    .text-green-400 { color: #34D399; }
    .text-red-400 { color: #F87171; }

    /* Background colors */
    .bg-blue-500 { background-color: #3B82F6; }
    .bg-amber-500 { background-color: #F59E0B; }

    /* ===================================================================
       RESPONSIVE DESIGN
    =================================================================== */

    @media (max-width: 768px) {
        .container {
            padding: 1rem;
        }

        .card {
            padding: 1.25rem;
            border-radius: 12px;
        }

        .app-header {
            padding: 1rem;
        }

        .app-title {
            font-size: 1.5rem;
        }

        .btn {
            padding: 0.625rem 1.25rem;
            font-size: 0.8125rem;
        }

        .results-table th,
        .results-table td {
            padding: 0.75rem 0.875rem;
            font-size: 0.8125rem;
        }
    }

    /* ===================================================================
       ACCESSIBILITY
    =================================================================== */

    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border-width: 0;
    }

    *:focus-visible {
        outline: 2px solid #3B82F6;
        outline-offset: 2px;
    }

    button:focus-visible,
    a:focus-visible,
    input:focus-visible,
    select:focus-visible {
        outline: 2px solid #3B82F6;
        outline-offset: 2px;
    }

    /* Reduced motion support */
    @media (prefers-reduced-motion: reduce) {
        *,
        *::before,
        *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
</style>
"""

# ============================================================================
# UTILITY FUNCTIONS FOR CLASS GENERATION
# ============================================================================

def input_classes(additional: str = "") -> str:
    """Standard input field classes"""
    return f"input-field {additional}".strip()

def button_classes(variant: str = "primary", additional: str = "") -> str:
    """Standard button classes"""
    return f"btn btn-{variant} {additional}".strip()

def card_classes(additional: str = "") -> str:
    """Standard card classes"""
    return f"card {additional}".strip()

def badge_classes(status: str, additional: str = "") -> str:
    """Badge with semantic status"""
    status_map = {
        'provido': 'badge-provido',
        'desprovido': 'badge-desprovido',
        'parcial': 'badge-parcial',
        'warning': 'badge-warning',
    }
    return f"badge {status_map.get(status.lower(), 'badge')} {additional}".strip()

def text_gradient(color: str = "blue") -> str:
    """Return gradient text class"""
    return f"text-gradient-{color}"
