# Technical Overview

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   React Application                    │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │           STJQueryBuilder (Main)                │  │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │  │  │
│  │  │  │ Filters  │  │   SQL    │  │   Results    │  │  │  │
│  │  │  │          │  │ Preview  │  │              │  │  │  │
│  │  │  └──────────┘  └──────────┘  └──────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                         │                              │  │
│  │                         ▼                              │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │         TanStack Query (State)                  │  │  │
│  │  │  ┌──────────────┐    ┌──────────────┐          │  │  │
│  │  │  │    Cache     │    │   Queries    │          │  │  │
│  │  │  └──────────────┘    └──────────────┘          │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│                         │                                    │
│                         ▼                                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  Mock API Layer                        │  │
│  │              (Future: Real API)                        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Component Hierarchy

```
App (QueryClientProvider)
 └── STJQueryBuilder
      ├── Header
      ├── Template Buttons
      ├── Filters Section
      │    ├── Legal Domain Dropdown
      │    ├── Trigger Words Multi-Select
      │    └── Acórdãos Toggle
      ├── SQLPreviewPanel
      │    └── Code Block
      └── Results Section
           └── JurisprudenceResultCard[]
                └── OutcomeBadge
```

## Design Patterns

### 1. Container/Presentational Pattern

**Container** (Smart Component):
- `STJQueryBuilder` - Manages state, handles business logic

**Presentational** (Dumb Components):
- `SQLPreviewPanel` - Displays SQL, no business logic
- `JurisprudenceResultCard` - Displays result data
- `OutcomeBadge` - Pure presentation

**Benefits**:
- Easier to test presentational components
- Better separation of concerns
- Reusable components

### 2. Custom Hooks Pattern

```typescript
// Data fetching abstraction
export function useJurisprudenceQuery(params: QueryParams) {
  return useQuery({
    queryKey: ['jurisprudence', params],
    queryFn: () => fetchJurisprudence(params),
  });
}

// Derived state
export function useSQLPreview(params: QueryParams): SQLPreview {
  // Compute SQL preview without API call
}
```

**Benefits**:
- Encapsulates complex logic
- Reusable across components
- Easier to test

### 3. Composition Pattern

```typescript
// Instead of large monolithic component
<STJQueryBuilder>
  <SQLPreviewPanel preview={sqlPreview} />
  <JurisprudenceResultCard result={result} />
</STJQueryBuilder>
```

**Benefits**:
- Smaller, focused components
- Better code organization
- Easier maintenance

## State Management Strategy

### Local State (useState)

Used for:
- UI-specific state (domain, triggerWords, onlyAcordaos)
- Form inputs
- Toggle states

```typescript
const [domain, setDomain] = useState<LegalDomain | null>(null);
const [selectedTriggerWords, setSelectedTriggerWords] = useState<TriggerWord[]>([]);
const [onlyAcordaos, setOnlyAcordaos] = useState(false);
```

### Derived State (useMemo)

Used for:
- Computed values based on state
- Prevents unnecessary recalculations

```typescript
const queryParams: QueryParams = useMemo(
  () => ({
    domain,
    triggerWords: selectedTriggerWords,
    onlyAcordaos,
  }),
  [domain, selectedTriggerWords, onlyAcordaos]
);
```

### Server State (TanStack Query)

Used for:
- API data
- Caching
- Loading/error states
- Background refetching

```typescript
const { data, isLoading, error } = useJurisprudenceQuery(queryParams);
```

**Why not Redux/Zustand?**
- TanStack Query handles server state better
- No need for global client state yet
- Simpler architecture for PoC
- Can add later if needed

## Data Flow

```
User Action → State Update → Derived State → API Query → Results
     ↓             ↓              ↓             ↓           ↓
  (click)     (setState)     (useMemo)    (useQuery)   (render)
```

### Example Flow: Filter Change

1. User selects "Direito Civil" from dropdown
2. `setDomain('Direito Civil')` updates local state
3. `queryParams` recomputes via useMemo
4. `useJurisprudenceQuery` detects param change
5. Query executes, shows loading state
6. Results return, component re-renders
7. SQL preview updates simultaneously

## Styling Architecture

### Tailwind Utility-First Approach

**Theme Customization**:
```javascript
// tailwind.config.js
theme: {
  extend: {
    colors: {
      terminal: {
        bg: '#0a0f1a',
        accent: '#f59e0b',
        // ... more colors
      }
    }
  }
}
```

**Component Classes**:
```css
/* index.css */
@layer components {
  .btn-terminal {
    @apply px-4 py-2 bg-terminal-accent/10 ...;
  }
}
```

**Benefits**:
- Consistent design system
- No naming conflicts
- Smaller CSS bundle (unused classes removed)
- Easy theme customization

### Why Not CSS-in-JS?

**Considered**: styled-components, emotion

**Decision**: Tailwind CSS

**Reasons**:
1. Better performance (no runtime styling)
2. Smaller bundle size
3. Faster development
4. Better tooling/autocomplete
5. Easier for team members to understand

## Type Safety

### TypeScript Strict Mode

```json
{
  "strict": true,
  "noUnusedLocals": true,
  "noUnusedParameters": true,
  "noFallthroughCasesInSwitch": true
}
```

### Type Inference

```typescript
// Explicit types for clarity
export type Outcome = 'provido' | 'desprovido' | 'parcial';

// Inferred types where obvious
const [domain, setDomain] = useState<LegalDomain | null>(null);
//    ^? LegalDomain | null (inferred)
```

