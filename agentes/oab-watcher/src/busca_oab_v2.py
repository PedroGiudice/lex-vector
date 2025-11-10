"""
Busca OAB v2 - Nova implementação com BuscaInteligente + Cache + Paginação

Migrado de busca_oab.py para usar sistema state-of-the-art.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

from .api_client import DJENClient
from .cache_manager import CacheManager
from .busca_inteligente import BuscaInteligente, ResultadoFiltro
from .models import RespostaBuscaOAB
from .utils import formatar_oab

logger = logging.getLogger(__name__)


class BuscaOABv2:
    """
    Gerenciador de buscas por número OAB - Versão 2.

    Features:
    - Cache inteligente (SQLite + gzip)
    - Filtro multi-camada (regex + estruturado)
    - Paginação automática
    - Scoring de relevância
    - Estatísticas detalhadas
    """

    def __init__(self, config: Dict):
        """
        Inicializa BuscaOABv2.

        Args:
            config: Dict de configuração (config.json)
        """
        self.config = config
        self.client = DJENClient(config)

        # Configurar diretórios
        self.data_root = Path(config['paths']['data_root'])
        self.output_dir = self.data_root / config['paths']['downloads_busca']
        self.cache_dir = self.data_root / "cache"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Inicializar cache
        self.cache_manager = CacheManager(
            cache_dir=self.cache_dir,
            default_ttl_hours=24,
            enable_compression=True
        )

        # Inicializar busca inteligente
        self.busca_inteligente = BuscaInteligente(
            cache_manager=self.cache_manager,
            threshold_relevancia=0.3,
            enable_cache=True
        )

        logger.info("BuscaOABv2 inicializada com cache e busca inteligente")

    def buscar(
        self,
        numero_oab: str,
        uf_oab: str,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        tribunal: Optional[str] = None,
        usar_paginacao: bool = True,
        max_items: Optional[int] = None
    ) -> Dict:
        """
        Busca publicações por número de OAB.

        Args:
            numero_oab: Número da OAB (ex: "129021")
            uf_oab: UF da OAB (ex: "SP")
            data_inicio: Data início (formato: YYYY-MM-DD)
            data_fim: Data fim (formato: YYYY-MM-DD)
            tribunal: Sigla tribunal (opcional, ex: "TJSP")
            usar_paginacao: Se True, busca todas as páginas (default: True)
            max_items: Máximo de items a buscar da API (None = sem limite)

        Returns:
            Dict com resultado processado e estatísticas
        """
        # Validar inputs
        if not numero_oab or not uf_oab:
            raise ValueError("numero_oab e uf_oab são obrigatórios")

        oab_formatada = formatar_oab(numero_oab, uf_oab)

        logger.info(f"="*70)
        logger.info(f"BUSCA OAB: {oab_formatada}")
        logger.info(f"="*70)

        if data_inicio and data_fim:
            logger.info(f"Período: {data_inicio} a {data_fim}")
        if tribunal:
            logger.info(f"Tribunal: {tribunal}")
        if usar_paginacao:
            logger.info(f"Paginação: ATIVADA (max_items={max_items or 'ilimitado'})")

        # Montar params da API
        params = {}
        if data_inicio:
            params['data_inicio'] = data_inicio
        if data_fim:
            params['data_fim'] = data_fim
        if tribunal:
            params['siglaTribunal'] = tribunal.upper()

        # Buscar items da API
        try:
            if usar_paginacao:
                logger.info("Iniciando busca com paginação...")
                all_items = self.client.get_all_pages(
                    endpoint='/api/v1/comunicacao',
                    params=params,
                    page_size=100,
                    max_items=max_items,
                    show_progress=True
                )
                total_api = len(all_items)
            else:
                logger.info("Buscando primeira página apenas...")
                response = self.client.get('/api/v1/comunicacao', params)
                all_items = response.get('items', [])
                total_api = len(all_items)

            logger.info(f"Total de items obtidos da API: {total_api}")

            # Aplicar filtro inteligente
            logger.info("Aplicando filtro inteligente...")
            resultados_filtrados = self.busca_inteligente.buscar_com_cache(
                items=all_items,
                numero_oab=numero_oab,
                uf_oab=uf_oab,
                data_inicio=data_inicio,
                data_fim=data_fim,
                ttl_hours=24
            )

            logger.info(f"Items relevantes após filtro: {len(resultados_filtrados)}")

            # Gerar estatísticas
            stats = self.busca_inteligente.gerar_relatorio(resultados_filtrados)

            # Extrair tribunais únicos
            tribunais = stats.get('tribunais', [])

            # Converter ResultadoFiltro para formato serializável
            items_serializaveis = [
                {
                    **r.item_original,
                    '_relevancia_score': r.relevancia_score,
                    '_motivos': r.motivos
                }
                for r in resultados_filtrados
            ]

            # Montar resultado final
            resultado = {
                "oab": oab_formatada,
                "numero_oab": numero_oab,
                "uf_oab": uf_oab.upper(),
                "data_busca": datetime.now().isoformat(),
                "filtros_aplicados": {
                    "data_inicio": data_inicio,
                    "data_fim": data_fim,
                    "tribunal": tribunal,
                    "paginacao": usar_paginacao,
                    "max_items": max_items
                },
                "total_api": total_api,
                "total_publicacoes": len(resultados_filtrados),
                "tribunais": tribunais,
                "estatisticas": stats,
                "items": items_serializaveis,
                "cache_info": self.cache_manager.get_stats() if self.cache_manager else {}
            }

            # Salvar JSON
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"oab_{uf_oab}_{numero_oab}_{timestamp}.json"
            output_file = self.output_dir / filename

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2)

            resultado['arquivo_json'] = str(output_file)

            # Log final
            logger.info("="*70)
            logger.info(f"BUSCA CONCLUÍDA: {oab_formatada}")
            logger.info(f"Total API: {total_api}")
            logger.info(f"Relevantes: {len(resultados_filtrados)} ({len(resultados_filtrados)/total_api*100:.1f}%)")
            logger.info(f"Score médio: {stats.get('score_medio', 0):.2f}")
            logger.info(f"Tribunais: {', '.join(tribunais)}")
            logger.info(f"Arquivo: {output_file}")
            logger.info("="*70)

            return resultado

        except Exception as e:
            logger.error(f"Erro na busca: {e}", exc_info=True)
            raise

    def buscar_multiplas_oabs(
        self,
        oabs: List[tuple],
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        usar_paginacao: bool = True
    ) -> List[Dict]:
        """
        Busca publicações para múltiplas OABs.

        Args:
            oabs: Lista de tuplas (numero, uf). Ex: [("129021", "SP"), ("234567", "RJ")]
            data_inicio: Data início
            data_fim: Data fim
            usar_paginacao: Se True, busca todas as páginas

        Returns:
            Lista de resultados (um Dict por OAB)
        """
        resultados = []

        logger.info(f"="*70)
        logger.info(f"BUSCA MÚLTIPLA: {len(oabs)} OABs")
        logger.info(f"="*70)

        for i, (numero, uf) in enumerate(oabs, 1):
            logger.info(f"\n[{i}/{len(oabs)}] Processando {formatar_oab(numero, uf)}...")

            try:
                resultado = self.buscar(
                    numero_oab=numero,
                    uf_oab=uf,
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    usar_paginacao=usar_paginacao
                )
                resultados.append(resultado)

            except Exception as e:
                logger.error(f"Erro ao buscar {formatar_oab(numero, uf)}: {e}")
                continue

        logger.info(f"\n{'='*70}")
        logger.info(f"BUSCA MÚLTIPLA CONCLUÍDA: {len(resultados)}/{len(oabs)} sucessos")
        logger.info(f"{'='*70}")

        return resultados

    def limpar_cache(self, pattern: Optional[str] = None) -> int:
        """
        Limpa cache (útil para forçar reprocessamento).

        Args:
            pattern: Pattern SQL LIKE (ex: "busca_129021_%") ou None para limpar tudo

        Returns:
            Número de items removidos
        """
        if pattern:
            return self.cache_manager.invalidate_pattern(pattern)
        else:
            return self.cache_manager.clear_all()

    def estatisticas_cache(self) -> Dict:
        """Retorna estatísticas do cache."""
        return self.cache_manager.get_stats()
