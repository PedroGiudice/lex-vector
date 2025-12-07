"""
Estágio 3: Extrator de Texto (EXTRACTION)

Extrai texto de PDFs usando dois caminhos:
- NATIVE: Extração via pdfplumber (páginas com texto extraível)
- OCR: Extração via Tesseract (páginas scaneadas/rasterizadas)

Pipeline:
1. Lê layout.json (metadados de cada página)
2. Para cada página:
   - Se NATIVE: usa pdfplumber com safe_bbox
   - Se RASTER_NEEDED: usa pytesseract na imagem limpa
3. Aplica limpeza semântica via DocumentCleaner
4. Gera final.md estruturado com fronteiras de página

Output Format (Structured Markdown):
    ## [[PAGE_001]] [TYPE: NATIVE]
    (Conteúdo textual limpo da página 1...)

    ## [[PAGE_002]] [TYPE: OCR]
    (Conteúdo extraído via Tesseract da página 2...)

Author: Pedro Giudice
Date: 2025-11-24
"""

import json
import logging
import sys
from pathlib import Path
from typing import Literal

# Adiciona o diretório raiz ao PYTHONPATH quando executado como script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

import pdfplumber
import pytesseract
from PIL import Image

from src.config import EXTRACT_CONFIG, ExtractConfig, PageType, get_images_dir, get_output_dir
from src.core.cleaner import DocumentCleaner
from src.engines.cleaning_engine import get_cleaner

# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# =============================================================================
# EXTRATOR DE TEXTO
# =============================================================================


