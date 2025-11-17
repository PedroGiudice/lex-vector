"""
Fixtures compartilhadas para a suite de testes do djen-tracker.

Este módulo centraliza fixtures comuns utilizadas em múltiplos arquivos de teste,
incluindo diretórios temporários, PDFs de teste, mocks de respostas de API, etc.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from io import BytesIO

# Importar módulos src
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def temp_dir():
    """
    Diretório temporário para testes.
    Removido automaticamente após o teste.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def cache_dir(temp_dir):
    """
    Diretório de cache para testes.
    """
    cache_path = temp_dir / "cache"
    cache_path.mkdir(parents=True, exist_ok=True)
    return cache_path


@pytest.fixture
def downloads_dir(temp_dir):
    """
    Diretório de downloads para testes.
    """
    downloads_path = temp_dir / "downloads"
    downloads_path.mkdir(parents=True, exist_ok=True)
    return downloads_path


@pytest.fixture
def sample_pdf_path(temp_dir):
    """
    Cria um PDF de teste válido (mínimo).

    Returns:
        Path para PDF de teste
    """
    pdf_path = temp_dir / "test_document.pdf"

    # Criar PDF mínimo válido (header correto)
    # Este é um PDF de 1 página vazio válido
    minimal_pdf = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 4 0 R
