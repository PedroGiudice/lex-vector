/**
 * Theme Switcher for FastHTML Workbench
 *
 * Handles smooth theme transitions via CSS custom properties.
 * Listens for HTMX events to switch themes when modules load.
 */

// Theme definitions (accent colors per module)
const THEMES = {
    shared: {
        accent: '#f59e0b',
        accentSecondary: '#d97706',
        accentGlow: 'rgba(245, 158, 11, 0.15)',
    },
    stj: {
        accent: '#8b5cf6',
        accentSecondary: '#7c3aed',
        accentGlow: 'rgba(139, 92, 246, 0.15)',
    },
    text_extractor: {
        accent: '#d97706',
        accentSecondary: '#b45309',
        accentGlow: 'rgba(217, 119, 6, 0.15)',
    },
    doc_assembler: {
        accent: '#0ea5e9',
        accentSecondary: '#0284c7',
        accentGlow: 'rgba(14, 165, 233, 0.15)',
    },
    trello: {
        accent: '#10b981',
        accentSecondary: '#059669',
        accentGlow: 'rgba(16, 185, 129, 0.15)',
    },
};

// Current theme tracking
let currentTheme = 'shared';

/**
 * Apply a theme by updating CSS custom properties.
 * @param {string} themeId - Theme identifier
 */
function applyTheme(themeId) {
    const theme = THEMES[themeId] || THEMES.shared;
    const root = document.documentElement;

    // Update CSS variables
    root.style.setProperty('--accent', theme.accent);
    root.style.setProperty('--accent-secondary', theme.accentSecondary);
    root.style.setProperty('--accent-glow', theme.accentGlow);
    root.style.setProperty('--border-focus', theme.accent);

    currentTheme = themeId;
    console.log(`[Theme] Switched to: ${themeId}`);
}

/**
 * Preload theme before HTMX request completes.
 * Called from hx-on--htmx-before-request attribute.
 * @param {string} themeId - Theme identifier
 */
function preloadTheme(themeId) {
    // Add slight delay for visual effect
    requestAnimationFrame(() => {
        applyTheme(themeId);
    });
}

/**
 * Update sidebar active state.
 * @param {string} moduleId - Active module identifier
 */
function updateSidebarActive(moduleId) {
    // Remove active from all items
    document.querySelectorAll('.sidebar-item').forEach(item => {
        item.classList.remove('active');
    });

    // Add active to matching item
    const activeItem = document.querySelector(
        `.sidebar-item[hx-get*="/m/${moduleId}/"]`
    );
    if (activeItem) {
        activeItem.classList.add('active');
    }
}

// Listen for HTMX theme switch events
document.body.addEventListener('themeSwitch', (event) => {
    const { theme } = event.detail;
    if (theme) {
        applyTheme(theme);
        updateSidebarActive(theme);
    }
});

// Listen for HTMX after-swap to handle theme from response headers
document.body.addEventListener('htmx:afterSwap', (event) => {
    // Check for theme in HX-Trigger header
    const trigger = event.detail.xhr?.getResponseHeader('HX-Trigger');
    if (trigger) {
        try {
            const parsed = JSON.parse(trigger);
            if (parsed.themeSwitch?.theme) {
                applyTheme(parsed.themeSwitch.theme);
                updateSidebarActive(parsed.themeSwitch.theme);
            }
        } catch (e) {
            // Not JSON or no theme, ignore
        }
    }
});

// Handle browser back/forward navigation
window.addEventListener('popstate', () => {
    const path = window.location.pathname;
    const match = path.match(/^\/m\/([^/]+)/);
    if (match) {
        const moduleId = match[1];
        applyTheme(moduleId);
        updateSidebarActive(moduleId);
    } else {
        applyTheme('shared');
    }
});

// Initialize theme based on current URL
document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    const match = path.match(/^\/m\/([^/]+)/);
    if (match) {
        applyTheme(match[1]);
        updateSidebarActive(match[1]);
    }
});
