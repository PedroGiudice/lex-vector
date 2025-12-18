"""
CSS generation from theme configurations.

Generates:
1. CSS custom properties (:root variables)
2. Base component styles (using variables)
3. Utility classes

The generated CSS uses CSS custom properties (variables) so themes
can be switched at runtime by updating :root values via JavaScript.
"""

from .base import BaseTheme


def generate_css_variables(theme: BaseTheme) -> str:
    """
    Generate CSS custom properties for a theme.

    This is the lightweight version - only variables, no component styles.
    Use for theme switching without full CSS regeneration.
    """
    vars_dict = theme.to_css_vars()
    vars_css = "\n".join(f"    {k}: {v};" for k, v in vars_dict.items())

    return f"""
:root {{
{vars_css}
}}
"""


def generate_css(theme: BaseTheme) -> str:
    """
    Generate complete CSS stylesheet from a theme.

    Includes:
    - CSS custom properties
    - Reset/normalization
    - Component styles (buttons, cards, badges, etc.)
    - Utility classes
    - Animations
    """

    return f"""<style>
/* ============================================================================
   THEME: {theme.name}
   Generated CSS - Do not edit manually
   ============================================================================ */

/* ----------------------------------------------------------------------------
   CSS Custom Properties (Theme Variables)
   ---------------------------------------------------------------------------- */
:root {{
    /* Backgrounds */
    --bg-primary: {theme.bg_primary};
    --bg-secondary: {theme.bg_secondary};
    --bg-tertiary: {theme.bg_tertiary};
    --bg-hover: {theme.bg_hover};

    /* Text */
    --text-primary: {theme.text_primary};
    --text-secondary: {theme.text_secondary};
    --text-muted: {theme.text_muted};

    /* Accent (module-specific) */
    --accent: {theme.accent_primary};
    --accent-secondary: {theme.accent_secondary};
    --accent-muted: {theme.accent_muted};
    --accent-glow: {theme.accent_glow};

    /* Semantic */
    --success: {theme.success};
    --danger: {theme.danger};
    --warning: {theme.warning};
    --info: {theme.info};

    /* Borders */
    --border: {theme.border_default};
    --border-hover: {theme.border_hover};
    --border-focus: {theme.border_focus};

    /* Typography */
    --font-mono: {theme.font_mono};
    --font-sans: {theme.font_sans};

    /* Transitions */
    --transition-fast: 150ms ease;
    --transition-normal: 200ms ease;
    --transition-slow: 300ms ease;
}}

/* Smooth theme transitions */
:root {{
    transition:
        --accent var(--transition-normal),
        --accent-secondary var(--transition-normal),
        --accent-glow var(--transition-normal);
}}

/* ----------------------------------------------------------------------------
   Base Reset & Normalization
   ---------------------------------------------------------------------------- */
*, *::before, *::after {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

html {{
    font-size: 16px;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}}

body {{
    background-color: var(--bg-primary);
    color: var(--text-primary);
    font-family: var(--font-sans);
    line-height: 1.6;
    min-height: 100vh;
}}

/* Custom Scrollbar */
::-webkit-scrollbar {{
    width: 8px;
    height: 8px;
}}

::-webkit-scrollbar-track {{
    background: var(--bg-secondary);
}}

::-webkit-scrollbar-thumb {{
    background: var(--bg-hover);
    border-radius: 4px;
}}

::-webkit-scrollbar-thumb:hover {{
    background: var(--border-hover);
}}

/* ----------------------------------------------------------------------------
   Layout Components
   ---------------------------------------------------------------------------- */
.container {{
    width: 100%;
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 1rem;
}}

.grid-2 {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
}}

@media (max-width: 768px) {{
    .grid-2 {{
        grid-template-columns: 1fr;
    }}
}}

/* ----------------------------------------------------------------------------
   Cards
   ---------------------------------------------------------------------------- */
.card {{
    background-color: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
}}

.card-header {{
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--border);
    background: linear-gradient(90deg, var(--accent-glow) 0%, transparent 100%);
}}

.card-header h2,
.card-header h3 {{
    color: var(--accent);
    font-family: var(--font-mono);
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}}

.card-body {{
    padding: 1.25rem;
}}

.card-footer {{
    padding: 1rem 1.25rem;
    border-top: 1px solid var(--border);
    background-color: var(--bg-tertiary);
}}

/* ----------------------------------------------------------------------------
   Buttons
   ---------------------------------------------------------------------------- */
.btn {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.625rem 1.25rem;
    font-family: var(--font-sans);
    font-size: 0.875rem;
    font-weight: 500;
    border-radius: 6px;
    border: 1px solid transparent;
    cursor: pointer;
    transition: all var(--transition-fast);
    text-decoration: none;
}}

.btn:disabled {{
    opacity: 0.5;
    cursor: not-allowed;
}}

.btn-primary {{
    background-color: var(--accent);
    color: var(--bg-primary);
    border-color: var(--accent);
}}

.btn-primary:hover:not(:disabled) {{
    background-color: var(--accent-secondary);
    border-color: var(--accent-secondary);
}}

.btn-secondary {{
    background-color: transparent;
    color: var(--text-secondary);
    border-color: var(--border);
}}

.btn-secondary:hover:not(:disabled) {{
    background-color: var(--bg-hover);
    color: var(--text-primary);
    border-color: var(--border-hover);
}}

.btn-ghost {{
    background-color: transparent;
    color: var(--text-secondary);
    border-color: transparent;
}}

.btn-ghost:hover:not(:disabled) {{
    background-color: var(--bg-hover);
    color: var(--accent);
}}

/* ----------------------------------------------------------------------------
   Form Elements
   ---------------------------------------------------------------------------- */
.input-field {{
    width: 100%;
    padding: 0.625rem 0.875rem;
    background-color: var(--bg-tertiary);
    color: var(--text-primary);
    border: 1px solid var(--border);
    border-radius: 6px;
    font-family: var(--font-sans);
    font-size: 0.875rem;
    transition: all var(--transition-fast);
}}

.input-field:hover {{
    border-color: var(--border-hover);
}}

.input-field:focus {{
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-glow);
}}

.input-field::placeholder {{
    color: var(--text-muted);
}}

/* Select dropdown */
select.input-field {{
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2394a3b8'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 0.75rem center;
    background-size: 1rem;
    padding-right: 2.5rem;
}}

/* Toggle Switch */
.toggle-switch {{
    position: relative;
    display: inline-block;
    width: 44px;
    height: 24px;
}}

.toggle-switch input {{
    opacity: 0;
    width: 0;
    height: 0;
}}

.toggle-slider {{
    position: absolute;
    cursor: pointer;
    inset: 0;
    background-color: var(--bg-hover);
    border-radius: 24px;
    transition: var(--transition-fast);
}}

.toggle-slider::before {{
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: var(--text-secondary);
    border-radius: 50%;
    transition: var(--transition-fast);
}}

input:checked + .toggle-slider {{
    background-color: var(--accent);
}}

input:checked + .toggle-slider::before {{
    transform: translateX(20px);
    background-color: var(--bg-primary);
}}

/* Pills (multi-select) */
.pill {{
    display: inline-flex;
    align-items: center;
    padding: 0.375rem 0.75rem;
    background-color: transparent;
    color: var(--text-secondary);
    border: 1px solid var(--border);
    border-radius: 9999px;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all var(--transition-fast);
}}

.pill:hover {{
    border-color: var(--accent);
    color: var(--accent);
}}

.pill.selected {{
    background-color: var(--accent);
    color: var(--bg-primary);
    border-color: var(--accent);
}}

/* ----------------------------------------------------------------------------
   Badges
   ---------------------------------------------------------------------------- */
.badge {{
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.625rem;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

.badge-provido {{
    background-color: rgba(34, 197, 94, 0.15);
    color: var(--success);
    border: 1px solid var(--success);
}}

.badge-desprovido {{
    background-color: rgba(220, 38, 38, 0.15);
    color: var(--danger);
    border: 1px solid var(--danger);
}}

.badge-parcial {{
    background-color: rgba(234, 179, 8, 0.15);
    color: var(--warning);
    border: 1px solid var(--warning);
}}

.badge-info {{
    background-color: rgba(59, 130, 246, 0.15);
    color: var(--info);
    border: 1px solid var(--info);
}}

.badge-accent {{
    background-color: var(--accent-glow);
    color: var(--accent);
    border: 1px solid var(--accent);
}}

/* ----------------------------------------------------------------------------
   Terminal / Code Display
   ---------------------------------------------------------------------------- */
.terminal {{
    background-color: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1rem;
    font-family: var(--font-mono);
    font-size: 0.8125rem;
    line-height: 1.5;
    max-height: 400px;
    overflow-y: auto;
}}

.terminal-line {{
    padding: 0.125rem 0;
    color: var(--accent);
}}

.terminal-error {{
    color: var(--danger);
}}

.terminal-warning {{
    color: var(--warning);
}}

.terminal-success {{
    color: var(--success);
}}

.sql-preview {{
    background-color: rgba(0, 0, 0, 0.3);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1rem;
    font-family: var(--font-mono);
    font-size: 0.8125rem;
    color: var(--accent);
    white-space: pre-wrap;
    overflow-x: auto;
}}

/* ----------------------------------------------------------------------------
   Tables
   ---------------------------------------------------------------------------- */
.results-table {{
    width: 100%;
    border-collapse: collapse;
}}

.results-table th {{
    background-color: var(--bg-tertiary);
    color: var(--text-secondary);
    font-weight: 600;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.75rem 1rem;
    text-align: left;
    border-bottom: 1px solid var(--border);
}}

.results-table td {{
    padding: 0.875rem 1rem;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
}}

.results-table tr:hover td {{
    background-color: var(--bg-hover);
}}

/* ----------------------------------------------------------------------------
   Module Header
   ---------------------------------------------------------------------------- */
.module-header {{
    background: linear-gradient(90deg, var(--accent-glow) 0%, transparent 100%);
    border-left: 3px solid var(--accent);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}}

.module-header h1 {{
    font-family: var(--font-mono);
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}}

.module-header .tagline {{
    color: var(--text-secondary);
    font-size: 0.875rem;
}}

/* ----------------------------------------------------------------------------
   Sidebar Navigation
   ---------------------------------------------------------------------------- */
.sidebar {{
    width: 240px;
    background-color: var(--bg-secondary);
    border-right: 1px solid var(--border);
    min-height: 100vh;
    padding: 1rem 0;
}}

.sidebar-header {{
    padding: 0 1rem 1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}}

.sidebar-title {{
    font-family: var(--font-mono);
    font-size: 1rem;
    font-weight: 700;
    color: var(--accent);
}}

.sidebar-item {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    color: var(--text-secondary);
    text-decoration: none;
    transition: all var(--transition-fast);
    position: relative;
    cursor: pointer;
    border: none;
    background: none;
    width: 100%;
    text-align: left;
    font-size: 0.875rem;
}}

.sidebar-item:hover {{
    background-color: var(--bg-hover);
    color: var(--text-primary);
}}

.sidebar-item.active {{
    color: var(--accent);
    background-color: var(--accent-glow);
}}

.sidebar-item.active::before {{
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background-color: var(--accent);
}}

.sidebar-icon {{
    font-size: 1.125rem;
}}

/* ----------------------------------------------------------------------------
   Loading States
   ---------------------------------------------------------------------------- */
.loading {{
    display: inline-block;
    width: 1rem;
    height: 1rem;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}}

@keyframes spin {{
    to {{ transform: rotate(360deg); }}
}}

.htmx-indicator {{
    display: none;
}}

.htmx-request .htmx-indicator {{
    display: inline-block;
}}

.htmx-request.htmx-indicator {{
    display: inline-block;
}}

/* Skeleton loading */
.skeleton {{
    background: linear-gradient(
        90deg,
        var(--bg-tertiary) 25%,
        var(--bg-hover) 50%,
        var(--bg-tertiary) 75%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 4px;
}}

@keyframes shimmer {{
    0% {{ background-position: 200% 0; }}
    100% {{ background-position: -200% 0; }}
}}

/* ----------------------------------------------------------------------------
   App Layout
   ---------------------------------------------------------------------------- */
.app-layout {{
    display: flex;
    min-height: 100vh;
}}

.app-main {{
    flex: 1;
    padding: 1.5rem;
    overflow-y: auto;
}}

.app-header {{
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--border);
    background-color: var(--bg-secondary);
}}

/* ----------------------------------------------------------------------------
   Workspace (HTMX target area)
   ---------------------------------------------------------------------------- */
#workspace {{
    min-height: calc(100vh - 4rem);
}}

#workspace.htmx-swapping {{
    opacity: 0.5;
    transition: opacity var(--transition-fast);
}}

#workspace.htmx-settling {{
    opacity: 1;
    transition: opacity var(--transition-fast);
}}
</style>"""
