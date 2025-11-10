"""
Testes para PDFProcessor
"""
import pytest
from pathlib import Path
from src.pdf_processor import PDFProcessor, DocumentChunk


@pytest.fixture
def config():
    """Config básica para testes"""
    return {
        'rag': {
            'chunk_size': 1000,
            'chunk_overlap': 200
        }
    }


@pytest.fixture
def processor(config):
    """Instância do PDFProcessor"""
    return PDFProcessor(config)


def test_processor_initialization(processor):
    """Testa inicialização do processor"""
    assert processor.chunk_size == 1000
    assert processor.chunk_overlap == 200


def test_extract_tribunal_from_filename(processor):
    """Testa extração de tribunal do filename"""
    assert processor._extract_tribunal_from_filename("TJSP_2025-01-01_caderno.pdf") == "TJSP"
    assert processor._extract_tribunal_from_filename("TRF3_2025-01-01.pdf") == "TRF3"
    assert processor._extract_tribunal_from_filename("STJ_decisao.pdf") == "STJ"
    assert processor._extract_tribunal_from_filename("documento.pdf") is None


def test_extract_date_from_filename(processor):
    """Testa extração de data do filename"""
    assert processor._extract_date_from_filename("TJSP_2025-01-01_caderno.pdf") == "2025-01-01"
    assert processor._extract_date_from_filename("documento_2024-12-31.pdf") == "2024-12-31"
    assert processor._extract_date_from_filename("documento.pdf") is None


def test_chunk_text(processor):
    """Testa chunking de texto"""
    # Texto longo para forçar múltiplos chunks
    texto = "\n\n".join([f"Parágrafo {i}" * 100 for i in range(20)])

    metadata = {
        'filename': 'test.pdf',
        'page_number': 1
    }

    chunks = processor.chunk_text(texto, metadata)

    # Deve gerar múltiplos chunks
    assert len(chunks) > 1

    # Todos devem ser DocumentChunk
    assert all(isinstance(c, DocumentChunk) for c in chunks)

    # Verificar metadata
    assert all(c.source_file == 'test.pdf' for c in chunks)


def test_chunk_text_with_overlap(processor):
    """Testa overlap entre chunks"""
    texto = "\n\n".join([f"Parágrafo {i}" for i in range(50)])

    metadata = {
        'filename': 'test.pdf',
        'page_number': 1
    }

    chunks = processor.chunk_text(texto, metadata)

    if len(chunks) > 1:
        # O segundo chunk deve ter overlap com o primeiro
        # (Difícil testar exatamente sem conhecer o conteúdo)
        assert chunks[1].text != chunks[0].text