class TextExtractor:
    """
    Extrai texto de PDFs usando pdfplumber (NATIVE) ou Tesseract (OCR).

    Integra com DocumentCleaner para limpeza semântica de assinaturas
    e certificações digitais.

    Example:
        >>> extractor = TextExtractor()
        >>> markdown = extractor.extract(
        ...     layout_path=Path("outputs/doc_001/layout.json"),
        ...     pdf_path=Path("inputs/document.pdf"),
        ...     images_dir=Path("outputs/doc_001/images")
        ... )
        >>> extractor.save(markdown, Path("outputs/doc_001/final.md"))
    """

    def __init__(self, config: ExtractConfig = EXTRACT_CONFIG):
        """
        Inicializa extrator com configuração e cleaner.

        Args:
            config: Configuração de extração (idioma Tesseract, PSM, etc.)
        """
        self.config = config
        self.cleaner = DocumentCleaner()
        self.adaptive_cleaner = get_cleaner()  # New adaptive engine
        logger.info("TextExtractor inicializado")
        logger.info(f"  Tesseract lang: {config.tesseract_lang}")
        logger.info(f"  Tesseract PSM: {config.tesseract_psm}")
        logger.info(f"  Limpeza semântica: {'ativada' if config.apply_cleaning else 'desativada'}")
        logger.info(f"  Adaptive Cleaning Engine: ativado")

    def extract(
        self, layout_path: Path, pdf_path: Path, images_dir: Path | None = None
    ) -> str:
        """
        Extrai texto de todas as páginas e retorna markdown estruturado.

        Args:
            layout_path: Caminho para layout.json (metadados de páginas)
            pdf_path: Caminho para PDF original
            images_dir: Diretório com imagens processadas (para OCR)

        Returns:
            String com markdown estruturado (## [[PAGE_XXX]] [TYPE: ...])

        Raises:
            FileNotFoundError: Se layout.json ou PDF não existir
            ValueError: Se layout.json inválido
            RuntimeError: Se Tesseract não estiver instalado

        Example:
            >>> markdown = extractor.extract(
            ...     layout_path=Path("outputs/doc_001/layout.json"),
            ...     pdf_path=Path("inputs/document.pdf"),
            ...     images_dir=Path("outputs/doc_001/images")
            ... )
            >>> print(markdown[:100])
            ## [[PAGE_001]] [TYPE: NATIVE]
            TRIBUNAL REGIONAL FEDERAL DA 3ª REGIÃO...
        """
        # Validações
        if not layout_path.exists():
            raise FileNotFoundError(f"Layout não encontrado: {layout_path}")

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")

        # Carrega metadados do layout
        logger.info(f"Carregando layout: {layout_path}")
        with open(layout_path, "r", encoding="utf-8") as f:
            layout = json.load(f)

        if "pages" not in layout:
            raise ValueError("layout.json inválido: campo 'pages' não encontrado")

        pages_metadata = layout["pages"]
        total_pages = len(pages_metadata)

        logger.info(f"Total de páginas: {total_pages}")
        logger.info(f"PDF: {pdf_path.name}")

        # Extrai texto de cada página
        markdown_parts = []

        for page_meta in pages_metadata:
            page_num = page_meta["page_num"]
            page_type = page_meta["type"]
            safe_bbox = tuple(page_meta["safe_bbox"])

            logger.info(f"Processando página {page_num}/{total_pages} ({page_type})")

            # Extração baseada no tipo
            if page_type == PageType.NATIVE:
                text = self._extract_native(pdf_path, page_num, safe_bbox)
            elif page_type == PageType.RASTER_NEEDED:
                if images_dir is None:
                    raise ValueError(
                        f"Página {page_num} é RASTER_NEEDED mas images_dir não foi fornecido"
                    )
                image_path = images_dir / f"page_{page_num:03d}.png"
                text = self._extract_ocr(image_path)
            else:
                logger.warning(f"Tipo desconhecido '{page_type}' na página {page_num}, pulando")
                continue

            # Limpeza semântica
            if self.config.apply_cleaning:
                text = self._clean_text(text)

            # Formata para markdown
            page_markdown = self._format_page(page_num, page_type, text)
            markdown_parts.append(page_markdown)

        # Junta todas as páginas
        final_markdown = "\n\n".join(markdown_parts)

        logger.info(f"Extração concluída: {total_pages} páginas processadas")
        return final_markdown

    def _extract_native(self, pdf_path: Path, page_num: int, safe_bbox: tuple) -> str:
        """
        Extrai texto de página nativa via pdfplumber.

        Uses strict char filtering by X coordinate to handle rotated tarja text
        that may have x0 coordinates inside the safe_bbox but visually belongs
        to the lateral tarja zone.

        Args:
            pdf_path: Caminho para PDF
            page_num: Número da página (1-indexed)
            safe_bbox: Bounding box segura (x0, y0, x1, y1) sem tarjas

        Returns:
            Texto extraído (pode estar vazio se falhar)

        Example:
            >>> text = extractor._extract_native(
            ...     Path("doc.pdf"),
            ...     page_num=1,
            ...     safe_bbox=(10, 10, 590, 832)
            ... )
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # pdfplumber usa 0-indexed
                page = pdf.pages[page_num - 1]

                x0, y0, x1, y1 = safe_bbox

                # Filter chars strictly by X coordinate
                # This handles rotated text in tarjas where x0 may be inside bbox
                # but the char visually belongs to the tarja zone
                filtered_chars = [
                    char for char in page.chars
                    if (char["x0"] >= x0 and
                        char["x1"] <= x1 and
                        char["top"] >= y0 and
                        char["bottom"] <= y1)
                ]

                if not filtered_chars:
                    logger.warning(f"Página {page_num} NATIVE retornou texto vazio após filtro")
                    return ""

                # Rebuild text from filtered chars using pdfplumber's internal method
                # by creating a filtered page object
                cropped = page.crop(safe_bbox)

                # Override chars with strictly filtered set
                cropped_with_filter = cropped.filter(
                    lambda obj: (obj["object_type"] != "char" or
                                (obj["x0"] >= x0 and obj["x1"] <= x1))
                )

                text = cropped_with_filter.extract_text()

                if not text:
                    logger.warning(f"Página {page_num} NATIVE retornou texto vazio")
                    return ""

                logger.debug(f"Página {page_num}: {len(text)} caracteres extraídos")
                return text

        except Exception as e:
            logger.error(f"Erro ao extrair página {page_num} via pdfplumber: {e}")
            return ""

    def _extract_ocr(self, image_path: Path) -> str:
        """
        Extrai texto de imagem via Tesseract.

        Args:
            image_path: Caminho para imagem processada (PNG)

        Returns:
            Texto extraído via OCR

        Raises:
            FileNotFoundError: Se imagem não existir
            RuntimeError: Se Tesseract não estiver instalado

        Example:
            >>> text = extractor._extract_ocr(
            ...     Path("outputs/doc_001/images/page_002.png")
            ... )
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

        try:
            # Carrega imagem
            image = Image.open(image_path)

            # Configura Tesseract
            custom_config = f"--psm {self.config.tesseract_psm}"

            # Extrai texto
            text = pytesseract.image_to_string(
                image, lang=self.config.tesseract_lang, config=custom_config
            )

            if not text or not text.strip():
                logger.warning(f"OCR retornou texto vazio para {image_path.name}")
                return ""

            logger.debug(f"OCR {image_path.name}: {len(text)} caracteres extraídos")
            return text

        except pytesseract.TesseractNotFoundError:
            raise RuntimeError(
                "Tesseract não encontrado. Instale com: sudo apt install tesseract-ocr tesseract-ocr-por"
            )
        except Exception as e:
            logger.error(f"Erro ao processar OCR de {image_path.name}: {e}")
            return ""

    def _clean_text(self, text: str) -> str:
        """
        Aplica limpeza semântica via Adaptive CleanerEngine.

        Remove assinaturas digitais, certificações, cabeçalhos/rodapés
        usando padrões específicos de sistemas judiciais brasileiros.
        Detecta automaticamente o sistema via fingerprints.

        Args:
            text: Texto cru extraído

        Returns:
            Texto limpo (ou original se limpeza falhar)

        Example:
            >>> raw = "Documento PJE\\n\\nAssinado digitalmente por João..."
            >>> clean = extractor._clean_text(raw)
            >>> "Assinado digitalmente" in clean
            False
        """
        if not text or len(text) < 10:
            return text

        try:
            # Detects system via fingerprints and applies weighted rules
            force_system = self.config.cleaning_system if self.config.cleaning_system != "auto" else None

            # Detect system first for logging
            detection = self.adaptive_cleaner.detect_system(text)

            # Clean text
            cleaned_text = self.adaptive_cleaner.clean(text, force_system=force_system)

            # Log statistics
            original_len = len(text)
            final_len = len(cleaned_text)
            reduction_pct = ((original_len - final_len) / original_len) * 100 if original_len > 0 else 0.0

            logger.debug(
                f"Adaptive Cleaning ({detection.system}, conf={detection.confidence:.2f}): "
                f"{original_len} → {final_len} chars "
                f"(-{reduction_pct:.1f}%)"
            )

            return cleaned_text

        except Exception as e:
            logger.warning(f"Erro na limpeza adaptativa: {e}, usando texto original")
            return text

    def _format_page(
        self, page_num: int, page_type: Literal["NATIVE", "RASTER_NEEDED"], text: str
    ) -> str:
        """
        Formata página para markdown estruturado.

        Args:
            page_num: Número da página (1-indexed)
            page_type: NATIVE ou RASTER_NEEDED
            text: Texto extraído

        Returns:
            String formatada: ## [[PAGE_XXX]] [TYPE: ...]\\n(texto)

        Example:
            >>> formatted = extractor._format_page(1, "NATIVE", "Conteúdo...")
            >>> print(formatted)
            ## [[PAGE_001]] [TYPE: NATIVE]
            Conteúdo...
        """
        # Mapeia tipo interno para tipo público
        public_type = "NATIVE" if page_type == PageType.NATIVE else "OCR"

        # Formata com padding de 3 dígitos
        header = f"## [[PAGE_{page_num:03d}]] [TYPE: {public_type}]"

        # Garante texto não vazio
        content = text.strip() if text else "(página vazia)"

        return f"{header}\n{content}"

    def save(self, markdown: str, output_path: Path) -> None:
        """
        Salva markdown estruturado em arquivo.

        Args:
            markdown: Conteúdo markdown estruturado
            output_path: Caminho para salvar final.md

        Example:
            >>> extractor.save(
            ...     markdown="## [[PAGE_001]]...",
            ...     output_path=Path("outputs/doc_001/final.md")
            ... )
        """
        # Cria diretório se não existir
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Salva com encoding UTF-8
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        logger.info(f"Markdown salvo: {output_path}")
        logger.info(f"  Tamanho: {len(markdown)} bytes")


# =============================================================================
# CLI
# =============================================================================


def main(
    layout_json: Path,
    pdf_path: Path,
    images_dir: Path | None = None,
    output_md: Path | None = None,
    no_clean: bool = False,
    system: str | None = None,
):
    """
    Extrai texto de PDF usando layout.json e gera final.md estruturado.

    Args:
        layout_json: Caminho para layout.json (output do step_01_analyze)
        pdf_path: Caminho para PDF original
        images_dir: Diretório com imagens processadas (output do step_02_vision)
        output_md: Caminho para salvar final.md (padrão: mesmo dir que layout.json)
        no_clean: Desabilita limpeza semântica
        system: Sistema judicial manual (PJE, ESAJ, etc.) - padrão: auto-detect

    Example:
        python step_03_extract.py \\
            --layout-json outputs/doc_001/layout.json \\
            --pdf-path inputs/document.pdf \\
            --images-dir outputs/doc_001/images \\
            --output-md outputs/doc_001/final.md
    """
    # Configuração customizada
    config = ExtractConfig(
        tesseract_lang=EXTRACT_CONFIG.tesseract_lang,
        tesseract_psm=EXTRACT_CONFIG.tesseract_psm,
        apply_cleaning=not no_clean,
        cleaning_system=system,
    )

    # Inicializa extrator
    extractor = TextExtractor(config)

    # Extrai texto
    logger.info("=" * 60)
    logger.info("STEP 03: EXTRACTION")
    logger.info("=" * 60)

    markdown = extractor.extract(
        layout_path=layout_json, pdf_path=pdf_path, images_dir=images_dir
    )

    # Define output path se não fornecido
    if output_md is None:
        output_md = layout_json.parent / "final.md"

    # Salva
    extractor.save(markdown, output_md)

    logger.info("=" * 60)
    logger.info("EXTRAÇÃO CONCLUÍDA")
    logger.info("=" * 60)
    logger.info(f"Output: {output_md}")


if __name__ == "__main__":
    import typer

    app = typer.Typer(
        help="Estágio 3: Extração de texto de PDFs (NATIVE + OCR)",
        add_completion=False,
    )

    @app.command()
    def extract(
        layout_json: Path = typer.Option(
            ..., "--layout-json", "-l", help="Caminho para layout.json"
        ),
        pdf_path: Path = typer.Option(..., "--pdf-path", "-p", help="Caminho para PDF original"),
        images_dir: Path = typer.Option(
            None, "--images-dir", "-i", help="Diretório com imagens processadas (para OCR)"
        ),
        output_md: Path = typer.Option(
            None, "--output-md", "-o", help="Caminho para salvar final.md"
        ),
        no_clean: bool = typer.Option(
            False, "--no-clean", help="Desabilita limpeza semântica"
        ),
        system: str = typer.Option(
            None, "--system", "-s", help="Sistema judicial (PJE, ESAJ, auto)"
        ),
    ):
        """Extrai texto de PDF e gera final.md estruturado."""
        main(
            layout_json=layout_json,
            pdf_path=pdf_path,
            images_dir=images_dir,
            output_md=output_md,
            no_clean=no_clean,
            system=system,
        )

    app()
