"""
Testes para JurisprudenceExtractor
"""
import pytest
from src.jurisprudence_extractor import JurisprudenceExtractor


@pytest.fixture
def config():
    """Config básica para testes"""
    return {
        'extraction': {
            'temas_interesse': [
                'direito civil',
                'direito penal',
                'responsabilidade civil'
            ],
            'min_confidence': 0.6,
            'extract_fields': [
                'numero_processo',
                'tribunal',
                'vara',
                'data_publicacao',
                'tipo_decisao',
                'tema',
                'ementa',
                'dispositivo',
                'partes'
            ]
        },
        'paths': {
            'data_root': '/tmp/legal-lens-test'
        }
    }


class MockRAGEngine:
    """Mock do RAGEngine para testes"""

    def search(self, query, top_k=5, filter_metadata=None):
        return []

    def search_by_theme(self, theme, top_k=20):
        return []


@pytest.fixture
def extractor(config):
    """Instância do JurisprudenceExtractor"""
    rag_engine = MockRAGEngine()
    return JurisprudenceExtractor(config, rag_engine)


def test_extractor_initialization(extractor):
    """Testa inicialização do extractor"""
    assert len(extractor.temas_interesse) == 3
    assert extractor.min_confidence == 0.6


def test_extract_numero_processo(extractor):
    """Testa extração de número de processo"""
    texto1 = "Processo: 1234567-89.2024.1.00.0001"
    assert extractor.extract_numero_processo(texto1) == "1234567-89.2024.1.00.0001"

    texto2 = "Proc. n° 1234567-89.2024.1.00.0001"
    assert extractor.extract_numero_processo(texto2) == "1234567-89.2024.1.00.0001"

    texto3 = "Sem número de processo"
    assert extractor.extract_numero_processo(texto3) is None


def test_extract_tipo_decisao(extractor):
    """Testa extração de tipo de decisão"""
    assert extractor.extract_tipo_decisao("A sentença foi proferida") == "sentença"
    assert extractor.extract_tipo_decisao("Acórdão do tribunal") == "Acórdão"
    assert extractor.extract_tipo_decisao("Despacho do juiz") == "Despacho"
    assert extractor.extract_tipo_decisao("Sem decisão") is None


def test_extract_vara(extractor):
    """Testa extração de vara"""
    assert extractor.extract_vara("3ª Vara Cível") is not None
    assert extractor.extract_vara("1a vara criminal") is not None
    assert extractor.extract_vara("Sem vara") is None


def test_extract_partes(extractor):
    """Testa extração de partes"""
    texto = """
    Autor: João da Silva
    Réu: Maria Santos
    Requerente: Pedro Oliveira
    """

    partes = extractor.extract_partes(texto)

    assert len(partes) > 0
    assert any("João da Silva" in parte or "Silva" in parte for parte in partes)


def test_extract_ementa(extractor):
    """Testa extração de ementa"""
    texto = """
    EMENTA: Responsabilidade civil. Acidente de trânsito. Danos materiais e morais.
    A responsabilidade do condutor resta caracterizada quando demonstrada a culpa.

    DISPOSITIVO: Julgo procedente o pedido.
    """

    ementa = extractor.extract_ementa(texto)

    assert ementa is not None
    assert "Responsabilidade civil" in ementa or "responsabilidade" in ementa.lower()


def test_extract_dispositivo(extractor):
    """Testa extração de dispositivo"""
    texto = """
    ISTO POSTO, julgo procedente o pedido para condenar o réu
    ao pagamento de indenização por danos morais.
    """

    dispositivo = extractor.extract_dispositivo(texto)

    assert dispositivo is not None
    assert "julgo" in dispositivo.lower() or "procedente" in dispositivo.lower()
