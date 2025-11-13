"""
Normalização de texto pós-limpeza.

Remove espaços excessivos, linhas vazias, e outros artifacts
que permanecem após a remoção de padrões de assinatura.
"""

import re


class TextNormalizer:
    """
    Normaliza texto após limpeza de padrões.

    Operações:
    - Remove múltiplos espaços em branco
    - Remove espaços no início/fim de linhas
    - Limita linhas vazias consecutivas (máx 2)
    - Remove linhas com apenas pontuação/símbolos isolados
    - Remove espaços antes de pontuação
    """

    def normalize(self, text: str) -> str:
        """
        Normaliza texto aplicando todas as regras.

        Args:
            text: Texto a ser normalizado

        Returns:
            Texto normalizado

        Example:
            >>> normalizer = TextNormalizer()
            >>> normalizer.normalize("Texto     com    espaços\\n\\n\\n\\nexcessivos")
            'Texto com espaços\\n\\nescessivos'
        """
        if not text:
            return text

        # 1. Remove múltiplos espaços em branco (mas não quebras de linha)
        text = re.sub(r'[ \t]+', ' ', text)

        # 2. Remove espaços no início/fim de cada linha
        text = re.sub(r'^[ \t]+|[ \t]+$', '', text, flags=re.MULTILINE)

        # 3. Remove múltiplas linhas vazias (máximo 2 consecutivas)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 4. Remove linhas com apenas pontuação/símbolos isolados
        # Ex: linhas com apenas: _ _ _ ou - - - ou = = =
        text = re.sub(r'^\s*[_\-=*]{1,5}\s*$', '', text, flags=re.MULTILINE)

        # 5. Remove espaços antes de pontuação comum
        text = re.sub(r'\s+([.,;:!?)])', r'\1', text)

        # 6. Remove espaços depois de pontuação de abertura
        text = re.sub(r'([\(])\s+', r'\1', text)

        # 7. Trim final
        text = text.strip()

        return text

    def remove_excessive_whitespace(self, text: str) -> str:
        """
        Remove apenas espaços em branco excessivos.

        Mais conservador que normalize() - não toca em linhas vazias.
        """
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'^[ \t]+|[ \t]+$', '', text, flags=re.MULTILINE)
        return text.strip()

    def collapse_blank_lines(self, text: str, max_consecutive: int = 2) -> str:
        """
        Colapsa linhas vazias consecutivas.

        Args:
            text: Texto a processar
            max_consecutive: Número máximo de linhas vazias consecutivas permitidas

        Returns:
            Texto com linhas vazias limitadas
        """
        pattern = f'\\n{{{max_consecutive + 1},}}'
        replacement = '\n' * max_consecutive
        return re.sub(pattern, replacement, text)
