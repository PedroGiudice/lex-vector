# FastHTML STJ PoC - Backend-for-Frontend Pattern

**Proof of Concept**: FastHTML as a secure BFF layer for the STJ (Superior Tribunal de Justiça) jurisprudence module.

## Quick Start

```bash
cd /home/user/Claude-Code-Projetos/legal-workbench/poc-fasthtml-stj
source .venv/bin/activate
python app.py
```

Visit: http://localhost:5001

---

## What This PoC Demonstrates

### 1. Terminal Aesthetic (Data-Driven UI)
- **Background**: `#0a0f1a` (near-black blue)
- **Text**: `#e2e8f0` (cool gray)
- **Accent**: `#f59e0b` (amber) for actions
- **Badges**: Color-coded outcomes (PROVIDO=green, DESPROVIDO=red, PARCIAL=yellow)
- **Typography**: Monospace for data, clean sans for labels
- **NO emojis**: Custom CSS badges only

### 2. HTMX-Powered Interactivity
- **Live SQL Preview**: Updates as user changes filters (no page reload)
- **Multi-select keywords**: Pills that update query in real-time
- **Template buttons**: One-click application of common queries
- **Search results**: Async loading with loading indicators

### 3. Server-Side Event Streaming (SSE)
- **Download Center**: Real-time log streaming from backend
- **Server-side proxy pattern**: Backend API tokens never reach browser
- **Terminal output**: Simulates connecting to `http://stj-service:8000/api/v1/download`

### 4. Python End-to-End
- Share Pydantic models with backend (not shown in PoC, but trivial)
- Type hints throughout
- Modular component architecture

---

## Architecture: BFF Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                             │
│  (NO tokens, NO sensitive data, HTMX only)                  │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS
                     │
┌────────────────────▼────────────────────────────────────────┐
│              FastHTML BFF (this PoC)                        │
│  - Session management                                        │
│  - Server-side rendering                                     │
│  - API token storage (environment vars)                      │
│  - Log streaming proxy                                       │
│  - HTMX coordination                                         │
└────────────────────┬────────────────────────────────────────┘
                     │ Internal network (Docker)
                     │
┌────────────────────▼────────────────────────────────────────┐
│            FastAPI Backend Services                         │
│  - stj-service:8000/api/v1/...                              │
│  - djen-service:8000/api/v1/...                             │
│  - PostgreSQL, Redis, etc.                                  │
└─────────────────────────────────────────────────────────────┘
```

**Security Benefits**:
- Browser never sees backend API tokens
- Session cookies managed server-side
- CSRF protection built into FastHTML
- No CORS issues (same origin)

---

## Code Comparison

### React (Current Approach)

**Pros**:
- Rich ecosystem (react-query, zustand, MUI)
- Strong TypeScript support
- Excellent dev tools
- Large community

**Cons**:
- Separate frontend/backend codebases
- Build step required (Vite/Webpack)
- Token management in browser (localStorage/cookies)
- CORS configuration needed
- API mocking for development
- Larger deployment footprint

**Lines of Code (estimated)**:
```
src/
├── components/          ~400 LOC
├── hooks/               ~150 LOC
├── api/                 ~200 LOC
├── types/               ~100 LOC
├── App.tsx              ~150 LOC
└── main.tsx             ~50 LOC
                         ─────────
Total:                   ~1,050 LOC
```

---

### FastHTML (This PoC)

**Pros**:
- Python end-to-end (one language)
- No build step (instant reload)
- Tokens stay server-side (secure by default)
- Share models with backend trivially
- Simpler deployment (single service)
- HTMX is tiny (14kb vs React's ~140kb)

**Cons**:
- Smaller ecosystem (fewer components)
- Learning curve for HTMX patterns
- Less mature tooling
- Smaller community
- Server load for rendering (vs static SPA)

**Lines of Code (this PoC)**:
```
components/
├── query_builder.py     ~180 LOC
├── results.py           ~150 LOC
└── terminal.py          ~120 LOC
app.py                   ~250 LOC
styles.py                ~380 LOC
mock_data.py             ~150 LOC
                         ─────────
