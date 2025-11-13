"""
citation_parser.py - Parser de citações legais brasileiras

Identifica e extrai citações de artigos de lei em textos jurídicos.

Padrões suportados:
- Art. 5º
- artigo 121
- Lei 8.069/90, art. 3º
- CF/88, art. 5º, inciso X
- CC, art. 186
- CPC/2015, art. 319, §1º
"""
import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class LegalCitation:
    """Representa uma citação legal encontrada."""
    raw_text: str              # Texto original da citação
    law_code: Optional[str]    # Código da lei (CF, CC, CPC, etc)
    law_number: Optional[str]  # Número da lei (8.069, 10.406, etc)
    law_year: Optional[str]    # Ano da lei (1990, 2002, etc)
    article: str               # Número do artigo
    paragraph: Optional[str]   # Parágrafo (§1º, §2º)
    inciso: Optional[str]      # Inciso (I, II, III, etc)
    alinea: Optional[str]      # Alínea (a, b, c, etc)
    start_pos: int             # Posição inicial no texto
    end_pos: int               # Posição final no texto

    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return {
            'raw_text': self.raw_text,
            'law_code': self.law_code,
            'law_number': self.law_number,
            'law_year': self.law_year,
            'article': self.article,
            'paragraph': self.paragraph,
            'inciso': self.inciso,
            'alinea': self.alinea,
            'position': (self.start_pos, self.end_pos)
        }

    def __str__(self) -> str:
        """Representação legível."""
        parts = []
        if self.law_code:
            parts.append(self.law_code)
        elif self.law_number:
            parts.append(f"Lei {self.law_number}")
            if self.law_year:
                parts[-1] += f"/{self.law_year}"

        parts.append(f"art. {self.article}")

        if self.paragraph:
            parts.append(f"§{self.paragraph}")
        if self.inciso:
            parts.append(f"inciso {self.inciso}")
        if self.alinea:
            parts.append(f"alínea {self.alinea}")

        return ", ".join(parts)


