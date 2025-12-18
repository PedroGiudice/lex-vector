# Task: Redesign Trello Command Center UI

## Context
The Trello Command Center frontend needs a visual redesign to match a modern "dark tech" aesthetic.

## Style Reference
Read the style reference file:
- **File**: `/home/cmr-auto/Downloads/copy-of-gemini-prompt-architect/App.tsx`

Key design patterns to extract and apply:
1. **Colors**: Background `#09090b`, zinc-800/900 for cards, indigo-500 for accents
2. **Typography**: font-mono for data, text-xs for labels, UPPERCASE tracking-wider for section headers
3. **Borders**: `border-zinc-800`, subtle, `rounded-sm` (minimal corners)
4. **Animations**: `animate-in fade-in` for smooth transitions
5. **Layout**: Clean sections with consistent spacing

## Target Project
- **Path**: `/home/cmr-auto/claude-work/repos/Claude-Code-Projetos/legal-workbench/frontend`
- **Stack**: React 18 + TypeScript + Tailwind CSS + Zustand

## Key Files to Modify
1. `src/index.css` - Update base colors and global styles
2. `src/components/trello/NavigationPanel.tsx` - Sidebar with boards/filters
3. `src/components/trello/DataTable.tsx` - Main data table
4. `src/components/trello/ActionButtons.tsx` - Export actions (has bugs)
5. `tailwind.config.js` - Extend theme if needed

## Design Guidelines
- **Slightly less "terminal-like"** than the reference - softer feel while keeping dark tech aesthetic
- Keep the existing layout structure (sidebar + table + actions panel)
- Use indigo/violet for interactive elements and accents
- Labels should remain colorful but slightly muted (not neon)
- Maintain data density - this is a data extraction tool

## Known Bugs to Fix
1. **Download button** - Not working (JSON/CSV export)
2. **Copy to clipboard button** - Not working

## Verification
After changes, the app should:
1. Load at http://localhost/app without errors
2. Display boards in sidebar
3. Show cards in table with proper styling
4. Download and Copy buttons should work

## DO NOT
- Change the core functionality
- Modify API endpoints or data structures
- Remove existing features
