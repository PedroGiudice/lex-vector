"""
Testes para Step 02: Vision Pipeline (O Saneador)
"""

import json
from pathlib import Path

import numpy as np
import pytest

from src.steps.step_02_vision import VisionProcessor, PageLayout
from src.config import VisionConfig, PageType


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def vision_processor():
    """Cria VisionProcessor com configuração padrão."""
    return VisionProcessor()


@pytest.fixture
def sample_layout_data():
    """Layout JSON de exemplo com páginas NATIVE e RASTER_NEEDED."""
    return {
        "document_id": "test_doc",
        "pages": [
            {
                "page_num": 1,
                "type": PageType.NATIVE,
                "safe_bbox": [0, 0, 612, 792],
                "has_tarja": False,
                "text_chars": 1500
            },
            {
                "page_num": 2,
                "type": PageType.RASTER_NEEDED,
                "safe_bbox": [50, 50, 562, 742],
                "has_tarja": True,
                "text_chars": 20
            },
            {
                "page_num": 3,
                "type": PageType.RASTER_NEEDED,
                "safe_bbox": [0, 0, 612, 792],
                "has_tarja": False,
                "text_chars": 0
            }
        ]
    }


@pytest.fixture
def temp_layout_json(tmp_path, sample_layout_data):
    """Cria arquivo layout.json temporário."""
    layout_path = tmp_path / "layout.json"
    with open(layout_path, "w") as f:
        json.dump(sample_layout_data, f)
    return layout_path


# =============================================================================
# TESTS: FILTER PAGES
# =============================================================================

def test_filter_raster_pages(vision_processor, sample_layout_data):
    """Testa filtro de páginas RASTER_NEEDED."""
    pages = vision_processor._filter_raster_pages(sample_layout_data)

    assert len(pages) == 2, "Deve filtrar 2 páginas RASTER_NEEDED"
    assert pages[0].page_num == 2
    assert pages[1].page_num == 3

    # Verifica estrutura PageLayout
    assert isinstance(pages[0], PageLayout)
    assert pages[0].type == PageType.RASTER_NEEDED
    assert pages[0].safe_bbox == (50, 50, 562, 742)
    assert pages[0].has_tarja is True


def test_filter_empty_layout(vision_processor):
    """Testa filtro com layout vazio."""
    pages = vision_processor._filter_raster_pages({"pages": []})
    assert pages == []


def test_filter_only_native(vision_processor):
    """Testa filtro quando todas as páginas são NATIVE."""
    layout = {
        "pages": [
            {"page_num": 1, "type": PageType.NATIVE, "safe_bbox": [0, 0, 612, 792]}
        ]
    }
    pages = vision_processor._filter_raster_pages(layout)
    assert pages == []


# =============================================================================
# TESTS: PIPELINE
# =============================================================================

def test_apply_pipeline_grayscale(vision_processor):
    """Testa conversão para grayscale."""
    # Cria imagem BGR sintética (100x100, azul)
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[:, :, 0] = 255  # Canal B (azul)

    processed = vision_processor._apply_pipeline(image)

    # Verifica shape (deve ser grayscale)
    assert processed.ndim == 2, "Imagem processada deve ser grayscale (2D)"
    assert processed.shape == (100, 100)


def test_apply_pipeline_binary(vision_processor):
    """Testa binarização (valores apenas 0 ou 255)."""
    # Cria imagem gradiente
    image = np.tile(np.arange(256, dtype=np.uint8), (100, 1))
    image = np.stack([image] * 3, axis=-1)  # BGR

    processed = vision_processor._apply_pipeline(image)

    # Verifica valores binários
    unique_values = np.unique(processed)
    assert len(unique_values) <= 2, "Imagem deve ser binária (máx 2 valores)"
    assert 0 in unique_values or 255 in unique_values


