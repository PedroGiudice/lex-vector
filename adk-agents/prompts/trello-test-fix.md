# Task: Fix and Test Trello Command Center Frontend

## Current Error

The frontend at `http://localhost/app` crashes with:
```
TypeError: Cannot read properties of undefined (reading 'map')
```

The error occurs because `rawStructure.cards` might be undefined when the API returns data.

## Location

`legal-workbench/frontend/src/services/trelloApi.ts` line ~142:
```typescript
rawStructure.cards.forEach(card => {  // cards might be undefined!
```

## Your Task

1. **Fix the immediate crash** - add null checks where needed
2. **Run the frontend** and verify it loads without errors
3. **Execute E2E tests** as defined in the original spec (see below)
4. **Fix any additional bugs** found during testing
5. **Iterate** until all tests pass

## E2E Test Scenarios (from original spec)

Test at: `http://localhost/app`

1. Page loads with "Trello Command Center" header
2. Board selector shows available boards
3. Data table shows cards when board selected
4. Single card selection works (click row → highlight + checkbox)
5. Batch selection works (multiple checkboxes)
6. Select all works (header checkbox)
7. Export JSON works (select cards → JSON format → Download)
8. Export CSV works
9. Copy to clipboard works
10. Filter by list works

## Files to Check/Fix

- `legal-workbench/frontend/src/services/trelloApi.ts` - API client
- `legal-workbench/frontend/src/store/trelloStore.ts` - State management
- `legal-workbench/frontend/src/components/trello/DataTable.tsx` - Table component
- `legal-workbench/frontend/src/components/trello/NavigationPanel.tsx` - Sidebar

## API Info

- Boards: `GET http://localhost/api/trello/api/v1/boards`
- Board data: `GET http://localhost/api/trello/api/v1/boards/{id}`
- Returns: `{ board, lists, cards }` (no labels/members yet)

## Success Criteria

- [ ] No JavaScript errors in console
- [ ] Page loads and shows boards
- [ ] Cards display in table
- [ ] Selection works (single + batch)
- [ ] Export downloads file
- [ ] Filters work
