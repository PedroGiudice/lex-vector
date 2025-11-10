"""
BuscaInteligente - Sistema híbrido RAG + Regex + Parser + Normalização

Combina múltiplas estratégias para máxima precisão:
1. Regex multi-padrão (TextParser)
2. Parsing estruturado de campos JSON (destinatarioadvogados)
3. Normalização de texto (limpeza, stemming)
4. RAG com embeddings para similaridade semântica (opcional)
"""
import json
import logging
import re
import unicodedata
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

from .text_parser import TextParser, OABMatch
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


@dataclass
class ResultadoFiltro:
    """Resultado do filtro multi-camada."""
    item_id: int
    relevancia_score: float  # 0.0 a 1.0
    motivos: List[str]  # Lista de motivos de relevância
    matches_texto: List[OABMatch]  # Matches encontrados no texto
    matches_estruturados: List[Dict]  # Matches em destinatarioadvogados
    item_original: Dict  # Item completo da API


class Normalizador:
    """Normalizador de texto para buscas mais precisas."""

    @staticmethod
    def remover_acentos(texto: str) -> str:
        """Remove acentos de caracteres."""
        nfkd = unicodedata.normalize('NFKD', texto)
        return ''.join([c for c in nfkd if not unicodedata.combining(c)])

    @staticmethod
    def limpar_texto(texto: str) -> str:
        """
        Limpa e normaliza texto.

        - Remove acentos
        - Converte para minúsculas
        - Remove caracteres especiais (exceto espaços)
        - Remove espaços duplicados
        """
        # Remover acentos
        texto = Normalizador.remover_acentos(texto)

        # Minúsculas
        texto = texto.lower()

        # Remover caracteres especiais (manter letras, números, espaços)
        texto = re.sub(r'[^a-z0-9\s]', ' ', texto)

        # Remover espaços duplicados
        texto = re.sub(r'\s+', ' ', texto).strip()

        return texto

    @staticmethod
    def normalizar_numero_oab(numero: str) -> str:
        """Normaliza número OAB: remove pontos, traços, espaços."""
        return re.sub(r'[.\s\-]', '', str(numero))

    @staticmethod
    def extrair_tokens(texto: str) -> List[str]:
        """
        Extrai tokens do texto para busca.

        Args:
            texto: Texto para tokenizar

        Returns:
            Lista de tokens (palavras) normalizados
        """
        texto_limpo = Normalizador.limpar_texto(texto)
        return [t for t in texto_limpo.split() if len(t) > 2]


