"""
OAB Filter - Sistema de Filtro Profissional para Publicações por OAB

Integra todos os componentes para filtro robusto:
- PDFTextExtractor: Extração multi-estratégia
- CacheManager: Cache inteligente
- OABMatcher: Detecção de padrões OAB
- Scoring de relevância contextual
- Exportação multi-formato

Author: Claude Code (Development Agent)
Version: 1.0.0
"""

import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, asdict, field
from datetime import datetime

from .pdf_text_extractor import PDFTextExtractor, ExtractionStrategy
from .cache_manager import CacheManager
from .oab_matcher import OABMatcher, OABMatch


logger = logging.getLogger(__name__)


@dataclass
class PublicacaoMatch:
    """
    Representa uma publicação que contém OAB(s) de interesse.

    Atributos completos para análise forense e priorização.
    """
    # Identificação
    tribunal: str
    data_publicacao: str  # YYYY-MM-DD
    arquivo_pdf: str  # Path absoluto

    # Matches OAB
    oab_numero: str
    oab_uf: str
    total_mencoes: int  # Quantas vezes essa OAB aparece no documento

    # Contexto
    texto_contexto: str  # 200 chars ao redor da primeira menção
    pagina_numero: Optional[int] = None
    posicao_documento: int = 0  # Posição no texto (0-based)

    # Scoring
    score_relevancia: float = 0.0  # 0.0-1.0
    score_contexto: float = 0.0  # Score do OABMatcher
    score_densidade: float = 0.0  # Baseado em múltiplas menções
    score_posicao: float = 0.0  # Baseado em posição no doc

    # Classificação
    tipo_ato: Optional[str] = None  # "Intimação", "Sentença", "Despacho", etc
    palavras_chave_encontradas: List[str] = field(default_factory=list)

    # Metadata
    extraction_strategy: str = ""
    total_paginas: int = 0
    tamanho_documento_chars: int = 0
    processado_em: str = field(default_factory=lambda: datetime.now().isoformat())

    # Flags
    requer_revisao_manual: bool = False  # OCR ou score baixo
    erro_extracao: bool = False

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return asdict(self)