def test_apply_pipeline_with_denoise(vision_processor):
    """Testa pipeline com denoise habilitado."""
    config = VisionConfig(denoise_strength=10)
    processor = VisionProcessor(config)

    image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    processed = processor._apply_pipeline(image)

    assert processed.shape == (100, 100)


def test_apply_pipeline_no_denoise(vision_processor):
    """Testa pipeline com denoise desabilitado."""
    config = VisionConfig(denoise_strength=0)
    processor = VisionProcessor(config)

    image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    processed = processor._apply_pipeline(image)

    assert processed.shape == (100, 100)


# =============================================================================
# TESTS: OUTPUT PATH
# =============================================================================

def test_get_output_path():
    """Testa geração de caminho de saída."""
    config = VisionConfig(output_format="png")
    processor = VisionProcessor(config)

    path = processor._get_output_path("doc123", 5)

    assert path.name == "page_005.png"
    assert "doc123" in str(path)
    assert "images" in str(path)


def test_get_output_path_jpg():
    """Testa geração de caminho com formato JPG."""
    config = VisionConfig(output_format="jpg")
    processor = VisionProcessor(config)

    path = processor._get_output_path("doc456", 42)

    assert path.name == "page_042.jpg"


# =============================================================================
# TESTS: INTEGRATION
# =============================================================================

def test_process_missing_layout(vision_processor, tmp_path):
    """Testa erro quando layout.json não existe."""
    with pytest.raises(FileNotFoundError, match="Layout não encontrado"):
        vision_processor.process(
            layout_path=tmp_path / "missing.json",
            pdf_path=tmp_path / "dummy.pdf",
            doc_id="test"
        )


def test_process_missing_pdf(vision_processor, temp_layout_json, tmp_path):
    """Testa erro quando PDF não existe."""
    with pytest.raises(FileNotFoundError, match="PDF não encontrado"):
        vision_processor.process(
            layout_path=temp_layout_json,
            pdf_path=tmp_path / "missing.pdf",
            doc_id="test"
        )


def test_process_empty_raster_pages(vision_processor, tmp_path):
    """Testa processamento quando não há páginas RASTER_NEEDED."""
    # Layout com apenas páginas NATIVE
    layout_data = {
        "pages": [
            {"page_num": 1, "type": PageType.NATIVE, "safe_bbox": [0, 0, 612, 792]}
        ]
    }

    layout_path = tmp_path / "layout.json"
    with open(layout_path, "w") as f:
        json.dump(layout_data, f)

    # PDF dummy (não será usado)
    pdf_path = tmp_path / "dummy.pdf"
    pdf_path.touch()

    results = vision_processor.process(layout_path, pdf_path, "test")

    assert results == [], "Deve retornar lista vazia quando não há páginas RASTER_NEEDED"


# =============================================================================
# TESTS: EDGE CASES
# =============================================================================

def test_safe_bbox_validation():
    """Testa validação de safe_bbox inválido."""
    # Verifica que PageLayout aceita tuple
    layout = PageLayout(
        page_num=1,
        type=PageType.RASTER_NEEDED,
        safe_bbox=(0, 0, 612, 792),
        has_tarja=False,
        text_chars=0
    )

    assert layout.safe_bbox == (0, 0, 612, 792)


def test_config_defaults():
    """Testa valores padrão da configuração."""
    config = VisionConfig()

    assert config.render_dpi == 300
    assert config.otsu_threshold == 0
    assert config.denoise_strength == 10
    assert config.output_format == "png"
    assert config.jpeg_quality == 95


# =============================================================================
# TESTS: SMOKE TESTS
# =============================================================================

def test_vision_processor_instantiation():
    """Testa criação de VisionProcessor."""
    processor = VisionProcessor()
    assert processor.config is not None
    assert processor.config.render_dpi == 300


def test_vision_processor_custom_config():
    """Testa criação com configuração customizada."""
    config = VisionConfig(render_dpi=150, denoise_strength=5)
    processor = VisionProcessor(config)

    assert processor.config.render_dpi == 150
    assert processor.config.denoise_strength == 5
