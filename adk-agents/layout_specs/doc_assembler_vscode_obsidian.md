# Doc Assembler Layout Specification v1

> Approved layout decisions from Q&A session (2024-12-17)

## Visual Identity

### Inspiration
- **Primary**: VS Code, Obsidian, Claude Desktop, GitHub (dark modes)
- **Style**: Brutalism + Glassmorphism hybrid
  - Brutalism: Clean geometric forms, bold typography
  - Glassmorphism: Blur effects on overlays/modals, subtle transparency
- **UX Priority**: Seamless, intuitive interaction - decorative elements welcome when they enhance usability

### NOT This
- No "legal green" or "juridical" color schemes
- Not a terminal aesthetic

## Color Palette

### Backgrounds
| Element | Color | Notes |
|---------|-------|-------|
| Main background | `#1e1e2e` | VS Code-like dark |
| Sidebar background | `#181825` | Slightly darker |
| Doc viewer | `#f5f5f5` or `#ffffff` | Paper-like, toggleable |
| Overlay/Modal | `rgba(24, 24, 37, 0.85)` | With backdrop-blur |

### Borders & Dividers
| Element | Style |
|---------|-------|
| Panel dividers | `1px solid #3f3f46` |
| Resize handle | Same color, with hover state `#52525b` |
| Focus rings | `#3b82f6` (blue-500) |

### Text
| Type | Color |
|------|-------|
| Primary | `#e4e4e7` |
| Secondary | `#a1a1aa` |
| Muted | `#71717a` |
| On light bg | `#1f2937` |

### Accents
| Use | Color |
|-----|-------|
| Interactive elements | `#3b82f6` (blue-500) |
| Success/Valid | `#22c55e` (green-500) |
| Warning | `#f59e0b` (amber-500) |
| Error | `#ef4444` (red-500) |
| Annotation highlight | `#fbbf24` (amber-400) with 40% opacity |

## Layout Structure

### Columns
```
┌──────────┬────────────────────────────────┬──────────┐
│  20%     │            60%                 │   20%    │
│ Sidebar  │         Main Content           │ Sidebar  │
│  Left    │        (Doc Viewer)            │  Right   │
│          │                                │          │
│ Collaps- │    Paper-like background       │ Annota-  │
│ ible     │    Monospace font              │ tions    │
│ tabs     │    Syntax highlighting         │ panel    │
└──────────┴────────────────────────────────┴──────────┘
```

### Sidebar Behavior
- **Resizable**: Drag handles between panels
- **Collapsible**: Click to collapse to icon bar
- **Minimum width**: 200px expanded, 48px collapsed
- **Maximum width**: 400px

### Header
- **Style**: Minimal, icons only
- **Height**: 48px max
- **Content**: Logo icon, breadcrumb, action icons
- **No**: Full title bar or large headers

### Document Viewer
- **Background**: Light (paper-like) - #f5f5f5 default
- **Toggle**: User can switch to dark mode
- **Padding**: 32px horizontal, 24px vertical
- **Max width**: 800px centered (like reading mode)

## Typography

### Font Stack
```css
/* UI Elements */
--font-ui: 'Inter', system-ui, -apple-system, sans-serif;

/* Document Content */
--font-document: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;

/* Headings */
--font-heading: 'Inter', system-ui, sans-serif;
```

### Sizes
| Element | Size | Weight |
|---------|------|--------|
| H1 | 24px | 700 |
| H2 | 18px | 600 |
| H3 | 16px | 600 |
| Body UI | 14px | 400 |
| Document | 14px | 400 |
| Small/Caption | 12px | 400 |

### Line Height
- UI: 1.5
- Document: 1.75 (better readability)

## Components

### Sidebar Left Tabs
```
┌─────────────────────┐
│ [v] Upload          │  ← Collapsible section
│ ┌─────────────────┐ │
│ │   Dropzone      │ │
│ │   Click/Drop    │ │
│ └─────────────────┘ │
├─────────────────────┤
│ [v] Templates       │  ← Collapsible section
│   • Template 1      │
│   • Template 2      │
├─────────────────────┤
│ [>] How to Use      │  ← Collapsed by default
└─────────────────────┘
```

### Annotations (Sidebar Right)
```
┌─────────────────────┐
│ Annotations    (3)  │
│─────────────────────│
│ ┌─────────────────┐ │
│ │ nome_autor      │ │
│ │ Line 12         │ │
│ │ "João Silva..." │ │
│ └─────────────────┘ │
│ ┌─────────────────┐ │
│ │ data_contrato   │ │
│ │ Line 24         │ │
│ │ "15/03/2024"    │ │
│ └─────────────────┘ │
└─────────────────────┘
```

### Document Highlights
- **Selection**: Blue border + light blue background
- **Annotation**: Amber/yellow highlight (#fbbf24 at 40% opacity)
- **Hover**: Subtle brightness increase
- **Active**: Border emphasis

## Interactions

### Resize Handles
- Visible on hover (1px → 4px on hover)
- Cursor: `col-resize`
- Color transition: 150ms ease

### Collapsible Sections
- Smooth height transition (200ms ease)
- Chevron rotation animation
- Persist state in localStorage

### Buttons
- Border-radius: 6px
- Padding: 8px 16px
- Hover: brightness(1.1)
- Active: scale(0.98)

## Responsive

### Breakpoints
```css
--sm: 640px;
--md: 768px;
--lg: 1024px;
--xl: 1280px;
```

### Mobile (< 768px)
- Single column layout
- Sidebars become bottom sheets
- Document full width

### Tablet (768px - 1024px)
- Two columns (main + right sidebar)
- Left sidebar collapses to icon bar

### Desktop (> 1024px)
- Full three-column layout
- All panels visible

## Accessibility

### Requirements
- Minimum contrast ratio: 4.5:1
- Focus indicators visible
- Keyboard navigation for all actions
- ARIA labels on interactive elements
- Screen reader announcements for state changes

### Dark Mode Document Viewer
When toggled to dark:
- Background: #1e1e2e
- Text: #e4e4e7
- Maintain annotation visibility

---

*Version 1.0 - 2024-12-17*
