# FRAMEWORK-AGNOSTIC MODULE ARCHITECTURE

**Version:** 2.1
**Date:** 2025-12-14
**Status:** Architecture Design
**Pattern:** API Gateway / Backends for Frontends (BFF)

---

## CORE ARCHITECTURE

```
                              ┌─────────────────┐
                              │     TRAEFIK     │
                              │  (Port 80/443)  │
                              │   Dashboard:    │
                              │   :8080         │
                              └────────┬────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              ▼                        ▼                        ▼
    PathPrefix(`/`)         PathPrefix(`/api/stj`)    PathPrefix(`/api/text`)
              │                        │                        │
              ▼                        ▼                        ▼
    ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
    │  FASTHTML HUB   │     │   STJ SERVICE   │     │ TEXT EXTRACTOR  │
    │   (frontend)    │     │   (FastAPI)     │     │   (FastAPI)     │
    │   Port 5001     │     │   Port 8000     │     │   Port 8000     │
    └─────────────────┘     └─────────────────┘     └─────────────────┘
              │                        │                        │
              └────────────────────────┴────────────────────────┘
                                       │
                              ┌────────┴────────┐
                              │  SHARED VOLUME  │
                              │    /data        │
                              └─────────────────┘
```

---

## WHY THIS ARCHITECTURE

### The "Honda Civic" Problem: SOLVED

| Problem | Old Way (Streamlit) | New Way (Traefik + FastHTML) |
|---------|---------------------|------------------------------|
| 20-min PDF processing | UI freezes, re-renders | Backend processes, frontend polls |
| Service location | Hardcoded `localhost:8001` | Just `/api/text/process` |
| Swap backend tech | Rewrite frontend | Frontend never knows |
| Service discovery | Manual, error-prone | Traefik dashboard |

### FastHTML + Docker + Traefik = "Low Floor, No Ceiling"

| Framework | Floor | Ceiling | Verdict |
|-----------|-------|---------|---------|
| Streamlit | Low | Low (re-render hell) | Outgrown |
| Reflex | High | Low (abstraction trap) | Avoid |
| FastHTML | Low | **None** | ✅ Production |

---

## DOCKER-COMPOSE.YML (PRODUCTION)

```yaml
version: "3.8"

services:
  # ============================================================
  # 1. TRAEFIK - The Invisible Router
  # ============================================================
  reverse-proxy:
    image: traefik:v3.0
    command:
      - "--api.insecure=true"                    # Dashboard at :8080
      - "--providers.docker=true"                # Auto-discover containers
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
    ports:
      - "80:80"       # Main entry point
      - "8080:8080"   # Traefik Dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - legal-network

  # ============================================================
  # 2. FASTHTML HUB - The Frontend (SSR, HTMX)
  # ============================================================
  frontend-hub:
    build: ./hub
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.hub.rule=PathPrefix(`/`)"
      - "traefik.http.routers.hub.entrypoints=web"
      - "traefik.http.routers.hub.priority=1"    # Lowest priority (catch-all)
      - "traefik.http.services.hub.loadbalancer.server.port=5001"
    volumes:
      - shared-data:/data                        # Shared with backends
    environment:
      - DATA_PATH=/data
    networks:
      - legal-network
    depends_on:
      - reverse-proxy

  # ============================================================
  # 3. STJ SERVICE - Jurisprudence API
  # ============================================================
  api-stj:
    build: ./api/stj
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.stj.rule=PathPrefix(`/api/stj`)"
      - "traefik.http.routers.stj.entrypoints=web"
      - "traefik.http.routers.stj.priority=10"   # Higher priority than hub
      - "traefik.http.middlewares.stj-strip.stripprefix.prefixes=/api/stj"
      - "traefik.http.routers.stj.middlewares=stj-strip"
      - "traefik.http.services.stj.loadbalancer.server.port=8000"
    volumes:
      - shared-data:/data
      - stj-db:/app/db                           # Persistent DuckDB
    environment:
      - DATA_PATH=/data
      - DB_PATH=/app/db/stj.duckdb
    networks:
      - legal-network

  # ============================================================
  # 4. TEXT EXTRACTOR SERVICE - PDF Processing
  # ============================================================
  api-text-extractor:
    build: ./api/text-extractor
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.text.rule=PathPrefix(`/api/text`)"
      - "traefik.http.routers.text.entrypoints=web"
      - "traefik.http.routers.text.priority=10"
      - "traefik.http.middlewares.text-strip.stripprefix.prefixes=/api/text"
      - "traefik.http.routers.text.middlewares=text-strip"
      - "traefik.http.services.text.loadbalancer.server.port=8000"
    volumes:
      - shared-data:/data
    environment:
      - DATA_PATH=/data
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    networks:
      - legal-network

  # ============================================================
  # 5. DOC ASSEMBLER SERVICE - Document Generation
  # ============================================================
  api-doc-assembler:
    build: ./api/doc-assembler
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.doc.rule=PathPrefix(`/api/doc`)"
      - "traefik.http.routers.doc.entrypoints=web"
      - "traefik.http.routers.doc.priority=10"
      - "traefik.http.middlewares.doc-strip.stripprefix.prefixes=/api/doc"
      - "traefik.http.routers.doc.middlewares=doc-strip"
      - "traefik.http.services.doc.loadbalancer.server.port=8000"
    volumes:
      - shared-data:/data
      - templates:/app/templates
    environment:
      - DATA_PATH=/data
      - TEMPLATES_PATH=/app/templates
    networks:
      - legal-network

  # ============================================================
  # 6. TRELLO MCP SERVICE - Task Integration
  # ============================================================
  api-trello:
    build: ./api/trello-mcp
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.trello.rule=PathPrefix(`/api/trello`)"
      - "traefik.http.routers.trello.entrypoints=web"
      - "traefik.http.routers.trello.priority=10"
      - "traefik.http.middlewares.trello-strip.stripprefix.prefixes=/api/trello"
      - "traefik.http.routers.trello.middlewares=trello-strip"
      - "traefik.http.services.trello.loadbalancer.server.port=8000"
    environment:
      - TRELLO_API_KEY=${TRELLO_API_KEY}
      - TRELLO_API_TOKEN=${TRELLO_API_TOKEN}
    networks:
      - legal-network

# ============================================================
# VOLUMES - Persistent Storage
# ============================================================
volumes:
  shared-data:     # Files shared between frontend and backends
  stj-db:          # DuckDB persistence for STJ
  templates:       # Document templates

# ============================================================
# NETWORKS
# ============================================================
networks:
  legal-network:
    driver: bridge
```

