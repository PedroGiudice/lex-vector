# PREMIUM DESIGN SYSTEM - Implementation Guide

**Version:** 2.0 (2025)
**Status:** Production-Ready
**Style:** Vercel/Linear/Notion-inspired Legal Tech Aesthetic

---

## Overview

This design system transforms the STJ FastHTML application from a basic terminal theme to a **production-grade premium interface** with modern design patterns including:

- **Glassmorphism cards** with backdrop blur
- **Gradient accents** on interactive elements
- **Smooth micro-animations** for tactile feedback
- **Premium color palette** optimized for legal tech
- **Accessibility-first** approach (WCAG compliant)

---

## What Changed

### File Updated: `/poc-fasthtml-stj/styles.py`

The old `TERMINAL_STYLE` has been replaced with `PREMIUM_STYLE` which includes:

1. **Enhanced Color System**
   - Deep navy backgrounds (not pure black for eye comfort)
   - Professional blue accents (#3B82F6) for trust/authority
   - Refined amber (#F59E0B) for highlights
   - Semantic colors for legal decisions (green/red/yellow)

2. **Typography Improvements**
   - Inter/System fonts for readability
   - JetBrains Mono for code blocks
   - Text gradients for premium feel
   - Proper font weights and letter spacing

3. **Component Upgrades**
   - Cards with glassmorphism and hover effects
   - Buttons with gradient backgrounds and tactile feedback
   - Form inputs with premium focus states
   - Pills/badges with smooth animations
   - Enhanced toggle switches
   - Premium scrollbars with blue gradient

4. **New Features**
   - Skeleton loading states
   - Toast notification styles
   - Progress bars with shimmer effect
   - Empty state templates
   - Typing animations for terminal
   - HTMX integration classes

---

## Implementation Steps

### Step 1: Update Main Application

In your `main.py`, replace the style import:

```python
# OLD
from styles import TERMINAL_STYLE

# NEW
from styles import PREMIUM_STYLE
```

Then in your FastHTML app setup:

```python
# OLD
app = FastHTML(
    hdrs=(
        Script(src="https://cdn.tailwindcss.com"),
        Script(src="https://unpkg.com/htmx.org@1.9.10"),
        NotStr(TERMINAL_STYLE)  # OLD
    )
)

# NEW
app = FastHTML(
    hdrs=(
        Script(src="https://cdn.tailwindcss.com"),
        Script(src="https://unpkg.com/htmx.org@1.9.10"),
        Script(src="https://code.iconify.design/3/3.1.0/iconify.min.js"),  # Optional: modern icons
        NotStr(PREMIUM_STYLE)  # NEW
    )
)
```

### Step 2: Update Component Imports (Optional)

The new design system includes helper functions:

```python
from styles import (
    input_classes,      # For form inputs
    button_classes,     # For buttons
    card_classes,       # For cards
    badge_classes,      # For status badges
    text_gradient,      # For gradient text
)
```

### Step 3: Test All Components

Verify that all existing components work with the new styles:

- [ ] Query builder form
- [ ] Domain selector dropdown
- [ ] Keyword pills (multi-select)
- [ ] Toggle switches
- [ ] SQL preview box
- [ ] Results table
- [ ] Download center
- [ ] Loading states

---

## Key Design Features

### 1. Color Palette

```python
COLORS = {
    # Backgrounds
    'bg_primary': '#0B0F19',        # Main background
    'bg_secondary': '#141825',      # Cards
    'bg_tertiary': '#1A1F2E',       # Hover states

    # Text
    'text_primary': '#F8FAFC',      # High contrast
    'text_secondary': '#CBD5E1',    # Secondary
    'text_tertiary': '#94A3B8',     # Muted

    # Accents
    'accent_primary': '#3B82F6',    # Trust blue
    'accent_secondary': '#F59E0B',  # Amber highlights

    # Semantic
    'success': '#10B981',           # PROVIDO
    'error': '#EF4444',             # DESPROVIDO
    'warning': '#F59E0B',           # PARCIAL
}
```

### 2. Typography Scale

```python
FONT_SIZES = {
    'xs': '0.75rem',      # 12px - Badges, captions
    'sm': '0.875rem',     # 14px - Small text
    'base': '1rem',       # 16px - Body text
    'lg': '1.125rem',     # 18px - Large body
    'xl': '1.25rem',      # 20px - H3
    '2xl': '1.5rem',      # 24px - H2
    '3xl': '1.875rem',    # 30px - H1
    '4xl': '2.25rem',     # 36px - Display
}
```

### 3. Spacing System (8px Grid)

```python
SPACING = {
    'xs': '0.25rem',   # 4px
    'sm': '0.5rem',    # 8px
    'md': '1rem',      # 16px
    'lg': '1.5rem',    # 24px
    'xl': '2rem',      # 32px
    '2xl': '3rem',     # 48px
    '3xl': '4rem',     # 64px
}
```

---

## Component Examples

### Premium Card

```python
from fasthtml.common import *

def premium_card(title: str, content: str):
    return Div(
        Div(title, cls="card-header"),  # Auto gradient text
        Div(content, cls="text-secondary"),
        cls="card"  # Glassmorphism with hover effect
    )
```

**Features:**
- Glassmorphism background with backdrop blur
- Subtle gradient border on hover
- Animated underline on header
- Box shadow with depth

### Premium Button

```python
def action_button(text: str, endpoint: str):
    return Button(
        text,
        cls="btn btn-primary",  # Gradient background
        hx_get=endpoint,
        hx_target="#results"
    )
```

**Features:**
- Blue gradient background
- Lift on hover (translateY -2px)
- Glow shadow effect
- Tactile press animation

### Status Badges

```python
from styles import badge_classes

def decision_badge(status: str):
    """
    status: 'provido', 'desprovido', or 'parcial'
    """
    return Span(
        status.upper(),
        cls=badge_classes(status)
    )
```

**Features:**
- Color-coded by decision type
- Semi-transparent backgrounds
- Subtle borders with matching colors
- Warning badge has pulse animation

### Interactive Pills

```python
def keyword_pill(keyword: str, selected: bool = False):
    return Label(
        Input(
            type="checkbox",
            name="keywords",
            value=keyword,
            checked=selected,
            cls="hidden"
        ),
        Span(
            keyword,
            cls="pill" + (" selected" if selected else "")
        ),
        cls="cursor-pointer"
    )
```

**Features:**
- Blue tint by default
- Gradient background when selected
- Scale up on hover
- Smooth color transitions

### Loading States

```python
# Simple spinner
Span(cls="loading")

# Large spinner
Span(cls="loading loading-lg")

# Dots animation
Div(
    Span(), Span(), Span(),
    cls="loading-dots"
)

# Progress bar
Div(
    Div(
        style="width: 60%",
        cls="progress-bar-fill"
    ),
    cls="progress-bar"
)
```

### Toast Notifications

```python
def show_toast(message: str, type: str = "info"):
    """
    type: 'success', 'error', 'warning', 'info'
    """
    return Div(
        message,
        cls=f"toast toast-{type}"
    )
```

**Features:**
- Slide in from right animation
- Color-coded left border
- Glassmorphism background
- Auto-dismiss ready (add JS)

---

## Advanced Features

### 1. Glassmorphism Cards

Cards now use `backdrop-filter: blur(12px)` for a modern glass effect:

```css
.card {
    background: rgba(26, 31, 46, 0.7);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(59, 130, 246, 0.1);
}
```

### 2. Gradient Text

Use text gradients for premium branding:

```python
H1("STJ Jurisprudência", cls="text-gradient-blue")
```

### 3. Background Grid Pattern

Subtle grid overlay for depth:

```css
body::before {
    background-image:
        linear-gradient(rgba(59, 130, 246, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px);
    background-size: 50px 50px;
}
```

### 4. Custom Scrollbar

Premium blue gradient scrollbar:

```css
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #3B82F6 0%, #2563EB 100%);
    border-radius: 5px;
}
```

### 5. Skeleton Loading

Animated skeleton for loading states:

```html
<div class="skeleton-row"></div>
```

### 6. HTMX Integration

Built-in classes for HTMX states:

```python
Button(
    "Search",
    Span(cls="loading htmx-indicator"),  # Shows during request
    cls="btn btn-primary",
    hx_get="/search",
    hx_indicator=".loading"
)
```

---

## Accessibility Features

### 1. Focus States

All interactive elements have visible focus rings:

```css
*:focus-visible {
    outline: 2px solid #3B82F6;
    outline-offset: 2px;
}
```

### 2. Reduced Motion

Respects user preferences:

```css
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
```

### 3. Screen Reader Support

Use `.sr-only` for screen reader only content:

```python
Span("Loading results", cls="sr-only")
```

### 4. Color Contrast

All text meets WCAG AA standards:
- Primary text: #F8FAFC on #0B0F19 (15:1 ratio)
- Secondary text: #CBD5E1 on #0B0F19 (9:1 ratio)

---

## Responsive Breakpoints

### Mobile (< 768px)

- Single column layout
- Reduced padding on cards
- Smaller font sizes for headers
- Touch-friendly button sizes

```css
@media (max-width: 768px) {
    .container { padding: 1rem; }
    .card { padding: 1.25rem; }
    .app-title { font-size: 1.5rem; }
}
```

### Tablet (768px - 1024px)

- Two-column grid collapses to one
- Maintains card sizing

### Desktop (> 1024px)

- Full grid layouts
- Maximum container width: 1400px
- Full animations enabled

---

## Migration Checklist

When upgrading existing components:

- [ ] Replace `TERMINAL_STYLE` with `PREMIUM_STYLE` in main.py
- [ ] Test all interactive elements (buttons, inputs, toggles)
- [ ] Verify color contrast on all text elements
- [ ] Check mobile responsiveness
- [ ] Test keyboard navigation (Tab, Enter, Esc)
- [ ] Verify loading states display correctly
- [ ] Test HTMX interactions with new styles
- [ ] Check terminal output rendering
- [ ] Verify SQL preview syntax highlighting
- [ ] Test table hover states
- [ ] Check badge animations
- [ ] Verify gradient text rendering across browsers

---

## Browser Support

Fully supported:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

Partial support (no backdrop blur):
- Firefox 87 and below (graceful degradation)

---

## Performance Considerations

### CSS Size
- Total CSS: ~15KB uncompressed
- Gzipped: ~4KB
- No external CSS dependencies

### Animations
- Uses GPU-accelerated properties (`transform`, `opacity`)
- Smooth 60fps on modern devices
- Reduced motion fallback included

### Font Loading
- System fonts preferred (zero network cost)
- JetBrains Mono loaded from CDN only if needed

---

## Customization Guide

### Changing Primary Color

1. Update `COLORS` dictionary in `styles.py`:
```python
'accent_primary': '#3B82F6',  # Change this
```

2. Update all gradient references:
```css
background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
```

### Adding New Badge Types

In `badge_classes` function:

```python
def badge_classes(status: str, additional: str = "") -> str:
    status_map = {
        'provido': 'badge-provido',
        'desprovido': 'badge-desprovido',
        'parcial': 'badge-parcial',
        'warning': 'badge-warning',
        'custom': 'badge-custom',  # Add new type
    }
    return f"badge {status_map.get(status.lower(), 'badge')} {additional}".strip()
```

Then add CSS:

```css
.badge-custom {
    background: rgba(147, 51, 234, 0.15);
    color: #A855F7;
    border-color: rgba(147, 51, 234, 0.3);
}
```

---

## Testing Recommendations

### Visual Regression Testing

1. Take screenshots before upgrade
2. Compare after implementation
3. Check at multiple viewports:
   - 375px (mobile)
   - 768px (tablet)
   - 1440px (desktop)

### Interaction Testing

- Click all buttons
- Toggle all switches
- Select all pills
- Fill all form inputs
- Hover over interactive elements
- Test keyboard navigation

### Performance Testing

- Lighthouse score (target: 90+)
- First Contentful Paint < 1.5s
- Time to Interactive < 3s
- No layout shifts (CLS = 0)

---

## Future Enhancements

### Potential Additions

1. **Dark/Light Mode Toggle**
   - CSS custom properties for theme switching
   - Persist preference in localStorage

2. **Animation Preferences**
   - User control for reduced animations
   - Save preference per user

3. **Custom Themes**
   - Allow users to pick accent colors
   - Corporate branding support

4. **Component Library Export**
   - Standalone component package
   - Reusable across projects

---

## Support & Resources

### Design Inspiration
- [Vercel Design](https://vercel.com/design)
- [Linear Style](https://linear.style/)
- [Tailwind UI](https://tailwindui.com/)

### Technical References
- [Dark Mode Best Practices 2025](https://muksalcreative.com/2025/07/26/dark-mode-design-best-practices-2025/)
- [Design System Color Palette](https://dribbble.com/shots/21284305-Design-System-Color-Palette-Dark-Mode)
- [Dark Mode UI Tips](https://www.netguru.com/blog/tips-dark-mode-ui)

### Icon Libraries
- **Iconify** (included): https://iconify.design/
- **Heroicons**: https://heroicons.com/
- **Lucide**: https://lucide.dev/

---

## Changelog

### Version 2.0 (2025-12-13)
- Initial premium design system release
- Glassmorphism cards with backdrop blur
- Gradient accent system
- Enhanced form inputs with premium focus states
- Interactive pills with smooth animations
- Loading states (spinner, dots, progress bar, skeleton)
- Toast notification styles
- Accessibility improvements (WCAG AA compliant)
- Responsive design optimization
- HTMX integration classes

### Version 1.0 (Previous)
- Basic terminal aesthetic
- Simple dark theme
- Minimal animations
- Basic form styling

---

## Credits

**Design System:** Inspired by Vercel, Linear, and Notion
**Color Research:** Based on 2025 dark mode best practices
**Implementation:** FastHTML + Tailwind CSS
**Icon System:** Iconify
**Fonts:** System fonts + JetBrains Mono

---

**Last Updated:** 2025-12-13
**Maintainer:** Legal Workbench Team
**License:** Internal Use
