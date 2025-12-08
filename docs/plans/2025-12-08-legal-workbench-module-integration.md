# Legal Workbench Module Integration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate all standalone tools (STJ, Trello, Doc Assembler) as modules in the Legal Workbench Streamlit hub.

**Architecture:** Each module wrapper in `modules/` imports ONLY backend logic from `ferramentas/*/src/` (never the standalone Streamlit apps). The main `app.py` dynamically loads these wrappers via `config.yaml`. Absolute separation: wrappers = UI only, backends = logic only.

**Tech Stack:** Python 3.12, Streamlit, DuckDB (STJ), python-dotenv (Trello)

**Root Cause Analysis:**
1. Modules "disappeared" because they were never integrated - only standalone apps existed
2. `config.yaml` referenced modules (`docs`, `juris`) that didn't exist in `modules/`
3. Each tool in `ferramentas/` is a full Streamlit app (with `set_page_config()`) - can't be imported as module

---

## Task 1: Fix Config and Clean Broken References

**Files:**
- Modify: `legal-workbench/config.yaml`

**Step 1: Update config.yaml with correct module list**

Replace entire content:

```yaml
system:
  version: "2.6.0"
  env: "WSL2"

modules:
  - id: "text_extractor"
    name: "Text Extractor"
    active: true
    backend: "ferramentas/legal-text-extractor"

  - id: "doc_assembler"
    name: "Document Assembler"
    active: true
    backend: "ferramentas/legal-doc-assembler"

  - id: "stj"
    name: "STJ Dados Abertos"
    active: true
    backend: "ferramentas/stj-dados-abertos"

  - id: "trello"
    name: "Trello MCP"
    active: true
    backend: "ferramentas/trello-mcp"
```

**Step 2: Verify file saved correctly**

Run: `cat legal-workbench/config.yaml`
Expected: Shows 4 modules with correct IDs

**Step 3: Commit**

```bash
git add legal-workbench/config.yaml
git commit -m "fix(workbench): update config.yaml with correct module references"
```

---

## Task 2: Create Document Assembler Module Wrapper

**Files:**
- Create: `legal-workbench/modules/doc_assembler.py`

**Step 1: Create the module wrapper**

```python
# modules/doc_assembler.py
"""
Document Assembler Module - Streamlit UI wrapper.
Imports backend logic from ferramentas/legal-doc-assembler/src.
DOES NOT duplicate business logic.
"""

import streamlit as st
import sys
import json
import tempfile
import zipfile
from pathlib import Path
from io import BytesIO

# Backend imports
backend_path = Path(__file__).parent.parent / "ferramentas" / "legal-doc-assembler"
sys.path.insert(0, str(backend_path))

from src.normalizers import normalize_all
from src.engine import DocumentEngine
from src.batch_engine import BatchProcessor


def render():
    """Renders the Document Assembler UI within Legal Workbench."""
    st.header("Document Assembler")
    st.caption("Normalize and assemble legal documents from templates")

    # Session state
    if "doc_data" not in st.session_state:
        st.session_state.doc_data = {}
    if "batch_results" not in st.session_state:
        st.session_state.batch_results = None

    # Tabs for Single vs Batch
    tab_single, tab_batch = st.tabs(["Single Document", "Batch Processing"])

    with tab_single:
        _render_single_mode()

    with tab_batch:
        _render_batch_mode()


def _render_single_mode():
    """Single document processing interface."""
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Input Data")
        json_input = st.text_area(
            "JSON Data",
            placeholder='{"nome": "JOAO DA SILVA", "cpf": "12345678901"}',
            height=200
        )

        uploaded_json = st.file_uploader("Or upload JSON file", type=["json"])
        if uploaded_json:
            json_input = uploaded_json.read().decode("utf-8")
            st.code(json_input, language="json")

        if st.button("Normalize Data", use_container_width=True):
            try:
                data = json.loads(json_input) if json_input else {}
                normalized = normalize_all(data)
                st.session_state.doc_data = normalized
                st.success("Data normalized successfully!")
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")

    with col2:
        st.subheader("Normalized Output")
        if st.session_state.doc_data:
            st.json(st.session_state.doc_data)
        else:
            st.info("Enter data and click 'Normalize Data'")


def _render_batch_mode():
    """Batch processing interface."""
    st.subheader("Batch Processing")
    st.info("Upload multiple JSON files or a ZIP archive for batch normalization.")

    uploaded_files = st.file_uploader(
        "Upload JSON files",
        type=["json", "zip"],
        accept_multiple_files=True
    )

    if uploaded_files and st.button("Process Batch", use_container_width=True):
        results = []
        progress = st.progress(0, "Processing...")

        for i, file in enumerate(uploaded_files):
            try:
                if file.name.endswith(".zip"):
                    # Handle ZIP files
                    with zipfile.ZipFile(BytesIO(file.read())) as zf:
                        for name in zf.namelist():
                            if name.endswith(".json"):
                                data = json.loads(zf.read(name).decode("utf-8"))
                                normalized = normalize_all(data)
                                results.append({"file": name, "data": normalized, "status": "OK"})
                else:
                    data = json.loads(file.read().decode("utf-8"))
                    normalized = normalize_all(data)
                    results.append({"file": file.name, "data": normalized, "status": "OK"})
            except Exception as e:
                results.append({"file": file.name, "data": None, "status": f"ERROR: {e}"})

            progress.progress((i + 1) / len(uploaded_files))

        st.session_state.batch_results = results
        progress.empty()
        st.success(f"Processed {len(results)} files")

    # Display batch results
    if st.session_state.batch_results:
        st.markdown("---")
        st.subheader("Batch Results")

        for result in st.session_state.batch_results:
            with st.expander(f"{result['file']} - {result['status']}"):
                if result["data"]:
                    st.json(result["data"])
```

