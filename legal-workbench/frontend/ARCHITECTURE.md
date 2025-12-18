# Frontend Architecture

## Component Hierarchy

```
App
└── MainLayout
    ├── Header
    │   └── Logo + Clear Document Button
    ├── Sidebar (Left - 240px)
    │   ├── DropZone
    │   ├── UploadProgress (conditional)
    │   ├── DetectedPatterns (conditional)
    │   └── Instructions
    ├── DocumentViewer (Center - flex-1)
    │   ├── Paragraph List
    │   │   └── FieldAnnotation (inline)
    │   └── TextSelectionPopup (conditional)
    └── AnnotationList (Right - 300px)
        ├── Annotation Items
        │   └── Delete Button
        ├── Save Template Modal (conditional)
        └── ToastContainer
```

## State Management Flow

```
User Action
    ↓
Component Event Handler
    ↓
Zustand Store Action
    ↓
State Update (immutable)
    ↓
Component Re-render
    ↓
UI Update
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Browser                               │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │              React Application                    │  │
│  │                                                   │  │
│  │  ┌─────────────────────────────────────────┐    │  │
│  │  │        Zustand Store                    │    │  │
│  │  │  - documentId                           │    │  │
│  │  │  - textContent                          │    │  │
│  │  │  - paragraphs                           │    │  │
│  │  │  - annotations                          │    │  │
│  │  │  - detectedPatterns                     │    │  │
│  │  │  - selectedText                         │    │  │
│  │  │  - toasts                               │    │  │
│  │  └─────────────────────────────────────────┘    │  │
│  │           ↑                    ↓                 │  │
│  │  ┌─────────────┐      ┌──────────────────┐     │  │
│  │  │  Components │      │   API Service    │     │  │
│  │  │  - Layout   │      │   (Axios)        │     │  │
│  │  │  - Document │      └──────────────────┘     │  │
│  │  │  - Upload   │               ↓                │  │
│  │  │  - UI       │      ┌──────────────────┐     │  │
│  │  └─────────────┘      │   HTTP Requests  │     │  │
│  │                       └──────────────────┘     │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────┘
                      │
                      ↓
            ┌─────────────────────┐
            │   Backend API       │
            │   (Port 8000)       │
            │                     │
            │  - Upload           │
            │  - Patterns         │
            │  - Save Template    │
            │  - List Templates   │
            └─────────────────────┘
```

## Component Responsibility Matrix

| Component | Responsibility | State Access | Side Effects |
|-----------|---------------|--------------|--------------|
| App | Root component | None | None |
| MainLayout | Layout orchestration | None | None |
| Header | App branding, clear action | documentId | clearDocument |
| Sidebar | Upload & instructions | documentId, detectedPatterns | uploadDocument |
| DocumentViewer | Document display | paragraphs, annotations, selectedText | setSelectedText |
| TextSelectionPopup | Field creation | selectedText | addAnnotation |
| AnnotationList | Annotation management | annotations | removeAnnotation, saveTemplate |
| DropZone | File input | isUploading | onFileSelect callback |
| UploadProgress | Progress display | uploadProgress | None |
| Button | Reusable button | None | onClick callback |
| Input | Form input | None | onChange callback |
| Modal | Dialog container | None | onClose callback |
| Toast | Notifications | toasts | removeToast |

## Hook Responsibilities

### useTextSelection
- Monitors window.getSelection()
- Calculates paragraph-relative positions
- Provides selection data and clear function
- Isolated from component logic

### useAnnotations
- Provides annotation CRUD operations
- Field name validation (snake_case)
- Duplicate checking
- Position-based filtering
- Wraps store actions with business logic

### useDocumentUpload
- File validation (type, size)
- Upload orchestration
- Progress tracking
- Error handling
- Wraps store upload action

## State Management Principles

### Single Source of Truth
All application state lives in the Zustand store at `src/store/documentStore.ts`.

### Immutable Updates
All state updates create new objects/arrays rather than mutating existing ones.

```typescript
// Good
set(state => ({ annotations: [...state.annotations, newAnnotation] }))

// Bad
state.annotations.push(newAnnotation)
```

### Derived State
Use selectors and computed values instead of storing redundant state.