class CitationParser:
    """Parser de citações legais."""

    # Mapeamento de códigos comuns
    LAW_CODES = {
        'CF': 'Constituição Federal',
        'CC': 'Código Civil',
        'CPC': 'Código de Processo Civil',
        'CPP': 'Código de Processo Penal',
        'CP': 'Código Penal',
        'CLT': 'Consolidação das Leis do Trabalho',
        'CDC': 'Código de Defesa do Consumidor',
        'ECA': 'Estatuto da Criança e do Adolescente',
        'CTN': 'Código Tributário Nacional',
    }

    # Padrões regex (ordenados por especificidade)
    PATTERNS = [
        # Padrão completo: Lei 8.069/90, art. 3º, §1º, inciso II, alínea a
        r'(?:Lei\s+(?P<lei_num>[\d.]+)(?:/(?P<lei_ano>\d{2,4}))?[,\s]+)?'
        r'(?:(?P<codigo>[A-Z]{2,4})(?:/(?P<cod_ano>\d{2,4}))?[,\s]+)?'
        r'(?:art(?:igo)?\.?\s+(?P<artigo>\d+[º°]?(?:-[A-Z])?)'
        r'(?:[,\s]+§\s*(?P<paragrafo>\d+[º°]?))?'
        r'(?:[,\s]+inc(?:iso)?\.?\s+(?P<inciso>[IVXLCDM]+|[a-z]))?'
        r'(?:[,\s]+al(?:ínea)?\.?\s+(?P<alinea>[a-z]))?)',

        # Padrão simplificado: Art. 5º
        r'(?:art(?:igo)?\.?\s+(?P<artigo>\d+[º°]?(?:-[A-Z])?)'
        r'(?:[,\s]+§\s*(?P<paragrafo>\d+[º°]?))?'
        r'(?:[,\s]+inc(?:iso)?\.?\s+(?P<inciso>[IVXLCDM]+))?'
        r'(?:[,\s]+al(?:ínea)?\.?\s+(?P<alinea>[a-z]))?)',
    ]

    def __init__(self):
        """Inicializa parser."""
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.PATTERNS
        ]

    def parse(self, text: str) -> List[LegalCitation]:
        """
        Extrai todas as citações legais do texto.

        Args:
            text: Texto para analisar

        Returns:
            Lista de citações encontradas
        """
        citations = []
        seen_positions = set()  # Evitar duplicatas

        for pattern in self.compiled_patterns:
            for match in pattern.finditer(text):
                start, end = match.span()

                # Evitar duplicatas (mesmo range de posição)
                if (start, end) in seen_positions:
                    continue
                seen_positions.add((start, end))

                groups = match.groupdict()

                # Extrair componentes
                citation = LegalCitation(
                    raw_text=match.group(0),
                    law_code=groups.get('codigo'),
                    law_number=groups.get('lei_num'),
                    law_year=groups.get('lei_ano') or groups.get('cod_ano'),
                    article=self._clean_article(groups.get('artigo', '')),
                    paragraph=self._clean_number(groups.get('paragrafo')),
                    inciso=groups.get('inciso'),
                    alinea=groups.get('alinea'),
                    start_pos=start,
                    end_pos=end
                )

                citations.append(citation)

        # Ordenar por posição no texto
        citations.sort(key=lambda c: c.start_pos)

        return citations

    def _clean_article(self, article: str) -> str:
        """Remove símbolos de grau do número do artigo."""
        if not article:
            return ''
        return article.replace('º', '').replace('°', '').strip()

    def _clean_number(self, num: Optional[str]) -> Optional[str]:
        """Remove símbolos de grau de números (parágrafos)."""
        if not num:
            return None
        return num.replace('º', '').replace('°', '').strip()

    def get_law_name(self, code: Optional[str]) -> Optional[str]:
        """Retorna nome completo da lei a partir do código."""
        if not code:
            return None
        return self.LAW_CODES.get(code.upper())

    def deduplicate(self, citations: List[LegalCitation]) -> List[LegalCitation]:
        """
        Remove citações duplicadas (mesmo artigo/lei).

        Mantém apenas a primeira ocorrência.
        """
        seen = set()
        unique = []

        for citation in citations:
            key = (
                citation.law_code,
                citation.law_number,
                citation.article,
                citation.paragraph,
                citation.inciso,
                citation.alinea
            )

            if key not in seen:
                seen.add(key)
                unique.append(citation)

        return unique


# ============================================================================
# TESTES
# ============================================================================

if __name__ == "__main__":
    parser = CitationParser()

    # Texto de teste
    test_text = """
    Com base no art. 5º da CF/88, especialmente o inciso X, e no
    artigo 186 do CC, combinado com o art. 927 do Código Civil,
    constata-se a responsabilidade civil. Ainda, a Lei 8.069/90,
    art. 3º, §1º, inciso II, alínea a, estabelece proteção integral.
    O CPC/2015, art. 319, determina os requisitos da petição inicial.
    """

    print("🔍 Analisando texto...\n")

    citations = parser.parse(test_text)

    print(f"📋 {len(citations)} citações encontradas:\n")

    for i, citation in enumerate(citations, 1):
        print(f"{i}. {citation}")
        print(f"   Raw: '{citation.raw_text}'")
        if citation.law_code:
            law_name = parser.get_law_name(citation.law_code)
            print(f"   Lei: {law_name}")
        print()

    # Testar deduplicação
    print("\n🔄 Testando deduplicação...")
    test_dup = "Art. 5º da CF e novamente o art. 5º da CF/88"
    citations_dup = parser.parse(test_dup)
    print(f"   Antes: {len(citations_dup)} citações")

    unique = parser.deduplicate(citations_dup)
    print(f"   Depois: {len(unique)} citações únicas")