class OABFilter:
    """
    Filtro profissional de publicações por OAB.

    Processa PDFs de cadernos judiciais e identifica publicações
    relevantes para OABs específicas com alta precisão.

    Usage:
        >>> filter = OABFilter(
        ...     cache_dir=Path("/data/cache"),
        ...     enable_ocr=False
        ... )
        >>> matches = filter.filter_by_oabs(
        ...     pdf_paths=[Path("caderno1.pdf"), Path("caderno2.pdf")],
        ...     target_oabs=[("123456", "SP"), ("789012", "RJ")],
        ...     min_score=0.5
        ... )
        >>> print(f"Found {len(matches)} relevant publications")

    Attributes:
        extractor: PDFTextExtractor para extração de texto
        cache_manager: CacheManager para cache de textos
        matcher: OABMatcher para detecção de OABs
    """

    # Palavras-chave para classificação de tipo de ato
    TIPOS_ATO = {
        'Intimação': ['intima', 'intimação', 'intimado', 'intimada'],
        'Sentença': ['sentença', 'julgo procedente', 'julgo improcedente'],
        'Despacho': ['despacho', 'indefiro', 'defiro'],
        'Decisão': ['decisão', 'decido', 'determino'],
        'Acórdão': ['acórdão', 'acordam'],
        'Audiência': ['audiência', 'designo', 'assinalo'],
        'Citação': ['cita', 'citação', 'citado', 'citada'],
        'Julgamento': ['julgamento', 'julgar'],
    }

    def __init__(
        self,
        cache_dir: Path,
        enable_ocr: bool = False,
        ocr_lang: str = 'por',
        max_age_days: int = 30,
        compress_cache: bool = True
    ):
        """
        Inicializa OABFilter.

        Args:
            cache_dir: Diretório para cache
            enable_ocr: Habilitar OCR como fallback
            ocr_lang: Idioma para OCR
            max_age_days: Idade máxima de cache
            compress_cache: Comprimir cache
        """
        self.cache_dir = Path(cache_dir)

        # Inicializar componentes
        self.extractor = PDFTextExtractor(
            enable_ocr=enable_ocr,
            ocr_lang=ocr_lang
        )

        self.cache_manager = CacheManager(
            cache_dir=cache_dir,
            compress=compress_cache,
            max_age_days=max_age_days
        )

        self.matcher = OABMatcher()

        logger.info(
            f"OABFilter inicializado (OCR={enable_ocr}, cache={cache_dir})"
        )

    def _extract_metadata_from_filename(
        self,
        pdf_path: Path
    ) -> Tuple[str, str]:
        """
        Extrai tribunal e data do nome do arquivo.

        Formato esperado: TJSP_2025-11-13_D.pdf

        Args:
            pdf_path: Path do PDF

        Returns:
            (tribunal, data_publicacao)
        """
        import re

        filename = pdf_path.stem

        # Tentar extrair tribunal e data
        match = re.match(r'([A-Z0-9]+)_(\d{4}-\d{2}-\d{2})_[DE]', filename)

        if match:
            tribunal, data = match.groups()
            return tribunal, data
        else:
            logger.warning(
                f"Nome de arquivo não segue padrão esperado: {filename}"
            )
            return "DESCONHECIDO", "DESCONHECIDA"

    def _classify_tipo_ato(self, texto_contexto: str) -> Optional[str]:
        """
        Classifica tipo de ato baseado em palavras-chave no contexto.

        Args:
            texto_contexto: Texto ao redor da OAB

        Returns:
            Tipo de ato ou None
        """
        texto_lower = texto_contexto.lower()

        for tipo, keywords in self.TIPOS_ATO.items():
            for keyword in keywords:
                if keyword in texto_lower:
                    return tipo

        return None

    def _calculate_density_score(
        self,
        total_mencoes: int,
        tamanho_documento: int
    ) -> float:
        """
        Calcula score de densidade (múltiplas menções = mais relevante).

        Args:
            total_mencoes: Número de vezes que OAB aparece
            tamanho_documento: Tamanho do documento em chars

        Returns:
            Score 0.0-1.0
        """
        if tamanho_documento == 0:
            return 0.0

        # Densidade relativa
        densidade = total_mencoes / (tamanho_documento / 1000)  # Por 1000 chars

        # Normalizar para 0.0-1.0 (densidade > 5 = score máximo)
        score = min(1.0, densidade / 5.0)

        # Bônus por múltiplas menções
        if total_mencoes >= 3:
            score = min(1.0, score + 0.2)
        elif total_mencoes >= 2:
            score = min(1.0, score + 0.1)

        return score

    def _calculate_position_score(
        self,
        posicao: int,
        tamanho_documento: int
    ) -> float:
        """
        Calcula score baseado em posição no documento.

        Publicações no início (cabeçalho, primeiras páginas) são
        geralmente mais relevantes.

        Args:
            posicao: Posição no texto (0-based)
            tamanho_documento: Tamanho total em chars

        Returns:
            Score 0.0-1.0
        """
        if tamanho_documento == 0:
            return 0.5

        # Posição relativa (0.0 = início, 1.0 = fim)
        posicao_relativa = posicao / tamanho_documento

        # Score inversamente proporcional à posição
        # Início (0-20%) = score alto (0.8-1.0)
        # Meio (20-80%) = score médio (0.4-0.8)
        # Fim (80-100%) = score baixo (0.0-0.4)

        if posicao_relativa <= 0.2:
            score = 0.8 + (0.2 * (1.0 - (posicao_relativa / 0.2)))
        elif posicao_relativa <= 0.8:
            score = 0.4 + (0.4 * (1.0 - ((posicao_relativa - 0.2) / 0.6)))
        else:
            score = 0.4 * (1.0 - ((posicao_relativa - 0.8) / 0.2))

        return max(0.0, min(1.0, score))

    def _calculate_final_score(
        self,
        score_contexto: float,
        score_densidade: float,
        score_posicao: float,
        tipo_ato: Optional[str]
    ) -> float:
        """
        Calcula score final de relevância.

        Pesos:
        - Contexto: 40%
        - Densidade: 30%
        - Posição: 20%
        - Tipo de ato: 10%

        Args:
            score_contexto: Score do OABMatcher
            score_densidade: Score de densidade
            score_posicao: Score de posição
            tipo_ato: Tipo de ato classificado

        Returns:
            Score final 0.0-1.0
        """
        score = (
            score_contexto * 0.4 +
            score_densidade * 0.3 +
            score_posicao * 0.2
        )

        # Bônus por tipo de ato identificado
        if tipo_ato:
            score += 0.1

        return min(1.0, score)

    def filter_single_pdf(
        self,
        pdf_path: Path,
        target_oabs: List[Tuple[str, str]],
        min_score: float = 0.5,
        use_cache: bool = True
    ) -> List[PublicacaoMatch]:
        """
        Filtra um único PDF por OABs específicas.

        Args:
            pdf_path: Path para PDF
            target_oabs: Lista de (numero, uf) desejadas
            min_score: Score mínimo para incluir
            use_cache: Usar cache de textos

        Returns:
            Lista de PublicacaoMatch encontrados
        """
        logger.info(f"Processando {pdf_path.name}...")

        # Extrair metadata do nome do arquivo
        tribunal, data_pub = self._extract_metadata_from_filename(pdf_path)

        # Tentar recuperar do cache
        cached_entry = None
        if use_cache:
            cached_entry = self.cache_manager.get(pdf_path)

        # Extrair texto
        if cached_entry:
            logger.debug(f"Usando cache para {pdf_path.name}")
            texto = cached_entry.text
            extraction_strategy = cached_entry.extraction_strategy
            page_count = cached_entry.page_count
        else:
            logger.debug(f"Extraindo texto de {pdf_path.name}")
            result = self.extractor.extract(pdf_path)

            if not result.success:
                logger.error(
                    f"Falha ao extrair texto de {pdf_path.name}: "
                    f"{result.error_message}"
                )
                return []

            texto = result.text
            extraction_strategy = result.strategy.value
            page_count = result.page_count

            # Salvar no cache
            if use_cache:
                self.cache_manager.save(
                    pdf_path=pdf_path,
                    text=texto,
                    extraction_strategy=extraction_strategy,
                    page_count=page_count,
                    metadata=result.metadata
                )

        # Buscar OABs específicas
        oab_matches = self.matcher.filter_by_oabs(
            text=texto,
            target_oabs=target_oabs,
            min_score=min_score * 0.8  # Threshold menor no matcher
        )

        if not oab_matches:
            logger.debug(f"Nenhuma OAB alvo encontrada em {pdf_path.name}")
            return []

        # Criar PublicacaoMatch para cada OAB encontrada
        publicacoes = []

        for oab_match in oab_matches:
            # Contar total de menções dessa OAB
            total_mencoes = texto.lower().count(
                f"{oab_match.numero}/{oab_match.uf}".lower()
            ) + texto.lower().count(
                f"{oab_match.numero}-{oab_match.uf}".lower()
            )

            # Calcular scores
            score_densidade = self._calculate_density_score(
                total_mencoes, len(texto)
            )

            score_posicao = self._calculate_position_score(
                oab_match.posicao_inicio, len(texto)
            )

            # Classificar tipo de ato
            tipo_ato = self._classify_tipo_ato(oab_match.texto_contexto)

            # Score final
            score_final = self._calculate_final_score(
                score_contexto=oab_match.score_contexto,
                score_densidade=score_densidade,
                score_posicao=score_posicao,
                tipo_ato=tipo_ato
            )

            # Verificar threshold final
            if score_final < min_score:
                logger.debug(
                    f"OAB {oab_match.numero}/{oab_match.uf} abaixo do threshold "
                    f"(score={score_final:.2f})"
                )
                continue

            # Criar PublicacaoMatch
            pub_match = PublicacaoMatch(
                tribunal=tribunal,
                data_publicacao=data_pub,
                arquivo_pdf=str(pdf_path.absolute()),
                oab_numero=oab_match.numero,
                oab_uf=oab_match.uf,
                total_mencoes=total_mencoes,
                texto_contexto=oab_match.texto_contexto,
                posicao_documento=oab_match.posicao_inicio,
                score_relevancia=score_final,
                score_contexto=oab_match.score_contexto,
                score_densidade=score_densidade,
                score_posicao=score_posicao,
                tipo_ato=tipo_ato,
                extraction_strategy=extraction_strategy,
                total_paginas=page_count,
                tamanho_documento_chars=len(texto),
                requer_revisao_manual=(
                    extraction_strategy == ExtractionStrategy.OCR.value or
                    score_final < 0.6
                ),
                erro_extracao=False
            )

            publicacoes.append(pub_match)

        logger.info(
            f"Encontradas {len(publicacoes)} publicações relevantes em "
            f"{pdf_path.name}"
        )

        return publicacoes

    def filter_by_oabs(
        self,
        pdf_paths: List[Path],
        target_oabs: List[Tuple[str, str]],
        min_score: float = 0.5,
        use_cache: bool = True,
        sort_by_score: bool = True
    ) -> List[PublicacaoMatch]:
        """
        Filtra múltiplos PDFs por OABs específicas.

        Args:
            pdf_paths: Lista de paths para PDFs
            target_oabs: Lista de (numero, uf) desejadas
            min_score: Score mínimo de relevância (0.0-1.0)
            use_cache: Usar cache de textos
            sort_by_score: Ordenar por score descendente

        Returns:
            Lista de PublicacaoMatch consolidada
        """
        logger.info(
            f"Filtrando {len(pdf_paths)} PDFs por {len(target_oabs)} OABs"
        )

        all_matches = []

        for pdf_path in pdf_paths:
            try:
                matches = self.filter_single_pdf(
                    pdf_path=pdf_path,
                    target_oabs=target_oabs,
                    min_score=min_score,
                    use_cache=use_cache
                )
                all_matches.extend(matches)

            except Exception as e:
                logger.error(f"Erro ao processar {pdf_path.name}: {e}")
                continue

        # Ordenar se solicitado
        if sort_by_score:
            all_matches.sort(key=lambda m: m.score_relevancia, reverse=True)

        logger.info(
            f"Filtro concluído: {len(all_matches)} publicações relevantes "
            f"em {len(pdf_paths)} PDFs"
        )

        return all_matches

    def get_cache_stats(self):
        """Retorna estatísticas de cache."""
        return self.cache_manager.get_stats()

    def invalidate_cache(self, older_than_days: Optional[int] = None) -> int:
        """Invalida cache antigo."""
        return self.cache_manager.invalidate_old(older_than_days)


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) < 2:
        print("Uso: python oab_filter.py <pdf1> [pdf2] ...")
        sys.exit(1)

    # Criar filtro
    cache_dir = Path("/tmp/oab_filter_cache")
    filter_obj = OABFilter(cache_dir=cache_dir, enable_ocr=False)

    # PDFs para processar
    pdf_paths = [Path(p) for p in sys.argv[1:]]

    # OABs de interesse (exemplo)
    target_oabs = [
        ('123456', 'SP'),
        ('789012', 'RJ'),
    ]

    print("\n" + "=" * 70)
    print("OAB FILTER - Sistema Profissional de Filtro")
    print("=" * 70)
    print(f"\nProcessando {len(pdf_paths)} PDFs...")
    print(f"Buscando {len(target_oabs)} OABs: {target_oabs}\n")

    # Executar filtro
    matches = filter_obj.filter_by_oabs(
        pdf_paths=pdf_paths,
        target_oabs=target_oabs,
        min_score=0.5
    )

    # Exibir resultados
    print("\n" + "=" * 70)
    print(f"RESULTADOS: {len(matches)} publicações encontradas")
    print("=" * 70)

    for i, match in enumerate(matches[:10], 1):  # Mostrar top 10
        print(f"\n{i}. OAB {match.oab_numero}/{match.oab_uf}")
        print(f"   Score: {match.score_relevancia:.2f}")
        print(f"   Tribunal: {match.tribunal}")
        print(f"   Data: {match.data_publicacao}")
        print(f"   Tipo: {match.tipo_ato or 'N/A'}")
        print(f"   Menções: {match.total_mencoes}")
        print(f"   Contexto: {match.texto_contexto[:100]}...")

    # Estatísticas de cache
    print("\n" + "=" * 70)
    print("CACHE STATS")
    print("=" * 70)
    stats = filter_obj.get_cache_stats()
    print(stats)
