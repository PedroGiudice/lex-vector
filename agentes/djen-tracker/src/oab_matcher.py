"""
OAB Matcher com Pattern Recognition e Context Scoring

Implementa detecção robusta de números OAB em textos com:
- 12+ padrões regex cobrindo variações de formatação
- Scoring baseado em contexto (palavras próximas)
- Normalização de resultados
- Deduplicação inteligente

Author: Claude Code (Development Agent)
Version: 1.0.0
"""

import re
import logging
from typing import List, Tuple, Set, Dict, Optional
from dataclasses import dataclass
from collections import defaultdict


logger = logging.getLogger(__name__)


@dataclass
class OABMatch:
    """Representa um match de OAB encontrado em texto."""
    numero: str  # Número normalizado (sem pontos/traços)
    uf: str  # UF normalizada (maiúsculas)
    texto_contexto: str  # Contexto ao redor (200 chars)
    posicao_inicio: int  # Posição no texto original
    posicao_fim: int
    score_contexto: float  # Score 0.0-1.0 baseado em contexto
    padrao_usado: str  # Nome do padrão regex que encontrou
    texto_original: str  # Match original completo

    def __hash__(self):
        """Hash para deduplicação."""
        return hash((self.numero, self.uf))

    def __eq__(self, other):
        """Igualdade para deduplicação."""
        if not isinstance(other, OABMatch):
            return False
        return self.numero == other.numero and self.uf == other.uf


