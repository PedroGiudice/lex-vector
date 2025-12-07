"""
Text Extractor Module - Streamlit UI for legal-text-extractor

Provides:
- PDF upload interface
- Real-time extraction progress
- Output preview and download
"""
import streamlit as st
import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime

# Add ferramentas to path for imports
FERRAMENTAS_PATH = Path(__file__).parent.parent / "ferramentas" / "legal-text-extractor"
if str(FERRAMENTAS_PATH) not in sys.path:
    sys.path.insert(0, str(FERRAMENTAS_PATH))


def render():
    """Main render function for the Text Extractor module."""
    st.title("Text Extractor")
    st.caption("Extrai texto limpo de PDFs jurídicos brasileiros")

    # Check dependencies
    if not _check_dependencies():
        return

    st.markdown("---")

    # Layout: Upload + Options | Output
    col_upload, col_output = st.columns([1, 2])

    with col_upload:
        st.markdown("#### Upload")
        uploaded_file = st.file_uploader(
            "Selecione um PDF",
            type=["pdf"],
            help="Arraste ou clique para selecionar um arquivo PDF jurídico"
        )

        st.markdown("#### Opções")
        system_hint = st.selectbox(
            "Sistema Judicial (opcional)",
            options=["Auto-detectar", "PJe", "ESAJ", "eProc", "Projudi", "TJSP", "STF", "STJ"],
            index=0,
            help="Deixe em Auto-detectar para identificação automática"
        )

        output_format = st.selectbox(
            "Formato de Saída",
            options=["text", "markdown", "json"],
            index=0,
            help="Formato do arquivo de saída"
        )

        # Extract button
        extract_btn = st.button(
            "Extrair Texto",
            type="primary",
            disabled=uploaded_file is None,
            use_container_width=True
        )

    with col_output:
        st.markdown("#### Output")

        # Initialize session state for results
        if "extraction_result" not in st.session_state:
            st.session_state.extraction_result = None
        if "extraction_stats" not in st.session_state:
            st.session_state.extraction_stats = None

        # Process extraction
        if extract_btn and uploaded_file is not None:
            _run_extraction(uploaded_file, system_hint, output_format)

        # Display results
        if st.session_state.extraction_result:
            _display_results(output_format)
        else:
            st.info("Faça upload de um PDF e clique em 'Extrair Texto' para começar.")


def _check_dependencies() -> bool:
    """Check if required dependencies are available."""
    missing = []

    try:
        import pdfplumber
    except ImportError:
        missing.append("pdfplumber")

    # Check if extractor module is accessible
    try:
        from src.pipeline.orchestrator import PipelineOrchestrator
    except ImportError as e:
        st.error(f"""
        **Dependências não encontradas**

        O módulo `legal-text-extractor` não está configurado corretamente.

        Execute no terminal:
        ```bash
        cd legal-workbench/ferramentas/legal-text-extractor
        pip install -r requirements.txt
        ```

        Erro: `{e}`
        """)
        return False

    if missing:
        st.error(f"Dependências faltando: {', '.join(missing)}")
        return False

    return True


def _run_extraction(uploaded_file, system_hint: str, output_format: str):
    """Run the extraction pipeline with progress updates."""
    from src.pipeline.orchestrator import PipelineOrchestrator, PipelineResult

    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = Path(tmp.name)

    try:
        # Progress container
        progress_container = st.empty()
        status_container = st.empty()

        # Initialize orchestrator
        orchestrator = PipelineOrchestrator()

        # Progress callback for Streamlit
        def on_progress(current: int, total: int, message: str):
            if total > 0:
                progress_container.progress(current / total, text=f"Página {current}/{total}")
            status_container.text(message)

        # Run extraction
        start_time = time.time()
        result: PipelineResult = orchestrator.process(tmp_path, progress_callback=on_progress)
        elapsed = time.time() - start_time

        # Clear progress indicators
        progress_container.empty()
        status_container.empty()

        if result.success:
            st.session_state.extraction_result = result.text
            st.session_state.extraction_stats = {
                "total_pages": result.total_pages,
                "processing_time_ms": result.processing_time_ms,
                "elapsed_seconds": elapsed,
                "warnings": result.warnings,
                "patterns_learned": result.patterns_learned,
                "filename": uploaded_file.name,
                "timestamp": datetime.now().isoformat(),
            }
            st.success(f"Extração concluída em {elapsed:.1f}s")
        else:
            st.error(f"Falha na extração: {result.metadata.get('error', 'Erro desconhecido')}")
            if result.warnings:
                for w in result.warnings:
                    st.warning(w)

    finally:
        # Cleanup temp file
        tmp_path.unlink(missing_ok=True)


def _display_results(output_format: str):
    """Display extraction results with stats and download options."""
    result = st.session_state.extraction_result
    stats = st.session_state.extraction_stats

    # Stats row
    if stats:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Páginas", stats["total_pages"])
        with c2:
            st.metric("Tempo", f"{stats['elapsed_seconds']:.1f}s")
        with c3:
            st.metric("Caracteres", f"{len(result):,}")
        with c4:
            st.metric("Warnings", len(stats.get("warnings", [])))

    # Text output
    st.text_area(
        "Texto Extraído",
        value=result,
        height=400,
        help="Texto limpo extraído do PDF"
    )

    # Download buttons
    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        # Determine extension based on format
        ext_map = {"text": "txt", "markdown": "md", "json": "json"}
        ext = ext_map.get(output_format, "txt")

        filename = stats.get("filename", "documento").replace(".pdf", f"_extracted.{ext}")

        st.download_button(
            label=f"Download (.{ext})",
            data=result,
            file_name=filename,
            mime="text/plain",
            use_container_width=True
        )

    with col_dl2:
        if st.button("Limpar", use_container_width=True):
            st.session_state.extraction_result = None
            st.session_state.extraction_stats = None
            st.rerun()

    # Show warnings if any
    if stats and stats.get("warnings"):
        with st.expander(f"Warnings ({len(stats['warnings'])})"):
            for w in stats["warnings"]:
                st.warning(w)
