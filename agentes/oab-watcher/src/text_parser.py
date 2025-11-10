"""
TextParser - Detecção de OAB em textos com regex multi-padrão e scoring
"""
import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OABMatch:
    """Representa uma correspondência de OAB encontrada no texto."""
    numero: str
    uf: str
    pattern_usado: str
    confidence: float  # 0.0 a 1.0
    posicao_inicio: int
    posicao_fim: int
    texto_contexto: str  # 50 chars antes e depois


class TextParser:
    """
    Parser de textos jurídicos para detectar números de OAB.

    Features:
    - 7 regex patterns diferentes para cobrir variações de formato
    - Scoring de confiança por pattern
    - Normalização de números (remove pontos/espaços)
    - Detecção de falsos positivos
    - Extração de contexto

    Formatos suportados:
    - OAB 129021/SP
    - OAB/SP 129021
    - OAB-SP nº 129021
    - OAB 129.021/SP
    - OAB SP 129021
    - advogado OAB 129021 SP
    - Dr. João Silva (OAB 129021/SP)
    """

    # Patterns ordenados por confidence (maior para menor)
    PATTERNS = [
        # Pattern 1: OAB NUMERO/UF (formato completo com número formatado) - confidence 0.95
        {
            'regex': r'OAB[\s\-/]*(\d{1,3}\.\d{3}|\d{4,6})[\s\-/]+([A-Z]{2})',
            'confidence': 0.95,
            'nome': 'padrao_completo'
        },
        # Pattern 2: OAB/UF NUMERO ou OAB-UF NUMERO - confidence 0.90
        {
            'regex': r'OAB[\s\-/]+([A-Z]{2})[\s\-/nº]*(\d{1,6})',
            'confidence': 0.90,
            'nome': 'oab_uf_numero'
        },
        # Pattern 3: OAB NUMERO/UF (padrão básico) - confidence 0.88
        {
            'regex': r'OAB[\s\-/]*(\d{4,6})[\s\-/]+([A-Z]{2})',
            'confidence': 0.88,
            'nome': 'padrao_basico'
        },
        # Pattern 4: Dentro de parênteses (OAB 129021/SP) - confidence 0.85
        {
            'regex': r'\(OAB[\s\-/]*(\d{4,6})[\s\-/]+([A-Z]{2})\)',
            'confidence': 0.85,
            'nome': 'em_parenteses'
        },
        # Pattern 5: Após nome "Dr./Dra." - confidence 0.82
        {
            'regex': r'(?:Dr\.?|Dra\.?)[\s\w]+OAB[\s\-/]*(\d{4,6})[\s\-/]+([A-Z]{2})',
            'confidence': 0.82,
            'nome': 'apos_dr'
        },
        # Pattern 6: Após "advogado"/"advogada" - confidence 0.78
        {
            'regex': r'(?:advogado|advogada)[\s\w]*OAB[\s\-/]*(\d{4,6})[\s\-/]+([A-Z]{2})',
            'confidence': 0.78,
            'nome': 'apos_advogado'
        },
        # Pattern 7: Genérico com "OAB" seguido de número e UF - confidence 0.75
        {
            'regex': r'OAB[^\d]*(\d{4,6})[^\w]*([A-Z]{2})',
            'confidence': 0.75,
            'nome': 'generico'
        }
    ]

    # UFs válidas do Brasil
    UFS_VALIDAS = {
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    }

    def __init__(self):
        """Inicializa o parser compilando os regex patterns."""
        self.compiled_patterns = []

        for pattern in self.PATTERNS:
            try:
                compiled = re.compile(pattern['regex'], re.IGNORECASE)
                self.compiled_patterns.append({
                    'compiled': compiled,
                    'confidence': pattern['confidence'],
                    'nome': pattern['nome']
                })
                logger.debug(f"Pattern compilado: {pattern['nome']}")
            except re.error as e:
                logger.error(f"Erro ao compilar pattern {pattern['nome']}: {e}")

        logger.info(f"TextParser inicializado com {len(self.compiled_patterns)} patterns")

    @staticmethod
    def normalizar_numero_oab(numero: str) -> str:
        """
        Normaliza número de OAB removendo formatação.

        Args:
            numero: Número com possível formatação (129.021 ou 129021)

        Returns:
            Número limpo (129021)
        """
        # Remove pontos, espaços, traços
        return re.sub(r'[.\s\-]', '', numero)

    def validar_uf(self, uf: str) -> bool:
        """
        Valida se UF é válida.

        Args:
            uf: Sigla UF (2 letras)

        Returns:
            True se válida
        """
        return uf.upper() in self.UFS_VALIDAS

    def detectar_falso_positivo(self, match: OABMatch, texto: str) -> bool:
        """
        Detecta se match é falso positivo.

        Falsos positivos comuns:
        - Número de processo (não é OAB)
        - Datas (não é OAB)
        - Códigos de tribunal (não é OAB)

        Args:
            match: Match encontrado
            texto: Texto completo

        Returns:
            True se é falso positivo
        """
        # Verificar se UF é inválida
        if not self.validar_uf(match.uf):
            logger.debug(f"Falso positivo: UF inválida {match.uf}")
            return True

        # Verificar se número é muito curto (< 3 dígitos)
        if len(match.numero) < 3:
            logger.debug(f"Falso positivo: número muito curto {match.numero}")
            return True

        # Verificar se número é muito longo (> 6 dígitos)
        if len(match.numero) > 6:
            logger.debug(f"Falso positivo: número muito longo {match.numero}")
            return True

        # Contexto suspeito (processo, data, etc)
        contexto_lower = match.texto_contexto.lower()
        palavras_suspeitas = ['processo', 'data', 'código', 'protocolo', 'nº', 'art.']

        for palavra in palavras_suspeitas:
            if palavra in contexto_lower and 'oab' not in contexto_lower:
                logger.debug(f"Falso positivo: contexto suspeito '{palavra}'")
                return True

        return False

    def extrair_contexto(self, texto: str, inicio: int, fim: int, janela: int = 50) -> str:
        """
        Extrai contexto ao redor do match.

        Args:
            texto: Texto completo
            inicio: Posição início do match
            fim: Posição fim do match
            janela: Caracteres antes e depois (default: 50)

        Returns:
            String com contexto
        """
        contexto_inicio = max(0, inicio - janela)
        contexto_fim = min(len(texto), fim + janela)

        contexto = texto[contexto_inicio:contexto_fim]

        # Adicionar reticências se cortou
        if contexto_inicio > 0:
            contexto = '...' + contexto
        if contexto_fim < len(texto):
            contexto = contexto + '...'

        return contexto

    def buscar_oab(
        self,
        texto: str,
        numero_oab_alvo: str,
        uf_oab_alvo: str,
        threshold_confidence: float = 0.3
    ) -> Tuple[bool, float, List[OABMatch]]:
        """
        Busca OAB específica no texto com scoring.

        Args:
            texto: Texto para buscar
            numero_oab_alvo: Número OAB procurado (ex: "129021")
            uf_oab_alvo: UF OAB procurada (ex: "SP")
            threshold_confidence: Confiança mínima para considerar match (default: 0.3)

        Returns:
            Tupla (encontrou: bool, score_maximo: float, matches: List[OABMatch])
        """
        # Normalizar inputs
        numero_normalizado = self.normalizar_numero_oab(numero_oab_alvo)
        uf_normalizada = uf_oab_alvo.upper()

        matches = []
        score_maximo = 0.0

        # Tentar cada pattern
        for pattern_data in self.compiled_patterns:
            regex = pattern_data['compiled']
            confidence = pattern_data['confidence']
            nome = pattern_data['nome']

            for match in regex.finditer(texto):
                try:
                    # Extrair grupos (varia por pattern)
                    groups = match.groups()

                    # Identificar qual grupo é número e qual é UF
                    # Assumindo que UF sempre são 2 letras maiúsculas
                    numero_encontrado = None
                    uf_encontrada = None

                    for group in groups:
                        if group and len(group) == 2 and group.isupper():
                            uf_encontrada = group
                        elif group and group.isdigit():
                            numero_encontrado = group

                    if not numero_encontrado or not uf_encontrada:
                        continue

                    # Normalizar número encontrado
                    numero_encontrado = self.normalizar_numero_oab(numero_encontrado)

                    # Verificar se é match
                    if numero_encontrado == numero_normalizado and uf_encontrada == uf_normalizada:
                        # Extrair contexto
                        contexto = self.extrair_contexto(
                            texto,
                            match.start(),
                            match.end()
                        )

                        # Criar OABMatch
                        oab_match = OABMatch(
                            numero=numero_encontrado,
                            uf=uf_encontrada,
                            pattern_usado=nome,
                            confidence=confidence,
                            posicao_inicio=match.start(),
                            posicao_fim=match.end(),
                            texto_contexto=contexto
                        )

                        # Verificar falso positivo
                        if not self.detectar_falso_positivo(oab_match, texto):
                            if confidence >= threshold_confidence:
                                matches.append(oab_match)
                                score_maximo = max(score_maximo, confidence)

                                logger.debug(
                                    f"Match encontrado: OAB {numero_encontrado}/{uf_encontrada} "
                                    f"(pattern={nome}, confidence={confidence:.2f})"
                                )

                except Exception as e:
                    logger.error(f"Erro ao processar match do pattern {nome}: {e}")
                    continue

        encontrou = len(matches) > 0

        if encontrou:
            logger.info(
                f"OAB {numero_oab_alvo}/{uf_oab_alvo} encontrada! "
                f"{len(matches)} matches, score máximo: {score_maximo:.2f}"
            )
        else:
            logger.debug(f"OAB {numero_oab_alvo}/{uf_oab_alvo} NÃO encontrada")

        return (encontrou, score_maximo, matches)

    def buscar_todas_oabs(self, texto: str) -> List[OABMatch]:
        """
        Busca TODAS as OABs presentes no texto.

        Args:
            texto: Texto para buscar

        Returns:
            Lista de OABMatch encontrados
        """
        todas_matches = []

        for pattern_data in self.compiled_patterns:
            regex = pattern_data['compiled']
            confidence = pattern_data['confidence']
            nome = pattern_data['nome']

            for match in regex.finditer(texto):
                try:
                    groups = match.groups()

                    numero_encontrado = None
                    uf_encontrada = None

                    for group in groups:
                        if group and len(group) == 2 and group.isupper():
                            uf_encontrada = group
                        elif group and group.replace('.', '').isdigit():
                            numero_encontrado = group

                    if not numero_encontrado or not uf_encontrada:
                        continue

                    numero_encontrado = self.normalizar_numero_oab(numero_encontrado)

                    contexto = self.extrair_contexto(texto, match.start(), match.end())

                    oab_match = OABMatch(
                        numero=numero_encontrado,
                        uf=uf_encontrada,
                        pattern_usado=nome,
                        confidence=confidence,
                        posicao_inicio=match.start(),
                        posicao_fim=match.end(),
                        texto_contexto=contexto
                    )

                    if not self.detectar_falso_positivo(oab_match, texto):
                        todas_matches.append(oab_match)

                except Exception as e:
                    logger.error(f"Erro ao processar match: {e}")
                    continue

        # Remover duplicatas (mesma posição)
        matches_unicos = []
        posicoes_vistas = set()

        for match in todas_matches:
            key = (match.posicao_inicio, match.posicao_fim)
            if key not in posicoes_vistas:
                matches_unicos.append(match)
                posicoes_vistas.add(key)

        logger.info(f"Total de OABs encontradas: {len(matches_unicos)}")

        return matches_unicos
