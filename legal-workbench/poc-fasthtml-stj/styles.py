"""
Terminal Aesthetic Theme for STJ Module
Colors and Tailwind utility classes
"""

# Color Palette
COLORS = {
    'bg_primary': '#0a0f1a',      # Near-black blue background
    'text_primary': '#e2e8f0',    # Cool gray text
    'accent_amber': '#f59e0b',    # Actions, highlights
    'accent_red': '#dc2626',      # Warnings, DESPROVIDO
    'accent_green': '#22c55e',    # Success, PROVIDO
    'accent_yellow': '#eab308',   # PARCIAL badges
    'border': '#1e293b',          # Subtle borders
    'bg_secondary': '#1a2332',    # Card backgrounds
    'bg_hover': '#2d3748',        # Hover states
}

# CDN for Tailwind CSS
TAILWIND_CDN = "https://cdn.tailwindcss.com"

# Base HTML template with custom CSS
TERMINAL_STYLE = """
<style>
    * {
        box-sizing: border-box;
    }

    body {
        background-color: #0a0f1a;
        color: #e2e8f0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        margin: 0;
        padding: 0;
    }

    /* Monospace for data */
    .font-mono {
        font-family: 'Courier New', Courier, monospace;
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #1a2332;
    }

    ::-webkit-scrollbar-thumb {
        background: #2d3748;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #4a5568;
    }

    /* Badge styles */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        border-radius: 0.25rem;
        letter-spacing: 0.05em;
    }

    .badge-provido {
        background-color: rgba(34, 197, 94, 0.15);
        color: #22c55e;
        border: 1px solid #22c55e;
    }

    .badge-desprovido {
        background-color: rgba(220, 38, 38, 0.15);
        color: #dc2626;
        border: 1px solid #dc2626;
    }

    .badge-parcial {
        background-color: rgba(234, 179, 8, 0.15);
        color: #eab308;
        border: 1px solid #eab308;
    }

    .badge-warning {
        background-color: rgba(220, 38, 38, 0.1);
        color: #dc2626;
        border: 1px solid #dc2626;
        animation: pulse-border 2s infinite;
    }

    @keyframes pulse-border {
        0%, 100% { border-color: #dc2626; opacity: 1; }
        50% { border-color: #ef4444; opacity: 0.8; }
    }

    /* Card styles */
    .card {
        background-color: #1a2332;
        border: 1px solid #1e293b;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }

    .card-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: #f59e0b;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #1e293b;
    }

    /* Input styles */
    .input-field {
        background-color: #0a0f1a;
        border: 1px solid #1e293b;
        color: #e2e8f0;
        padding: 0.5rem 0.75rem;
        border-radius: 0.375rem;
        width: 100%;
        transition: all 0.2s;
    }

    .input-field:focus {
        outline: none;
        border-color: #f59e0b;
        box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.1);
    }

    .input-field:hover {
        border-color: #2d3748;
    }

    /* Button styles */
    .btn {
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        border: none;
        font-size: 0.875rem;
    }

    .btn-primary {
        background-color: #f59e0b;
        color: #0a0f1a;
    }

    .btn-primary:hover {
        background-color: #d97706;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(245, 158, 11, 0.2);
    }

    .btn-secondary {
        background-color: #1e293b;
        color: #e2e8f0;
        border: 1px solid #2d3748;
    }

    .btn-secondary:hover {
        background-color: #2d3748;
        border-color: #4a5568;
    }

    .btn-template {
        background-color: rgba(245, 158, 11, 0.1);
        color: #f59e0b;
        border: 1px solid #f59e0b;
        padding: 0.375rem 0.75rem;
        font-size: 0.75rem;
    }

    .btn-template:hover {
        background-color: rgba(245, 158, 11, 0.2);
    }

    /* Terminal/Code block styles */
    .terminal {
        background-color: #0a0f1a;
        border: 1px solid #1e293b;
        border-radius: 0.5rem;
        padding: 1rem;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.875rem;
        color: #f59e0b;
        overflow-x: auto;
        max-height: 400px;
        overflow-y: auto;
    }

    .terminal-line {
        color: #22c55e;
        margin: 0.25rem 0;
        line-height: 1.5;
    }

    .terminal-error {
        color: #dc2626;
    }

    .terminal-warning {
        color: #eab308;
    }

    /* SQL Preview */
    .sql-preview {
        background-color: #0a0f1a;
        border: 1px solid #2d3748;
        border-radius: 0.5rem;
        padding: 1rem;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.8rem;
        color: #f59e0b;
        white-space: pre-wrap;
        word-wrap: break-word;
        line-height: 1.6;
    }

    .sql-keyword {
        color: #60a5fa;
        font-weight: 600;
    }

    .sql-table {
        color: #22c55e;
    }

    .sql-string {
        color: #fbbf24;
    }

    /* Toggle switch */
    .toggle-switch {
        position: relative;
        display: inline-block;
        width: 48px;
        height: 24px;
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
        background-color: #1e293b;
        border: 1px solid #2d3748;
        transition: 0.3s;
        border-radius: 24px;
    }

    .toggle-slider:before {
        position: absolute;
        content: "";
        height: 16px;
        width: 16px;
        left: 3px;
        bottom: 3px;
        background-color: #4a5568;
        transition: 0.3s;
        border-radius: 50%;
    }

    input:checked + .toggle-slider {
        background-color: rgba(245, 158, 11, 0.2);
        border-color: #f59e0b;
    }

    input:checked + .toggle-slider:before {
        transform: translateX(24px);
        background-color: #f59e0b;
    }

    /* Multi-select pills */
    .pill {
        display: inline-block;
        background-color: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid #f59e0b;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        margin: 0.25rem;
        cursor: pointer;
        transition: all 0.2s;
    }

    .pill:hover {
        background-color: rgba(245, 158, 11, 0.25);
        transform: scale(1.05);
    }

    .pill.selected {
        background-color: #f59e0b;
        color: #0a0f1a;
    }

    /* Results table */
    .results-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin-top: 1rem;
    }

    .results-table th {
        background-color: #1a2332;
        color: #f59e0b;
        padding: 0.75rem;
        text-align: left;
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border-bottom: 2px solid #1e293b;
    }

    .results-table td {
        padding: 0.75rem;
        border-bottom: 1px solid #1e293b;
        font-size: 0.875rem;
    }

    .results-table tr:hover {
        background-color: rgba(245, 158, 11, 0.05);
    }

    /* Loading animation */
    .loading {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid #1e293b;
        border-top-color: #f59e0b;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    /* HTMX indicators */
    .htmx-indicator {
        display: none;
    }

    .htmx-request .htmx-indicator {
        display: inline-block;
    }

    /* Layout utilities */
    .container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 2rem;
    }

    .grid-2 {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1.5rem;
    }

    @media (max-width: 768px) {
        .grid-2 {
            grid-template-columns: 1fr;
        }
    }

    /* Header */
    .app-header {
        background-color: #1a2332;
        border-bottom: 2px solid #f59e0b;
        padding: 1.5rem 2rem;
        margin-bottom: 2rem;
    }

    .app-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #f59e0b;
        margin: 0;
        font-family: 'Courier New', Courier, monospace;
    }

    .app-subtitle {
        font-size: 0.875rem;
        color: #94a3b8;
        margin-top: 0.25rem;
    }
</style>
"""

# Utility functions for common class combinations
def input_classes(additional: str = "") -> str:
    """Standard input field classes"""
    return f"input-field {additional}".strip()

def button_classes(variant: str = "primary", additional: str = "") -> str:
    """Standard button classes"""
    return f"btn btn-{variant} {additional}".strip()

def card_classes(additional: str = "") -> str:
    """Standard card classes"""
    return f"card {additional}".strip()
