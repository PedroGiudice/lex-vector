import streamlit as st
import sys
import os
import tempfile
from pathlib import Path
import pandas as pd

# Path setup for backend module (LTE/backend)
BACKEND_PATH = Path(__file__).parent.parent / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from src.pipeline.orchestrator import PipelineOrchestrator, PipelineResult

# 1. PAGE CONFIG
st.set_page_config(layout="wide", page_title="Legal CLI", page_icon="⚖️")

# 2. DARK THEME CSS - White text with colored accents
st.markdown("""
<style>
    /* Global Dark Background, White Text */
    .stApp {
        background-color: #0a0a0a;
        color: #ffffff;
        font-family: 'Courier New', monospace;
    }

    /* Main text - White */
    .stMarkdown, p, span, label, .stTextArea textarea {
        color: #ffffff !important;
    }

    /* Headers - Cyan accent */
    h1, h2, h3 {
        color: #00d4ff !important;
    }
    h1 {
        border-bottom: 2px solid #ff00ff;
        padding-bottom: 10px;
    }

    /* Sidebar header - Magenta */
    .stSidebar h1, .stSidebar h2, .stSidebar h3 {
        color: #ff00ff !important;
    }

    /* Primary Button - Cyan */
    .stButton>button {
        border: 2px solid #00d4ff;
        background-color: transparent;
        color: #00d4ff !important;
        border-radius: 4px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #00d4ff;
        color: #0a0a0a !important;
    }

    /* Success messages - Green */
    .stSuccess {
        color: #00ff88 !important;
    }

    /* Warning/Error - Orange/Red */
    .stWarning { color: #ffaa00 !important; }
    .stError { color: #ff4444 !important; }

    /* Tabs - Yellow accent */
    .stTabs [data-baseweb="tab"] {
        color: #ffffff !important;
    }
    .stTabs [aria-selected="true"] {
        color: #ffdd00 !important;
        border-bottom-color: #ffdd00 !important;
    }

    /* DataFrame/Table styling */
    .stDataFrame { color: #ffffff !important; }

    /* File uploader */
    .stFileUploader label { color: #ffffff !important; }

    /* Selectbox */
    .stSelectbox label { color: #ffffff !important; }

    /* Progress bar - Gradient */
    .stProgress > div > div {
        background: linear-gradient(90deg, #00d4ff, #ff00ff);
    }

    /* Caption/small text - Gray */
    .stCaption, small {
        color: #888888 !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_orchestrator() -> PipelineOrchestrator:
    """
    Initialize and cache the PipelineOrchestrator.

    Uses @st.cache_resource to prevent reloading heavy ML models
    on every Streamlit interaction.
    """
    return PipelineOrchestrator(context_db_path=None, caso_info=None)


def save_uploaded_file_to_temp(uploaded_file) -> Path:
    """
    Save Streamlit uploaded file (BytesIO) to a temporary file.

    Uses tempfile.NamedTemporaryFile to create a unique file path,
    avoiding conflicts in concurrent usage scenarios.

    Args:
        uploaded_file: Streamlit UploadedFile object (BytesIO-like)

    Returns:
        Path to the temporary file
    """
    # Create unique temp file to avoid concurrent user conflicts
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", prefix="legal_extractor_") as tmp:
        tmp.write(uploaded_file.getbuffer())
        return Path(tmp.name)


def map_result_to_session_state(result: PipelineResult) -> dict:
    """
    Map PipelineOrchestrator result to the UI session_state structure.

    Args:
        result: PipelineResult from the orchestrator

    Returns:
        Dictionary with 'raw', 'json', and 'debug' keys for UI display
    """
    # RAW: The extracted text
    raw_text = result.text if result.text else "[NO TEXT EXTRACTED]"

    # JSON: Structured extraction metadata
    json_data = {
        "status": "success" if result.success else "failed",
        "total_pages": result.total_pages,
        "patterns_learned": result.patterns_learned,
        "processing_time_ms": result.processing_time_ms,
        "warnings": result.warnings,
        "metadata": result.metadata,
    }

    # DEBUG: Processing metrics as DataFrame
    metrics_data = {
        "metric": [
            "Total Pages",
            "Processing Time (ms)",
            "Patterns Learned",
            "Success",
            "Warnings Count",
        ],
        "value": [
            result.total_pages,
            result.processing_time_ms or 0,
            result.patterns_learned,
            "YES" if result.success else "NO",
            len(result.warnings),
        ],
    }
    debug_df = pd.DataFrame(metrics_data)

    return {
        "raw": raw_text,
        "json": json_data,
        "debug": debug_df,
    }


# 3. HEADER (Simple & Safe)
st.title(">> LEGAL_EXTRACTOR_V1")

# 4. SIDEBAR
with st.sidebar:
    st.header(">> INPUT_ZONE")
    uploaded_file = st.file_uploader("UPLOAD_TARGET [PDF]", type=['pdf'])
    # System selection (reserved for future ContextStore integration)
    # When context_db_path is provided, this will be passed to caso_info
    system = st.selectbox("JUDICIAL_SYSTEM", ["AUTO_DETECT", "PJE", "ESAJ", "STF"])
    process_btn = st.button(">> EXECUTE PIPELINE", use_container_width=True)

    # Developer tools section
    st.divider()
    st.caption(">> DEV_TOOLS")
    if st.button("RELOAD_BACKEND", use_container_width=True, help="Hot-fix: reload orchestrator after backend changes"):
        st.cache_resource.clear()
        st.success("> [OK] CACHE CLEARED")
        st.rerun()

# 5. MAIN EXECUTION
if process_btn:
    if uploaded_file is None:
        st.error("> [ERROR] NO FILE UPLOADED. PLEASE UPLOAD A PDF.")
    else:
        # Get cached orchestrator instance
        orchestrator = get_orchestrator()

        # Progress placeholder for real-time updates
        progress_bar = st.progress(0)
        status_container = st.status(">> RUNNING SYSTEM...", expanded=True)

        with status_container:
            st.write("> [INIT] MEMORY CHECK...")
            st.write("> [OK] CORE MODULES LOADED")
            st.write("> [PROC] SAVING UPLOADED FILE...")

            # Save uploaded BytesIO to temp file
            temp_file_path = save_uploaded_file_to_temp(uploaded_file)
            st.write(f"> [OK] TEMP FILE: {temp_file_path}")

            # Progress callback for orchestrator
            def progress_callback(current_page: int, total_pages: int, message: str):
                """Update Streamlit progress bar and status."""
                if total_pages > 0:
                    progress = current_page / total_pages
                    progress_bar.progress(progress)
                st.write(f"> [PROC] {message}")

            st.write("> [EXEC] STARTING PIPELINE...")

            try:
                # INTEGRATION POINT: Real backend call
                result: PipelineResult = orchestrator.process(
                    pdf_path=temp_file_path,
                    progress_callback=progress_callback,
                )

                # Map result to UI structure
                st.session_state['results'] = map_result_to_session_state(result)

                # Final status update
                progress_bar.progress(1.0)

                if result.success:
                    st.write(f"> [OK] EXTRACTED {result.total_pages} PAGES")
                    st.write(f"> [OK] PROCESSING TIME: {result.processing_time_ms}ms")
                    status_container.update(label=">> PROCESS COMPLETE", state="complete")
                else:
                    st.write("> [WARN] EXTRACTION COMPLETED WITH ISSUES")
                    for warning in result.warnings:
                        st.write(f"> [WARN] {warning}")
                    status_container.update(label=">> PROCESS COMPLETE (WITH WARNINGS)", state="complete")

            except Exception as e:
                st.write(f"> [ERROR] PIPELINE FAILED: {e}")
                status_container.update(label=">> PROCESS FAILED", state="error")
                # Store error state in results
                st.session_state['results'] = {
                    "raw": f"[EXTRACTION FAILED]\n\nError: {e}",
                    "json": {"status": "error", "error": str(e)},
                    "debug": pd.DataFrame({"metric": ["Error"], "value": [str(e)]}),
                }
            finally:
                # Cleanup: Clear marker cache to free memory
                orchestrator.clear_marker_cache(temp_file_path)
                # Remove temp file to avoid disk clutter
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass  # Ignore if file already removed

# 6. RESULTS DISPLAY
if 'results' in st.session_state:
    tab1, tab2, tab3 = st.tabs(["RAW_TEXT", "JSON_DATA", "METRICS"])
    with tab1: st.text_area("", st.session_state['results']['raw'], height=400)
    with tab2: st.json(st.session_state['results']['json'])
    with tab3: st.dataframe(st.session_state['results']['debug'], use_container_width=True)
