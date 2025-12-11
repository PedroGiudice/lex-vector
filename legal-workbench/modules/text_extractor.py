# modules/text_extractor.py
"""
Text Extractor UI Module for Legal Workbench.

Provides Streamlit interface for the legal-text-extractor backend.
Supports low-memory mode for systems with <10GB RAM.
Integrates Step 04 (Bibliotecário/Gemini classification).
"""

import streamlit as st
from pathlib import Path
import sys
import time
import json

# Adiciona o diretório do backend ao path (diretório tem hífen, não pode ser importado direto)
backend_path = Path(__file__).parent.parent / "ferramentas" / "legal-text-extractor"
sys.path.insert(0, str(backend_path))

from main import LegalTextExtractor, ExtractionResult
from src.steps.step_04_classify import GeminiBibliotecario, BibliotecarioConfig


def check_marker_availability(low_memory_mode: bool = False) -> tuple[bool, str]:
    """
    Check if Marker engine is available.

    Returns:
        (available, message) tuple
    """
    try:
        extractor = LegalTextExtractor(low_memory_mode=low_memory_mode)
        if extractor.marker_engine.is_available():
            return True, "Marker disponível"
        else:
            ok, reason = extractor.marker_engine.check_resources()
            return False, reason
    except Exception as e:
        return False, str(e)


