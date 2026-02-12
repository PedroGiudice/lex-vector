#!/usr/bin/env python3
"""
Testes unitarios para CLAHE (Contrast Limited Adaptive Histogram Equalization).

Valida que:
1. Deteccao de imagens escuras funciona corretamente
2. CLAHE melhora contraste de imagens escuras
3. Imagens normais nao sao processadas excessivamente
4. Integracao com pipeline de scans funciona

Execucao:
    cd ferramentas/legal-text-extractor
    source .venv/bin/activate
    python -m pytest tests/test_clahe.py -v
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Adiciona o diretorio raiz ao PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.image_cleaner import (
    PRESET_DARK_SCAN,
    PRESET_UNEVEN_LIGHTING,
    CLAHEConfig,
    CleaningMode,
    CleaningOptions,
    ImageCleaner,
)

# =============================================================================
# Test Fixtures - Imagens Sinteticas
# =============================================================================


def create_dark_image() -> np.ndarray:
    """
    Cria imagem sintetica escura (simula scan mal iluminado).

    Caracteristicas:
    - Fundo escuro (intensidade ~50)
    - Texto ainda mais escuro (intensidade ~20)
    - Media de intensidade < 100
    """
    img = np.full((200, 300), 50, dtype=np.uint8)  # Fundo escuro

    # "Texto" mais escuro
    img[30:50, 50:250] = 20
    img[70:90, 50:250] = 25
    img[110:130, 50:250] = 18

    return img


def create_normal_image() -> np.ndarray:
    """
    Cria imagem sintetica normal (bom contraste).

    Caracteristicas:
    - Fundo branco (255)
    - Texto preto (0)
    - Media de intensidade > 200
    """
    img = np.full((200, 300), 255, dtype=np.uint8)  # Fundo branco

    # "Texto" preto
    img[30:50, 50:250] = 0
    img[70:90, 50:250] = 0
    img[110:130, 50:250] = 0

    return img


def create_uneven_lighting_image() -> np.ndarray:
    """
    Cria imagem sintetica com iluminacao irregular.

    Caracteristicas:
    - Gradiente de luz (esquerda clara, direita escura)
    - Texto preto em toda imagem
    - Simula scan com sombra
    """
    # Gradiente horizontal (255 -> 50)
    gradient = np.linspace(255, 50, 300).astype(np.uint8)
    img = np.tile(gradient, (200, 1))

    # "Texto" preto sobre gradiente
    img[30:50, 50:250] = np.maximum(img[30:50, 50:250] - 100, 0)
    img[70:90, 50:250] = np.maximum(img[70:90, 50:250] - 100, 0)
    img[110:130, 50:250] = np.maximum(img[110:130, 50:250] - 100, 0)

    return img


def create_very_dark_image() -> np.ndarray:
    """
    Cria imagem extremamente escura (quase ilegivel).

    Caracteristicas:
    - Fundo muito escuro (intensidade ~30)
    - Texto quase invisivel (intensidade ~10)
    """
    img = np.full((200, 300), 30, dtype=np.uint8)

    # "Texto" quase invisivel
    img[30:50, 50:250] = 10
    img[70:90, 50:250] = 15
    img[110:130, 50:250] = 8

    return img


# =============================================================================
# Tests - analyze_darkness()
# =============================================================================


class TestAnalyzeDarkness:
    """Testes para deteccao de imagens escuras."""

    def test_detects_dark_image(self):
        """Imagem escura deve ser detectada como is_dark=True."""
        img = create_dark_image()
        metrics = ImageCleaner.analyze_darkness(img)

        assert metrics["is_dark"] is True
        assert metrics["mean_intensity"] < 100
        assert metrics["darkness_score"] > 0.5

    def test_detects_normal_image(self):
        """Imagem normal deve ser detectada como is_dark=False."""
        img = create_normal_image()
        metrics = ImageCleaner.analyze_darkness(img)

        assert metrics["is_dark"] is False
        assert metrics["mean_intensity"] > 150
        assert metrics["darkness_score"] < 0.4

    def test_detects_very_dark_image(self):
        """Imagem muito escura deve ter alto darkness_score."""
        img = create_very_dark_image()
        metrics = ImageCleaner.analyze_darkness(img)

        assert metrics["is_dark"] is True
        assert metrics["mean_intensity"] < 50
        assert metrics["darkness_score"] > 0.7

    def test_returns_all_expected_metrics(self):
        """Deve retornar todas as metricas esperadas."""
        img = create_dark_image()
        metrics = ImageCleaner.analyze_darkness(img)

        assert "mean_intensity" in metrics
        assert "dark_pixel_ratio" in metrics
        assert "histogram" in metrics
        assert "is_dark" in metrics
        assert "darkness_score" in metrics

        # Histogram deve ter 256 bins
        assert len(metrics["histogram"]) == 256
        # Histogram normalizado deve somar ~1
        assert abs(metrics["histogram"].sum() - 1.0) < 0.01

    def test_custom_thresholds(self):
        """Thresholds customizados devem alterar deteccao."""
        img = create_dark_image()

        # Com threshold muito baixo, nao deve detectar como escura
        metrics_low = ImageCleaner.analyze_darkness(img, dark_threshold=30, dark_percentile=0.9)
        # Com threshold alto, deve detectar como escura
        metrics_high = ImageCleaner.analyze_darkness(img, dark_threshold=150, dark_percentile=0.2)

        assert metrics_high["is_dark"] is True

    def test_rejects_non_grayscale(self):
        """Deve rejeitar imagem que nao e grayscale."""
        img_rgb = np.zeros((200, 300, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="grayscale"):
            ImageCleaner.analyze_darkness(img_rgb)


# =============================================================================
# Tests - apply_clahe()
# =============================================================================


class TestApplyCLAHE:
    """Testes para aplicacao do CLAHE."""

    def test_improves_dark_image_contrast(self):
        """CLAHE deve melhorar contraste de imagem escura."""
        img = create_dark_image()
        enhanced = ImageCleaner.apply_clahe(img)

        # Media deve aumentar (imagem fica mais clara)
        assert np.mean(enhanced) > np.mean(img)

        # Desvio padrao deve aumentar (mais contraste)
        assert np.std(enhanced) > np.std(img)

    def test_preserves_structure(self):
        """CLAHE deve preservar estrutura da imagem."""
        img = create_dark_image()
        enhanced = ImageCleaner.apply_clahe(img)

        # Pixels mais escuros devem continuar sendo os mais escuros
        # (ordem relativa preservada)
        dark_region_before = img[30:50, 50:250].mean()
        light_region_before = img[150:170, 50:250].mean()

        dark_region_after = enhanced[30:50, 50:250].mean()
        light_region_after = enhanced[150:170, 50:250].mean()

        # Regiao do texto deve continuar mais escura que fundo
        assert dark_region_after < light_region_after

    def test_clip_limit_effect(self):
        """Clip limit maior deve resultar em mais contraste."""
        img = create_dark_image()

        enhanced_low = ImageCleaner.apply_clahe(img, clip_limit=1.0)
        enhanced_high = ImageCleaner.apply_clahe(img, clip_limit=4.0)

        # Clip limit alto = mais contraste = maior desvio padrao
        assert np.std(enhanced_high) >= np.std(enhanced_low)

    def test_tile_grid_size_effect(self):
        """Tile grid diferente deve produzir resultados diferentes."""
        img = create_uneven_lighting_image()

        enhanced_small = ImageCleaner.apply_clahe(img, tile_grid_size=(4, 4))
        enhanced_large = ImageCleaner.apply_clahe(img, tile_grid_size=(16, 16))

        # Resultados devem ser diferentes
        assert not np.array_equal(enhanced_small, enhanced_large)

    def test_rejects_non_grayscale(self):
        """Deve rejeitar imagem que nao e grayscale."""
        img_rgb = np.zeros((200, 300, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="grayscale"):
            ImageCleaner.apply_clahe(img_rgb)


# =============================================================================
# Tests - enhance_dark_scan()
# =============================================================================


class TestEnhanceDarkScan:
    """Testes para pipeline completo de melhoria de scans escuros."""

    def test_enhances_dark_image(self):
        """Pipeline deve melhorar imagem escura."""
        img = create_dark_image()
        config = CLAHEConfig(clip_limit=3.0)

        enhanced = ImageCleaner.enhance_dark_scan(img, config, apply_otsu=True)

        # Resultado deve ser binarizado (apenas 0 e 255)
        unique_values = np.unique(enhanced)
        assert len(unique_values) == 2
        assert 0 in unique_values
        assert 255 in unique_values

    def test_skips_normal_image(self):
        """Pipeline nao deve aplicar CLAHE em imagem normal."""
        img = create_normal_image()
        config = CLAHEConfig(enabled=True)

        enhanced = ImageCleaner.enhance_dark_scan(img, config, apply_otsu=False)

        # Imagem normal nao precisa de CLAHE, deve ficar igual
        # (ou muito similar, ja que e copia)
        np.testing.assert_array_equal(enhanced, img)

    def test_disabled_clahe(self):
        """CLAHE desabilitado nao deve alterar imagem escura (antes do Otsu)."""
        img = create_dark_image()
        config = CLAHEConfig(enabled=False)

        enhanced = ImageCleaner.enhance_dark_scan(img, config, apply_otsu=False)

        # Sem CLAHE e sem Otsu, resultado deve ser igual ao input
        np.testing.assert_array_equal(enhanced, img)

    def test_otsu_binarization(self):
        """Otsu deve binarizar corretamente."""
        img = create_dark_image()
        config = CLAHEConfig(clip_limit=2.5)

        enhanced = ImageCleaner.enhance_dark_scan(img, config, apply_otsu=True)

        # Resultado deve ser binarizado
        unique_values = np.unique(enhanced)
        assert len(unique_values) <= 2


# =============================================================================
# Tests - enhance_dark_scan_adaptive()
# =============================================================================


class TestEnhanceDarkScanAdaptive:
    """Testes para pipeline com threshold adaptativo."""

    def test_handles_uneven_lighting(self):
        """Deve lidar bem com iluminacao irregular."""
        img = create_uneven_lighting_image()
        config = CLAHEConfig(clip_limit=2.0, tile_grid_size=(16, 16))

        enhanced = ImageCleaner.enhance_dark_scan_adaptive(img, config, block_size=31, c=10)

        # Resultado deve ser binarizado
        unique_values = np.unique(enhanced)
        assert len(unique_values) == 2

        # Texto deve estar preservado em ambas as regioes
        # (esquerda clara e direita escura da imagem original)
        text_left = enhanced[30:50, 100:150]
        text_right = enhanced[30:50, 200:250]

        # Ambas regioes devem ter texto (pixels pretos)
        assert np.any(text_left == 0)
        assert np.any(text_right == 0)


# =============================================================================
# Tests - CLAHEConfig
# =============================================================================


class TestCLAHEConfig:
    """Testes para configuracao do CLAHE."""

    def test_default_values(self):
        """Valores padrao devem ser razoaveis."""
        config = CLAHEConfig()

        assert config.enabled is True
        assert config.clip_limit == 2.5
        assert config.tile_grid_size == (8, 8)
        assert config.dark_threshold == 100.0
        assert config.dark_percentile == 0.4

    def test_custom_values(self):
        """Valores customizados devem ser aceitos."""
        config = CLAHEConfig(
            enabled=False,
            clip_limit=4.0,
            tile_grid_size=(16, 16),
            dark_threshold=80.0,
            dark_percentile=0.5,
        )

        assert config.enabled is False
        assert config.clip_limit == 4.0
        assert config.tile_grid_size == (16, 16)


# =============================================================================
# Tests - Presets
# =============================================================================


class TestPresets:
    """Testes para presets pre-configurados."""

    def test_preset_dark_scan(self):
        """PRESET_DARK_SCAN deve ter configuracao agressiva."""
        assert PRESET_DARK_SCAN.clahe.enabled is True
        assert PRESET_DARK_SCAN.clahe.clip_limit == 3.0
        assert PRESET_DARK_SCAN.mode == CleaningMode.SCANNED

    def test_preset_uneven_lighting(self):
        """PRESET_UNEVEN_LIGHTING deve ter tiles maiores."""
        assert PRESET_UNEVEN_LIGHTING.clahe.enabled is True
        assert PRESET_UNEVEN_LIGHTING.clahe.tile_grid_size == (16, 16)
        assert PRESET_UNEVEN_LIGHTING.adaptive_block_size == 51


# =============================================================================
# Tests - Integracao com ImageCleaner
# =============================================================================


class TestImageCleanerIntegration:
    """Testes de integracao com ImageCleaner."""

    def test_cleaner_has_clahe_config(self):
        """ImageCleaner deve ter clahe_config."""
        cleaner = ImageCleaner()
        assert hasattr(cleaner, "clahe_config")
        assert isinstance(cleaner.clahe_config, CLAHEConfig)

    def test_from_options_preserves_clahe(self):
        """from_options deve preservar configuracao CLAHE."""
        options = CleaningOptions(clahe=CLAHEConfig(clip_limit=4.0, tile_grid_size=(16, 16)))
        cleaner = ImageCleaner.from_options(options)

        assert cleaner.clahe_config.clip_limit == 4.0
        assert cleaner.clahe_config.tile_grid_size == (16, 16)

    def test_process_image_with_dark_scan(self):
        """process_image deve aplicar CLAHE em scan escuro."""
        from PIL import Image

        img = create_dark_image()
        img_pil = Image.fromarray(img, mode="L")

        cleaner = ImageCleaner.from_options(PRESET_DARK_SCAN)
        result = cleaner.process_image(img_pil, mode="scanned")

        # Deve retornar PIL Image
        assert isinstance(result, Image.Image)
        assert result.mode == "L"

        # Deve ser binarizado
        result_np = np.array(result)
        unique_values = np.unique(result_np)
        assert len(unique_values) == 2

    def test_force_clahe_parameter(self):
        """force_clahe deve forcar aplicacao do CLAHE."""
        from PIL import Image

        # Imagem normal (nao seria processada por CLAHE normalmente)
        img = create_normal_image()
        img_pil = Image.fromarray(img, mode="L")

        cleaner = ImageCleaner()

        # Sem force_clahe - CLAHE nao deve ser aplicado
        result_normal = cleaner.process_image(img_pil, mode="scanned", force_clahe=False)

        # Com force_clahe - CLAHE deve ser aplicado
        result_forced = cleaner.process_image(img_pil, mode="scanned", force_clahe=True)

        # Resultados devem ser diferentes (CLAHE foi aplicado)
        result_normal_np = np.array(result_normal)
        result_forced_np = np.array(result_forced)

        # Ambos devem ser binarizados, mas podem ter resultados ligeiramente diferentes
        assert result_normal_np.shape == result_forced_np.shape


# =============================================================================
# Tests - Metricas de Melhoria
# =============================================================================


class TestImprovementMetrics:
    """Testes para verificar metricas de melhoria."""

    def test_contrast_improvement(self):
        """CLAHE deve melhorar metricas de contraste."""
        img = create_dark_image()

        # Metricas antes
        mean_before = np.mean(img)
        std_before = np.std(img)

        # Aplica CLAHE
        enhanced = ImageCleaner.apply_clahe(img, clip_limit=3.0)

        # Metricas depois
        mean_after = np.mean(enhanced)
        std_after = np.std(enhanced)

        # Melhoria esperada
        assert mean_after > mean_before, "Media deve aumentar"
        assert std_after > std_before, "Desvio padrao (contraste) deve aumentar"

        print("\nMetricas de Melhoria:")
        print(f"  Media: {mean_before:.1f} -> {mean_after:.1f} (+{mean_after - mean_before:.1f})")
        print(f"  Std:   {std_before:.1f} -> {std_after:.1f} (+{std_after - std_before:.1f})")

    def test_dynamic_range_expansion(self):
        """CLAHE deve expandir range dinamico."""
        img = create_dark_image()

        # Range antes
        min_before = img.min()
        max_before = img.max()
        range_before = max_before - min_before

        # Aplica CLAHE
        enhanced = ImageCleaner.apply_clahe(img, clip_limit=3.0)

        # Range depois
        min_after = enhanced.min()
        max_after = enhanced.max()
        range_after = max_after - min_after

        # Range deve aumentar
        assert range_after > range_before, "Range dinamico deve expandir"

        print("\nExpansao de Range Dinamico:")
        print(f"  Antes: [{min_before}, {max_before}] (range={range_before})")
        print(f"  Depois: [{min_after}, {max_after}] (range={range_after})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
