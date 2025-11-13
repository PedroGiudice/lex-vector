"""
article_extractor.py - Extrator de artigos completos

Extrai artigos de leis com toda sua estrutura:
- Caput
- Parágrafos
- Incisos
- Alíneas
- Contexto (artigos adjacentes opcionalmente)
"""
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
import json

from citation_parser import LegalCitation
from corpus_indexer import CorpusIndexer, Article


@dataclass
class ExtractedArticle:
    """Artigo extraído com metadata completa."""
    law_code: str
    law_name: str
    article_number: str
    citation_raw: str        # Citação original encontrada
    content: str             # Texto completo
    caput: str               # Caput
    paragraphs: List[str]    # Parágrafos
    requested_paragraph: Optional[str] = None  # Se foi pedido § específico
    requested_inciso: Optional[str] = None     # Se foi pedido inciso específico
    found: bool = True       # Se foi encontrado no corpus

    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return asdict(self)

    def to_markdown(self) -> str:
        """Formata em Markdown."""
        lines = []
        lines.append(f"## {self.law_name} - Artigo {self.article_number}")
        lines.append("")

        if self.caput:
            lines.append(f"**Caput:**")
            lines.append(self.caput)
            lines.append("")

        if self.paragraphs:
            lines.append(f"**Parágrafos:**")
            for i, para in enumerate(self.paragraphs, 1):
                lines.append(f"§{i}º {para}")
                lines.append("")

        return "\n".join(lines)


class ArticleExtractor:
    """Extrator de artigos de leis."""

    def __init__(self, indexer: CorpusIndexer):
        """
        Inicializa extrator.

        Args:
            indexer: Indexador de corpus já inicializado
        """
        self.indexer = indexer

    def extract(self, citation: LegalCitation) -> ExtractedArticle:
        """
        Extrai artigo completo baseado em citação.

        Args:
            citation: Citação legal parseada

        Returns:
            Artigo extraído
        """
        # Resolver código da lei
        law_code = self._resolve_law_code(citation)

        if not law_code:
            return self._not_found_article(citation, "Código de lei não identificado")

        # Buscar artigo no corpus
        article = self.indexer.find_article(law_code, citation.article)

        if not article:
            return self._not_found_article(citation, f"Artigo não encontrado no corpus ({law_code})")

        # Obter nome da lei
        law_name = self._get_law_name(law_code)

        # Extrair parte específica se solicitada
        content = article.content
        requested_paragraph = citation.paragraph
        requested_inciso = citation.inciso

        # TODO: Implementar extração de § e inciso específicos
        # Por ora, retorna artigo completo

        return ExtractedArticle(
            law_code=law_code,
            law_name=law_name,
            article_number=article.number,
            citation_raw=citation.raw_text,
            content=content,
            caput=article.caput,
            paragraphs=article.paragraphs,
            requested_paragraph=requested_paragraph,
            requested_inciso=requested_inciso,
            found=True
        )

    def extract_multiple(self, citations: List[LegalCitation]) -> List[ExtractedArticle]:
        """
        Extrai múltiplos artigos.

        Args:
            citations: Lista de citações

        Returns:
            Lista de artigos extraídos
        """
        return [self.extract(citation) for citation in citations]

    def _resolve_law_code(self, citation: LegalCitation) -> Optional[str]:
        """
        Resolve código da lei a partir da citação.

        Prioridade:
        1. citation.law_code (ex: CF, CC)
        2. citation.law_number (ex: 8.069 → ECA)
        3. Heurísticas (faixas de artigos)

        Returns:
            Código da lei ou None
        """
        # Se código explícito, usar direto
        if citation.law_code:
            return citation.law_code.upper()

        # Se número da lei, mapear
        if citation.law_number:
            law_mapping = {
                '8.069': 'ECA',      # Lei 8.069/90
                '8078': 'CDC',       # Lei 8.078/90
                '10.406': 'CC',      # Lei 10.406/2002
                '13.105': 'CPC',     # Lei 13.105/2015
                '5.172': 'CTN',      # Lei 5.172/66
            }
            return law_mapping.get(citation.law_number.replace('.', ''))

        # Heurísticas baseadas em faixas de artigos
        # (simplificado - em produção seria mais robusto)
        article_num = int(citation.article) if citation.article.isdigit() else 0

        if 1 <= article_num <= 250:
            return 'CF'  # Provavelmente Constituição Federal
        elif 1 <= article_num <= 2046:
            return 'CC'  # Provavelmente Código Civil

        return None  # Não foi possível resolver

    def _get_law_name(self, law_code: str) -> str:
        """Retorna nome completo da lei."""
        law_names = {
            'CF': 'Constituição Federal de 1988',
            'CC': 'Código Civil (Lei 10.406/2002)',
            'CPC': 'Código de Processo Civil (Lei 13.105/2015)',
            'CPP': 'Código de Processo Penal (Decreto-Lei 3.689/1941)',
            'CP': 'Código Penal (Decreto-Lei 2.848/1940)',
            'CLT': 'Consolidação das Leis do Trabalho (Decreto-Lei 5.452/1943)',
            'CDC': 'Código de Defesa do Consumidor (Lei 8.078/1990)',
            'ECA': 'Estatuto da Criança e do Adolescente (Lei 8.069/1990)',
            'CTN': 'Código Tributário Nacional (Lei 5.172/1966)',
        }
        return law_names.get(law_code.upper(), f"Lei {law_code}")

    def _not_found_article(self, citation: LegalCitation, reason: str) -> ExtractedArticle:
        """Cria artigo "não encontrado"."""
        return ExtractedArticle(
            law_code=citation.law_code or "DESCONHECIDO",
            law_name="Lei não identificada",
            article_number=citation.article,
            citation_raw=citation.raw_text,
            content=f"[ARTIGO NÃO ENCONTRADO: {reason}]",
            caput="",
            paragraphs=[],
            found=False
        )


# ============================================================================
# TESTES
# ============================================================================

if __name__ == "__main__":
    from pathlib import Path
    from citation_parser import CitationParser

    # Inicializar
    db_path = Path(__file__).parent.parent / "corpus" / "index.db"
    indexer = CorpusIndexer(db_path)
    extractor = ArticleExtractor(indexer)
    parser = CitationParser()

    # Texto de teste
    test_text = """
    Conforme o art. 5º da CF/88, todos são iguais perante a lei.
    O artigo 186 do CC estabelece responsabilidade civil.
    """

    print("🔍 Analisando documento...\n")

    # Parsear citações
    citations = parser.parse(test_text)
    print(f"📋 {len(citations)} citações encontradas")

    # Extrair artigos
    print(f"\n📖 Extraindo artigos do corpus...\n")

    for citation in citations:
        article = extractor.extract(citation)

        if article.found:
            print(f"✅ {article.law_code} Art. {article.article_number}")
            print(f"   {article.law_name}")
            print(f"   Caput: {article.caput[:100]}...")
        else:
            print(f"❌ {citation.raw_text}")
            print(f"   {article.content}")

        print()

    # Exportar em JSON
    articles = extractor.extract_multiple(citations)
    output = {
        'total_citations': len(citations),
        'total_found': sum(1 for a in articles if a.found),
        'articles': [a.to_dict() for a in articles]
    }

    print("\n📄 JSON Export:")
    print(json.dumps(output, indent=2, ensure_ascii=False))