class OABMatcher:
    """
    Matcher robusto de números OAB com 12+ padrões regex.

    Detecta OABs em múltiplos formatos:
    - OAB/SP 123.456
    - OAB/SP 123456
    - 123.456/SP
    - 123456-SP
    - Adv.: João Silva (OAB 123456/SP)
    - Dr. João Silva - OAB/SP nº 123.456
    - Advogado(a): OAB/SP 123456
    - E mais variações...

    Attributes:
        ufs_validas: Set de UFs brasileiras válidas
        palavras_contexto_positivo: Palavras que aumentam score
        palavras_contexto_negativo: Palavras que diminuem score
    """

    # UFs válidas do Brasil
    UFS_VALIDAS = {
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    }

    # Palavras que indicam contexto de advogado (aumentam score)
    CONTEXTO_POSITIVO = {
        'advogado', 'advogada', 'adv', 'dr', 'dra', 'doutor', 'doutora',
        'defensor', 'defensora', 'procurador', 'procuradora',
        'causídico', 'causídica', 'patrono', 'patrona',
        'representante', 'subscrito', 'subscrita',
        'intimação', 'intimado', 'intimada'
    }

    # Palavras que indicam que não é OAB (diminuem score)
    CONTEXTO_NEGATIVO = {
        'processo', 'cnpj', 'cpf', 'telefone', 'cep',
        'protocolo', 'senha', 'código', 'numero'
    }

    def __init__(self):
        """Inicializa OABMatcher com padrões compilados."""
        self.patterns = self._compile_patterns()
        logger.debug(f"OABMatcher inicializado com {len(self.patterns)} padrões")

    def _compile_patterns(self) -> List[Tuple[str, re.Pattern]]:
        """
        Compila padrões regex para detecção de OAB.

        Returns:
            Lista de (nome_padrao, pattern_compilado)
        """
        patterns = []

        # Padrão 1: OAB/UF 123.456 ou OAB/UF 123456
        patterns.append((
            "oab_slash_uf_numero",
            re.compile(
                r'\bOAB[/\s]*([A-Z]{2})[^\d]{0,5}(\d{1,3}\.?\d{3})\b',
                re.IGNORECASE
            )
        ))

        # Padrão 2: OAB UF 123.456 (sem barra)
        patterns.append((
            "oab_espaco_uf_numero",
            re.compile(
                r'\bOAB\s+([A-Z]{2})\s+n?º?\s?(\d{1,3}\.?\d{3})\b',
                re.IGNORECASE
            )
        ))

        # Padrão 3: 123.456/SP ou 123456/SP
        patterns.append((
            "numero_slash_uf",
            re.compile(
                r'\b(\d{1,3}\.?\d{3})[/\s]*([A-Z]{2})\b'
            )
        ))

        # Padrão 4: 123456-SP ou 123.456-SP
        patterns.append((
            "numero_hifen_uf",
            re.compile(
                r'\b(\d{1,3}\.?\d{3})-([A-Z]{2})\b'
            )
        ))

        # Padrão 5: Adv.: Nome (OAB 123456/SP)
        patterns.append((
            "adv_parenteses_oab",
            re.compile(
                r'\(OAB[/\s]*([A-Z]{2})[^\d]{0,5}(\d{1,3}\.?\d{3})\)',
                re.IGNORECASE
            )
        ))

        # Padrão 6: Advogado(a): OAB/SP 123456
        patterns.append((
            "advogado_oab_uf_numero",
            re.compile(
                r'Advogad[oa]s?[:\s]+OAB[/\s]*([A-Z]{2})[^\d]{0,5}(\d{1,3}\.?\d{3})',
                re.IGNORECASE
            )
        ))

        # Padrão 7: Dr./Dra. Nome - OAB/SP nº 123.456
        patterns.append((
            "dr_nome_oab",
            re.compile(
                r'Dr[a]?\.\s+[\w\s]+-\s*OAB[/\s]*([A-Z]{2})\s+n?º?\s?(\d{1,3}\.?\d{3})',
                re.IGNORECASE
            )
        ))

        # Padrão 8: OAB-UF: 123.456
        patterns.append((
            "oab_hifen_uf_dois_pontos",
            re.compile(
                r'\bOAB-([A-Z]{2}):\s*(\d{1,3}\.?\d{3})\b',
                re.IGNORECASE
            )
        ))

        # Padrão 9: Inscrição OAB/UF sob o nº 123.456
        patterns.append((
            "inscricao_oab",
            re.compile(
                r'Inscrição\s+OAB[/\s]*([A-Z]{2})\s+(?:sob\s+)?(?:o\s+)?n?º?\s?(\d{1,3}\.?\d{3})',
                re.IGNORECASE
            )
        ))

        # Padrão 10: Procurador(a): OAB 123456 - SP
        patterns.append((
            "procurador_oab_numero_uf",
            re.compile(
                r'Procurador[a]?[:\s]+OAB\s+(\d{1,3}\.?\d{3})\s*[-/]\s*([A-Z]{2})',
                re.IGNORECASE
            )
        ))

        # Padrão 11: Defensor(a): 123456/SP
        patterns.append((
            "defensor_numero_uf",
            re.compile(
                r'Defensor[a]?[:\s]+(\d{1,3}\.?\d{3})[/\s]*([A-Z]{2})',
                re.IGNORECASE
            )
        ))

        # Padrão 12: Patrono(a): Nome (OAB 123.456-SP)
        patterns.append((
            "patrono_oab",
            re.compile(
                r'Patronos?[a]?[:\s]+[\w\s]+\(OAB\s+(\d{1,3}\.?\d{3})[-/]([A-Z]{2})\)',
                re.IGNORECASE
            )
        ))

        # Padrão 13: Registro OAB nº 123.456 (SP)
        patterns.append((
            "registro_oab_numero_uf_parenteses",
            re.compile(
                r'Registro\s+OAB\s+n?º?\s?(\d{1,3}\.?\d{3})\s*\(([A-Z]{2})\)',
                re.IGNORECASE
            )
        ))

        logger.debug(f"Compilados {len(patterns)} padrões regex")
        return patterns

    def normalize_oab(self, numero: str, uf: str) -> Tuple[str, str]:
        """
        Normaliza número OAB e UF.

        Args:
            numero: Número OAB (pode ter pontos/traços)
            uf: UF (pode estar em minúsculas)

        Returns:
            (numero_normalizado, uf_normalizada)
        """
        # Remover pontos e traços do número
        numero_clean = re.sub(r'[.\-\s]', '', numero)

        # UF em maiúsculas
        uf_clean = uf.upper().strip()

        return numero_clean, uf_clean

    def validate_oab(self, numero: str, uf: str) -> bool:
        """
        Valida se número OAB e UF são plausíveis.

        Args:
            numero: Número OAB normalizado
            uf: UF normalizada

        Returns:
            True se válido, False caso contrário
        """
        # UF deve ser válida
        if uf not in self.UFS_VALIDAS:
            return False

        # Número deve ter 4-6 dígitos
        if not numero.isdigit():
            return False

        if not (4 <= len(numero) <= 6):
            return False

        # Número não deve ser sequencial óbvio (111111, 123456, etc)
        if numero == numero[0] * len(numero):  # Todos dígitos iguais
            return False

        return True

    def extract_context(
        self,
        text: str,
        start: int,
        end: int,
        context_chars: int = 200
    ) -> str:
        """
        Extrai contexto ao redor de um match.

        Args:
            text: Texto completo
            start: Posição inicial do match
            end: Posição final do match
            context_chars: Caracteres antes e depois

        Returns:
            Contexto formatado
        """
        ctx_start = max(0, start - context_chars)
        ctx_end = min(len(text), end + context_chars)

        context = text[ctx_start:ctx_end]

        # Adicionar elipses se truncado
        if ctx_start > 0:
            context = '...' + context
        if ctx_end < len(text):
            context = context + '...'

        return context.strip()

    def score_context(self, context: str) -> float:
        """
        Calcula score baseado no contexto ao redor do match.

        Score baseado em:
        - Palavras positivas (advogado, dr, intimação, etc) = +0.3
        - Palavras negativas (processo, cpf, telefone, etc) = -0.2
        - Presença de nome próprio antes = +0.2
        - Formatação adequada (dentro de parênteses, após dois pontos) = +0.1

        Args:
            context: Texto do contexto

        Returns:
            Score 0.0-1.0
        """
        score = 0.5  # Score base

        context_lower = context.lower()

        # Palavras positivas
        positive_matches = sum(
            1 for word in self.CONTEXTO_POSITIVO
            if word in context_lower
        )
        if positive_matches > 0:
            score += min(0.3, positive_matches * 0.1)

        # Palavras negativas
        negative_matches = sum(
            1 for word in self.CONTEXTO_NEGATIVO
            if word in context_lower
        )
        if negative_matches > 0:
            score -= min(0.2, negative_matches * 0.1)

        # Presença de nome próprio (heurística: palavra iniciando com maiúscula)
        if re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+', context):
            score += 0.2

        # Formatação adequada
        if '(' in context or ')' in context:
            score += 0.05
        if ':' in context:
            score += 0.05

        # Garantir range 0.0-1.0
        return max(0.0, min(1.0, score))

    def find_all(
        self,
        text: str,
        min_score: float = 0.4,
        deduplicate: bool = True
    ) -> List[OABMatch]:
        """
        Encontra todos os números OAB no texto.

        Args:
            text: Texto para buscar
            min_score: Score mínimo para incluir match (0.0-1.0)
            deduplicate: Se True, remove duplicatas

        Returns:
            Lista de OABMatch ordenados por score descendente
        """
        matches = []

        # Aplicar cada padrão
        for pattern_name, pattern in self.patterns:
            for match in pattern.finditer(text):
                try:
                    groups = match.groups()

                    # Dependendo do padrão, ordem pode ser (uf, numero) ou (numero, uf)
                    if pattern_name in [
                        "oab_slash_uf_numero",
                        "oab_espaco_uf_numero",
                        "oab_hifen_uf_dois_pontos",
                        "inscricao_oab",
                        "adv_parenteses_oab",
                        "advogado_oab_uf_numero",
                        "dr_nome_oab"
                    ]:
                        uf_raw, numero_raw = groups[0], groups[1]
                    elif pattern_name in [
                        "registro_oab_numero_uf_parenteses",
                        "patrono_oab"
                    ]:
                        numero_raw, uf_raw = groups[0], groups[1]
                    elif pattern_name == "procurador_oab_numero_uf":
                        numero_raw, uf_raw = groups[0], groups[1]
                    elif pattern_name in ["defensor_numero_uf"]:
                        numero_raw, uf_raw = groups[0], groups[1]
                    else:
                        # Para padrões genéricos, tentar inferir
                        if len(groups[0]) == 2 and groups[0].isalpha():
                            uf_raw, numero_raw = groups[0], groups[1]
                        else:
                            numero_raw, uf_raw = groups[0], groups[1]

                    # Normalizar
                    numero, uf = self.normalize_oab(numero_raw, uf_raw)

                    # Validar
                    if not self.validate_oab(numero, uf):
                        logger.debug(
                            f"OAB inválida ignorada: {numero}/{uf} "
                            f"(padrão: {pattern_name})"
                        )
                        continue

                    # Extrair contexto
                    start, end = match.span()
                    context = self.extract_context(text, start, end)

                    # Calcular score
                    score = self.score_context(context)

                    # Verificar threshold
                    if score < min_score:
                        logger.debug(
                            f"OAB com score baixo ignorada: {numero}/{uf} "
                            f"(score={score:.2f}, min={min_score})"
                        )
                        continue

                    # Criar match
                    oab_match = OABMatch(
                        numero=numero,
                        uf=uf,
                        texto_contexto=context,
                        posicao_inicio=start,
                        posicao_fim=end,
                        score_contexto=score,
                        padrao_usado=pattern_name,
                        texto_original=match.group(0)
                    )

                    matches.append(oab_match)

                except Exception as e:
                    logger.warning(
                        f"Erro ao processar match de {pattern_name}: {e}"
                    )
                    continue

        # Deduplicar
        if deduplicate:
            matches = self._deduplicate_matches(matches)

        # Ordenar por score descendente
        matches.sort(key=lambda m: m.score_contexto, reverse=True)

        logger.info(
            f"Encontrados {len(matches)} números OAB únicos no texto "
            f"(após {len(self.patterns)} padrões)"
        )

        return matches

    def _deduplicate_matches(self, matches: List[OABMatch]) -> List[OABMatch]:
        """
        Remove duplicatas mantendo match com maior score.

        Args:
            matches: Lista de matches (pode ter duplicatas)

        Returns:
            Lista deduplic ada
        """
        # Agrupar por (numero, uf)
        grouped: Dict[Tuple[str, str], List[OABMatch]] = defaultdict(list)

        for match in matches:
            key = (match.numero, match.uf)
            grouped[key].append(match)

        # Para cada grupo, manter apenas o de maior score
        deduplicated = []
        for key, group in grouped.items():
            best_match = max(group, key=lambda m: m.score_contexto)
            deduplicated.append(best_match)

        logger.debug(
            f"Deduplicação: {len(matches)} matches → "
            f"{len(deduplicated)} únicos"
        )

        return deduplicated

    def filter_by_oabs(
        self,
        text: str,
        target_oabs: List[Tuple[str, str]],
        min_score: float = 0.4
    ) -> List[OABMatch]:
        """
        Busca OABs específicas no texto.

        Args:
            text: Texto para buscar
            target_oabs: Lista de (numero, uf) desejadas
                         Ex: [('123456', 'SP'), ('789012', 'RJ')]
            min_score: Score mínimo para incluir match

        Returns:
            Lista de OABMatch encontrados para as OABs alvo
        """
        # Normalizar OABs alvo
        target_set = set()
        for numero, uf in target_oabs:
            numero_norm, uf_norm = self.normalize_oab(numero, uf)
            target_set.add((numero_norm, uf_norm))

        logger.info(
            f"Buscando {len(target_set)} OABs específicas no texto"
        )

        # Encontrar todas
        all_matches = self.find_all(text, min_score=min_score)

        # Filtrar apenas as desejadas
        filtered = [
            match for match in all_matches
            if (match.numero, match.uf) in target_set
        ]

        logger.info(
            f"Encontradas {len(filtered)} das {len(target_set)} OABs buscadas"
        )

        return filtered


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    # Texto de exemplo
    texto_exemplo = """
    PODER JUDICIÁRIO
    TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO

    Processo nº 1234567-89.2025.8.26.0100

    Advogado(a): Dr. João da Silva - OAB/SP nº 123.456
    Advogada: Dra. Maria Santos (OAB 789012/SP)
    Procurador: José Oliveira - OAB 345678 - RJ
    Defensor Público: Pedro Costa (OAB/MG 567890)

    Intimação de Advogado:
    Fica intimado o Dr. Carlos Ferreira, OAB/DF 234567, para...

    Patrono da parte autora: Ana Paula (OAB 456789-BA)
    """

    matcher = OABMatcher()

    # Encontrar todas OABs
    print("\n" + "=" * 70)
    print("TODAS AS OABS ENCONTRADAS")
    print("=" * 70)

    matches = matcher.find_all(texto_exemplo, min_score=0.3)

    for i, match in enumerate(matches, 1):
        print(f"\n{i}. OAB: {match.numero}/{match.uf}")
        print(f"   Score: {match.score_contexto:.2f}")
        print(f"   Padrão: {match.padrao_usado}")
        print(f"   Contexto: {match.texto_contexto[:100]}...")

    # Filtrar OABs específicas
    print("\n" + "=" * 70)
    print("FILTRO POR OABS ESPECÍFICAS")
    print("=" * 70)

    target_oabs = [
        ('123456', 'SP'),
        ('789012', 'SP'),
        ('999999', 'RJ')  # Essa não existe no texto
    ]

    filtered = matcher.filter_by_oabs(texto_exemplo, target_oabs, min_score=0.3)

    print(f"\nBuscadas: {len(target_oabs)} OABs")
    print(f"Encontradas: {len(filtered)} OABs\n")

    for match in filtered:
        print(f"- {match.numero}/{match.uf} (score: {match.score_contexto:.2f})")
