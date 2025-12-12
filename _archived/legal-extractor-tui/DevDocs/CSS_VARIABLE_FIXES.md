# CSS Variable Fixes Applied (2025-11-27)

## Problem
Textual v0.80.0+ does NOT support custom CSS variable definitions. Only built-in theme variables work.

## Changes Applied

### 1. `/src/legal_extractor_tui/styles/base.tcss`

**REMOVED custom variable definitions (lines 17-31):**
- `$stage-pending`, `$stage-active`, `$stage-complete`, `$stage-error`
- Duplicate definitions of `$panel`, `$surface`, `$primary`
- `$confidence-high`, `$confidence-medium`, `$confidence-low`

**REPLACED with documentation comment** explaining the mapping to built-in variables.

**UPDATED confidence badge classes (lines 123-135):**
```tcss
.confidence-high {
    color: $success;      /* was $confidence-high */
}

.confidence-medium {
    color: $warning;      /* was $confidence-medium */
}

.confidence-low {
    color: $error;        /* was $confidence-low */
}
```

### 2. `/src/legal_extractor_tui/styles/widgets.tcss`

**UPDATED ExtractionProgress stage classes (lines 175-199):**
```tcss
.stage.pending {
    background: $surface 10%;
    border-left: solid $surface;
    /* was $stage-pending */
}

.stage.active {
    color: $secondary;
    background: $secondary 20%;
    border-left: thick $secondary;
    /* was $stage-active */
}

.stage.complete {
    color: $success;
    background: $success 10%;
    border-left: solid $success;
    /* was $stage-complete */
}

.stage.error {
    color: $error;
    background: $error 20%;
    border-left: thick $error;
    /* was $stage-error */
}
```

## Variable Mapping

| Custom Variable | Replaced With | Reason |
|-----------------|---------------|--------|
| `$stage-pending` | `$surface` | Neutral gray for inactive state |
| `$stage-active` | `$secondary` | Purple for active processing |
| `$stage-complete` | `$success` | Green for completed state |
| `$stage-error` | `$error` | Red for error state |
| `$confidence-high` | `$success` | Green for high confidence |
| `$confidence-medium` | `$warning` | Orange for medium confidence |
| `$confidence-low` | `$error` | Red for low confidence |

## Built-in Textual Variables

These are the ONLY variables supported by Textual:
- `$primary` - Main accent color
- `$secondary` - Secondary accent color
- `$accent` - Highlight color
- `$foreground` - Text color
- `$background` - Background color
- `$surface` - Elevated surfaces
- `$panel` - Panel backgrounds
- `$success` - Success states (green)
- `$warning` - Warning states (orange)
- `$error` - Error states (red)

## Verification

```bash
# Check for remaining custom variables (should return nothing)
grep -n '\$stage-\|\$confidence-' src/legal_extractor_tui/styles/*.tcss
```

## Result

All CSS variable errors should now be resolved. The app uses only Textual's built-in theme variables.