---

## HTMX INTEGRATION (No Hardcoded URLs)

### In FastHTML Hub:

```python
# OLD WAY (BAD)
Form(hx_post="http://localhost:8001/process", ...)

# NEW WAY (GOOD) - Traefik handles routing
Form(hx_post="/api/text/process", ...)
```

### Example: Upload PDF for Processing

```python
# hub/modules/text_extractor/components.py

def upload_form() -> FT:
    return Form(
        Input(type="file", name="pdf", accept=".pdf"),
        Button("Processar PDF", type="submit"),

        # Traefik routes /api/text/* to text-extractor service
        hx_post="/api/text/upload",
        hx_target="#results",
        hx_indicator="#loading",
        hx_encoding="multipart/form-data",
    )

def poll_status(job_id: str) -> FT:
    return Div(
        # Poll for long-running job status
        hx_get=f"/api/text/status/{job_id}",
        hx_trigger="every 2s",
        hx_swap="innerHTML",
        id="job-status",
    )
```

### Backend Never Knows About Frontend

```python
# api/text-extractor/main.py (FastAPI)

@app.post("/upload")  # NOT /api/text/upload - Traefik strips prefix
async def upload_pdf(pdf: UploadFile):
    job_id = str(uuid.uuid4())
    # Save to shared volume
    path = Path("/data/uploads") / f"{job_id}.pdf"
    path.write_bytes(await pdf.read())

    # Start background processing
    background_tasks.add_task(process_pdf, job_id)

    return {"job_id": job_id, "status": "processing"}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    # Check job status
    result_path = Path("/data/results") / f"{job_id}.json"
    if result_path.exists():
        return {"status": "complete", "result": json.loads(result_path.read_text())}
    return {"status": "processing"}
```

---

## SHARED VOLUME WORKFLOW

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   FRONTEND   │       │   BACKEND    │       │   BACKEND    │
│   (Hub)      │       │ (Extractor)  │       │ (Assembler)  │
└──────┬───────┘       └──────┬───────┘       └──────┬───────┘
       │                      │                      │
       │  Upload PDF          │                      │
       │─────────────────────▶│                      │
       │                      │                      │
       │                      │ Save to /data/uploads│
       │                      │────────────┐         │
       │                      │            ▼         │
       │               ┌──────┴──────────────────────┴──────┐
       │               │         SHARED VOLUME              │
       │               │            /data                   │
       │               │  ┌─────────────────────────────┐   │
       │               │  │ /uploads/abc123.pdf         │   │
       │               │  │ /results/abc123.json        │   │
       │               │  │ /templates/contrato.docx    │   │
       │               │  │ /output/contrato_final.docx │   │
       │               │  └─────────────────────────────┘   │
       │               └────────────────────────────────────┘
       │                      │                      │
       │  Poll /status        │                      │
       │─────────────────────▶│                      │
       │                      │                      │
       │  {status: complete}  │                      │
       │◀─────────────────────│                      │
       │                      │                      │
       │  Download from       │                      │
       │  /data/results       │                      │
       │◀─────────────────────┘                      │
