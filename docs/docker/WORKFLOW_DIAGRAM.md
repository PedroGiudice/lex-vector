# Legal Workbench - Docker Workflow Diagrams

**Autor**: Pedro Giudice
**Data**: 2025-12-11
**Versão**: 1.0.0
**Status**: Draft

Este documento contém os diagramas do workflow de dockerização do Legal Workbench, mostrando a arquitetura de containers, deploy, fluxo de dados e topologia de rede.

---

## Índice

1. [Diagrama de Componentes](#1-diagrama-de-componentes)
2. [Diagrama de Deploy](#2-diagrama-de-deploy)
3. [Diagrama de Dados](#3-diagrama-de-dados)
4. [Diagrama de Rede](#4-diagrama-de-rede)
5. [Glossário](#glossário)
6. [Referências](#referências)

---

## 1. Diagrama de Componentes

Este diagrama mostra como os containers se comunicam entre si, suas dependências e interfaces expostas.

```mermaid
graph TB
    subgraph "Legal Workbench Docker Architecture"
        subgraph "Frontend Layer"
            HUB[Hub Streamlit<br/>app.py<br/>Port: 8501]
        end

        subgraph "Backend Services"
            EXTRACTOR[Legal Text Extractor<br/>Marker + Gemini API<br/>Port: 8502]
            ASSEMBLER[Legal Doc Assembler<br/>docxtpl Engine<br/>Port: 8503]
            STJ[STJ Dados Abertos<br/>DuckDB Service<br/>Port: 8504]
            TRELLO[Trello MCP Server<br/>MCP Protocol<br/>Port: 8505]
        end

        subgraph "External Services"
            GEMINI[Google Gemini API<br/>Vision + Text]
            TRELLO_API[Trello REST API<br/>OAuth]
        end

        subgraph "Data Layer"
            DATA_VOL[(juridico-data<br/>Volume<br/>~/juridico-data)]
            DB_VOL[(DuckDB Files<br/>stj.db)]
        end

        subgraph "Shared Resources"
            CONFIG[config.yaml<br/>Module Registry]
            MODULES[modules/<br/>UI Wrappers]
        end
    end

    %% Frontend to Backend Communication
    HUB -->|HTTP POST| EXTRACTOR
    HUB -->|HTTP POST| ASSEMBLER
    HUB -->|SQL Query| STJ
    HUB -->|MCP Protocol| TRELLO

    %% Backend to External Services
    EXTRACTOR -->|REST API| GEMINI
    TRELLO -->|REST API| TRELLO_API

    %% Data Layer Access
    EXTRACTOR -->|Read/Write PDFs| DATA_VOL
    ASSEMBLER -->|Read Templates<br/>Write DOCX| DATA_VOL
    STJ -->|Read/Write| DB_VOL

    %% Shared Configuration
    HUB -->|Load Config| CONFIG
    HUB -->|Import Modules| MODULES
    MODULES -->|Sys.path Import| EXTRACTOR
    MODULES -->|Sys.path Import| ASSEMBLER
    MODULES -->|Direct Import| STJ
    MODULES -->|MCP Client| TRELLO

    %% Styling
    classDef frontend fill:#3b82f6,stroke:#1e40af,color:#fff
    classDef backend fill:#8b5cf6,stroke:#6d28d9,color:#fff
    classDef external fill:#ef4444,stroke:#b91c1c,color:#fff
    classDef data fill:#10b981,stroke:#047857,color:#fff
    classDef shared fill:#f59e0b,stroke:#d97706,color:#fff

    class HUB frontend
    class EXTRACTOR,ASSEMBLER,STJ,TRELLO backend
    class GEMINI,TRELLO_API external
    class DATA_VOL,DB_VOL data
    class CONFIG,MODULES shared
```

### Descrição dos Componentes

| Componente | Tipo | Porta | Descrição |
|------------|------|-------|-----------|
| **Hub Streamlit** | Frontend | 8501 | Entry point da aplicação. Interface web que orquestra todos os módulos |
| **Legal Text Extractor** | Backend | 8502 | Serviço de extração de texto usando Marker (OCR) + Gemini (classificação) |
| **Legal Doc Assembler** | Backend | 8503 | Serviço de montagem de documentos usando templates docxtpl |
| **STJ Dados Abertos** | Backend | 8504 | Serviço de consulta a dados abertos do STJ usando DuckDB |
| **Trello MCP Server** | Backend | 8505 | Servidor MCP para integração com Trello API |
| **juridico-data** | Volume | - | Volume persistente para PDFs, templates e outputs |
| **stj.db** | Volume | - | Banco DuckDB com dados do STJ |

---

## 2. Diagrama de Deploy

Este diagrama mostra a sequência completa de build e deploy dos containers.

```mermaid
sequenceDiagram
    actor Dev as Developer
    participant Git as Git Repo
    participant Docker as Docker Engine
    participant Registry as Container Registry
    participant Compose as Docker Compose
    participant Network as Docker Networks
    participant Volume as Docker Volumes
    participant Hub as Hub Container
    participant Extractor as Extractor Container
    participant Assembler as Assembler Container
    participant STJ as STJ Container
    participant Trello as Trello Container
    participant Health as Health Checks

    %% Phase 1: Preparation
    Note over Dev,Git: Phase 1: Repository Setup
    Dev->>Git: git clone legal-workbench
    Git-->>Dev: Source code + Dockerfiles
    Dev->>Dev: Create .env file<br/>(GEMINI_API_KEY, TRELLO_KEY)
    Dev->>Dev: Verify ~/juridico-data exists

    %% Phase 2: Build
    Note over Dev,Docker: Phase 2: Build Images
    Dev->>Docker: docker-compose build --no-cache

    Docker->>Docker: Build base-python:3.11-slim image
    Note right of Docker: Common base for all services

    Docker->>Docker: Build legal-text-extractor
    Note right of Docker: Install Marker, Tesseract, deps

    Docker->>Docker: Build legal-doc-assembler
    Note right of Docker: Install docxtpl, python-docx

    Docker->>Docker: Build stj-dados-abertos
    Note right of Docker: Install DuckDB, setup schemas

    Docker->>Docker: Build trello-mcp-server
    Note right of Docker: Install MCP SDK, httpx

    Docker->>Docker: Build legal-workbench-hub
    Note right of Docker: Install Streamlit, copy modules/

    Docker-->>Registry: Push images (optional)

    %% Phase 3: Network Setup
    Note over Dev,Network: Phase 3: Network Creation
    Dev->>Compose: docker-compose up -d
    Compose->>Network: Create legal-workbench-network (bridge)
    Compose->>Network: Create legal-data-network (internal)

    %% Phase 4: Volume Setup
    Note over Compose,Volume: Phase 4: Volume Mounting
    Compose->>Volume: Mount ~/juridico-data to all services
    Compose->>Volume: Create named volume legal-duckdb
    Compose->>Volume: Set permissions (1000:1000)

    %% Phase 5: Service Startup
    Note over Compose,Trello: Phase 5: Start Services (Dependency Order)

    Compose->>STJ: Start stj-dados-abertos
    STJ->>Volume: Initialize DuckDB at /data/stj.db
    STJ->>Health: Expose /health endpoint
    Health-->>Compose: STJ healthy

    Compose->>Trello: Start trello-mcp-server
    Trello->>Trello: Load MCP config from /app/configs
    Trello->>Health: Expose /health endpoint
    Health-->>Compose: Trello healthy

    Compose->>Extractor: Start legal-text-extractor
    Extractor->>Extractor: Verify Marker installation
    Extractor->>Extractor: Test Gemini API connectivity
    Extractor->>Health: Expose /health endpoint
    Health-->>Compose: Extractor healthy

    Compose->>Assembler: Start legal-doc-assembler
    Assembler->>Volume: Scan /data/templates/*.docx
    Assembler->>Health: Expose /health endpoint
    Health-->>Compose: Assembler healthy

    Compose->>Hub: Start legal-workbench-hub
    Hub->>Hub: Load config.yaml
    Hub->>Hub: Import modules/ wrappers
    Hub->>Extractor: Test connection http://extractor:8502/health
    Hub->>Assembler: Test connection http://assembler:8503/health
    Hub->>STJ: Test connection http://stj:8504/health
    Hub->>Trello: Test connection http://trello:8505/health
    Hub->>Health: Expose /health endpoint
    Health-->>Compose: Hub healthy

    %% Phase 6: Verification
    Note over Dev,Hub: Phase 6: Deployment Verification
    Dev->>Hub: curl http://localhost:8501/health
    Hub-->>Dev: 200 OK + Service Status

    Dev->>Dev: Open browser http://localhost:8501
    Hub-->>Dev: Streamlit UI loaded

    Dev->>Hub: Test Text Extractor module
    Hub->>Extractor: POST /extract {pdf_path}
    Extractor->>Volume: Read PDF from /data/input/
    Extractor->>Extractor: Run Marker pipeline
    Extractor-->>Hub: Extracted text + metadata
    Hub-->>Dev: Display results in UI

    Note over Dev,Health: Deployment Complete
```

### Ordem de Dependências

```mermaid
graph TD
    START[docker-compose up] --> NETWORK[Create Networks]
    NETWORK --> VOLUMES[Mount Volumes]
    VOLUMES --> STJ_START[Start stj-dados-abertos]
    VOLUMES --> TRELLO_START[Start trello-mcp-server]

    STJ_START --> STJ_HEALTH{Health Check}
    TRELLO_START --> TRELLO_HEALTH{Health Check}

    STJ_HEALTH -->|Pass| EXTRACTOR_START[Start legal-text-extractor]
    TRELLO_HEALTH -->|Pass| EXTRACTOR_START

    EXTRACTOR_START --> EXTRACTOR_HEALTH{Health Check}
    EXTRACTOR_HEALTH -->|Pass| ASSEMBLER_START[Start legal-doc-assembler]

    ASSEMBLER_START --> ASSEMBLER_HEALTH{Health Check}
    ASSEMBLER_HEALTH -->|Pass| HUB_START[Start legal-workbench-hub]

    HUB_START --> HUB_HEALTH{Health Check}
    HUB_HEALTH -->|Pass| READY[System Ready]

    STJ_HEALTH -->|Fail| RETRY1[Retry 3x]
    TRELLO_HEALTH -->|Fail| RETRY2[Retry 3x]
    EXTRACTOR_HEALTH -->|Fail| RETRY3[Retry 3x]
    ASSEMBLER_HEALTH -->|Fail| RETRY4[Retry 3x]
    HUB_HEALTH -->|Fail| RETRY5[Retry 3x]

    RETRY1 -->|Fail| ERROR[Deploy Failed]
    RETRY2 -->|Fail| ERROR
    RETRY3 -->|Fail| ERROR
    RETRY4 -->|Fail| ERROR
    RETRY5 -->|Fail| ERROR

    classDef success fill:#10b981,stroke:#047857,color:#fff
    classDef fail fill:#ef4444,stroke:#b91c1c,color:#fff
    classDef process fill:#3b82f6,stroke:#1e40af,color:#fff

    class READY success
    class ERROR fail
    class START,NETWORK,VOLUMES,STJ_START,TRELLO_START,EXTRACTOR_START,ASSEMBLER_START,HUB_START process
```

---

## 3. Diagrama de Dados

Este diagrama mostra o fluxo completo de dados através do sistema.

```mermaid
graph TB
    subgraph "External Data Sources"
        USER_PDF[User Upload<br/>PDF Document]
        STJ_API[STJ Open Data API<br/>Jurisprudence]
        TRELLO_BOARD[Trello Board<br/>Tasks & Cards]
    end

    subgraph "Data Ingestion"
        UPLOAD[Streamlit Upload<br/>File Handler]
        API_FETCH[API Fetcher<br/>HTTP Client]
    end

    subgraph "Storage Layer"
        subgraph "juridico-data Volume"
            INPUT_DIR[input/<br/>Raw PDFs]
            TEMPLATES_DIR[templates/<br/>DOCX Templates]
            OUTPUT_DIR[output/<br/>Generated Files]
            CACHE_DIR[cache/<br/>Processed Data]
        end

        subgraph "Database Volume"
            DUCKDB[(stj.db<br/>DuckDB Database)]
        end
    end

    subgraph "Processing Services"
        subgraph "Text Extractor Pipeline"
            MARKER[Marker OCR<br/>PDF → Markdown]
            GEMINI_CLASS[Gemini Classifier<br/>Section Tagging]
            CLEANER[Document Cleaner<br/>Artifact Removal]
        end

        subgraph "STJ Pipeline"
            INGEST[Data Ingestion<br/>JSON → Parquet]
            QUERY[Query Engine<br/>SQL Interface]
        end

        subgraph "Document Assembly"
            TEMPLATE_LOAD[Template Loader<br/>DOCX Reader]
            RENDER[Jinja2 Renderer<br/>Context Merge]
            EXPORT[Document Exporter<br/>DOCX Writer]
        end

        subgraph "Trello Integration"
            MCP_SERVER[MCP Server<br/>Protocol Handler]
            TRELLO_CLIENT[Trello Client<br/>REST API]
        end
    end

    subgraph "Hub Orchestration"
        HUB_CORE[Streamlit Hub<br/>app.py]
        MODULE_TEXT[modules/text_extractor.py]
        MODULE_DOC[modules/doc_assembler.py]
        MODULE_STJ[modules/stj.py]
        MODULE_TRELLO[modules/trello.py]
    end

    subgraph "Output Delivery"
        UI_DISPLAY[UI Display<br/>Streamlit Components]
        DOWNLOAD[File Download<br/>Browser Download]
    end

    %% Data Flow: Text Extraction
    USER_PDF -->|Upload| UPLOAD
    UPLOAD -->|Write| INPUT_DIR
    INPUT_DIR -->|Read| MARKER
    MARKER -->|Markdown| GEMINI_CLASS
    GEMINI_CLASS -->|Classified Sections| CLEANER
    CLEANER -->|Clean Text| CACHE_DIR
    CACHE_DIR -->|Return| MODULE_TEXT
    MODULE_TEXT -->|Display| UI_DISPLAY

    %% Data Flow: STJ Query
    STJ_API -->|Fetch JSON| API_FETCH
    API_FETCH -->|Ingest| INGEST
    INGEST -->|Write Parquet| DUCKDB
    MODULE_STJ -->|SQL Query| QUERY
    QUERY -->|Read| DUCKDB
    QUERY -->|Result Set| MODULE_STJ
    MODULE_STJ -->|Display| UI_DISPLAY

    %% Data Flow: Document Assembly
    TEMPLATES_DIR -->|Load| TEMPLATE_LOAD
    CACHE_DIR -->|Context Data| RENDER
    TEMPLATE_LOAD -->|Template Object| RENDER
    RENDER -->|Rendered DOCX| EXPORT
    EXPORT -->|Write| OUTPUT_DIR
    OUTPUT_DIR -->|Return Path| MODULE_DOC
    MODULE_DOC -->|Download Link| DOWNLOAD

    %% Data Flow: Trello
    MODULE_TRELLO -->|MCP Request| MCP_SERVER
    MCP_SERVER -->|REST API Call| TRELLO_CLIENT
    TRELLO_CLIENT -->|HTTP| TRELLO_BOARD
    TRELLO_BOARD -->|Response| TRELLO_CLIENT
    TRELLO_CLIENT -->|MCP Response| MODULE_TRELLO
    MODULE_TRELLO -->|Display| UI_DISPLAY

    %% Hub Orchestration
    HUB_CORE -->|Import| MODULE_TEXT
    HUB_CORE -->|Import| MODULE_DOC
    HUB_CORE -->|Import| MODULE_STJ
    HUB_CORE -->|Import| MODULE_TRELLO

    %% Styling
    classDef external fill:#ef4444,stroke:#b91c1c,color:#fff
    classDef storage fill:#10b981,stroke:#047857,color:#fff
    classDef process fill:#8b5cf6,stroke:#6d28d9,color:#fff
    classDef hub fill:#3b82f6,stroke:#1e40af,color:#fff
    classDef output fill:#f59e0b,stroke:#d97706,color:#fff

    class USER_PDF,STJ_API,TRELLO_BOARD external
    class INPUT_DIR,TEMPLATES_DIR,OUTPUT_DIR,CACHE_DIR,DUCKDB storage
    class MARKER,GEMINI_CLASS,CLEANER,INGEST,QUERY,TEMPLATE_LOAD,RENDER,EXPORT,MCP_SERVER,TRELLO_CLIENT process
    class HUB_CORE,MODULE_TEXT,MODULE_DOC,MODULE_STJ,MODULE_TRELLO hub
    class UI_DISPLAY,DOWNLOAD output
```

### Fluxos de Dados Detalhados

#### 1. Extração de Texto (PDF → Texto Limpo)

```mermaid
sequenceDiagram
    actor User
    participant Hub as Streamlit Hub
    participant Volume as juridico-data
    participant Extractor as Text Extractor
    participant Marker as Marker Engine
    participant Gemini as Gemini API
    participant Cache as Cache Directory

    User->>Hub: Upload PDF (5MB)
    Hub->>Volume: Write to /data/input/doc123.pdf
    Volume-->>Hub: File saved

    Hub->>Extractor: POST /extract<br/>{path: "/data/input/doc123.pdf"}

    Extractor->>Volume: Read PDF (5MB)
    Volume-->>Extractor: PDF bytes

    Extractor->>Marker: Process PDF
    Note right of Marker: OCR + Layout Detection<br/>~30s for 50 pages
    Marker-->>Extractor: Markdown (500KB)

    Extractor->>Gemini: Classify sections<br/>(Markdown chunks)
    Note right of Gemini: Vision API<br/>Bibliotecário prompt
    Gemini-->>Extractor: Section labels + confidence

    Extractor->>Extractor: Clean artifacts<br/>(headers, footers, noise)

    Extractor->>Cache: Write metadata<br/>/data/cache/doc123.json
    Cache-->>Extractor: Saved

    Extractor-->>Hub: {<br/>  text: "...",<br/>  sections: [...],<br/>  system: "pje",<br/>  confidence: 95<br/>}

    Hub-->>User: Display extracted text<br/>+ section navigation
```

#### 2. Consulta STJ (Query → Resultado)

```mermaid
sequenceDiagram
    actor User
    participant Hub as Streamlit Hub
    participant STJ as STJ Service
    participant DuckDB as DuckDB Engine
    participant Volume as legal-duckdb Volume

    User->>Hub: Enter search query<br/>"recurso especial AND direito civil"

    Hub->>STJ: POST /query<br/>{<br/>  query: "...",<br/>  filters: {year: 2024}<br/>}

    STJ->>STJ: Parse query → SQL
    Note right of STJ: Query builder<br/>FTS + filters

    STJ->>DuckDB: EXECUTE SQL<br/>SELECT * FROM acórdãos<br/>WHERE fts_match(...)<br/>AND ano = 2024

    DuckDB->>Volume: Read stj.db (2GB)
    Note right of Volume: Parquet scan<br/>Zero-copy reads
    Volume-->>DuckDB: Data chunks

    DuckDB->>DuckDB: Filter + Sort<br/>(Vectorized execution)

    DuckDB-->>STJ: Result set (500 rows)

    STJ->>STJ: Format response<br/>(JSON serialization)

    STJ-->>Hub: {<br/>  total: 500,<br/>  results: [...],<br/>  execution_time: "120ms"<br/>}

    Hub-->>User: Display paginated results<br/>with highlighting
```

#### 3. Montagem de Documento (Template + Dados → DOCX)

```mermaid
sequenceDiagram
    actor User
    participant Hub as Streamlit Hub
    participant Assembler as Doc Assembler
    participant Volume as juridico-data
    participant Jinja as Jinja2 Engine

    User->>Hub: Select template<br/>"petição_inicial.docx"
    User->>Hub: Fill form fields<br/>{autor: "...", réu: "..."}

    Hub->>Assembler: POST /assemble<br/>{<br/>  template: "petição_inicial.docx",<br/>  context: {...}<br/>}

    Assembler->>Volume: Read /data/templates/<br/>petição_inicial.docx
    Volume-->>Assembler: Template file (50KB)

    Assembler->>Assembler: Parse DOCX<br/>(python-docx)

    Assembler->>Jinja: Render template<br/>with context
    Note right of Jinja: Replace Jinja2 tags<br/>{{autor}}, {{réu}}, etc.
    Jinja-->>Assembler: Rendered content

    Assembler->>Assembler: Generate DOCX<br/>(docxtpl)

    Assembler->>Volume: Write /data/output/<br/>petição_123.docx
    Volume-->>Assembler: File saved (75KB)

    Assembler-->>Hub: {<br/>  output_path: "/data/output/petição_123.docx",<br/>  size: 75000<br/>}

    Hub-->>User: Download button<br/>+ preview link
```

---

## 4. Diagrama de Rede

Este diagrama mostra a topologia de rede completa do sistema.

```mermaid
graph TB
    subgraph "External Network (Internet)"
        BROWSER[User Browser<br/>HTTP/HTTPS]
        GEMINI_EXT[Gemini API<br/>generativelanguage.googleapis.com]
        TRELLO_EXT[Trello API<br/>api.trello.com]
    end

    subgraph "Host Network (Docker Host)"
        HOST_8501[localhost:8501<br/>→ hub:8501]
        HOST_8502[localhost:8502<br/>→ extractor:8502]
        HOST_8503[localhost:8503<br/>→ assembler:8503]
        HOST_8504[localhost:8504<br/>→ stj:8504]
        HOST_8505[localhost:8505<br/>→ trello:8505]

        HOST_VOL[~/juridico-data<br/>Host Volume]
    end

    subgraph "Docker Network: legal-workbench-network (Bridge)"
        subgraph "Hub Container"
            HUB_APP[Streamlit App<br/>EXPOSE 8501]
            HUB_VOL_MOUNT[/data → juridico-data]
        end

        subgraph "Extractor Container"
            EXT_APP[FastAPI App<br/>EXPOSE 8502]
            EXT_VOL_MOUNT[/data → juridico-data]
            EXT_MARKER[Marker Service<br/>Internal]
        end

        subgraph "Assembler Container"
            ASM_APP[FastAPI App<br/>EXPOSE 8503]
            ASM_VOL_MOUNT[/data → juridico-data]
            ASM_ENGINE[docxtpl Engine<br/>Internal]
        end

        subgraph "STJ Container"
            STJ_APP[FastAPI App<br/>EXPOSE 8504]
            STJ_VOL_MOUNT[/data → juridico-data]
            STJ_DUCK[DuckDB Engine<br/>Internal]
        end

        subgraph "Trello Container"
            TRL_APP[MCP Server<br/>EXPOSE 8505]
            TRL_CLIENT[HTTP Client<br/>Internal]
        end
    end

    subgraph "Docker Network: legal-data-network (Internal)"
        DATA_VOLUME[(juridico-data<br/>Volume)]
        DB_VOLUME[(legal-duckdb<br/>Volume)]
    end

    %% External Access
    BROWSER -->|HTTP| HOST_8501
    HOST_8501 -.->|Port Mapping| HUB_APP

    BROWSER -.->|Direct Debug| HOST_8502
    HOST_8502 -.->|Port Mapping| EXT_APP

    BROWSER -.->|Direct Debug| HOST_8503
    HOST_8503 -.->|Port Mapping| ASM_APP

    BROWSER -.->|Direct Debug| HOST_8504
    HOST_8504 -.->|Port Mapping| STJ_APP

    BROWSER -.->|Direct Debug| HOST_8505
    HOST_8505 -.->|Port Mapping| TRL_APP

    %% Container to Container (Bridge Network)
    HUB_APP -->|http://extractor:8502| EXT_APP
    HUB_APP -->|http://assembler:8503| ASM_APP
    HUB_APP -->|http://stj:8504| STJ_APP
    HUB_APP -->|http://trello:8505| TRL_APP

    %% Container to External APIs
    EXT_APP -->|HTTPS| GEMINI_EXT
    TRL_CLIENT -->|HTTPS| TRELLO_EXT

    %% Volume Mounts (Data Network)
    HUB_VOL_MOUNT -.->|Mount| DATA_VOLUME
    EXT_VOL_MOUNT -.->|Mount| DATA_VOLUME
    ASM_VOL_MOUNT -.->|Mount| DATA_VOLUME
    STJ_VOL_MOUNT -.->|Mount| DATA_VOLUME

    DATA_VOLUME -.->|Bind Mount| HOST_VOL
    STJ_DUCK -.->|Mount| DB_VOLUME

    %% Internal Services (No External Access)
    EXT_APP -->|localhost| EXT_MARKER
    ASM_APP -->|localhost| ASM_ENGINE
    STJ_APP -->|localhost| STJ_DUCK
    TRL_APP -->|localhost| TRL_CLIENT

    %% Styling
    classDef external fill:#ef4444,stroke:#b91c1c,color:#fff
    classDef host fill:#f59e0b,stroke:#d97706,color:#000
    classDef container fill:#3b82f6,stroke:#1e40af,color:#fff
    classDef internal fill:#8b5cf6,stroke:#6d28d9,color:#fff
    classDef volume fill:#10b981,stroke:#047857,color:#fff

    class BROWSER,GEMINI_EXT,TRELLO_EXT external
    class HOST_8501,HOST_8502,HOST_8503,HOST_8504,HOST_8505,HOST_VOL host
    class HUB_APP,EXT_APP,ASM_APP,STJ_APP,TRL_APP container
    class EXT_MARKER,ASM_ENGINE,STJ_DUCK,TRL_CLIENT internal
    class DATA_VOLUME,DB_VOLUME volume
```

### Configuração de Rede

#### 1. Bridge Network: `legal-workbench-network`

```yaml
networks:
  legal-workbench-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
          gateway: 172.28.0.1
```

**Características**:
- Permite comunicação entre containers via DNS interno
- Containers podem acessar internet para APIs externas
- Portas expostas são mapeadas para o host

**Resolução DNS Interna**:
- `extractor` → `172.28.0.2:8502`
- `assembler` → `172.28.0.3:8503`
- `stj` → `172.28.0.4:8504`
- `trello` → `172.28.0.5:8505`
- `hub` → `172.28.0.10:8501`

#### 2. Internal Network: `legal-data-network`

```yaml
networks:
  legal-data-network:
    driver: bridge
    internal: true  # No external access
```

**Características**:
- Rede isolada sem acesso à internet
- Usada apenas para comunicação com volumes de dados
- Maior segurança para dados sensíveis

#### 3. Port Mapping Table

| Service | Internal Port | Host Port | Protocol | Public |
|---------|--------------|-----------|----------|--------|
| Hub | 8501 | 8501 | HTTP | Yes (UI) |
| Extractor | 8502 | 8502 | HTTP | No (Debug only) |
| Assembler | 8503 | 8503 | HTTP | No (Debug only) |
| STJ | 8504 | 8504 | HTTP | No (Debug only) |
| Trello MCP | 8505 | 8505 | MCP/HTTP | No (Debug only) |

#### 4. Firewall Rules

```bash
# Allow only Hub to be publicly accessible
iptables -A INPUT -p tcp --dport 8501 -j ACCEPT

# Block direct access to backend services
iptables -A INPUT -p tcp --dport 8502:8505 -j DROP

# Allow internal Docker network communication
iptables -A FORWARD -i docker0 -o docker0 -j ACCEPT
```

---

## Glossário

| Termo | Descrição |
|-------|-----------|
| **Bridge Network** | Tipo de rede Docker que permite comunicação entre containers no mesmo host |
| **Internal Network** | Rede Docker isolada sem acesso à internet |
| **Volume Mount** | Mecanismo de persistência que mapeia diretórios entre host e container |
| **Health Check** | Verificação periódica de disponibilidade de um serviço |
| **MCP Protocol** | Model Context Protocol - protocolo para comunicação com LLMs |
| **DuckDB** | Banco de dados analítico embarcado, otimizado para OLAP |
| **Marker** | Engine de OCR otimizado para PDFs com layout complexo |
| **docxtpl** | Biblioteca Python para templating de documentos DOCX |
| **Streamlit** | Framework Python para criação de web apps de dados |

---

## Referências

### Documentação Oficial

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Networks](https://docs.docker.com/network/)
- [Docker Volumes](https://docs.docker.com/storage/volumes/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [DuckDB Documentation](https://duckdb.org/docs/)

### Arquivos Relacionados

- `/home/user/Claude-Code-Projetos/legal-workbench/CLAUDE.md` - Regras de desenvolvimento
- `/home/user/Claude-Code-Projetos/legal-workbench/config.yaml` - Configuração de módulos
- `/home/user/Claude-Code-Projetos/ARCHITECTURE.md` - Arquitetura geral do projeto
- `/home/user/Claude-Code-Projetos/docs/docker/` - Documentação Docker adicional

### Próximos Passos

1. Criar `docker-compose.yml` baseado nestes diagramas
2. Criar Dockerfiles individuais para cada serviço
3. Implementar health checks em cada container
4. Configurar CI/CD para build automatizado
5. Criar scripts de backup para volumes persistentes

---

**Última atualização**: 2025-12-11
**Autor**: Pedro Giudice (PGR)
**Versão do documento**: 1.0.0
