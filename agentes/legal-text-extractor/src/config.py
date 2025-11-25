"""
Configuração centralizada do Legal Text Extractor.

Usa caminhos absolutos baseados em Path(__file__).parent para evitar
erros de path no WSL2.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Literal


# =============================================================================
# PATHS ABSOLUTOS
# =============================================================================

# Raiz do projeto
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Diretórios principais
SRC_DIR = PROJECT_ROOT / "src"
INPUTS_DIR = PROJECT_ROOT / "inputs"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
TEST_DOCUMENTS_DIR = PROJECT_ROOT / "test-documents"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Core modules
CORE_DIR = SRC_DIR / "core"


# =============================================================================
# CONFIGURAÇÕES DO CARTÓGRAFO (step_01_layout)
# =============================================================================

@dataclass(frozen=True)
class LayoutConfig:
    """Configurações para análise de layout e detecção de tarjas."""

    # Threshold para considerar uma zona como "tarja lateral"
    # Se > X% dos caracteres estão nos últimos Y% da largura = tarja
    tarja_density_threshold: float = 0.15  # 15% dos chars
    tarja_zone_percent: float = 0.20  # últimos 20% da largura

    # Threshold mínimo de texto para considerar página NATIVE
    # Se safe_bbox tem < X caracteres extraíveis = RASTER_NEEDED
    min_text_chars: int = 50

    # Margem de segurança para o safe_bbox (pixels)
    safe_margin_px: int = 10

    # Bins para histograma de densidade no eixo X
    histogram_bins: int = 100

    # --- DETECÇÃO ADAPTATIVA DE BOUNDARY ---
    # Gap mínimo (em pontos) para considerar separação entre texto e tarja
    content_gap_threshold: float = 30.0

    # Usa detecção adaptativa (True) ou corte percentual fixo (False)
    use_adaptive_cut: bool = True

    # Zona onde procurar gaps (últimos X% da largura)
    # Se gap encontrado nessa zona, assume que é separação texto/tarja
    gap_search_zone_percent: float = 0.30  # últimos 30%


LAYOUT_CONFIG = LayoutConfig()


# =============================================================================
# CONFIGURAÇÕES DO SANEADOR (step_02_vision)
# =============================================================================

@dataclass(frozen=True)
class VisionConfig:
    """Configurações para processamento de imagem OpenCV."""

    # DPI para renderização PDF -> imagem
    render_dpi: int = 300

    # Threshold Otsu (0 = automático)
    otsu_threshold: int = 0

    # Denoise strength (0 = desabilitado)
    denoise_strength: int = 10

    # Formato de saída das imagens processadas
    output_format: Literal["png", "jpg"] = "png"

    # Qualidade JPEG (se output_format == "jpg")
    jpeg_quality: int = 95


VISION_CONFIG = VisionConfig()


# =============================================================================
# CONFIGURAÇÕES DO EXTRATOR (step_03_extract)
# =============================================================================

@dataclass(frozen=True)
class ExtractConfig:
    """Configurações para extração de texto."""

    # Idioma do Tesseract OCR
    tesseract_lang: str = "por"

    # PSM (Page Segmentation Mode) do Tesseract
    # 3 = Fully automatic page segmentation (default)
    # 6 = Assume a single uniform block of text
    tesseract_psm: int = 3

    # Aplicar limpeza semântica (src.core.cleaner) após extração
    apply_cleaning: bool = True

    # Sistema judicial para limpeza (None = auto-detect)
    cleaning_system: str | None = None


EXTRACT_CONFIG = ExtractConfig()


# =============================================================================
# TIPOS DE PÁGINA
# =============================================================================

class PageType:
    """Tipos de página detectados pelo Cartógrafo."""
    NATIVE = "NATIVE"           # Texto extraível via pdfplumber
    RASTER_NEEDED = "RASTER_NEEDED"  # Precisa OCR (scan/imagem)


# =============================================================================
# HELPERS
# =============================================================================

def ensure_dirs():
    """Cria diretórios necessários se não existirem."""
    INPUTS_DIR.mkdir(exist_ok=True)
    OUTPUTS_DIR.mkdir(exist_ok=True)


def get_output_dir(doc_id: str) -> Path:
    """Retorna diretório de output para um documento específico."""
    output_dir = OUTPUTS_DIR / doc_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_images_dir(doc_id: str) -> Path:
    """Retorna diretório de imagens para um documento específico."""
    images_dir = get_output_dir(doc_id) / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    return images_dir