Total:                   ~1,230 LOC
```

**Note**: PoC includes comprehensive styling. In production, you'd extract common components to reduce duplication.

---

### Reflex (Alternative Python Framework)

**Comparison**:
- Reflex uses React under the hood (compiles Python to React)
- More "Pythonic" feeling than FastHTML
- But still requires build step
- Larger runtime (React + Python compilation layer)
- FastHTML is more explicit about HTML structure

**When to choose Reflex over FastHTML**:
- Team prefers React-style component model
- Need complex client-side state machines
- Want Python but also React ecosystem

**When to choose FastHTML over Reflex**:
- Want minimal dependencies
- Prefer explicit HTML
- Server-side rendering is primary goal
- Don't need React ecosystem

---

## Honest Assessment

### Where FastHTML Shines ✅

1. **Rapid Prototyping**
   - No build step = instant feedback
   - Python end-to-end = share code with backend
   - HTMX is intuitive for server-rendered apps

2. **Security**
   - Tokens never reach browser
   - CSRF protection built-in
   - Same-origin by default (no CORS headaches)

3. **Simplicity**
   - One language (Python)
   - One deployment artifact
   - Fewer moving parts

4. **Performance** (for this use case)
   - Terminal UI = mostly server-rendered data
   - HTMX partial updates = minimal bandwidth
   - No large JS bundle to download

5. **Maintainability**
   - Less context switching (Python only)
   - Share Pydantic models with backend
   - Type hints throughout

### Where FastHTML Has Limitations ⚠️

1. **Rich Interactions**
   - Complex client-side state (drag-and-drop, real-time collaboration) is harder
   - No virtual DOM diffing (HTMX swaps HTML chunks)
   - Limited animation libraries (would need custom CSS/JS)

2. **Ecosystem**
   - Fewer pre-built components (no MUI equivalent)
   - Smaller community
   - Less Stack Overflow coverage

3. **Developer Experience**
   - No hot module replacement (full server reload)
   - Less mature browser dev tools
   - HTMX debugging requires network inspection

4. **Team Skills**
   - Frontend devs may prefer React (familiar)
   - HTMX patterns take time to learn
   - Less "transferable" to other projects

5. **Scalability Concerns**
   - Server-side rendering = more server load
   - Need good caching strategy
   - Can't offload rendering to CDN (like static React)

---

## When to Use FastHTML for Legal Workbench

### ✅ Good Fit For:

1. **Admin Dashboards**
   - Data-heavy tables
   - Form submissions
   - CRUD operations
   - Report generation

2. **Internal Tools**
   - Team has Python expertise
   - Security is paramount
   - Rapid iteration needed

3. **Data Visualization**
   - Charts rendered server-side
   - Real-time updates (SSE)
   - Terminal-style logs

### ❌ Poor Fit For:

1. **Document Editors**
   - Rich text editing
   - Real-time collaboration
   - Complex undo/redo

2. **Mobile-First Apps**
   - Offline support
   - Service workers
   - Native-like interactions

3. **High-Concurrency Public Apps**
   - Server rendering doesn't scale like static SPAs
   - CDN caching harder
   - Need good infrastructure

---

## Recommendation for STJ Module

### Hybrid Approach 🎯

**Use FastHTML for**:
- Query builder (this PoC)
- Results tables
- Download center
- Admin panels

**Use React for**:
- Document annotation (if complex)
- Real-time collaboration features
- Mobile companion app

**Architecture**:
```
FastHTML BFF ──┬─→ React SPA (embedded via iframe/route)
               │
               └─→ FastAPI backends (Docker)