**Step 2: Verify file created**

Run: `ls -la legal-workbench/modules/`
Expected: Shows `doc_assembler.py`

**Step 3: Commit**

```bash
git add legal-workbench/modules/doc_assembler.py
git commit -m "feat(workbench): add doc_assembler module wrapper"
```

---

## Task 3: Create STJ Dados Abertos Module Wrapper

**Files:**
- Create: `legal-workbench/modules/stj.py`

**Step 1: Read STJ backend interface**

Check database.py for available methods (reference only, don't modify).

**Step 2: Create the module wrapper**

```python
# modules/stj.py
"""
STJ Dados Abertos Module - Streamlit UI wrapper.
Imports backend logic from ferramentas/stj-dados-abertos/src.
DOES NOT duplicate business logic.
"""

import streamlit as st
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Backend imports
backend_path = Path(__file__).parent.parent / "ferramentas" / "stj-dados-abertos"
sys.path.insert(0, str(backend_path))

from src.downloader import STJDownloader
from src.processor import STJProcessor
from src.database import STJDatabase

# Constants
DATABASE_PATH = Path.home() / "juridico-data" / "stj" / "jurisprudencia.duckdb"


def render():
    """Renders the STJ Dados Abertos UI within Legal Workbench."""
    st.header("STJ Dados Abertos")
    st.caption("Download and analyze STJ jurisprudence data")

    # Session state
    if "stj_query_results" not in st.session_state:
        st.session_state.stj_query_results = None

    # Check database status
    db_exists = DATABASE_PATH.exists()

    # Status metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Database", "Ready" if db_exists else "Not Found")
    with col2:
        if db_exists:
            try:
                db = STJDatabase(str(DATABASE_PATH))
                count = db.get_total_count()
                st.metric("Total Records", f"{count:,}")
            except Exception:
                st.metric("Total Records", "N/A")
        else:
            st.metric("Total Records", "0")
    with col3:
        st.metric("Path", str(DATABASE_PATH.parent.name))

    st.markdown("---")

    # Tabs
    tab_search, tab_download, tab_stats = st.tabs(["Search", "Download", "Statistics"])

    with tab_search:
        _render_search_tab(db_exists)

    with tab_download:
        _render_download_tab()

    with tab_stats:
        _render_stats_tab(db_exists)


def _render_search_tab(db_exists: bool):
    """Search interface for existing data."""
    st.subheader("Search Jurisprudence")

    if not db_exists:
        st.warning("Database not found. Use the Download tab first.")
        return

    search_term = st.text_input("Search term", placeholder="Ex: dano moral, recurso especial...")

    col1, col2 = st.columns(2)
    with col1:
        limit = st.number_input("Max results", min_value=10, max_value=1000, value=100)
    with col2:
        orgao = st.selectbox("Orgao Julgador", ["Todos", "1T", "2T", "3T", "4T", "CE"])

    if st.button("Search", use_container_width=True) and search_term:
        try:
            db = STJDatabase(str(DATABASE_PATH))
            results = db.search(
                term=search_term,
                limit=limit,
                orgao=None if orgao == "Todos" else orgao
            )
            st.session_state.stj_query_results = results
            st.success(f"Found {len(results)} results")
        except Exception as e:
            st.error(f"Search error: {e}")

    # Display results
    if st.session_state.stj_query_results is not None:
        df = pd.DataFrame(st.session_state.stj_query_results)
        if not df.empty:
            st.dataframe(df, use_container_width=True, height=400)
        else:
            st.info("No results found")


def _render_download_tab():
    """Download interface for fetching new data."""
    st.subheader("Download Data")
    st.info("Download jurisprudence data from STJ open data portal.")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30)
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now()
        )

    if st.button("Start Download", use_container_width=True):
        st.warning("Download functionality requires running the standalone STJ app.")
        st.code(f"cd legal-workbench/ferramentas/stj-dados-abertos && streamlit run app.py", language="bash")
        st.info("For full download capabilities, use the standalone application.")


def _render_stats_tab(db_exists: bool):
    """Statistics view."""
    st.subheader("Database Statistics")

    if not db_exists:
        st.warning("Database not found.")
        return

    try:
        db = STJDatabase(str(DATABASE_PATH))

        # Get stats
        total = db.get_total_count()
        by_year = db.get_count_by_year()
        by_orgao = db.get_count_by_orgao()

        st.metric("Total Documents", f"{total:,}")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**By Year**")
            if by_year:
                df_year = pd.DataFrame(by_year)
                st.bar_chart(df_year.set_index("year")["count"])

        with col2:
            st.markdown("**By Orgao Julgador**")
            if by_orgao:
                df_orgao = pd.DataFrame(by_orgao)
                st.bar_chart(df_orgao.set_index("orgao")["count"])

    except Exception as e:
        st.error(f"Error loading stats: {e}")
```

**Step 3: Commit**

```bash
git add legal-workbench/modules/stj.py
git commit -m "feat(workbench): add stj module wrapper"
```

---

## Task 4: Create Trello Module Wrapper

**Files:**
- Create: `legal-workbench/modules/trello.py`

**Step 1: Create the module wrapper**

```python
# modules/trello.py
"""
Trello MCP Module - Streamlit UI wrapper.
Imports backend logic from ferramentas/trello-mcp/src.
DOES NOT duplicate business logic.
"""

import streamlit as st
import sys
import asyncio
import re
from pathlib import Path
from typing import Dict, Any, List

# Backend imports
backend_path = Path(__file__).parent.parent / "ferramentas" / "trello-mcp"
src_path = backend_path / "src"
sys.path.insert(0, str(src_path))

from models import EnvironmentSettings
from trello_client import TrelloClient

# Regex patterns for Brazilian legal data
REGEX_MAP = {
    "cpf": r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}",
    "cnpj": r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}",
    "oab": r"\d{1,6}/?[A-Z]{2}",
    "valor": r"R\$\s?(\d{1,3}(?:\.\d{3})*,\d{2})",
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
}


def render():
    """Renders the Trello MCP UI within Legal Workbench."""
    st.header("Trello MCP")
    st.caption("Extract and analyze data from Trello boards")

    # Session state
    if "trello_boards" not in st.session_state:
        st.session_state.trello_boards = []
    if "trello_extraction" not in st.session_state:
        st.session_state.trello_extraction = None

    # Check configuration
    try:
        settings = EnvironmentSettings()
        configured = bool(settings.trello_api_key and settings.trello_token)
    except Exception:
        configured = False

    # Status
    col1, col2 = st.columns(2)
    with col1:
        st.metric("API Status", "Configured" if configured else "Not Configured")
    with col2:
        st.metric("Boards Loaded", len(st.session_state.trello_boards))

    if not configured:
        st.warning("Trello API not configured. Create `.env` file with TRELLO_API_KEY and TRELLO_TOKEN.")
        st.code("""
# .env file in ferramentas/trello-mcp/
TRELLO_API_KEY=your_api_key
TRELLO_TOKEN=your_token
        """, language="bash")
        return

    st.markdown("---")

    # Tabs
    tab_boards, tab_extract = st.tabs(["Boards", "Data Extraction"])

    with tab_boards:
        _render_boards_tab(settings)

    with tab_extract:
        _render_extraction_tab()


def _render_boards_tab(settings: EnvironmentSettings):
    """Board listing and selection."""
    st.subheader("Your Boards")

    if st.button("Load Boards", use_container_width=True):
        try:
            client = TrelloClient(settings)
            boards = asyncio.run(client.get_boards())
            st.session_state.trello_boards = boards
            st.success(f"Loaded {len(boards)} boards")
        except Exception as e:
            st.error(f"Error loading boards: {e}")

    if st.session_state.trello_boards:
        for board in st.session_state.trello_boards:
            with st.expander(board.get("name", "Unknown")):
                st.json(board)


def _render_extraction_tab():
    """Data extraction with regex patterns."""
    st.subheader("Extract Legal Data")
    st.info("Extract CPF, CNPJ, OAB numbers, and monetary values from card descriptions.")

    text_input = st.text_area(
        "Text to analyze",
        placeholder="Paste card description or any text...",
        height=200
    )

    # Pattern selection
    selected_patterns = st.multiselect(
        "Patterns to extract",
        options=list(REGEX_MAP.keys()),
        default=["cpf", "cnpj", "oab", "valor"]
    )

    if st.button("Extract Data", use_container_width=True) and text_input:
        results = {}
        for pattern_name in selected_patterns:
            pattern = REGEX_MAP.get(pattern_name)
            if pattern:
                matches = re.findall(pattern, text_input)
                results[pattern_name] = list(set(matches))  # Unique values

        st.session_state.trello_extraction = results
        st.success("Extraction complete!")

    if st.session_state.trello_extraction:
        st.markdown("---")
        st.subheader("Results")

        for key, values in st.session_state.trello_extraction.items():
            with st.expander(f"{key.upper()} ({len(values)} found)"):
                if values:
                    for v in values:
                        st.code(v)
                else:
                    st.info("No matches found")
```

**Step 2: Commit**

```bash
git add legal-workbench/modules/trello.py
git commit -m "feat(workbench): add trello module wrapper"
```

---

## Task 5: Update Text Extractor Import Path

**Files:**
- Modify: `legal-workbench/modules/text_extractor.py:12`

**Step 1: Fix the import path**

The current import uses `legal_text_extractor` but the actual module name might differ. Verify:

Run: `ls legal-workbench/ferramentas/legal-text-extractor/`

Check if there's a `main.py` with `LegalTextExtractor` class.

**Step 2: Update import if needed**

If import fails, update line 12 from:
```python
from legal_text_extractor.main import LegalTextExtractor, ExtractionResult
```
to the correct path based on actual structure.

**Step 3: Test the module loads**

Run: `cd legal-workbench && python -c "from modules.text_extractor import render; print('OK')"`
Expected: "OK" or specific error to fix

**Step 4: Commit if changes made**

```bash
git add legal-workbench/modules/text_extractor.py
git commit -m "fix(workbench): correct text_extractor import path"
```

---

## Task 6: Verify All Modules Load

**Step 1: Test each module import**

```bash
cd legal-workbench
python -c "from modules.doc_assembler import render; print('doc_assembler: OK')"
python -c "from modules.stj import render; print('stj: OK')"
python -c "from modules.trello import render; print('trello: OK')"
python -c "from modules.text_extractor import render; print('text_extractor: OK')"
```

Expected: All print "OK"

**Step 2: Fix any import errors found**

Common issues:
- Missing `__init__.py` in src directories
- Missing dependencies in requirements.txt
- Wrong import paths

**Step 3: Final commit**

```bash
git add .
git commit -m "feat(workbench): complete module integration - all 4 modules functional"
```

---

## Task 7: Update Documentation

**Files:**
- Modify: `legal-workbench/README.md`

**Step 1: Update README with new module list**

Add section:

```markdown
## Modules (v2.6.0)

| Module | ID | Status | Backend |
|--------|-----|--------|---------|
| Text Extractor | text_extractor | Active | ferramentas/legal-text-extractor |
| Document Assembler | doc_assembler | Active | ferramentas/legal-doc-assembler |
| STJ Dados Abertos | stj | Active | ferramentas/stj-dados-abertos |
| Trello MCP | trello | Active | ferramentas/trello-mcp |

### Architecture

```
legal-workbench/
├── app.py              # Main hub (routing + sidebar)
├── config.yaml         # Module registry
├── modules/            # UI wrappers (Streamlit) - FRONTEND
│   ├── text_extractor.py
│   ├── doc_assembler.py
│   ├── stj.py
│   └── trello.py
└── ferramentas/        # Backend logic (pure Python)
    ├── legal-text-extractor/src/
    ├── legal-doc-assembler/src/
    ├── stj-dados-abertos/src/
    └── trello-mcp/src/
```

**Principle:** Absolute separation between frontend (modules/) and backend (ferramentas/src/).
```

**Step 2: Commit**

```bash
git add legal-workbench/README.md
git commit -m "docs(workbench): update README with module architecture"
```

---

## Task 8: Final Integration Test

**Step 1: Start the application**

```bash
cd legal-workbench
source .venv/bin/activate
streamlit run app.py --server.port 8501
```

**Step 2: Verify each module loads**

1. Click "Dashboard" - should show system status
2. Click "Text Extractor" - should show upload interface
3. Click "Document Assembler" - should show JSON input + batch tabs
4. Click "STJ Dados Abertos" - should show search/download/stats tabs
5. Click "Trello MCP" - should show boards/extraction tabs

**Step 3: Push all changes**

```bash
git push origin main
```

---

## Summary

| Task | Description | Estimated Time |
|------|-------------|----------------|
| 1 | Fix config.yaml | 2 min |
| 2 | Create doc_assembler.py | 5 min |
| 3 | Create stj.py | 5 min |
| 4 | Create trello.py | 5 min |
| 5 | Fix text_extractor imports | 3 min |
| 6 | Verify all imports | 3 min |
| 7 | Update documentation | 3 min |
| 8 | Integration test | 5 min |

**Total: ~30 minutes**
