# Quick Start Guide

## Run the Application

```bash
# From the project root
cd /home/user/Claude-Code-Projetos/legal-workbench/poc-react-stj

# Install dependencies (if not already done)
npm install

# Start the development server
npm run dev
```

The application will open automatically at http://localhost:3000

## Features to Try

### 1. Template Quick Buttons
Click on any template button to auto-populate filters:
- **Divergência entre Turmas** - Pre-configured search for divergences
- **Recursos Repetitivos** - Search for repetitive resources
- **Súmulas Recentes** - Recent jurisprudence summaries

### 2. Manual Filters
- **Legal Domain**: Select from dropdown (Direito Civil, Penal, etc.)
- **Trigger Words**: Click to toggle multiple keywords
- **Somente Acórdãos**: Toggle to filter only acórdãos

### 3. Live SQL Preview
Watch the SQL query update in real-time as you change filters!

### 4. Results
- View results with outcome badges
- Color-coded: Green (PROVIDO), Red (DESPROVIDO), Yellow (PARCIAL)

## Development Tools

### React Query Devtools
Click the React Query icon in the bottom-right corner to inspect queries and cache.

### Browser DevTools
Press F12 to open browser DevTools and inspect the terminal aesthetic styling.

## Next Steps

1. Try different filter combinations
2. Check the SQL preview to understand query generation
3. Review the code in `/src/components/STJQueryBuilder.tsx`
4. Customize colors in `/tailwind.config.js`