def render():
    """Renders the Streamlit UI for the Text Extractor module."""
    st.header("Text Extractor")
    st.caption("Extraia e limpe texto de documentos jurídicos em PDF.")

    # --- Session State Initialization ---
    if "extraction_result" not in st.session_state:
        st.session_state.extraction_result = None
    if "low_memory_mode" not in st.session_state:
        st.session_state.low_memory_mode = False
    if "classification_result" not in st.session_state:
        st.session_state.classification_result = None
    if "enable_classification" not in st.session_state:
        st.session_state.enable_classification = False
    if "classification_skip_cleaning" not in st.session_state:
        st.session_state.classification_skip_cleaning = False
    if "classification_model" not in st.session_state:
        st.session_state.classification_model = "gemini-2.5-flash"

    # --- Configuration Sidebar ---
    with st.expander("⚙️ Configurações", expanded=False):
        st.subheader("Extração")
        low_memory = st.checkbox(
            "🔋 Modo Baixa Memória",
            value=st.session_state.low_memory_mode,
            help="Ignora verificação de RAM. Use se seu sistema tem <10GB RAM mas tem swap disponível. "
                 "⚠️ Pode deixar o sistema lento para PDFs grandes."
        )
        st.session_state.low_memory_mode = low_memory

        st.divider()
        st.subheader("Classificação Semântica (Step 04)")

        enable_classification = st.checkbox(
            "🤖 Ativar Classificação com Gemini",
            value=st.session_state.enable_classification,
            help="Classifica o documento em categorias jurídicas usando IA (Gemini 2.5)."
        )
        st.session_state.enable_classification = enable_classification

        if enable_classification:
            col1, col2 = st.columns(2)

            with col1:
                model = st.selectbox(
                    "Modelo Gemini",
                    options=["gemini-2.5-flash", "gemini-2.5-pro"],
                    index=0 if st.session_state.classification_model == "gemini-2.5-flash" else 1,
                    help="Flash é mais rápido e barato. Pro tem melhor qualidade."
                )
                st.session_state.classification_model = model

            with col2:
                skip_cleaning = st.checkbox(
                    "Pular limpeza contextual",
                    value=st.session_state.classification_skip_cleaning,
                    help="Desativa a fase de limpeza, gerando apenas classificação."
                )
                st.session_state.classification_skip_cleaning = skip_cleaning

            st.info(
                "ℹ️ A classificação identifica seções como: Petição Inicial, Contestação, "
                "Sentença, Acórdão, etc. A limpeza remove ruído contextual preservando conteúdo."
            )

    # --- System Status ---
    available, message = check_marker_availability(st.session_state.low_memory_mode)

    if available:
        st.success("✅ Marker engine disponível")
    else:
        st.error(f"❌ Marker indisponível: {message}")

        # Show helpful suggestions
        st.markdown("""
        **Possíveis soluções:**
        1. **Ative o modo baixa memória** (checkbox acima) se você tem swap disponível
        2. Feche outros programas para liberar RAM
        3. Reinicie o WSL2 com `wsl --shutdown` e tente novamente

        **Nota:** O Marker requer ~10GB RAM para processar PDFs com OCR.
        Sistemas com menos RAM podem usar o modo baixa memória, mas o processamento será mais lento.
        """)

        if not st.session_state.low_memory_mode:
            if st.button("🔋 Tentar com Modo Baixa Memória"):
                st.session_state.low_memory_mode = True
                st.rerun()

    # --- File Uploader ---
    uploaded_file = st.file_uploader(
        "Selecione um arquivo PDF",
        type="pdf",
        help="Faça o upload de um PDF para extrair o texto.",
        disabled=not available
    )

    if uploaded_file:
        st.info(f"Arquivo selecionado: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")

        # --- Extraction Button ---
        if st.button("▶️ Iniciar Extração", use_container_width=True, disabled=not available):
            st.session_state.extraction_result = None
            st.session_state.classification_result = None

            # Save the uploaded file temporarily to pass its path to the backend
            temp_dir = Path.home() / "juridico-data" / "temp"
            temp_dir.mkdir(exist_ok=True, parents=True)
            temp_path = temp_dir / uploaded_file.name

            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # --- Progress Bar and Execution ---
            total_steps = 3 if st.session_state.enable_classification else 2
            progress_bar = st.progress(0, "Inicializando...")
            status_text = st.empty()

            try:
                # Step 1: Extract text
                extractor = LegalTextExtractor(low_memory_mode=st.session_state.low_memory_mode)

                status_text.text(f"1/{total_steps} Extraindo texto (pode demorar alguns minutos)...")
                progress_bar.progress(int(33 if total_steps == 3 else 50))
                time.sleep(0.1)

                result = extractor.process_pdf(temp_path)

                status_text.text(f"2/{total_steps} Limpeza e análise concluídas!")
                progress_bar.progress(int(66 if total_steps == 3 else 100))
                time.sleep(0.5)

                st.session_state.extraction_result = result

                # Step 2 (optional): Classify with Gemini
                if st.session_state.enable_classification:
                    status_text.text(f"3/{total_steps} Classificando documento com Gemini...")
                    progress_bar.progress(75)
                    time.sleep(0.1)

                    # Save extracted text to temporary markdown file for classification
                    output_dir = temp_dir / "output"
                    output_dir.mkdir(exist_ok=True, parents=True)
                    final_md_path = output_dir / "final.md"
                    final_md_path.write_text(result.text, encoding="utf-8")

                    # Configure and run Bibliotecario
                    config = BibliotecarioConfig(
                        model=st.session_state.classification_model,
                        skip_cleaning=st.session_state.classification_skip_cleaning,
                    )
                    bibliotecario = GeminiBibliotecario(config=config)

                    classification_result = bibliotecario.process(final_md_path, output_dir)
                    st.session_state.classification_result = classification_result

                    progress_bar.progress(100)
                    status_text.success("Extração e classificação concluídas com sucesso!")
                else:
                    status_text.success("Extração concluída com sucesso!")

                progress_bar.empty()

            except Exception as e:
                st.error(f"Ocorreu um erro durante o processamento: {e}")

                # Show more details for debugging
                if st.session_state.enable_classification and "Gemini" in str(e):
                    st.markdown("""
                    **Possíveis causas do erro com Gemini:**
                    1. Verifique se a variável de ambiente `GOOGLE_API_KEY` está configurada
                    2. Verifique sua conexão com a internet
                    3. O modelo selecionado pode estar temporariamente indisponível
                    4. Tente desativar a classificação ou usar outro modelo
                    """)

                st.session_state.extraction_result = None
                st.session_state.classification_result = None
            finally:
                # Clean up temporary files
                if temp_path.exists():
                    temp_path.unlink()
                if st.session_state.enable_classification:
                    output_dir = temp_dir / "output"
                    if output_dir.exists():
                        import shutil
                        shutil.rmtree(output_dir)

    # --- Results Display ---
    if st.session_state.extraction_result:
        result = st.session_state.extraction_result
        st.markdown("---")
        st.subheader("Resultados da Extração")

        # --- Metrics ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Sistema Detectado", result.system_name, f"{result.confidence}%")
        col2.metric("Redução de Texto", f"{result.reduction_pct:.1f}%")
        col3.metric("Caracteres Originais", f"{result.original_length:,}")
        col4.metric("Caracteres Finais", f"{result.final_length:,}")

        # --- Engine Info ---
        col5, col6 = st.columns(2)
        col5.metric("Páginas Nativas", result.native_pages)
        col6.metric("Páginas OCR", result.ocr_pages)

        # --- Classification Results (if enabled) ---
        if st.session_state.classification_result:
            st.markdown("---")
            st.subheader("📋 Resultados da Classificação Semântica")

            classification = st.session_state.classification_result

            # --- Classification Metrics ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Total de Seções", classification['classification'].total_sections)
            col2.metric("Total de Páginas", classification['classification'].total_pages)
            col3.metric("Modelo Usado", st.session_state.classification_model.replace("gemini-", "Gemini "))

            # --- Document Summary ---
            st.markdown("**Resumo do Documento:**")
            st.info(classification['classification'].summary)

            # --- Sections Table ---
            st.markdown("**Seções Identificadas:**")
            sections_data = []
            for section in classification['classification'].sections:
                sections_data.append({
                    "Seção": section.section_id,
                    "Tipo": section.type.value,
                    "Título": section.title[:50] + "..." if len(section.title) > 50 else section.title,
                    "Páginas": f"{section.start_page}-{section.end_page}",
                    "Confiança": f"{section.confidence:.0%}"
                })

            st.dataframe(sections_data, use_container_width=True, hide_index=True)

            # --- Cleaning Results (if not skipped) ---
            if classification['cleaning'] and classification['cleaning'].sections:
                st.markdown("**Resultados da Limpeza:**")
                col1, col2, col3 = st.columns(3)
                col1.metric("Caracteres Originais", f"{classification['cleaning'].total_chars_original:,}")
                col2.metric("Caracteres Limpos", f"{classification['cleaning'].total_chars_cleaned:,}")
                col3.metric("Redução", f"{classification['cleaning'].reduction_percent:.1f}%")

            # --- Download Buttons for Classification Outputs ---
            st.markdown("**Arquivos Gerados:**")
            download_cols = st.columns(3)

            # semantic_structure.json
            if 'semantic_structure.json' in classification['output_files']:
                with download_cols[0]:
                    structure_path = Path(classification['output_files']['semantic_structure.json'])
                    if structure_path.exists():
                        st.download_button(
                            label="📄 Estrutura JSON",
                            data=structure_path.read_text(encoding="utf-8"),
                            file_name="semantic_structure.json",
                            mime="application/json",
                            use_container_width=True
                        )

            # final_tagged.md
            if 'final_tagged.md' in classification['output_files']:
                with download_cols[1]:
                    tagged_path = Path(classification['output_files']['final_tagged.md'])
                    if tagged_path.exists():
                        st.download_button(
                            label="📝 Texto Tagueado",
                            data=tagged_path.read_text(encoding="utf-8"),
                            file_name="final_tagged.md",
                            mime="text/markdown",
                            use_container_width=True
                        )

            # final_cleaned.md
            if 'final_cleaned.md' in classification['output_files']:
                with download_cols[2]:
                    cleaned_path = Path(classification['output_files']['final_cleaned.md'])
                    if cleaned_path.exists():
                        st.download_button(
                            label="✨ Texto Limpo",
                            data=cleaned_path.read_text(encoding="utf-8"),
                            file_name="final_cleaned.md",
                            mime="text/markdown",
                            use_container_width=True
                        )

        # --- Extracted Text Output ---
        st.markdown("---")
        st.text_area(
            "Texto Extraído",
            value=result.text,
            height=400,
            help="Texto limpo e processado. Padrões de assinatura e formatação foram removidos."
        )

        # --- Download Button ---
        st.download_button(
            label="📥 Baixar texto extraído",
            data=result.text,
            file_name=f"extracted_{uploaded_file.name.replace('.pdf', '.txt')}" if uploaded_file else "extracted.txt",
            mime="text/plain"
        )
