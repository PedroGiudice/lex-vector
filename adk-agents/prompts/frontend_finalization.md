# Task: Finalize Doc Assembler Frontend (Phases 5, 6, 7)

## Current State
The frontend is partially implemented at:
`/home/cmr-auto/claude-work/repos/Claude-Code-Projetos/legal-workbench/frontend/`

Working features:
- DropZone for file upload
- Document viewer layout
- Basic annotation list
- Dark mode (GitHub theme)

## Remaining Work

### Phase 5: Pattern Detection UI (1-2h)
Files to modify/create:
- `src/components/document/PatternList.tsx` - Show detected patterns
- `src/components/document/PatternItem.tsx` - Accept/reject pattern
- Update `DocumentViewer.tsx` to highlight patterns in yellow
- Update `documentStore.ts` to manage pattern state

Features:
- Call `/api/doc/api/v1/builder/patterns` after upload
- Show detected patterns (CPF, dates, etc) in sidebar
- Each pattern has "Accept" button to convert to annotation
- Toggle to show/hide patterns in document

### Phase 6: Save Template Modal (2h)
Files to modify/create:
- `src/components/templates/SaveTemplateModal.tsx` - Modal form
- `src/components/templates/TemplateList.tsx` - List saved templates
- `src/components/templates/TemplateCard.tsx` - Template preview card
- Update `Sidebar.tsx` to show template list

Features:
- Modal with name + description inputs
- Validation before save
- Call `/api/doc/api/v1/builder/save` API
- Show success toast
- Template list shows saved templates
- Click template to load it

### Phase 7: Polish (2h)
Files to modify:
- Add loading spinners during API calls
- Add error boundaries
- Improve empty states
- Add keyboard shortcuts (Escape to cancel selection)
- Fix any TypeScript errors

## Design Guidelines (MUST FOLLOW)
```css
/* GitHub Dark Theme - DO NOT CHANGE */
--bg-primary: #0d1117;
--bg-secondary: #161b22;
--bg-tertiary: #21262d;
--text-primary: #c9d1d9;
--text-secondary: #8b949e;
--accent-primary: #58a6ff;
--accent-success: #3fb950;
--accent-danger: #f85149;
--border-default: #30363d;
```

## API Endpoints (Already Implemented)
- POST `/api/doc/api/v1/builder/upload` - Upload DOCX
- POST `/api/doc/api/v1/builder/patterns` - Detect patterns
- POST `/api/doc/api/v1/builder/save` - Save template
- GET `/api/doc/api/v1/builder/templates` - List templates

## Instructions
1. Use `read_file` to see existing code
2. Use `write_file` to create/modify files
3. Maintain TypeScript strict mode
4. Follow existing code patterns
5. Test that files have no syntax errors

START IMPLEMENTATION NOW.