```

---

## DIRECTORY STRUCTURE (FINAL)

```
legal-workbench/
├── docker-compose.yml          ← Production orchestration
├── .env                        ← Secrets (GEMINI_API_KEY, etc.)
│
├── hub/                        ← FastHTML Frontend (SSR)
│   ├── Dockerfile
│   ├── main.py                 # Entry point
│   ├── requirements.txt
│   ├── core/
│   │   ├── themes.py           # Theme system
│   │   └── loader.py           # Module registry
│   ├── layouts/
│   │   ├── shell.py            # Main layout
│   │   └── sidebar.py          # Navigation
│   ├── modules/                # UI modules (FastHTML native)
│   │   ├── stj/
│   │   ├── text_extractor/
│   │   ├── doc_assembler/
│   │   └── trello/
│   └── static/
│       ├── theme-contract.json
│       └── styles.css
│
├── api/                        ← Backend Services (FastAPI)
│   ├── stj/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── src/
│   ├── text-extractor/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── src/
│   ├── doc-assembler/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── src/
│   └── trello-mcp/
│       ├── Dockerfile
│       ├── main.py
│       └── src/
│
├── themes/                     ← Framework-agnostic themes
│   ├── contract.json           # Universal theme schema
│   └── modules.json            # Module → theme mapping
│
└── docs/
    └── plans/
```

---

## ROUTE MAPPING

| URL Pattern | Routed To | Service |
|-------------|-----------|---------|
| `/` | `frontend-hub:5001` | FastHTML Hub |
| `/m/*` | `frontend-hub:5001` | Module UI |
| `/api/stj/*` | `api-stj:8000` | STJ Service |
| `/api/text/*` | `api-text-extractor:8000` | Text Extractor |
| `/api/doc/*` | `api-doc-assembler:8000` | Doc Assembler |
| `/api/trello/*` | `api-trello:8000` | Trello MCP |
| `:8080` | Traefik Dashboard | Service Monitor |

---

## THEME INJECTION

### CSS Variables (Hub injects to all pages)

```css
:root {
  /* Base (always present) */
  --bg-primary: #0a0f1a;
  --text-primary: #e2e8f0;
  --success: #22c55e;
  --danger: #dc2626;

  /* Module-specific (switched on navigation) */
  --accent: #8b5cf6;
}
```

### Theme Switch on Module Load

```python
# Hub sidebar navigation
Button(
    "🔭 STJ Dados",
    hx_get="/m/stj/",
    hx_target="#workspace",
    # Trigger theme switch client-side
    hx_on__htmx_before_request="switchTheme('stj')",
)
```

---

## FRAMEWORK FLEXIBILITY (CLIENT MODULES)

If a client requires React/Vue/etc:

### Option A: Iframe in Hub

```python
# hub/modules/custom_react/__init__.py

@rt("/m/custom-react/")
def custom_react_module():
    return Div(
        Iframe(
            src="/api/custom-react/",  # Separate React container
            style="width:100%; height:100vh; border:none;",
        ),
        # Pass theme via postMessage
        Script("passThemeToIframe('custom-react')"),
    )
```

### Option B: Standalone Container

```yaml
# Add to docker-compose.yml
custom-react-module:
  build: ./modules-external/custom-react
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.custom.rule=PathPrefix(`/m/custom-react`)"
    - "traefik.http.services.custom.loadbalancer.server.port=3000"
```

---

## BENEFITS SUMMARY

| Benefit | Implementation |
|---------|----------------|
| **No hardcoded URLs** | Traefik path routing |
| **Backend swappable** | Rewrite in Rust, frontend unchanged |
| **Long tasks work** | Separate containers, polling |
| **Service visibility** | Traefik dashboard :8080 |
| **File sharing** | Shared volume /data |
| **Theme consistency** | CSS variables everywhere |
| **Client flexibility** | Iframe or container for any framework |

---

## STARTUP COMMANDS

```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f frontend-hub

# View Traefik dashboard
open http://localhost:8080

# Access application
open http://localhost
```

---

## NON-NEGOTIABLES

1. **Traefik is the entry point** — All traffic through port 80
2. **FastHTML Hub** — SSR frontend, no exceptions
3. **Path-based routing** — `/api/*` → backends, `/` → frontend
4. **Shared volume** — `/data` mounted to all services
5. **No hardcoded URLs** — Frontend uses `/api/*` paths only
