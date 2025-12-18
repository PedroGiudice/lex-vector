# Integration Example

How to integrate the STJ Client proxy layer into FastHTML routes.

## Step 1: Import the Client

```python
# app.py
from fasthtml.common import *
from services import STJClient, STJConnectionError, STJValidationError
```

## Step 2: Replace Mock Data with Real API Calls

### Before (Mock Data)

```python
@rt("/search-results")
def get(domain: str = "", keywords: List[str] = None):
    """HTMX endpoint: Execute search and return results"""

    # OLD: Mock data
    search_results = mock_data.generate_mock_acordaos(domain, keywords)

    return results.results_container(search_results)
```

### After (Real Backend)

```python
@rt("/search-results")
async def get(termo: str = "", orgao: str = "", dias: int = 365):
    """HTMX endpoint: Execute search and return results"""

    # Validate input
    if len(termo) < 3:
        return Div(
            "Search term must be at least 3 characters",
            cls="error-message"
        )

    try:
        # Call backend through proxy
        async with STJClient() as client:
            response = await client.search(
                termo=termo,
                orgao=orgao if orgao else None,
                dias=dias,
                limit=50
            )

        # Transform API response to UI components
        return results.results_container(
            acordaos=response.resultados,
            total=response.total
        )

    except STJValidationError as e:
        return Div(
            f"Invalid search: {e}",
            cls="error-message"
        )

    except STJConnectionError:
        return Div(
            "Cannot connect to backend. Please try again later.",
            cls="error-message"
        )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return Div(
            "An error occurred. Please try again.",
            cls="error-message"
        )
```

## Step 3: Update Stats Endpoint

### Before

```python
@rt("/")
def get():
    stats = mock_data.get_quick_stats()
    return Html(...)
```

### After

```python
@rt("/")
async def get():
    # Fetch real stats from backend
    try:
        async with STJClient() as client:
            stats_response = await client.get_stats()

        stats = {
            'total': stats_response.total_acordaos,
            'last_30_days': stats_response.ultimos_30_dias,
            'db_size': stats_response.tamanho_db_mb
        }

    except STJConnectionError:
        # Fallback to placeholder
        stats = {
            'total': 0,
            'last_30_days': 0,
            'db_size': 0.0
        }

    return Html(...)
```

## Step 4: Add Case Detail Modal

```python
@rt("/case/{case_id}")
async def get(case_id: str):
    """HTMX endpoint: Show case details in modal"""

    try:
        async with STJClient() as client:
            case = await client.get_case(case_id)

        return Div(
            # Modal overlay
            Div(
                # Modal content
                Div(
                    H2(f"Processo: {case.numero_processo}", cls="modal-title"),

                    Div(
                        Span("Órgão: ", cls="label"),
                        Span(case.orgao_julgador, cls="value"),
                    ),

                    Div(
                        Span("Relator: ", cls="label"),
                        Span(case.relator or "N/A", cls="value"),
                    ),

                    Div(
                        Span("Data Julgamento: ", cls="label"),
                        Span(case.data_julgamento.strftime("%d/%m/%Y") if case.data_julgamento else "N/A", cls="value"),
                    ),

                    Div(
                        H3("Ementa", cls="section-title"),
                        P(case.ementa or "Não disponível", cls="ementa"),
                    ),

                    # Close button
                    Button(
                        "Fechar",
                        hx_get="/close-modal",
                        hx_target="#modal-container",
                        hx_swap="outerHTML",
                        cls="btn-close"
                    ),

                    cls="modal-content"
                ),
                cls="modal-overlay"
            ),
            id="modal-container"
        )

    except STJNotFoundError:
        return Div(
            "Case not found",
            cls="error-message"
        )
```

## Step 5: Sync Status Polling

```python
@rt("/sync/status")
async def get():
    """HTMX endpoint: Poll sync status"""

    try:
        async with STJClient() as client:
            status = await client.get_sync_status()

        # Determine if still running
        is_running = status.status == "running"

        return Div(
            Div(
                Span("Status: ", cls="label"),
                Span(
                    status.status.upper(),
                    cls=f"badge badge-{status.status}"
                ),
            ),

            Div(
                Span("Processed: ", cls="label"),
                Span(f"{status.processed}/{status.downloaded}", cls="value"),
            ),

            Div(
                Span("Inserted: ", cls="label"),
                Span(str(status.inserted), cls="value text-green-400"),
            ),

            Div(
                Span("Duplicates: ", cls="label"),
                Span(str(status.duplicates), cls="value text-yellow-400"),
            ),

            Div(
                Span("Errors: ", cls="label"),
                Span(str(status.errors), cls="value text-red-400"),
            ),

            # Continue polling if running
            hx_get="/sync/status" if is_running else None,
            hx_trigger="every 2s" if is_running else None,
            hx_swap="outerHTML",
            id="sync-status-container"
        )

    except Exception as e:
        return Div(
            f"Cannot fetch sync status: {e}",
            cls="error-message"
        )
```

## Step 6: Trigger Sync

