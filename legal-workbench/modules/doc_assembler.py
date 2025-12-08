# modules/doc_assembler.py

import streamlit as st
from pathlib import Path
import sys
import json
import zipfile
import tempfile
from typing import Dict, Any, Optional, List

# Setup backend path (must be done before imports)
_backend_path = Path(__file__).parent.parent / "ferramentas" / "legal-doc-assembler"

# Module-level variables for lazy-loaded imports
_DocumentEngine = None
_BatchProcessor = None
_normalize_all = None


def _setup_imports():
    """Lazy import setup to avoid module resolution issues."""
    global _DocumentEngine, _BatchProcessor, _normalize_all

    if _DocumentEngine is None:
        if str(_backend_path) not in sys.path:
            sys.path.insert(0, str(_backend_path))

        from src.engine import DocumentEngine
        from src.batch_engine import BatchProcessor
        from src.normalizers import normalize_all

        _DocumentEngine = DocumentEngine
        _BatchProcessor = BatchProcessor
        _normalize_all = normalize_all

    return _DocumentEngine, _BatchProcessor, _normalize_all


def render():
    """Renders the Streamlit UI for the Document Assembler module."""
    # Initialize lazy imports
    _setup_imports()

    st.header("Document Assembler")
    st.caption("Monte documentos jurídicos a partir de templates .docx e dados JSON.")

    # --- Session State Initialization ---
    if "assembled_docs" not in st.session_state:
        st.session_state.assembled_docs = []
    if "batch_result" not in st.session_state:
        st.session_state.batch_result = None
    if "validation_result" not in st.session_state:
        st.session_state.validation_result = None

    # --- Tab Navigation ---
    tab1, tab2 = st.tabs(["📄 Documento Único", "📦 Processamento em Lote"])

    # ===== TAB 1: SINGLE DOCUMENT =====
    with tab1:
        render_single_document_tab()

    # ===== TAB 2: BATCH PROCESSING =====
    with tab2:
        render_batch_processing_tab()


def render_single_document_tab():
    """Render single document processing UI."""
    st.subheader("Processamento de Documento Único")
    st.markdown("Envie um template .docx e um arquivo JSON com os dados para gerar o documento.")

    col1, col2 = st.columns(2)

    with col1:
        template_file = st.file_uploader(
            "Template (.docx)",
            type="docx",
            key="single_template",
            help="Arquivo .docx com variáveis Jinja2 (ex: {{ nome }}, {{ cpf | cpf }})"
        )

    with col2:
        json_file = st.file_uploader(
            "Dados (JSON)",
            type="json",
            key="single_json",
            help="Arquivo JSON com os valores para as variáveis do template"
        )

    # --- Field Types Configuration ---
    with st.expander("⚙️ Configuração Avançada (Opcional)", expanded=False):
        st.markdown("**Tipos de campos para normalização automática:**")
        st.caption(
            "Deixe em branco para normalização automática básica. "
            "Cole um JSON mapeando campos para tipos: `{\"nome\": \"name\", \"cpf\": \"cpf\"}`"
        )

        field_types_json = st.text_area(
            "Mapeamento de Tipos",
            value="",
            height=100,
            placeholder='{"nome": "name", "endereco": "address", "cpf": "cpf", "cnpj": "cnpj"}',
            help=(
                "Tipos disponíveis: name, address, cpf, cnpj, cep, oab, text, raw. "
                "Exemplo: {\"nome\": \"name\", \"cpf\": \"cpf\"}"
            )
        )

    # --- Preview JSON Data ---
    if json_file:
        with st.expander("👁️ Visualizar Dados JSON", expanded=False):
            try:
                json_data = json.loads(json_file.getvalue().decode("utf-8"))
                st.json(json_data)
            except json.JSONDecodeError as e:
                st.error(f"JSON inválido: {e}")

    # --- Validation Button ---
    if template_file and json_file:
        col_validate, col_render = st.columns(2)

        with col_validate:
            if st.button("🔍 Validar Dados", use_container_width=True, key="validate_single"):
                validate_single_document(template_file, json_file)

        with col_render:
            if st.button("▶️ Gerar Documento", use_container_width=True, type="primary", key="render_single"):
                field_types = parse_field_types(field_types_json)
                render_single_document(template_file, json_file, field_types)

    # --- Validation Results Display ---
    if st.session_state.validation_result:
        display_validation_result(st.session_state.validation_result)

    # --- Assembled Documents Display ---
    if st.session_state.assembled_docs:
        st.markdown("---")
        st.subheader("📥 Documentos Gerados")

        for idx, doc_info in enumerate(st.session_state.assembled_docs):
            col_name, col_download = st.columns([3, 1])

            with col_name:
                st.text(f"✅ {doc_info['filename']}")

            with col_download:
                st.download_button(
                    label="Download",
                    data=doc_info['data'],
                    file_name=doc_info['filename'],
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"download_single_{idx}"
                )


