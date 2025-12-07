"""
ESTÁGIO 1: O CARTÓGRAFO (Layout Analysis)

Analisa a estrutura de páginas do PDF usando histograma de densidade de caracteres.
Detecta tarjas laterais (PJe/e-SAJ) e classifica páginas como NATIVE ou RASTER_NEEDED.

Algoritmo:
1. Para cada página, extrai char objects via pdfplumber
2. Cria histograma de densidade no eixo X (largura da página)
3. Detecta picos de densidade nos extremos (tarja lateral)
4. Define safe_bbox excluindo zonas de ruído
5. Classifica tipo de página baseado em quantidade de texto extraível

Output: outputs/{doc_id}/layout.json
"""

import json
import sys
from pathlib import Path
from typing import Literal

import pdfplumber

# Adiciona o diretório raiz ao PYTHONPATH quando executado como script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

from src.config import (
    LAYOUT_CONFIG,
    LayoutConfig,
    PageType,
    PageComplexity,
    COMPLEXITY_ENGINE_MAP,
    RASTER_QUALITY_THRESHOLDS,
    RasterQualityThresholds,
    get_output_dir,
)


class LayoutAnalyzer:
    """
    Analisador de layout de PDFs usando histograma de densidade.

    Detecta tarjas laterais (PJe, e-SAJ) e classifica páginas para
    determinar qual estratégia de extração usar (nativa ou OCR).
    """

    def __init__(
        self,
        config: LayoutConfig = LAYOUT_CONFIG,
        quality_thresholds: RasterQualityThresholds = RASTER_QUALITY_THRESHOLDS
    ):
        """
        Inicializa o analisador.

        Args:
            config: Configuração de layout (thresholds, bins, etc)
            quality_thresholds: Thresholds para classificação de qualidade raster
        """
        self.config = config
        self.quality_thresholds = quality_thresholds

    def analyze(self, pdf_path: Path) -> dict:
        """
        Analisa layout de todas as páginas do PDF.

        Args:
            pdf_path: Caminho para o arquivo PDF

        Returns:
            Dict com estrutura:
            {
                "doc_id": "nome_arquivo",
                "total_pages": 10,
                "pages": [
                    {
                        "page_num": 1,
                        "type": "NATIVE",
                        "safe_bbox": [x0, y0, x1, y1],
                        "has_tarja": False,
                        "char_count": 1234
                    },
                    ...
                ]
            }

        Raises:
            FileNotFoundError: Se PDF não existe
            ValueError: Se PDF está corrompido ou vazio
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

        doc_id = pdf_path.stem
        pages_data = []

        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) == 0:
                raise ValueError(f"PDF vazio: {pdf_path}")

            for page_num, page in enumerate(pdf.pages, start=1):
                page_data = self._analyze_page(page, page_num)
                pages_data.append(page_data)

        layout = {
            "doc_id": doc_id,
            "total_pages": len(pages_data),
            "pages": pages_data,
        }

        return layout

    def _analyze_page(self, page, page_num: int) -> dict:
        """
        Analisa uma página individual do PDF.

        Args:
            page: Objeto Page do pdfplumber
            page_num: Número da página (1-indexed)

        Returns:
            Dict com dados da página:
            {
                "page_num": 1,
                "type": "NATIVE" | "RASTER_NEEDED",
                "complexity": "native_clean" | "raster_dirty" | etc,
                "recommended_engine": "pdfplumber" | "tesseract" | "marker",
                "needs_cleaning": bool,
                "cleaning_reason": list[str] (opcional),
                "safe_bbox": [x0, y0, x1, y1],
                "has_tarja": bool,
                "tarja_x_cut": float | None,
                "char_count": int
            }
        """
        chars = page.chars
        page_width = page.width
        page_height = page.height

        # Detecta tarja lateral via histograma de densidade
        has_tarja, tarja_x_cut = self._detect_tarja(chars, page_width)

        # Define safe_bbox (área útil excluindo tarja)
        if has_tarja and tarja_x_cut is not None:
            safe_bbox = [
                0,
                0,
                tarja_x_cut - self.config.safe_margin_px,
                page_height,
            ]
        else:
            safe_bbox = [0, 0, page_width, page_height]

        # Conta caracteres na safe_bbox
        char_count = sum(
            1
            for char in chars
            if (
                safe_bbox[0] <= char["x0"] <= safe_bbox[2]
                and safe_bbox[1] <= char["top"] <= safe_bbox[3]
            )
        )

        # Classifica tipo de página
        if char_count >= self.config.min_text_chars:
            page_type = PageType.NATIVE
        else:
            page_type = PageType.RASTER_NEEDED

        # Monta resultado base
        page_data = {
            "page_num": page_num,
            "type": page_type,
            "safe_bbox": safe_bbox,
            "has_tarja": has_tarja,
            "char_count": char_count,
        }

        if has_tarja and tarja_x_cut is not None:
            page_data["tarja_x_cut"] = tarja_x_cut

        # === NOVA FUNCIONALIDADE: Classificação de complexidade ===

        # Estimar qualidade para páginas RASTER
        quality_metrics = None
        if page_type == PageType.RASTER_NEEDED:
            quality_metrics = self._estimate_raster_quality(
                page, safe_bbox, char_count
            )

        # Classificar complexidade
        complexity = self._classify_complexity(page_data, quality_metrics)
        page_data["complexity"] = complexity

        # Recomendar engine baseado em complexidade
        recommended_engine = COMPLEXITY_ENGINE_MAP.get(complexity, "pdfplumber")
        page_data["recommended_engine"] = recommended_engine

        # Determinar se precisa limpeza
        cleaning_reasons = []
        needs_cleaning = False

        if has_tarja:
            cleaning_reasons.append("lateral_stripe_detected")
            needs_cleaning = True

        if quality_metrics:
            if quality_metrics.get("has_watermark", False):
                cleaning_reasons.append("watermark_detected")
                needs_cleaning = True

            if quality_metrics.get("contrast_score", 1.0) < self.quality_thresholds.low_contrast_threshold:
                cleaning_reasons.append("low_contrast")
                needs_cleaning = True

            if quality_metrics.get("noise_level", 0.0) > self.quality_thresholds.high_noise_threshold:
                cleaning_reasons.append("high_noise")
                needs_cleaning = True

        page_data["needs_cleaning"] = needs_cleaning
        if cleaning_reasons:
            page_data["cleaning_reason"] = cleaning_reasons

        return page_data

    def _detect_tarja(
        self, chars: list, page_width: float
    ) -> tuple[bool, float | None]:
        """
        Detecta tarja lateral via histograma de densidade no eixo X.

        Algoritmo:
        1. Constrói histograma de densidade de caracteres
        2. Calcula threshold: % de chars nos últimos X% da largura
        3. Se threshold excedido = tarja detectada
        4. Retorna posição x_cut para excluir tarja

        Args:
            chars: Lista de char objects do pdfplumber
            page_width: Largura total da página em pontos

        Returns:
            Tupla (has_tarja, x_cut):
            - has_tarja: True se tarja detectada
            - x_cut: Posição X onde cortar (None se sem tarja)
        """
        if not chars:
            return False, None

        # Constrói histograma de densidade
        histogram = self._build_histogram(
            chars, page_width, self.config.histogram_bins
        )

        # Calcula zona de tarja (últimos X% da largura)
        tarja_zone_start_bin = int(
            self.config.histogram_bins * (1 - self.config.tarja_zone_percent)
        )

        # Conta chars na zona de tarja
        tarja_chars = sum(histogram[tarja_zone_start_bin:])
        total_chars = sum(histogram)

        if total_chars == 0:
            return False, None

        # Calcula densidade relativa
        tarja_density = tarja_chars / total_chars

        # Detecta tarja se densidade > threshold
        if tarja_density >= self.config.tarja_density_threshold:
            # Usa detecção adaptativa ou percentual fixo
            if self.config.use_adaptive_cut:
                # Encontra boundary real entre texto e tarja
                x_cut = self._find_content_boundary(chars, page_width)
            else:
                # Fallback: corte percentual fixo (comportamento antigo)
                x_cut = page_width * (1 - self.config.tarja_zone_percent)
            return True, x_cut
        else:
            return False, None

    def _build_histogram(
        self, chars: list, page_width: float, bins: int
    ) -> list[int]:
        """
        Constrói histograma de densidade de caracteres no eixo X.

        Divide a largura da página em N bins e conta quantos caracteres
        caem em cada bin baseado em sua posição X.

        Args:
            chars: Lista de char objects do pdfplumber
            page_width: Largura total da página em pontos
            bins: Número de bins do histograma

        Returns:
            Lista de tamanho `bins` com contagem de chars por bin
        """
        histogram = [0] * bins
        bin_width = page_width / bins

        for char in chars:
            # Posição X do caractere (centro)
            char_x = (char["x0"] + char["x1"]) / 2

            # Calcula qual bin pertence
            bin_idx = int(char_x / bin_width)

            # Garante que não ultrapasse limites
            bin_idx = min(bin_idx, bins - 1)
            bin_idx = max(bin_idx, 0)

            histogram[bin_idx] += 1

        return histogram

    def _find_content_boundary(
        self, chars: list, page_width: float
    ) -> float:
        """
        Encontra onde o texto LEGÍTIMO termina (não incluindo tarja).

        Usa detecção de gaps: procura espaços vazios significativos entre
        o corpo do texto e a tarja lateral.

        Algoritmo:
        1. Coleta posições x1 (fim) de todos os caracteres
        2. Agrupa por proximidade
        3. Encontra gap significativo na zona de tarja
        4. Retorna boundary = posição antes do gap

        Args:
            chars: Lista de char objects do pdfplumber
            page_width: Largura total da página em pontos

        Returns:
            Posição X onde o conteúdo legítimo termina
        """
        if not chars:
            return page_width

        # Coleta posições x1 (fim do caractere) - onde o texto realmente termina
        x_ends = sorted([c["x1"] for c in chars])

        if not x_ends:
            return page_width

        # Zona onde procurar gaps (últimos X% da página)
        gap_search_start = page_width * (1 - self.config.gap_search_zone_percent)

        # Procura gaps significativos na zona de tarja
        best_boundary = max(x_ends)  # fallback: maior x1

        for i in range(len(x_ends) - 1):
            current_x = x_ends[i]
            next_x = x_ends[i + 1]
            gap = next_x - current_x

            # Se encontramos um gap significativo na zona de busca
            if (
                gap >= self.config.content_gap_threshold
                and current_x >= gap_search_start
            ):
                # Este é provavelmente o fim do conteúdo legítimo
                best_boundary = current_x
                break

        return best_boundary

    def _has_judicial_artifacts(self, page_data: dict) -> bool:
        """
        Detecta presença de artefatos judiciais (tarjas, carimbos, marcas d'água).

        Args:
            page_data: Dict com dados da página (retorno de _analyze_page)

        Returns:
            True se possui artefatos judiciais (tarja lateral, etc)
        """
        # Por enquanto, considera apenas detecção de tarja
        # TODO: Expandir para detectar carimbos e marcas d'água via análise de imagem
        return page_data.get("has_tarja", False)

    def _estimate_raster_quality(
        self, page, safe_bbox: list, char_count: int
    ) -> dict:
        """
        Estima qualidade de uma página rasterizada.

        Args:
            page: Objeto Page do pdfplumber
            safe_bbox: Bounding box seguro [x0, y0, x1, y1]
            char_count: Número de caracteres extraídos

        Returns:
            Dict com métricas de qualidade:
            {
                "contrast_score": float (0.0-1.0),
                "noise_level": float (0.0-1.0),
                "char_density": float,
                "has_watermark": bool
            }
        """
        # NOTA: Esta é uma implementação placeholder que retorna valores default
        # Para implementação completa, seria necessário:
        # 1. Renderizar página como imagem (via pdf2image ou similar)
        # 2. Calcular histograma de intensidade -> contrast_score
        # 3. Calcular variância local de pixels -> noise_level
        # 4. Detectar padrões repetitivos -> has_watermark

        # Por enquanto, usa heurística baseada apenas em char_count
        bbox_area = (safe_bbox[2] - safe_bbox[0]) * (safe_bbox[3] - safe_bbox[1])
        char_density = char_count / bbox_area if bbox_area > 0 else 0.0

        # Heurística simples: páginas com poucos chars podem ser degradadas
        if char_density < 0.0001:  # Muito poucos chars
            return {
                "contrast_score": 0.3,  # Baixo contraste presumido
                "noise_level": 0.7,     # Alto ruído presumido
                "char_density": char_density,
                "has_watermark": False  # Não detectável sem análise de imagem
            }
        else:
            return {
                "contrast_score": 0.85,  # Contraste razoável presumido
                "noise_level": 0.3,      # Baixo ruído presumido
                "char_density": char_density,
                "has_watermark": False
            }

    def _classify_complexity(
        self, page_data: dict, quality_metrics: dict | None = None
    ) -> str:
        """
        Classifica complexidade da página com granularidade.

        Args:
            page_data: Dict com dados da página (retorno de _analyze_page)
            quality_metrics: Métricas de qualidade raster (opcional)

        Returns:
            String de PageComplexity (ex: "native_clean", "raster_dirty")
        """
        page_type = page_data["type"]

        # NATIVE pages: verificar artefatos judiciais
        if page_type == PageType.NATIVE:
            if self._has_judicial_artifacts(page_data):
                return PageComplexity.NATIVE_WITH_ARTIFACTS
            return PageComplexity.NATIVE_CLEAN

        # RASTER_NEEDED pages: classificar por qualidade
        if quality_metrics is None:
            # Fallback: se não há métricas, assume RASTER_DIRTY como default
            return PageComplexity.RASTER_DIRTY

        contrast = quality_metrics.get("contrast_score", 0.5)
        noise = quality_metrics.get("noise_level", 0.5)
        has_watermark = quality_metrics.get("has_watermark", False)

        # RASTER_CLEAN: alto contraste e sem artefatos
        if (
            contrast > self.quality_thresholds.high_contrast_threshold
            and not has_watermark
        ):
            return PageComplexity.RASTER_CLEAN

        # RASTER_DEGRADED: baixo contraste ou muito ruído
        if (
            contrast < self.quality_thresholds.low_contrast_threshold
            or noise > self.quality_thresholds.high_noise_threshold
        ):
            return PageComplexity.RASTER_DEGRADED

        # RASTER_DIRTY: caso intermediário (marca d'água, ruído moderado)
        return PageComplexity.RASTER_DIRTY

    def save(self, layout: dict, output_path: Path) -> None:
        """
        Salva layout.json no disco.

        Args:
            layout: Dict retornado por analyze()
            output_path: Caminho completo para salvar (ex: outputs/doc/layout.json)
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(layout, f, indent=2, ensure_ascii=False)


# =============================================================================
# CLI (TYPER)
# =============================================================================

if __name__ == "__main__":
    import typer

    app = typer.Typer(
        help="ESTÁGIO 1: Análise de layout de PDFs (O Cartógrafo)"
    )

    @app.command()
    def main(
        pdf_path: Path = typer.Argument(
            ..., help="Caminho para o arquivo PDF", exists=True
        ),
        output_dir: Path = typer.Option(
            None,
            "--output-dir",
            "-o",
            help="Diretório de saída (padrão: outputs/{doc_id})",
        ),
    ):
        """
        Analisa layout de um PDF e salva layout.json.

        Exemplos:
            python step_01_layout.py inputs/processo.pdf
            python step_01_layout.py inputs/processo.pdf -o custom_output/
        """
        # Resolve paths
        pdf_path = pdf_path.resolve()

        # Define output_dir
        if output_dir is None:
            output_dir = get_output_dir(pdf_path.stem)
        else:
            output_dir = output_dir.resolve()

        # Executa análise
        typer.echo(f"📊 Analisando layout: {pdf_path.name}")

        analyzer = LayoutAnalyzer()
        layout = analyzer.analyze(pdf_path)

        # Salva resultado
        layout_path = output_dir / "layout.json"
        analyzer.save(layout, layout_path)

        # Relatório
        typer.echo(f"✅ Layout salvo: {layout_path}")
        typer.echo(f"📄 Total de páginas: {layout['total_pages']}")

        # Estatísticas
        native_count = sum(
            1 for p in layout["pages"] if p["type"] == PageType.NATIVE
        )
        raster_count = sum(
            1 for p in layout["pages"] if p["type"] == PageType.RASTER_NEEDED
        )
        tarja_count = sum(1 for p in layout["pages"] if p["has_tarja"])

        typer.echo(f"  • NATIVE: {native_count} páginas")
        typer.echo(f"  • RASTER_NEEDED: {raster_count} páginas")
        typer.echo(f"  • Com tarja: {tarja_count} páginas")

        # Estatísticas de complexidade
        typer.echo("\n📊 Complexidade:")
        complexity_counts = {}
        for page in layout["pages"]:
            complexity = page.get("complexity", "unknown")
            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1

        for complexity, count in sorted(complexity_counts.items()):
            typer.echo(f"  • {complexity}: {count} páginas")

        # Estatísticas de engines recomendados
        typer.echo("\n🔧 Engines recomendados:")
        engine_counts = {}
        for page in layout["pages"]:
            engine = page.get("recommended_engine", "unknown")
            engine_counts[engine] = engine_counts.get(engine, 0) + 1

        for engine, count in sorted(engine_counts.items()):
            typer.echo(f"  • {engine}: {count} páginas")

        # Páginas que precisam limpeza
        needs_cleaning_count = sum(
            1 for p in layout["pages"] if p.get("needs_cleaning", False)
        )
        typer.echo(f"\n🧹 Páginas que precisam limpeza: {needs_cleaning_count}")

    app()