```typescript
// Store only raw annotations
annotations: FieldAnnotation[]

// Derive count in component
const count = annotations.length
```

### Action-Based Updates
All state changes go through named actions, never direct mutation.

```typescript
// Good
addAnnotation(annotation)

// Bad
set({ annotations: [...annotations, annotation] })
```

## API Integration Pattern

### Request Flow
```
Component
  ↓
Custom Hook (validation)
  ↓
Store Action
  ↓
API Service
  ↓
Axios Request
  ↓
Backend
```

### Response Flow
```
Backend
  ↓
Axios Response
  ↓
API Service (transform)
  ↓
Store Action (update state)
  ↓
Component Re-render
  ↓
UI Update
```

### Error Handling
```
API Error
  ↓
Catch in Store Action
  ↓
Add Error Toast
  ↓
Log to Console
  ↓
Throw (optional)
```

## Styling Architecture

### Tailwind Utility Classes
All styling uses Tailwind CSS utility classes for consistency and small bundle size.

### Theme System
Color palette defined in:
1. `tailwind.config.js` - Tailwind theme extension
2. `src/styles/theme.ts` - TypeScript constants
3. `src/index.css` - CSS variables

### Responsive Design
Mobile-first approach with Tailwind breakpoints:
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px

### Dark Mode
Single dark theme (no light mode toggle).

## Performance Optimizations

### Code Splitting
Vite automatically splits code at dynamic imports.

### React Optimizations
- Functional components only
- Zustand prevents unnecessary re-renders
- React.memo on expensive components (if needed)
- useCallback for event handlers (where beneficial)

### Bundle Size
- Tailwind CSS tree-shaking
- Vite production build optimizations
- Gzip compression in nginx
- Static asset caching

## Testing Strategy

### Unit Tests
- Component rendering
- Hook logic
- Validation functions
- State updates

### Integration Tests
- User flows
- API integration
- Form submission
- Error handling

### E2E Tests (Future)
- Complete workflows
- Cross-browser testing
- Accessibility testing

## Security Considerations

### XSS Prevention
- React auto-escapes content
- No dangerouslySetInnerHTML
- Input validation on all forms

### CSRF Protection
- Backend handles CSRF tokens
- Same-origin API calls
- Proper CORS configuration

### Secrets Management
- API URLs in environment variables
- No hardcoded credentials
- .env not committed to git

## Deployment Architecture

```
┌─────────────────────────────────────┐
│         Nginx (Port 3000)           │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   Static Files (dist/)       │  │
│  │   - HTML, CSS, JS            │  │
│  │   - Images, Fonts            │  │
│  └──────────────────────────────┘  │
│                                     │
│  Proxy /api → Backend:8000          │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│     Backend API (Port 8000)         │
│     - Upload                        │
│     - Patterns                      │
│     - Save                          │
│     - List                          │
└─────────────────────────────────────┘
```

## File Organization Rationale

### By Feature
```
components/
├── document/     # Document-related components
├── upload/       # Upload-related components
├── layout/       # Layout components
└── ui/          # Generic reusable components
```

### By Type
```
src/
├── components/   # React components
├── hooks/        # Custom hooks
├── services/     # API integration
├── store/        # State management
├── types/        # TypeScript types
└── styles/       # Theme configuration
```

## Design Patterns Used

### Container/Presenter
- Containers: MainLayout, DocumentViewer, AnnotationList
- Presenters: Button, Input, Modal, Toast

### Custom Hooks
Extract reusable logic from components into hooks.

### Composition
Build complex UIs from simple, reusable components.

### Controlled Components
All form inputs are controlled components with state.

### Service Layer
Separate API logic from component logic.

### Single Responsibility
Each component has one clear purpose.

## Future Enhancements

### Potential Improvements
- Real-time collaboration
- Undo/Redo functionality
- Keyboard shortcuts
- Drag to reorder annotations
- Bulk operations
- Template versioning
- Export to different formats
- Advanced pattern detection UI
- Multi-language support
- Offline support with service workers

### Scalability Considerations
- Component lazy loading
- Virtual scrolling for large documents
- Web workers for heavy computations
- GraphQL for optimized data fetching
- Server-side rendering (SSR) if needed

---

**Last Updated**: 2025-12-17
**Architecture Version**: 1.0.0
