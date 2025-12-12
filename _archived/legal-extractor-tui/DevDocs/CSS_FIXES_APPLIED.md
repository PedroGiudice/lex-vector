# CSS Syntax Fixes for Legal Extractor TUI

## Date: 2025-11-27

## Problem
Textual CSS (TCSS) does NOT support standard CSS `var(--name)` syntax. It uses `$name` instead.

## Files Fixed

### 1. base.tcss (246 lines)
**Changes:**
- Removed `:root { ... }` block containing CSS variables
- Converted all variables from `--name` to `$name` format (54 variables defined)
- Removed unsupported `::-webkit-scrollbar` pseudo-elements
- Fixed all `var(--name)` references to `$name`

**Variables defined:**
- `$primary`, `$secondary`, `$accent`
- `$foreground`, `$background`, `$surface`, `$panel`
- `$success`, `$warning`, `$error`, `$text-muted`
- `$stage-pending`, `$stage-active`, `$stage-complete`, `$stage-error`
- `$panel-bg`, `$panel-header`, `$panel-border`
- `$confidence-high`, `$confidence-medium`, `$confidence-low`

### 2. layout.tcss (347 lines)
**Changes:**
- Replaced all `var(--primary)` → `$primary`
- Replaced all `var(--accent)` → `$accent`
- Replaced all `var(--surface)` → `$surface`
- Replaced all `var(--panel)` → `$panel`
- Replaced all `var(--panel-bg)` → `$panel-bg`
- Replaced all `var(--panel-border)` → `$panel-border`
- Replaced all `var(--background)` → `$background`
- Removed unsupported `layer: overlay` property
- Removed unsupported `border-radius` properties

### 3. widgets.tcss (745 lines)
**Changes:**
- Replaced ALL `var(--name)` references with `$name` (18 different variables)
- Fixed references in:
  - FileSelector widget
  - SystemSelector widget
  - ConfigPanel widget
  - ExtractionProgress widget (including stage colors)
  - ResultsPanel widget
  - All standard Textual widgets (Button, Input, Label, etc.)
  - LogPanel widget
  - StatusBar widget

### 4. animations.tcss (85 lines)
**Status:** Already correct - uses `$variable` syntax throughout

## Conversion Rules Applied

```
var(--primary)           → $primary
var(--accent)            → $accent
var(--secondary)         → $secondary
var(--foreground)        → $foreground
var(--background)        → $background
var(--surface)           → $surface
var(--panel)             → $panel
var(--success)           → $success
var(--warning)           → $warning
var(--error)             → $error
var(--text-muted)        → $text-muted
var(--panel-bg)          → $panel-bg
var(--panel-border)      → $panel-border
var(--panel-header)      → $panel-header
var(--stage-pending)     → $stage-pending
var(--stage-active)      → $stage-active
var(--stage-complete)    → $stage-complete
var(--stage-error)       → $stage-error
var(--confidence-high)   → $confidence-high
var(--confidence-medium) → $confidence-medium
var(--confidence-low)    → $confidence-low
```

## Unsupported Properties Removed

1. `:root { ... }` - Not used in Textual, replaced with top-level `$variable` definitions
2. `::-webkit-scrollbar*` - Textual handles scrollbars automatically
3. `border-radius` - Not supported in Textual
4. `layer: overlay` - Not supported in Textual
5. `@keyframes` - Not present, but would be unsupported
6. `animation:` - Not present, but would be unsupported
7. `transform:` - Not present, but would be unsupported

## Verification

Run this command to verify no more `var(--` remains:

```bash
grep -r "var(--" /home/cmr-auto/claude-work/repos/Claude-Code-Projetos/legal-extractor-tui/src/legal_extractor_tui/styles/
```

**Result:** No output (confirmed - all fixed)

## Statistics

- Total lines of TCSS: 1,423
- Files modified: 3 (base.tcss, layout.tcss, widgets.tcss)
- Variables defined: 54
- CSS variable conversions: ~150+ instances

## Next Steps

1. Test the application with the fixed CSS
2. Verify all widgets render correctly
3. Check that theme colors are applied properly
4. Ensure no CSS-related errors in Textual console

## References

- Textual CSS documentation: https://textual.textualize.io/guide/CSS/
- Variable syntax: https://textual.textualize.io/guide/CSS/#css-variables