```

This gives you:
- Security benefits of FastHTML (tokens server-side)
- Simplicity for data-driven UIs
- Rich interactions where needed (React)
- Gradual migration path

---

## Production Checklist

If adopting FastHTML for Legal Workbench:

- [ ] Add authentication (OAuth2/JWT)
- [ ] Implement session management
- [ ] Set up Redis for caching
- [ ] Add rate limiting
- [ ] Implement proper error handling
- [ ] Add logging/monitoring
- [ ] Write integration tests
- [ ] Set up CI/CD pipeline
- [ ] Document HTMX patterns for team
- [ ] Create component library
- [ ] Add accessibility (ARIA labels)
- [ ] Optimize for mobile (responsive design)

---

## Technical Deep Dive

### How HTMX Works in This PoC

**Example: Live SQL Preview**

```python
# Component (query_builder.py)
Select(
    *options,
    hx_get="/sql-preview",           # Endpoint to call
    hx_trigger="change",              # When to call
    hx_target="#sql-preview-container", # Where to put response
    hx_include="[name='keywords']",   # Include other form fields
)

# Route (app.py)
@rt("/sql-preview")
def get(domain: str = "", keywords: List[str] = None):
    sql = generate_sql(domain, keywords)
    return Div(Pre(sql), id="sql-preview-container")
```

**What happens**:
1. User changes dropdown
2. HTMX sends GET to `/sql-preview?domain=...&keywords=...`
3. FastHTML renders new HTML
4. HTMX swaps content of `#sql-preview-container`
5. No JavaScript written!

### Server-Sent Events (SSE) for Streaming

```python
@rt("/stream-logs")
async def get():
    async def event_generator():
        for log_line in get_logs_from_backend():
            await asyncio.sleep(0.4)
            yield f'event: message\ndata: <div>{log_line}</div>\n\n'
        yield 'event: close\ndata: Done!\n\n'

    return EventStream(event_generator())
```

**Browser side** (HTMX):
```html
<div hx-ext="sse"
     sse-connect="/stream-logs"
     sse-swap="message"
     hx-swap="beforeend">
</div>
```

**This is the "server-side proxy" pattern**: Backend service streams logs to FastHTML, FastHTML proxies to browser via SSE. Browser never talks to backend directly.

---

## Performance Considerations

### FastHTML vs React (for this UI)

**Initial Load**:
- FastHTML: ~50kb (HTML + HTMX + CSS)
- React SPA: ~200kb (React + ReactDOM + MUI + app code)

**Subsequent Interactions**:
- FastHTML: 1-5kb HTML fragments
- React SPA: JSON response (~1kb) + client-side rendering

**Server Load**:
- FastHTML: Higher (renders HTML server-side)
- React SPA: Lower (client renders)

**Caching**:
- FastHTML: Cache HTML fragments (Jinja2-like)
- React SPA: Cache JSON (standard API caching)

**Verdict for STJ module**: FastHTML likely faster for initial load and data-heavy tables. React may feel snappier for complex interactions.

---

## Team Training Required

If adopting FastHTML:

**Week 1: Basics**
- FastHTML core concepts
- HTMX patterns (hx-get, hx-post, hx-target, hx-swap)
- Component architecture

**Week 2: Advanced**
- Server-Sent Events (SSE)
- Form handling and validation
- State management (sessions)

**Week 3: Production**
- Error handling patterns
- Testing strategies
- Deployment (Docker)

**Estimated ramp-up**: 2-3 weeks for Python devs, 4-6 weeks for frontend specialists.

---

## Conclusion

FastHTML is a **viable alternative** for the STJ module, especially for:
- Data-driven dashboards
- Terminal-style UIs
- Internal tools with high security requirements

**But it's not a silver bullet**. For complex client-side interactions, React remains superior.

**Recommended approach**: Hybrid architecture with FastHTML for data views and React for rich interactions.

---

## Resources

- [FastHTML Docs](https://docs.fastht.ml/)
- [HTMX Documentation](https://htmx.org/)
- [FastHTML Discord](https://discord.gg/fasthtml)
- [Tailwind CSS](https://tailwindcss.com/)

---

## Questions for Decision

Before adopting FastHTML for production:

1. **Team composition**: Do we have more Python or JS expertise?
2. **Feature roadmap**: Will we need complex client-side interactions?
3. **Deployment**: Can we handle server-rendered load?
4. **Timeline**: Can we afford learning curve?
5. **Maintenance**: Who will maintain this long-term?

Answer these honestly before committing to FastHTML. It's powerful, but not always the right choice.

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota
