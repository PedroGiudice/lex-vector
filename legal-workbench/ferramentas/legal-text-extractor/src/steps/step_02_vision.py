"""
Step 02: Vision Pipeline (O Saneador)

Processa páginas RASTER_NEEDED do PDF usando pipeline OpenCV:
1. Renderiza página como imagem (pdf2image)
2. Aplica crop usando safe_bbox do layout
3. Pipeline de limpeza:
   - Grayscale conversion
   - Otsu thresholding
   - Denoise (fastNlMeansDenoising)
4. Salva imagem processada para OCR

Input:  layout.json + PDF original
Output: Imagens limpas em outputs/{doc_id}/images/page_XXX.png
"""

import json
import logging
import sys
from pathlib import Path
from typing import NamedTuple

# Adiciona o diretório raiz ao PYTHONPATH quando executado como script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

import cv2
import numpy as np
from pdf2image import convert_from_path

from src.config import VISION_CONFIG, VisionConfig, get_images_dir, PageType


# =============================================================================
# LOGGING
# =============================================================================

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class PageLayout(NamedTuple):
    """Layout de uma página extraído do layout.json."""
    page_num: int
    type: str  # "NATIVE" ou "RASTER_NEEDED"
    safe_bbox: tuple[float, float, float, float]  # (x0, y0, x1, y1)
    has_tarja: bool
    text_chars: int


class ProcessedImage(NamedTuple):
    """Resultado do processamento de uma imagem."""
    page_num: int
    output_path: Path
    width: int
    height: int


# =============================================================================
# VISION PROCESSOR
# =============================================================================

class VisionProcessor:
    """
    Processa páginas RASTER_NEEDED usando pipeline OpenCV.

    Pipeline:
    1. Renderiza PDF page -> numpy array (pdf2image)
    2. Aplica crop usando safe_bbox
    3. Grayscale conversion
    4. Otsu thresholding (binarização automática)
    5. Denoise (remove ruído de scans antigos)
    6. Salva imagem processada
    """

    def __init__(self, config: VisionConfig = VISION_CONFIG):
        self.config = config

    def process(self, layout_path: Path, pdf_path: Path, doc_id: str) -> list[ProcessedImage]:
        """
        Processa todas as páginas RASTER_NEEDED de um PDF.

        Args:
            layout_path: Caminho para layout.json (output do step_01)
            pdf_path: Caminho para PDF original
            doc_id: ID do documento (para diretório de output)

        Returns:
            Lista de ProcessedImage com metadados das imagens geradas

        Raises:
            FileNotFoundError: Se layout.json ou PDF não existirem
            ValueError: Se layout.json estiver malformado
        """
        if not layout_path.exists():
            raise FileNotFoundError(f"Layout não encontrado: {layout_path}")

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

        # Carrega layout
        logger.info(f"Carregando layout de {layout_path}")
        with open(layout_path) as f:
            layout_data = json.load(f)

        # Extrai páginas que precisam de processamento
        pages_to_process = self._filter_raster_pages(layout_data)

        if not pages_to_process:
            logger.info("Nenhuma página RASTER_NEEDED encontrada")
            return []

        logger.info(f"Processando {len(pages_to_process)} páginas RASTER_NEEDED")

        # Processa cada página
        results = []
        for page_layout in pages_to_process:
            try:
                processed = self._process_page(
                    pdf_path=pdf_path,
                    page_layout=page_layout,
                    doc_id=doc_id
                )
                results.append(processed)
                logger.info(
                    f"Página {page_layout.page_num}: "
                    f"{processed.width}x{processed.height}px -> {processed.output_path.name}"
                )
            except Exception as e:
                logger.error(f"Erro ao processar página {page_layout.page_num}: {e}")
                # Continua processando outras páginas

        logger.info(f"Processamento concluído: {len(results)} imagens geradas")
        return results

    def _filter_raster_pages(self, layout_data: dict) -> list[PageLayout]:
        """
        Filtra páginas que precisam de processamento (type == RASTER_NEEDED).

        Args:
            layout_data: Dados do layout.json

        Returns:
            Lista de PageLayout para páginas RASTER_NEEDED
        """
        pages = []

        for page_data in layout_data.get("pages", []):
            if page_data.get("type") == PageType.RASTER_NEEDED:
                pages.append(PageLayout(
                    page_num=page_data["page_num"],
                    type=page_data["type"],
                    safe_bbox=tuple(page_data["safe_bbox"]),
                    has_tarja=page_data.get("has_tarja", False),
                    text_chars=page_data.get("text_chars", 0)
                ))

        return pages

    def _process_page(
        self,
        pdf_path: Path,
        page_layout: PageLayout,
        doc_id: str
    ) -> ProcessedImage:
        """
        Processa uma única página: renderiza, crop, pipeline OpenCV, salva.

        Args:
            pdf_path: Caminho para PDF
            page_layout: Layout da página
            doc_id: ID do documento

        Returns:
            ProcessedImage com metadados
        """
        # 1. Renderiza página
        logger.debug(f"Renderizando página {page_layout.page_num}")
        image = self._render_page(pdf_path, page_layout.page_num, page_layout.safe_bbox)

        # 2. Aplica pipeline OpenCV
        logger.debug(f"Aplicando pipeline OpenCV")
        processed = self._apply_pipeline(image)

        # 3. Salva imagem
        output_path = self._get_output_path(doc_id, page_layout.page_num)
        self._save_image(processed, output_path)

        return ProcessedImage(
            page_num=page_layout.page_num,
            output_path=output_path,
            width=processed.shape[1],
            height=processed.shape[0]
        )

    def _render_page(
        self,
        pdf_path: Path,
        page_num: int,
        safe_bbox: tuple[float, float, float, float]
    ) -> np.ndarray:
        """
        Renderiza uma página do PDF como imagem numpy e aplica crop.

        Args:
            pdf_path: Caminho para PDF
            page_num: Número da página (1-indexed)
            safe_bbox: Bounding box segura (x0, y0, x1, y1) em pontos PDF

        Returns:
            Imagem numpy (BGR) com crop aplicado

        Nota:
            pdf2image usa 1-indexed pages
            safe_bbox está em pontos PDF (72 DPI), precisa converter para pixels
        """
        # Renderiza página inteira
        images = convert_from_path(
            pdf_path,
            dpi=self.config.render_dpi,
            first_page=page_num,
            last_page=page_num
        )

        if not images:
            raise ValueError(f"Falha ao renderizar página {page_num}")

        # Converte PIL Image -> numpy array (RGB)
        pil_image = images[0]
        image = np.array(pil_image)

        # Converte RGB -> BGR (OpenCV padrão)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Aplica crop usando safe_bbox
        # Converte pontos PDF (72 DPI) -> pixels (render_dpi)
        scale = self.config.render_dpi / 72.0
        x0, y0, x1, y1 = safe_bbox

        # Coordenadas em pixels
        px0 = int(x0 * scale)
        py0 = int(y0 * scale)
        px1 = int(x1 * scale)
        py1 = int(y1 * scale)

        # Crop (numpy slicing: y primeiro, depois x)
        cropped = image[py0:py1, px0:px1]

        logger.debug(
            f"Crop aplicado: bbox PDF={safe_bbox} -> "
            f"pixels=({px0}, {py0}, {px1}, {py1}) -> "
            f"shape={cropped.shape}"
        )

        return cropped

    def _apply_pipeline(self, image: np.ndarray) -> np.ndarray:
        """
        Aplica pipeline OpenCV: grayscale -> otsu -> denoise.

        Pipeline:
        1. Grayscale: Reduz dimensionalidade (3 canais -> 1)
        2. Otsu Threshold: Binarização automática (separa texto/fundo)
        3. Denoise: Remove ruído de scans antigos

        Args:
            image: Imagem BGR (numpy array)

        Returns:
            Imagem processada (grayscale, 1 canal)
        """
        # 1. Grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 2. Otsu Thresholding
        # cv2.THRESH_OTSU calcula threshold automaticamente
        # Retorna: (threshold_value, binary_image)
        _, binary = cv2.threshold(
            gray,
            self.config.otsu_threshold,  # Ignorado quando usando OTSU
            255,  # Valor máximo (branco)
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        # 3. Denoise (se configurado)
        if self.config.denoise_strength > 0:
            denoised = cv2.fastNlMeansDenoising(
                binary,
                h=self.config.denoise_strength,
                templateWindowSize=7,
                searchWindowSize=21
            )
            return denoised

        return binary

    def _save_image(self, image: np.ndarray, output_path: Path) -> None:
        """
        Salva imagem processada.

        Args:
            image: Imagem numpy
            output_path: Caminho de saída
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if self.config.output_format == "jpg":
            cv2.imwrite(
                str(output_path),
                image,
                [cv2.IMWRITE_JPEG_QUALITY, self.config.jpeg_quality]
            )
        else:  # png (default)
            cv2.imwrite(str(output_path), image)

        logger.debug(f"Imagem salva: {output_path}")

    def _get_output_path(self, doc_id: str, page_num: int) -> Path:
        """
        Retorna caminho de saída para imagem processada.

        Args:
            doc_id: ID do documento
            page_num: Número da página (1-indexed)

        Returns:
            Path para outputs/{doc_id}/images/page_XXX.{ext}
        """
        images_dir = get_images_dir(doc_id)
        ext = self.config.output_format
        filename = f"page_{page_num:03d}.{ext}"
        return images_dir / filename


# =============================================================================
# CLI
# =============================================================================

def main(
    layout_json: Path,
    pdf_path: Path,
    doc_id: str | None = None,
    verbose: bool = False
):
    """
    CLI para processar páginas RASTER_NEEDED.

    Args:
        layout_json: Caminho para layout.json (output do step_01)
        pdf_path: Caminho para PDF original
        doc_id: ID do documento (default: nome do PDF sem extensão)
        verbose: Ativa logging detalhado

    Exemplo:
        python step_02_vision.py \\
            outputs/doc123/layout.json \\
            inputs/processo.pdf \\
            --doc-id doc123
    """
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    # Deriva doc_id se não fornecido
    if doc_id is None:
        doc_id = pdf_path.stem

    # Processa
    processor = VisionProcessor()
    results = processor.process(layout_json, pdf_path, doc_id)

    # Summary
    print(f"\n{'='*60}")
    print(f"PROCESSAMENTO CONCLUÍDO")
    print(f"{'='*60}")
    print(f"Documento:       {doc_id}")
    print(f"Imagens geradas: {len(results)}")

    if results:
        total_pixels = sum(r.width * r.height for r in results)
        avg_size = total_pixels / len(results)
        print(f"Tamanho médio:   {avg_size / 1_000_000:.1f} MP")
        print(f"\nImagens:")
        for r in results:
            print(f"  - Página {r.page_num:3d}: {r.width}x{r.height}px")


if __name__ == "__main__":
    import typer

    app = typer.Typer()
    app.command()(main)
    app()