>>
>>
/MediaBox [0 0 612 792]
/Contents 5 0 R
>>
endobj
4 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
5 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000262 00000 n
0000000341 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
433
%%EOF
"""

    with open(pdf_path, 'wb') as f:
        f.write(minimal_pdf)

    return pdf_path


@pytest.fixture
def sample_pdf_with_oab(temp_dir):
    """
    Cria um PDF de teste com texto contendo OABs.

    NOTA: Para testes reais, usa PyPDF2 para criar PDF com texto extraível.
    """
    try:
        from PyPDF2 import PdfWriter
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        pdf_path = temp_dir / "oab_document.pdf"

        # Criar PDF com reportlab
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)

        # Adicionar texto com OABs
        c.drawString(100, 750, "TRIBUNAL DE JUSTIÇA DE SÃO PAULO")
        c.drawString(100, 730, "Processo nº 1234567-89.2025.8.26.0100")
        c.drawString(100, 710, "")
        c.drawString(100, 690, "Advogado: Dr. João da Silva - OAB/SP nº 123.456")
        c.drawString(100, 670, "Advogada: Dra. Maria Santos (OAB 789012/SP)")
        c.drawString(100, 650, "Procurador: José Oliveira - OAB 345678 - RJ")
        c.drawString(100, 630, "")
        c.drawString(100, 610, "Intimação para advogado OAB/MG 567890")

        c.save()

        # Salvar em arquivo
        buffer.seek(0)
        with open(pdf_path, 'wb') as f:
            f.write(buffer.read())

        return pdf_path

    except ImportError:
        # Se reportlab não disponível, usar PDF mínimo
        return sample_pdf_path(temp_dir)


@pytest.fixture
def corrupted_pdf_path(temp_dir):
    """
    Cria um PDF corrompido (header inválido) para testes de validação.
    """
    pdf_path = temp_dir / "corrupted.pdf"

    with open(pdf_path, 'wb') as f:
        f.write(b"Not a valid PDF\nJust random bytes\n")

    return pdf_path


@pytest.fixture
def mock_api_response():
    """
    Mock de resposta da API DJEN.

    Returns:
        Dict simulando resposta de API
    """
    return {
        "tribunal": "STF",
        "data": "2025-11-17",
        "caderno": "Administrativo",
        "url": "https://comunica.pje.jus.br/stf/2025/11/17/admin.pdf",
        "disponibilidade": "2025-11-17T08:00:00",
        "tamanho_bytes": 1024000,
        "hash": "abc123def456"
    }


@pytest.fixture
def sample_text_with_oabs():
    """
    Texto de exemplo contendo múltiplas variações de formato OAB.

    Returns:
        String com texto contendo OABs em diversos formatos
    """
    return """
    PODER JUDICIÁRIO
    TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO

    Processo nº 1234567-89.2025.8.26.0100

    Advogado(a): Dr. João da Silva - OAB/SP nº 123.456
    Advogada: Dra. Maria Santos (OAB 789012/SP)
    Procurador: José Oliveira - OAB 345678 - RJ
    Defensor Público: Pedro Costa (OAB/MG 567890)

    Intimação de Advogado:
    Fica intimado o Dr. Carlos Ferreira, OAB/DF 234567, para comparecer...

    Patrono da parte autora: Ana Paula (OAB 456789-BA)

    Registro OAB nº 111222 (CE)
    Inscrição OAB/PR sob o nº 333.444

    Advogado subscrito: Marcos Pereira - OAB-GO: 555666

    FALSOS POSITIVOS (não devem ser detectados):
    Processo nº 123456/2024
    CPF: 123.456.789-01
    Telefone: (11) 98765-4321
    CNPJ: 12.345.678/0001-90
    """


@pytest.fixture
def sample_oab_list():
    """
    Lista de OABs de exemplo para testes de filtro.

    Returns:
        Lista de tuplas (numero, uf)
    """
    return [
        ('123456', 'SP'),
        ('789012', 'SP'),
        ('345678', 'RJ'),
        ('567890', 'MG'),
        ('234567', 'DF'),
        ('456789', 'BA'),
    ]


@pytest.fixture
def mock_extraction_result():
    """
    Mock de ExtractionResult para testes de cache e filtro.
    """
    from src.pdf_text_extractor import ExtractionResult, ExtractionStrategy

    return ExtractionResult(
        text="Texto extraído de exemplo com OAB/SP 123456",
        strategy=ExtractionStrategy.PDFPLUMBER,
        page_count=10,
        char_count=500,
        success=True,
        error_message=None,
        metadata={'test': True}
    )


@pytest.fixture
def mock_cache_entry():
    """
    Mock de CacheEntry para testes de cache.
    """
    from src.cache_manager import CacheEntry

    return CacheEntry(
        pdf_path="/tmp/test.pdf",
        pdf_hash="abc123def456",
        text="Texto cacheado",
        extraction_strategy="pdfplumber",
        cached_at=datetime.now().isoformat(),
        file_size_bytes=1024000,
        page_count=10,
        char_count=500,
        metadata={'cached': True}
    )


@pytest.fixture
def mock_oab_match():
    """
    Mock de OABMatch para testes de matcher.
    """
    from src.oab_matcher import OABMatch

    return OABMatch(
        numero="123456",
        uf="SP",
        texto_contexto="Advogado: Dr. João Silva - OAB/SP 123.456",
        posicao_inicio=100,
        posicao_fim=150,
        score_contexto=0.85,
        padrao_usado="oab_slash_uf_numero",
        texto_original="OAB/SP 123.456"
    )


@pytest.fixture(autouse=True)
def reset_environment_vars(monkeypatch):
    """
    Reseta variáveis de ambiente entre testes para evitar interferência.
    """
    # Remove CLAUDE_DATA_ROOT se existir
    monkeypatch.delenv('CLAUDE_DATA_ROOT', raising=False)

    yield


@pytest.fixture
def mock_tribunal_config():
    """
    Mock de configuração de tribunais para testes.
    """
    return {
        "tribunais_prioritarios": ["STF", "STJ", "TJSP", "TJRJ"],
        "cadernos": ["Administrativo", "Judicial"],
        "max_downloads_por_dia": 100
    }


@pytest.fixture
def sample_date_range():
    """
    Range de datas para testes (últimos 7 dias).
    """
    hoje = datetime.now()
    return [
        (hoje - timedelta(days=i)).strftime('%Y-%m-%d')
        for i in range(7)
    ]


# Markers personalizados
def pytest_configure(config):
    """
    Registra markers personalizados.
    """
    config.addinivalue_line(
        "markers", "slow: marca testes lentos (OCR, download, etc)"
    )
    config.addinivalue_line(
        "markers", "integration: marca testes de integração end-to-end"
    )
    config.addinivalue_line(
        "markers", "requires_network: marca testes que precisam de rede"
    )
    config.addinivalue_line(
        "markers", "requires_tesseract: marca testes que precisam tesseract instalado"
    )