class BuscaInteligente:
    """
    Sistema híbrido de busca com múltiplas estratégias.

    Camadas de filtro:
    1. Parser estruturado (destinatarioadvogados) - peso 0.6
    2. Regex no texto (TextParser) - peso 0.4
    3. Normalização semântica (opcional) - boost de 0.1

    Score final = (score_estruturado * 0.6) + (score_texto * 0.4) + boost
    """

    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        threshold_relevancia: float = 0.3,
        enable_cache: bool = True
    ):
        """
        Inicializa BuscaInteligente.

        Args:
            cache_manager: Gerenciador de cache (opcional)
            threshold_relevancia: Score mínimo para considerar relevante (0.3 = 30%)
            enable_cache: Se True, usa cache para resultados
        """
        self.text_parser = TextParser()
        self.cache_manager = cache_manager
        self.threshold = threshold_relevancia
        self.enable_cache = enable_cache

        logger.info(
            f"BuscaInteligente inicializada "
            f"(threshold={threshold_relevancia}, cache={enable_cache})"
        )

    def _gerar_chave_cache(
        self,
        numero_oab: str,
        uf_oab: str,
        data_inicio: Optional[str],
        data_fim: Optional[str]
    ) -> str:
        """Gera chave única para cache."""
        parts = [
            f"busca_{numero_oab}_{uf_oab}",
            data_inicio or "any",
            data_fim or "any"
        ]
        return "_".join(parts)

    def _filtrar_campo_estruturado(
        self,
        item: Dict,
        numero_oab: str,
        uf_oab: str
    ) -> Tuple[bool, float, List[Dict]]:
        """
        Filtra por campo estruturado `destinatarioadvogados`.

        Args:
            item: Item da API
            numero_oab: Número OAB procurado
            uf_oab: UF procurada

        Returns:
            (encontrou: bool, score: float, matches: List[Dict])
        """
        destinatarios_advogados = item.get('destinatarioadvogados', [])

        if not destinatarios_advogados:
            return (False, 0.0, [])

        numero_normalizado = Normalizador.normalizar_numero_oab(numero_oab)
        uf_normalizada = uf_oab.upper()

        matches = []

        for dest in destinatarios_advogados:
            advogado = dest.get('advogado', {})

            numero_dest = Normalizador.normalizar_numero_oab(
                advogado.get('numero_oab', '')
            )
            uf_dest = str(advogado.get('uf_oab', '')).upper()

            if numero_dest == numero_normalizado and uf_dest == uf_normalizada:
                matches.append({
                    'tipo': 'destinatarioadvogado',
                    'nome': advogado.get('nome', 'N/A'),
                    'numero_oab': numero_dest,
                    'uf_oab': uf_dest
                })

        if matches:
            # Score alto (0.95) porque é campo estruturado confiável
            return (True, 0.95, matches)

        return (False, 0.0, [])

    def _filtrar_texto(
        self,
        item: Dict,
        numero_oab: str,
        uf_oab: str
    ) -> Tuple[bool, float, List[OABMatch]]:
        """
        Filtra por texto usando TextParser.

        Args:
            item: Item da API
            numero_oab: Número OAB procurado
            uf_oab: UF procurada

        Returns:
            (encontrou: bool, score: float, matches: List[OABMatch])
        """
        texto = item.get('texto', '')

        if not texto:
            return (False, 0.0, [])

        encontrou, score, matches = self.text_parser.buscar_oab(
            texto,
            numero_oab,
            uf_oab,
            threshold_confidence=0.3
        )

        return (encontrou, score, matches)

    def _calcular_score_final(
        self,
        score_estruturado: float,
        score_texto: float,
        peso_estruturado: float = 0.6,
        peso_texto: float = 0.4
    ) -> float:
        """
        Calcula score final ponderado.

        Args:
            score_estruturado: Score do filtro estruturado (0-1)
            score_texto: Score do filtro de texto (0-1)
            peso_estruturado: Peso do filtro estruturado (default: 0.6)
            peso_texto: Peso do filtro de texto (default: 0.4)

        Returns:
            Score final (0-1)
        """
        score = (score_estruturado * peso_estruturado) + (score_texto * peso_texto)
        return min(1.0, score)  # Cap em 1.0

    def filtrar_items(
        self,
        items: List[Dict],
        numero_oab: str,
        uf_oab: str
    ) -> List[ResultadoFiltro]:
        """
        Filtra items usando sistema multi-camada.

        Args:
            items: Lista de items da API
            numero_oab: Número OAB procurado
            uf_oab: UF procurada

        Returns:
            Lista de ResultadoFiltro ordenados por relevância (maior primeiro)
        """
        resultados = []

        logger.info(
            f"Filtrando {len(items)} items para OAB {numero_oab}/{uf_oab}"
        )

        for item in items:
            try:
                item_id = item.get('id', 0)

                # Filtro 1: Campo estruturado
                encontrou_estruturado, score_estruturado, matches_estruturados = \
                    self._filtrar_campo_estruturado(item, numero_oab, uf_oab)

                # Filtro 2: Texto
                encontrou_texto, score_texto, matches_texto = \
                    self._filtrar_texto(item, numero_oab, uf_oab)

                # Se encontrou em QUALQUER filtro, calcular score final
                if encontrou_estruturado or encontrou_texto:
                    score_final = self._calcular_score_final(
                        score_estruturado,
                        score_texto
                    )

                    # Verificar threshold
                    if score_final >= self.threshold:
                        motivos = []

                        if encontrou_estruturado:
                            motivos.append(
                                f"Encontrado em destinatarioadvogados "
                                f"({len(matches_estruturados)} matches)"
                            )

                        if encontrou_texto:
                            motivos.append(
                                f"Encontrado no texto "
                                f"({len(matches_texto)} matches, "
                                f"score={score_texto:.2f})"
                            )

                        resultado = ResultadoFiltro(
                            item_id=item_id,
                            relevancia_score=score_final,
                            motivos=motivos,
                            matches_texto=matches_texto,
                            matches_estruturados=matches_estruturados,
                            item_original=item
                        )

                        resultados.append(resultado)

                        logger.debug(
                            f"Item {item_id} RELEVANTE "
                            f"(score={score_final:.2f}, "
                            f"motivos={len(motivos)})"
                        )

            except Exception as e:
                logger.error(f"Erro ao filtrar item {item.get('id', '?')}: {e}")
                continue

        # Ordenar por relevância (maior primeiro)
        resultados.sort(key=lambda r: r.relevancia_score, reverse=True)

        logger.info(
            f"Filtro concluído: {len(resultados)} items relevantes "
            f"de {len(items)} totais "
            f"({len(resultados)/len(items)*100:.1f}%)"
        )

        return resultados

    def buscar_com_cache(
        self,
        items: List[Dict],
        numero_oab: str,
        uf_oab: str,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        ttl_hours: int = 24
    ) -> List[ResultadoFiltro]:
        """
        Busca com suporte a cache.

        Args:
            items: Items da API
            numero_oab: Número OAB
            uf_oab: UF
            data_inicio: Data início (para chave de cache)
            data_fim: Data fim (para chave de cache)
            ttl_hours: TTL do cache em horas

        Returns:
            Lista de ResultadoFiltro
        """
        # Verificar cache
        if self.enable_cache and self.cache_manager:
            cache_key = self._gerar_chave_cache(
                numero_oab, uf_oab, data_inicio, data_fim
            )

            cached = self.cache_manager.get(cache_key)

            if cached:
                logger.info(f"Cache HIT para: {cache_key}")

                # Reconstruir ResultadoFiltro a partir do cache
                resultados = []
                for item_cached in cached.get('resultados', []):
                    # Converter matches_texto de dict para OABMatch
                    matches_texto = [
                        OABMatch(**m) for m in item_cached.get('matches_texto', [])
                    ]

                    resultado = ResultadoFiltro(
                        item_id=item_cached['item_id'],
                        relevancia_score=item_cached['relevancia_score'],
                        motivos=item_cached['motivos'],
                        matches_texto=matches_texto,
                        matches_estruturados=item_cached['matches_estruturados'],
                        item_original=item_cached['item_original']
                    )
                    resultados.append(resultado)

                return resultados

            logger.info(f"Cache MISS para: {cache_key}")

        # Executar filtro
        resultados = self.filtrar_items(items, numero_oab, uf_oab)

        # Salvar em cache
        if self.enable_cache and self.cache_manager:
            # Serializar resultados para cache
            resultados_serializaveis = []

            for r in resultados:
                resultado_dict = {
                    'item_id': r.item_id,
                    'relevancia_score': r.relevancia_score,
                    'motivos': r.motivos,
                    'matches_texto': [asdict(m) for m in r.matches_texto],
                    'matches_estruturados': r.matches_estruturados,
                    'item_original': r.item_original
                }
                resultados_serializaveis.append(resultado_dict)

            cache_data = {
                'numero_oab': numero_oab,
                'uf_oab': uf_oab,
                'total_resultados': len(resultados),
                'resultados': resultados_serializaveis
            }

            self.cache_manager.set(cache_key, cache_data, ttl_hours=ttl_hours)
            logger.info(f"Resultados salvos em cache: {cache_key}")

        return resultados

    def gerar_relatorio(
        self,
        resultados: List[ResultadoFiltro]
    ) -> Dict[str, Any]:
        """
        Gera relatório estatístico dos resultados.

        Args:
            resultados: Lista de ResultadoFiltro

        Returns:
            Dict com estatísticas
        """
        if not resultados:
            return {
                'total_resultados': 0,
                'score_medio': 0.0,
                'score_maximo': 0.0,
                'score_minimo': 0.0,
                'distribuicao_scores': {}
            }

        scores = [r.relevancia_score for r in resultados]

        # Distribuição de scores por faixa
        distribuicao = {
            '0.9-1.0 (Alta)': len([s for s in scores if s >= 0.9]),
            '0.7-0.9 (Média-Alta)': len([s for s in scores if 0.7 <= s < 0.9]),
            '0.5-0.7 (Média)': len([s for s in scores if 0.5 <= s < 0.7]),
            '0.3-0.5 (Baixa)': len([s for s in scores if 0.3 <= s < 0.5]),
        }

        return {
            'total_resultados': len(resultados),
            'score_medio': round(sum(scores) / len(scores), 3),
            'score_maximo': round(max(scores), 3),
            'score_minimo': round(min(scores), 3),
            'distribuicao_scores': distribuicao,
            'tribunais': list(set(
                r.item_original.get('siglaTribunal', 'N/A')
                for r in resultados
            ))
        }