```python
@rt("/sync/trigger")
async def post(dias: int = 30, force: bool = False):
    """HTMX endpoint: Trigger data sync"""

    try:
        async with STJClient() as client:
            status = await client.trigger_sync(
                dias=dias,
                force=force
            )

        return Div(
            Div(
                "Sync started successfully!",
                cls="success-message"
            ),

            # Start polling for status
            Div(
                hx_get="/sync/status",
                hx_trigger="load",
                hx_swap="outerHTML",
                id="sync-status-container"
            )
        )

    except Exception as e:
        return Div(
            f"Failed to start sync: {e}",
            cls="error-message"
        )
```

## Step 7: Health Check Badge

```python
@rt("/health-badge")
async def get():
    """HTMX endpoint: Show backend health status"""

    try:
        async with STJClient() as client:
            health = await client.health_check()

        is_healthy = health.status == "healthy" and health.database == "connected"

        return Div(
            Span(
                "●",
                cls=f"text-{'green' if is_healthy else 'red'}-400 text-2xl"
            ),
            Span(
                "Backend: " + ("Online" if is_healthy else "Offline"),
                cls="ml-2 text-sm"
            ),

            # Poll every 30s
            hx_get="/health-badge",
            hx_trigger="every 30s",
            hx_swap="outerHTML",
            id="health-badge"
        )

    except STJConnectionError:
        return Div(
            Span("●", cls="text-red-400 text-2xl"),
            Span("Backend: Offline", cls="ml-2 text-sm"),

            # Retry more frequently when down
            hx_get="/health-badge",
            hx_trigger="every 10s",
            hx_swap="outerHTML",
            id="health-badge"
        )
```

## Step 8: Update Component Functions

### results.py (results component)

```python
def results_container(acordaos: List[AcordaoSummary], total: int = 0) -> FT:
    """Results container component."""

    if not acordaos:
        return Div(
            # ASCII art for empty state
            Pre("""
    ╔════════════════════════════════╗
    ║   No results found             ║
    ║   Try adjusting your filters   ║
    ╚════════════════════════════════╝
            """, cls="ascii-art"),
            id="results-container"
        )

    return Div(
        Div(
            Span(f"Found {total} results", cls="results-count"),
            cls="results-header"
        ),

        Div(
            *[result_card(acordao) for acordao in acordaos],
            cls="results-list"
        ),

        id="results-container"
    )


def result_card(acordao: AcordaoSummary) -> FT:
    """Individual result card."""

    return Div(
        Div(
            Span(acordao.numero_processo, cls="process-number"),
            Span(
                acordao.resultado_julgamento or "N/A",
                cls=f"badge badge-{acordao.resultado_julgamento}"
            ),
            cls="card-header"
        ),

        Div(
            Div(
                Span("Órgão: ", cls="label"),
                Span(acordao.orgao_julgador, cls="value"),
            ),
            Div(
                Span("Relator: ", cls="label"),
                Span(acordao.relator or "N/A", cls="value"),
            ),
            cls="card-body"
        ),

        Div(
            P(
                acordao.ementa[:200] + "..." if acordao.ementa and len(acordao.ementa) > 200 else acordao.ementa or "N/A",
                cls="ementa-preview"
            ),
        ),

        # Click to open modal
        Button(
            "Ver Detalhes",
            hx_get=f"/case/{acordao.id}",
            hx_target="#modal-container",
            hx_swap="outerHTML",
            cls="btn-secondary"
        ),

        cls="result-card"
    )
```

## Complete Example Route File

```python
"""
Real API integration example.
Replace mock_data calls with STJClient calls.
"""

from fasthtml.common import *
from typing import List
from services import (
    STJClient,
    STJConnectionError,
    STJValidationError,
    STJNotFoundError,
    AcordaoSummary
)
from components import results
import logging

logger = logging.getLogger(__name__)


@rt("/api/search")
async def search(
    termo: str = "",
    orgao: str = "",
    dias: int = 365,
    limit: int = 50
):
    """Search endpoint with real backend."""

    if len(termo) < 3:
        return Div("Minimum 3 characters", cls="error")

    try:
        async with STJClient() as client:
            response = await client.search(
                termo=termo,
                orgao=orgao if orgao else None,
                dias=dias,
                limit=limit
            )

        return results.results_container(
            acordaos=response.resultados,
            total=response.total
        )

    except STJValidationError as e:
        return Div(str(e), cls="error")

    except STJConnectionError:
        return Div("Backend unavailable", cls="error")

    except Exception as e:
        logger.error(f"Search error: {e}")
        return Div("Error occurred", cls="error")


@rt("/api/case/{case_id}")
async def get_case(case_id: str):
    """Get case details."""

    try:
        async with STJClient() as client:
            case = await client.get_case(case_id)

        # Return modal with case details
        return case_detail_modal(case)

    except STJNotFoundError:
        return Div("Case not found", cls="error")
```

## Testing the Integration

```bash
# 1. Install dependencies
cd poc-fasthtml-stj
source .venv/bin/activate
pip install -r requirements.txt

# 2. Test the client
python services/test_stj_client.py

# 3. Start the app
python app.py

# 4. Visit http://localhost:5001
```

---

**Next Steps:**
1. Replace all `mock_data` calls with `STJClient` calls
2. Add error boundaries for all API calls
3. Implement loading states
4. Add retry UI for failed requests
5. Cache frequent queries
