# modules/text_extractor.py

import streamlit as st
from pathlib import Path
import sys
import time

# Adiciona o diretório de ferramentas ao path para importação do backend
tool_path = Path(__file__).parent.parent / "ferramentas"
sys.path.append(str(tool_path))

from legal_text_extractor.main import LegalTextExtractor, ExtractionResult

def render():
    """Renders the Streamlit UI for the Text Extractor module."""
    st.header("Text Extractor")
    st.caption("Extraia e limpe texto de documentos jurídicos em PDF.")

    # --- Session State Initialization ---
    if "extraction_result" not in st.session_state:
        st.session_state.extraction_result = None

    # --- File Uploader ---
    uploaded_file = st.file_uploader(
        "Selecione um arquivo PDF",
        type="pdf",
        help="Faça o upload de um PDF para extrair o texto."
    )

    if uploaded_file:
        st.info(f"Arquivo selecionado: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")

        # --- Extraction Button ---
        if st.button("▶️ Iniciar Extração", use_container_width=True):
            st.session_state.extraction_result = None
            
            # Save the uploaded file temporarily to pass its path to the backend
            temp_dir = Path.home() / "juridico-data" / "temp"
            temp_dir.mkdir(exist_ok=True)
            temp_path = temp_dir / uploaded_file.name
            
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # --- Progress Bar and Execution ---
            progress_bar = st.progress(0, "Inicializando...")
            status_text = st.empty()
            
            try:
                extractor = LegalTextExtractor()
                
                status_text.text("1/2 Extraindo texto...")
                progress_bar.progress(25)
                # Simular um tempo para a UI atualizar
                time.sleep(0.1)

                result = extractor.process_pdf(temp_path)
                
                status_text.text("2/2 Limpeza e análise concluídas!")
                progress_bar.progress(100)
                time.sleep(0.5)

                st.session_state.extraction_result = result
                status_text.success("Extração concluída com sucesso!")
                progress_bar.empty()

            except Exception as e:
                st.error(f"Ocorreu um erro durante a extração: {e}")
                st.session_state.extraction_result = None
            finally:
                # Clean up the temporary file
                if temp_path.exists():
                    temp_path.unlink()
    
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
        
        # --- Extracted Text Output ---
        st.text_area(
            "Texto Extraído",
            value=result.text,
            height=400,
            help="Texto limpo e processado. Padrões de assinatura e formatação foram removidos."
        )