def render_batch_processing_tab():
    """Render batch processing UI."""
    st.subheader("Processamento em Lote")
    st.markdown("Processe múltiplos documentos simultaneamente usando um template e vários arquivos JSON.")

    # --- File Uploaders ---
    template_file = st.file_uploader(
        "Template (.docx)",
        type="docx",
        key="batch_template",
        help="Template único para todos os documentos"
    )

    upload_method = st.radio(
        "Método de Upload:",
        options=["Arquivos JSON Individuais", "Arquivo ZIP com JSONs"],
        horizontal=True,
        key="batch_upload_method"
    )

    json_files = []

    if upload_method == "Arquivos JSON Individuais":
        uploaded_jsons = st.file_uploader(
            "Arquivos JSON",
            type="json",
            accept_multiple_files=True,
            key="batch_jsons",
            help="Selecione múltiplos arquivos JSON (Ctrl/Cmd + clique)"
        )
        if uploaded_jsons:
            json_files = uploaded_jsons
    else:
        uploaded_zip = st.file_uploader(
            "Arquivo ZIP",
            type="zip",
            key="batch_zip",
            help="Arquivo ZIP contendo múltiplos arquivos JSON"
        )
        if uploaded_zip:
            json_files = extract_json_from_zip(uploaded_zip)

    # --- Configuration Options ---
    with st.expander("⚙️ Configurações de Lote", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            max_workers = st.slider(
                "Número de Workers",
                min_value=1,
                max_value=8,
                value=4,
                help="Número de processos paralelos para renderização"
            )

        with col2:
            create_zip = st.checkbox(
                "Criar arquivo ZIP de saída",
                value=True,
                help="Agrupa todos os documentos gerados em um único arquivo ZIP"
            )

        name_field = st.text_input(
            "Campo para nome do arquivo",
            value="",
            placeholder="nome",
            help="Nome do campo JSON usado para nomear os arquivos de saída (deixe vazio para numeração sequencial)"
        )

        field_types_json = st.text_area(
            "Mapeamento de Tipos (JSON)",
            value="",
            height=100,
            placeholder='{"nome": "name", "cpf": "cpf", "endereco": "address"}',
            help="JSON com mapeamento de campos para tipos de normalização"
        )

    # --- Action Buttons ---
    if template_file and json_files:
        st.info(f"📊 **{len(json_files)}** arquivos JSON carregados")

        col_validate, col_process = st.columns(2)

        with col_validate:
            if st.button("🔍 Validar Todos", use_container_width=True, key="validate_batch"):
                validate_batch_documents(template_file, json_files)

        with col_process:
            if st.button("▶️ Processar Lote", use_container_width=True, type="primary", key="process_batch"):
                field_types = parse_field_types(field_types_json)
                process_batch_documents(
                    template_file,
                    json_files,
                    max_workers,
                    create_zip,
                    name_field if name_field else None,
                    field_types
                )

    # --- Batch Results Display ---
    if st.session_state.batch_result:
        display_batch_result(st.session_state.batch_result)


# ===== HELPER FUNCTIONS =====

def parse_field_types(field_types_json: str) -> Optional[Dict[str, str]]:
    """Parse field types JSON string into dictionary."""
    if not field_types_json.strip():
        return None

    try:
        field_types = json.loads(field_types_json)
        if not isinstance(field_types, dict):
            st.error("Mapeamento de tipos deve ser um objeto JSON válido")
            return None
        return field_types
    except json.JSONDecodeError as e:
        st.error(f"JSON de mapeamento inválido: {e}")
        return None


def extract_json_from_zip(zip_file) -> List[Any]:
    """Extract all JSON files from uploaded ZIP."""
    json_files = []

    try:
        with zipfile.ZipFile(zip_file, 'r') as zf:
            for filename in zf.namelist():
                if filename.endswith('.json') and not filename.startswith('__MACOSX'):
                    # Create a temporary file-like object for each JSON
                    content = zf.read(filename)
                    # Create a mock uploaded file object
                    json_files.append({
                        'name': Path(filename).name,
                        'content': content
                    })

        st.success(f"Extraídos {len(json_files)} arquivos JSON do ZIP")
    except Exception as e:
        st.error(f"Erro ao extrair ZIP: {e}")

    return json_files


def validate_single_document(template_file, json_file):
    """Validate single document data against template."""
    with st.spinner("Validando dados contra template..."):
        try:
            # Save template temporarily
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_template:
                tmp_template.write(template_file.getvalue())
                template_path = Path(tmp_template.name)

            # Load JSON data
            json_data = json.loads(json_file.getvalue().decode("utf-8"))

            # Validate using engine
            engine = _DocumentEngine()
            validation = engine.validate_data(template_path, json_data)

            # Store result
            st.session_state.validation_result = {
                'type': 'single',
                'validation': validation,
                'template_vars': engine.get_template_variables(template_path)
            }

            # Cleanup
            template_path.unlink()

        except Exception as e:
            st.error(f"Erro durante validação: {e}")
            st.session_state.validation_result = None


def render_single_document(template_file, json_file, field_types: Optional[Dict[str, str]]):
    """Render single document from template and JSON."""
    with st.spinner("Gerando documento..."):
        try:
            # Save template temporarily
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_template:
                tmp_template.write(template_file.getvalue())
                template_path = Path(tmp_template.name)

            # Load JSON data
            json_data = json.loads(json_file.getvalue().decode("utf-8"))

            # Create output path
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_output:
                output_path = Path(tmp_output.name)

            # Render document
            engine = _DocumentEngine(auto_normalize=True)
            result_path = engine.render(
                template_path=template_path,
                data=json_data,
                output_path=output_path,
                field_types=field_types
            )

            # Read generated document
            with open(result_path, 'rb') as f:
                doc_data = f.read()

            # Generate output filename
            output_filename = f"{template_file.name.replace('.docx', '')}_gerado.docx"

            # Store in session state
            st.session_state.assembled_docs.append({
                'filename': output_filename,
                'data': doc_data
            })

            # Cleanup
            template_path.unlink()
            result_path.unlink()

            st.success("✅ Documento gerado com sucesso!")

        except Exception as e:
            st.error(f"Erro ao gerar documento: {e}")


def validate_batch_documents(template_file, json_files):
    """Validate batch of documents."""
    with st.spinner("Validando arquivos em lote..."):
        try:
            # Save template temporarily
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_template:
                tmp_template.write(template_file.getvalue())
                template_path = Path(tmp_template.name)

            # Create temporary directory for JSON files
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_dir_path = Path(tmp_dir)
                json_paths = []

                # Save all JSON files
                for json_file in json_files:
                    if isinstance(json_file, dict):  # From ZIP
                        json_path = tmp_dir_path / json_file['name']
                        json_path.write_bytes(json_file['content'])
                    else:  # Uploaded file
                        json_path = tmp_dir_path / json_file.name
                        json_path.write_bytes(json_file.getvalue())
                    json_paths.append(json_path)

                # Validate
                processor = _BatchProcessor(max_workers=1)
                validation_result = processor.validate_batch(json_paths, template_path)

                # Store result
                st.session_state.validation_result = {
                    'type': 'batch',
                    'validation': validation_result
                }

            # Cleanup
            template_path.unlink()

        except Exception as e:
            st.error(f"Erro durante validação em lote: {e}")
            st.session_state.validation_result = None


def process_batch_documents(
    template_file,
    json_files,
    max_workers: int,
    create_zip: bool,
    name_field: Optional[str],
    field_types: Optional[Dict[str, str]]
):
    """Process batch of documents."""
    with st.spinner(f"Processando {len(json_files)} documentos com {max_workers} workers..."):
        progress_bar = st.progress(0, "Iniciando processamento...")

        try:
            # Save template temporarily
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_template:
                tmp_template.write(template_file.getvalue())
                template_path = Path(tmp_template.name)

            # Create temporary directories
            with tempfile.TemporaryDirectory() as tmp_json_dir, \
                 tempfile.TemporaryDirectory() as tmp_output_dir:

                tmp_json_path = Path(tmp_json_dir)
                tmp_output_path = Path(tmp_output_dir)
                json_paths = []

                # Save all JSON files
                progress_bar.progress(10, "Preparando arquivos...")
                for json_file in json_files:
                    if isinstance(json_file, dict):  # From ZIP
                        json_path = tmp_json_path / json_file['name']
                        json_path.write_bytes(json_file['content'])
                    else:  # Uploaded file
                        json_path = tmp_json_path / json_file.name
                        json_path.write_bytes(json_file.getvalue())
                    json_paths.append(json_path)

                # Process batch
                progress_bar.progress(30, "Processando documentos...")
                processor = _BatchProcessor(max_workers=max_workers, checkpoint_enabled=False)
                result = processor.process_batch(
                    json_files=json_paths,
                    template_path=template_path,
                    output_dir=tmp_output_path,
                    create_zip=create_zip,
                    name_field=name_field,
                    field_types=field_types,
                    resume=False
                )

                progress_bar.progress(80, "Coletando resultados...")

                # Store results
                batch_result = {
                    'summary': result,
                    'outputs': []
                }

                # Read output files
                if create_zip and result.get('zip_path'):
                    zip_path = Path(result['zip_path'])
                    with open(zip_path, 'rb') as f:
                        batch_result['zip_data'] = f.read()
                        batch_result['zip_name'] = zip_path.name
                else:
                    # Read individual files
                    for output_path_str in result['outputs']:
                        output_path = Path(output_path_str)
                        if output_path.exists():
                            with open(output_path, 'rb') as f:
                                batch_result['outputs'].append({
                                    'filename': output_path.name,
                                    'data': f.read()
                                })

                st.session_state.batch_result = batch_result

                progress_bar.progress(100, "Concluído!")

            # Cleanup
            template_path.unlink()

            st.success(f"✅ Processamento concluído: {result['success']} sucessos, {result['failed']} falhas")

        except Exception as e:
            st.error(f"Erro durante processamento em lote: {e}")
            st.session_state.batch_result = None


def display_validation_result(validation_result):
    """Display validation results."""
    st.markdown("---")
    st.subheader("📋 Resultado da Validação")

    if validation_result['type'] == 'single':
        validation = validation_result['validation']
        template_vars = validation_result['template_vars']

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Variáveis no Template", len(template_vars))

        with col2:
            status = "✅ Válido" if not validation['missing'] else "⚠️ Dados Incompletos"
            st.metric("Status", status)

        if validation['missing']:
            st.warning("**Campos Faltando:**")
            st.write(", ".join(validation['missing']))
            st.caption("Estes campos aparecerão como {{ campo }} no documento gerado.")

        if validation['extra']:
            st.info("**Campos Extras (não usados no template):**")
            st.write(", ".join(validation['extra']))

        with st.expander("🔤 Variáveis do Template", expanded=False):
            st.code(", ".join(sorted(template_vars)))

    else:  # batch
        validation = validation_result['validation']

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total de Arquivos", validation['total'])

        with col2:
            st.metric("Válidos", validation['valid_count'], delta_color="normal")

        with col3:
            st.metric("Inválidos", validation['invalid_count'], delta_color="inverse")

        if validation['errors']:
            with st.expander("⚠️ Erros Encontrados", expanded=True):
                for error in validation['errors']:
                    st.error(f"**{error['json_file']}**: {error['message']}")

        if validation['valid']:
            st.success("✅ Todos os arquivos estão válidos e prontos para processamento!")


def display_batch_result(batch_result):
    """Display batch processing results."""
    st.markdown("---")
    st.subheader("📊 Resultado do Processamento")

    summary = batch_result['summary']

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total", summary['total'])

    with col2:
        st.metric("✅ Sucesso", summary['success'])

    with col3:
        st.metric("❌ Falhas", summary['failed'])

    with col4:
        st.metric("⏱️ Duração", summary['duration_formatted'])

    # Errors display
    if summary['errors']:
        with st.expander("⚠️ Erros Detalhados", expanded=False):
            for error in summary['errors']:
                st.error(f"**{error['json_file']}**: {error['message']}")
                if error.get('traceback'):
                    with st.expander("Stack Trace"):
                        st.code(error['traceback'], language="python")

    # Download section
    st.markdown("### 📥 Downloads")

    if batch_result.get('zip_data'):
        # Single ZIP download
        st.download_button(
            label=f"⬇️ Download ZIP ({summary['success']} documentos)",
            data=batch_result['zip_data'],
            file_name=batch_result['zip_name'],
            mime="application/zip",
            use_container_width=True,
            type="primary"
        )
    else:
        # Individual file downloads
        for idx, output_info in enumerate(batch_result['outputs']):
            st.download_button(
                label=f"⬇️ {output_info['filename']}",
                data=output_info['data'],
                file_name=output_info['filename'],
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"download_batch_{idx}"
            )

    # Summary JSON
    with st.expander("📄 Relatório JSON", expanded=False):
        # Remove binary data before displaying
        display_summary = {k: v for k, v in summary.items() if k not in ['outputs']}
        display_summary['output_count'] = len(summary['outputs'])
        st.json(display_summary)