### Generic Types

```typescript
// TanStack Query types
useQuery<JurisprudenceResult[], Error>({
  queryKey: ['jurisprudence', params],
  queryFn: () => fetchJurisprudence(params),
});
```

## Performance Optimizations

### 1. Memoization

```typescript
// Prevents unnecessary object recreation
const queryParams = useMemo(() => ({...}), [deps]);
```

### 2. Conditional Query Execution

```typescript
// Only fetch when filters applied
enabled: params.domain !== null || params.triggerWords.length > 0
```

### 3. Query Caching

```typescript
// Cache for 5 minutes
staleTime: 5 * 60 * 1000
```

### 4. Code Splitting (Future)

```typescript
// Lazy load heavy components
const ExportDialog = lazy(() => import('./ExportDialog'));
```

## Error Handling

### API Errors

```typescript
const { data, error } = useJurisprudenceQuery(params);

if (error) {
  return <ErrorMessage error={error} />;
}
```

### Error Boundaries (Recommended for Production)

```typescript
class ErrorBoundary extends React.Component {
  componentDidCatch(error, errorInfo) {
    // Log to Sentry
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback />;
    }
    return this.props.children;
  }
}
```

## Accessibility Considerations

### Semantic HTML

```tsx
<header> // Not <div class="header">
<select> // Not custom dropdown
<button> // Not <div onclick>
```

### Keyboard Navigation

```tsx
// All interactive elements are keyboard accessible
<button onClick={...} />
<select onChange={...} />
<input type="checkbox" />
```

### Focus Management

```css
/* Visible focus indicators */
focus:outline-none focus:border-terminal-accent/50 focus:ring-1
```

### Screen Reader Support

```tsx
// Descriptive labels
<label htmlFor="domain">Legal Domain</label>
<select id="domain" ...>
```

## Build Configuration

### Vite Configuration

```typescript
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'), // Path aliases
    },
  },
});
```

**Why Vite?**
1. Faster than Create React App
2. Better development experience (HMR)
3. Optimized production builds
4. Native ES modules support
5. Plugin ecosystem

### TypeScript Configuration

```json
{
  "compilerOptions": {
    "strict": true, // Maximum type safety
    "jsx": "react-jsx", // New JSX transform
    "moduleResolution": "bundler", // Modern resolution
  }
}
```

## Testing Strategy (Summary)

1. **Unit Tests**: Individual components
2. **Integration Tests**: Component interactions
3. **E2E Tests**: User flows
4. **Accessibility Tests**: WCAG compliance
5. **Visual Regression**: Screenshot comparison

See `TESTING.md` for details.

## Deployment Strategy (Summary)

1. **Build**: `npm run build`
2. **Deploy**: Vercel, Netlify, or Docker
3. **Monitor**: Sentry, Analytics
4. **Rollback**: Platform-specific

See `DEPLOYMENT.md` for details.

## Future Enhancements

### Phase 2: Full Features
- [ ] Real API integration
- [ ] Authentication
- [ ] User preferences/saved queries
- [ ] Export functionality (PDF, CSV)
- [ ] Advanced filters (date ranges, courts)

### Phase 3: Performance
- [ ] Virtual scrolling for large lists
- [ ] Infinite scroll pagination
- [ ] Service worker for offline support
- [ ] Request deduplication

### Phase 4: Features
- [ ] Search history
- [ ] Favorite queries
- [ ] Collaborative features
- [ ] Annotations
- [ ] Document viewer

## Technology Decisions

| Choice | Alternative | Reason |
|--------|-------------|--------|
| React 18 | Vue, Svelte | Team expertise, ecosystem |
| TypeScript | JavaScript | Type safety, better DX |
| Vite | CRA, Next.js | Faster, simpler for PoC |
| TanStack Query | Redux, SWR | Better server state management |
| Tailwind | Styled Components | Performance, utility-first |
| Jest | Vitest | Mature, well-documented |

## Code Organization

```
src/
├── components/     # React components
│   ├── *.tsx      # Component implementation
│   └── *.test.tsx # Component tests
├── hooks/         # Custom React hooks
├── types/         # TypeScript type definitions
├── utils/         # Helper functions, mock data
├── App.tsx        # Root component
├── main.tsx       # Entry point
└── index.css      # Global styles
```

**Conventions**:
- PascalCase for components
- camelCase for functions/variables
- SCREAMING_SNAKE_CASE for constants
- Descriptive names over short names

## Development Workflow

1. **Start dev server**: `npm run dev`
2. **Make changes**: Hot reload applies instantly
3. **Run tests**: `npm test`
4. **Build**: `npm run build`
5. **Preview**: `npm run preview`

## Documentation

- `README.md` - Overview and setup
- `QUICKSTART.md` - Quick start guide
- `TECHNICAL_OVERVIEW.md` - This file
- `TESTING.md` - Testing guide
- `DEPLOYMENT.md` - Deployment guide
- `ACCESSIBILITY.md` - Accessibility checklist
- `PERFORMANCE.md` - Performance guide

## Support

For questions or issues:
1. Check documentation files
2. Review code comments
3. Check TypeScript types
4. Review test examples

## Contributing

1. Follow existing code style
2. Write tests for new features
3. Update documentation
4. Ensure all checks pass
5. Request review

## License

Internal project - Legal Workbench
