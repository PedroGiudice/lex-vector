"""
analyzer.py - Analisador de documentos jurídicos

Orquestra análise completa:
1. Recebe documento (TXT, MD ou JSON)
2. Identifica citações legais
3. Extrai artigos do corpus
4. Retorna análise estruturada
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from citation_parser import CitationParser, LegalCitation
from corpus_indexer import CorpusIndexer
from article_extractor import ArticleExtractor, ExtractedArticle


@dataclass
class AnalysisResult:
    """Resultado da análise de documento."""
    document_path: str
    document_type: str  # txt, md, json
    total_citations: int
    total_found: int
    total_not_found: int
    citations: List[Dict]
    articles: List[Dict]
    summary: Dict

    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Converte para JSON."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_markdown(self) -> str:
        """Converte para Markdown."""
        lines = []

        # Cabeçalho
        lines.append(f"# Análise Legal: {Path(self.document_path).name}")
        lines.append("")
        lines.append(f"**Documento:** `{self.document_path}`")
        lines.append(f"**Tipo:** {self.document_type.upper()}")
        lines.append("")

        # Sumário
        lines.append("## 📊 Sumário")
        lines.append("")
        lines.append(f"- **Citações encontradas:** {self.total_citations}")
        lines.append(f"- **Artigos localizados:** {self.total_found} ({self._percent(self.total_found, self.total_citations)}%)")
        lines.append(f"- **Não localizados:** {self.total_not_found}")
        lines.append("")

        # Leis citadas
        if self.summary['laws_cited']:
            lines.append("### Leis Citadas")
            lines.append("")
            for law, count in self.summary['laws_cited'].items():
                lines.append(f"- **{law}**: {count} artigo(s)")
            lines.append("")

        # Artigos extraídos
        if self.articles:
            lines.append("## 📖 Artigos Extraídos")
            lines.append("")

            for i, article_dict in enumerate(self.articles, 1):
                if not article_dict['found']:
                    continue

                lines.append(f"### {i}. {article_dict['law_name']} - Artigo {article_dict['article_number']}")
                lines.append("")
                lines.append(f"**Citação original:** `{article_dict['citation_raw']}`")
                lines.append("")

                if article_dict['caput']:
                    lines.append(f"**Caput:**")
                    lines.append(article_dict['caput'])
                    lines.append("")

                if article_dict['paragraphs']:
                    lines.append(f"**Parágrafos:**")
                    for j, para in enumerate(article_dict['paragraphs'], 1):
                        lines.append(f"§{j}º {para}")
                        lines.append("")

                lines.append("---")
                lines.append("")

        # Artigos não encontrados
        not_found = [a for a in self.articles if not a['found']]
        if not_found:
            lines.append("## ⚠️ Artigos Não Localizados")
            lines.append("")
            for article_dict in not_found:
                lines.append(f"- `{article_dict['citation_raw']}` - {article_dict['content']}")
            lines.append("")

        return "\n".join(lines)

    def _percent(self, part: int, total: int) -> int:
        """Calcula percentual."""
        return int((part / total * 100)) if total > 0 else 0


class DocumentAnalyzer:
    """Analisador de documentos jurídicos."""

    def __init__(self, corpus_db: Path):
        """
        Inicializa analisador.

        Args:
            corpus_db: Caminho do banco SQLite com corpus
        """
        self.indexer = CorpusIndexer(corpus_db)
        self.parser = CitationParser()
        self.extractor = ArticleExtractor(self.indexer)

    def analyze(
        self,
        document_path: Path,
        deduplicate: bool = True,
        output_format: str = "json"
    ) -> AnalysisResult:
        """
        Analisa documento jurídico.

        Args:
            document_path: Caminho do documento
            deduplicate: Se deve remover citações duplicadas
            output_format: Formato de saída (json, markdown)

        Returns:
            Resultado da análise
        """
        document_path = Path(document_path)

        if not document_path.exists():
            raise FileNotFoundError(f"Documento não encontrado: {document_path}")

        # Detectar tipo do documento
        doc_type = document_path.suffix.lstrip('.').lower()
        if doc_type not in ['txt', 'md', 'json']:
            doc_type = 'txt'  # Default

        # Ler documento
        text = self._read_document(document_path, doc_type)

        # Parsear citações
        citations = self.parser.parse(text)

        # Deduplicar se solicitado
        if deduplicate:
            citations = self.parser.deduplicate(citations)

        # Extrair artigos
        articles = self.extractor.extract_multiple(citations)

        # Calcular estatísticas
        total_citations = len(citations)
        total_found = sum(1 for a in articles if a.found)
        total_not_found = total_citations - total_found

        # Sumário
        laws_cited = {}
        for article in articles:
            if article.found:
                law_key = f"{article.law_code} - {article.law_name}"
                laws_cited[law_key] = laws_cited.get(law_key, 0) + 1

        summary = {
            'laws_cited': laws_cited,
            'total_citations': total_citations,
            'found': total_found,
            'not_found': total_not_found
        }

        # Criar resultado
        result = AnalysisResult(
            document_path=str(document_path),
            document_type=doc_type,
            total_citations=total_citations,
            total_found=total_found,
            total_not_found=total_not_found,
            citations=[c.to_dict() for c in citations],
            articles=[a.to_dict() for a in articles],
            summary=summary
        )

        return result

    def _read_document(self, path: Path, doc_type: str) -> str:
        """Lê documento baseado no tipo."""
        with open(path, 'r', encoding='utf-8') as f:
            if doc_type == 'json':
                data = json.load(f)
                # Se JSON, tentar extrair campo "text" ou "content"
                if isinstance(data, dict):
                    return data.get('text', data.get('content', json.dumps(data)))
                return json.dumps(data)
            else:
                # TXT ou MD
                return f.read()


# ============================================================================
# CLI DE TESTE
# ============================================================================

if __name__ == "__main__":
    import sys

    corpus_db = Path(__file__).parent.parent / "corpus" / "index.db"
    analyzer = DocumentAnalyzer(corpus_db)

    print("⚖️  Analisador de Documentos Jurídicos\n")

    if len(sys.argv) < 2:
        print("Uso: python analyzer.py <documento.txt> [--format json|markdown]\n")
        print("Exemplo:")
        print("  python analyzer.py documento.txt --format markdown > analise.md")
        sys.exit(0)

    doc_path = Path(sys.argv[1])
    output_format = "json"

    if "--format" in sys.argv:
        idx = sys.argv.index("--format")
        if idx + 1 < len(sys.argv):
            output_format = sys.argv[idx + 1].lower()

    print(f"📄 Analisando: {doc_path}")
    print(f"📋 Formato: {output_format}\n")

    try:
        result = analyzer.analyze(doc_path, deduplicate=True, output_format=output_format)

        # Exibir resultado
        if output_format == "markdown":
            print(result.to_markdown())
        else:
            print(result.to_json())

    except FileNotFoundError as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
