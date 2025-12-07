"""
Testes para classificação de complexidade de páginas.

Testa a detecção de complexidade granular (NATIVE_CLEAN, NATIVE_WITH_ARTIFACTS,
RASTER_CLEAN, RASTER_DIRTY, RASTER_DEGRADED) e recomendação de engines.
"""

import pytest
from pathlib import Path
import sys
import json

# Setup path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import (
    PageComplexity,
    PageType,
    COMPLEXITY_ENGINE_MAP,
    RASTER_QUALITY_THRESHOLDS,
)


class TestPageComplexityClassification:
    """Testes para classificação de complexidade de páginas."""

    def test_native_clean_classification(self):
        """Página nativa sem artefatos = NATIVE_CLEAN."""
        # Setup: página com texto nativo, sem tarja
        page_data = {
            "page_num": 1,
            "type": PageType.NATIVE,
            "has_tarja": False,
            "char_count": 1500,
            "safe_bbox": [0, 0, 595, 842],
        }

        # Expected: NATIVE_CLEAN
        complexity = self._classify_page(page_data)
        assert complexity == PageComplexity.NATIVE_CLEAN

    def test_native_with_artifacts(self):
        """Página nativa com tarja = NATIVE_WITH_ARTIFACTS."""
        # Setup: página com texto nativo + tarja lateral
        page_data = {
            "page_num": 1,
            "type": PageType.NATIVE,
            "has_tarja": True,
            "tarja_x_cut": 500.0,
            "char_count": 1200,
            "safe_bbox": [0, 0, 490, 842],
        }

        # Expected: NATIVE_WITH_ARTIFACTS
        complexity = self._classify_page(page_data)
        assert complexity == PageComplexity.NATIVE_WITH_ARTIFACTS

    def test_raster_clean_classification(self):
        """Scan limpo (alto contraste, sem noise) = RASTER_CLEAN."""
        # Setup: página raster com métricas de qualidade alta
        page_data = {
            "page_num": 1,
            "type": PageType.RASTER_NEEDED,
            "has_tarja": False,
            "char_count": 20,  # Poucos chars extraíveis (é scan)
            "quality_metrics": {
                "contrast_score": 0.85,  # Alto contraste
                "noise_level": 0.2,  # Baixo ruído
                "char_density": 0.6,  # Boa densidade
            },
        }

        # Expected: RASTER_CLEAN
        complexity = self._classify_page(page_data)
        assert complexity == PageComplexity.RASTER_CLEAN

    def test_raster_dirty_classification(self):
        """Scan com watermark/carimbos (contraste médio) = RASTER_DIRTY."""
        # Setup: página raster com artefatos visuais
        page_data = {
            "page_num": 1,
            "type": PageType.RASTER_NEEDED,
            "has_tarja": True,  # Pode ter tarja também
            "char_count": 15,
            "quality_metrics": {
                "contrast_score": 0.6,  # Contraste médio
                "noise_level": 0.4,  # Algum ruído
                "char_density": 0.4,  # Densidade OK
            },
        }

        # Expected: RASTER_DIRTY
        complexity = self._classify_page(page_data)
        assert complexity == PageComplexity.RASTER_DIRTY

    def test_raster_degraded_classification(self):
        """Scan muito sujo (baixo contraste, alto ruído) = RASTER_DEGRADED."""
        # Setup: página raster degradada
        page_data = {
            "page_num": 1,
            "type": PageType.RASTER_NEEDED,
            "has_tarja": False,
            "char_count": 5,  # Muito poucos chars (péssima extração)
            "quality_metrics": {
                "contrast_score": 0.3,  # Contraste baixo
                "noise_level": 0.7,  # Alto ruído
                "char_density": 0.2,  # Densidade ruim
            },
        }

        # Expected: RASTER_DEGRADED
        complexity = self._classify_page(page_data)
        assert complexity == PageComplexity.RASTER_DEGRADED

    def test_layout_json_includes_complexity(self):
        """layout.json deve incluir campo complexity."""
        # Setup: layout típico
        layout = {
            "doc_id": "test_doc",
            "total_pages": 2,
            "pages": [
                {
                    "page_num": 1,
                    "type": PageType.NATIVE,
                    "has_tarja": False,
                    "char_count": 1500,
                    "safe_bbox": [0, 0, 595, 842],
                },
                {
                    "page_num": 2,
                    "type": PageType.RASTER_NEEDED,
                    "has_tarja": False,
                    "char_count": 10,
                    "quality_metrics": {
                        "contrast_score": 0.85,
                        "noise_level": 0.2,
                        "char_density": 0.6,
                    },
                },
            ],
        }

        # Enriquece com complexity
        enriched = self._enrich_layout_with_complexity(layout)

        # Verifica que cada página tem complexity
        assert "complexity" in enriched["pages"][0]
        assert "complexity" in enriched["pages"][1]
        assert enriched["pages"][0]["complexity"] == PageComplexity.NATIVE_CLEAN
        assert enriched["pages"][1]["complexity"] == PageComplexity.RASTER_CLEAN

    def test_recommended_engine_based_on_complexity(self):
        """Cada complexity tem engine recomendado."""
        # Testa mapeamento completo
        assert (
            COMPLEXITY_ENGINE_MAP[PageComplexity.NATIVE_CLEAN] == "pdfplumber"
        )
        assert (
            COMPLEXITY_ENGINE_MAP[PageComplexity.NATIVE_WITH_ARTIFACTS]
            == "pdfplumber"
        )
        assert (
            COMPLEXITY_ENGINE_MAP[PageComplexity.RASTER_CLEAN] == "tesseract"
        )
        assert COMPLEXITY_ENGINE_MAP[PageComplexity.RASTER_DIRTY] == "marker"
        assert (
            COMPLEXITY_ENGINE_MAP[PageComplexity.RASTER_DEGRADED] == "marker"
        )

    def test_edge_case_no_quality_metrics(self):
        """Página raster sem quality_metrics = fallback RASTER_CLEAN."""
        page_data = {
            "page_num": 1,
            "type": PageType.RASTER_NEEDED,
            "has_tarja": False,
            "char_count": 10,
            # Sem quality_metrics
        }

        complexity = self._classify_page(page_data)
        # Fallback conservador: assume clean se não tem métricas
        assert complexity == PageComplexity.RASTER_CLEAN

    def test_edge_case_boundary_contrast_threshold(self):
        """Testa boundary exato dos thresholds de contraste."""
        thresholds = RASTER_QUALITY_THRESHOLDS

        # Contraste no limite alto (0.8)
        page_high = {
            "page_num": 1,
            "type": PageType.RASTER_NEEDED,
            "has_tarja": False,
            "char_count": 10,
            "quality_metrics": {
                "contrast_score": thresholds.high_contrast_threshold,  # 0.8
                "noise_level": 0.2,
                "char_density": 0.5,
            },
        }
        assert (
            self._classify_page(page_high) == PageComplexity.RASTER_CLEAN
        )

        # Contraste no limite baixo (0.4)
        page_low = {
            "page_num": 1,
            "type": PageType.RASTER_NEEDED,
            "has_tarja": False,
            "char_count": 10,
            "quality_metrics": {
                "contrast_score": thresholds.low_contrast_threshold,  # 0.4
                "noise_level": 0.5,
                "char_density": 0.3,
            },
        }
        # 0.4 <= score < 0.8 = DIRTY
        assert (
            self._classify_page(page_low) == PageComplexity.RASTER_DIRTY
        )

    def test_edge_case_high_noise_degrades_quality(self):
        """Alto ruído sempre resulta em RASTER_DEGRADED."""
        page_data = {
            "page_num": 1,
            "type": PageType.RASTER_NEEDED,
            "has_tarja": False,
            "char_count": 10,
            "quality_metrics": {
                "contrast_score": 0.9,  # Contraste excelente
                "noise_level": 0.7,  # Mas alto ruído
                "char_density": 0.5,
            },
        }

        complexity = self._classify_page(page_data)
        # Ruído alto sobrepõe contraste bom
        assert complexity == PageComplexity.RASTER_DEGRADED

    # ==========================================================================
    # HELPER METHODS (Implementação temporária para testes)
    # ==========================================================================

    def _classify_page(self, page_data: dict) -> str:
        """
        Classifica complexidade de uma página.

        Esta é uma implementação de referência para os testes.
        A implementação real deve ser movida para src/core/complexity.py
        """
        page_type = page_data.get("type")
        has_tarja = page_data.get("has_tarja", False)
        quality_metrics = page_data.get("quality_metrics", {})

        # NATIVE pages
        if page_type == PageType.NATIVE:
            if has_tarja:
                return PageComplexity.NATIVE_WITH_ARTIFACTS
            else:
                return PageComplexity.NATIVE_CLEAN

        # RASTER pages
        elif page_type == PageType.RASTER_NEEDED:
            # Sem métricas = assume CLEAN (conservador)
            if not quality_metrics:
                return PageComplexity.RASTER_CLEAN

            contrast = quality_metrics.get("contrast_score", 0.5)
            noise = quality_metrics.get("noise_level", 0.0)

            thresholds = RASTER_QUALITY_THRESHOLDS

            # Alto ruído sempre degrada
            if noise >= thresholds.high_noise_threshold:
                return PageComplexity.RASTER_DEGRADED

            # Classificação baseada em contraste
            if contrast >= thresholds.high_contrast_threshold:
                return PageComplexity.RASTER_CLEAN
            elif contrast >= thresholds.low_contrast_threshold:
                return PageComplexity.RASTER_DIRTY
            else:
                return PageComplexity.RASTER_DEGRADED

        # Fallback
        return PageComplexity.NATIVE_CLEAN

    def _enrich_layout_with_complexity(self, layout: dict) -> dict:
        """
        Adiciona campo 'complexity' a cada página do layout.

        Esta é uma implementação de referência para os testes.
        A implementação real deve ser integrada ao LayoutAnalyzer.
        """
        enriched = layout.copy()
        enriched["pages"] = []

        for page in layout["pages"]:
            page_copy = page.copy()
            page_copy["complexity"] = self._classify_page(page)
            enriched["pages"].append(page_copy)

        return enriched


class TestQualityThresholds:
    """Testes para configuração de thresholds de qualidade."""

    def test_thresholds_are_valid(self):
        """Thresholds devem estar em ranges válidos."""
        thresholds = RASTER_QUALITY_THRESHOLDS

        # Contraste entre 0.0 e 1.0
        assert 0.0 <= thresholds.high_contrast_threshold <= 1.0
        assert 0.0 <= thresholds.low_contrast_threshold <= 1.0
        assert (
            thresholds.low_contrast_threshold
            < thresholds.high_contrast_threshold
        )

        # Ruído entre 0.0 e 1.0
        assert 0.0 <= thresholds.high_noise_threshold <= 1.0

        # Densidade >= 0.0
        assert thresholds.min_clean_density >= 0.0

    def test_thresholds_are_sensible(self):
        """Thresholds devem ter valores sensatos para casos reais."""
        thresholds = RASTER_QUALITY_THRESHOLDS

        # Valores esperados (documentados em config.py)
        assert thresholds.high_contrast_threshold == 0.8
        assert thresholds.low_contrast_threshold == 0.4
        assert thresholds.high_noise_threshold == 0.6
        assert thresholds.min_clean_density == 0.5


class TestComplexityEngineMapping:
    """Testes para mapeamento de complexity -> engine."""

    def test_all_complexities_have_engine(self):
        """Todas as complexidades devem ter engine mapeado."""
        expected_complexities = {
            PageComplexity.NATIVE_CLEAN,
            PageComplexity.NATIVE_WITH_ARTIFACTS,
            PageComplexity.RASTER_CLEAN,
            PageComplexity.RASTER_DIRTY,
            PageComplexity.RASTER_DEGRADED,
        }

        mapped_complexities = set(COMPLEXITY_ENGINE_MAP.keys())

        assert mapped_complexities == expected_complexities

    def test_engine_values_are_valid(self):
        """Engines devem ser strings válidas."""
        valid_engines = {"pdfplumber", "tesseract", "marker"}

        for engine in COMPLEXITY_ENGINE_MAP.values():
            assert isinstance(engine, str)
            assert engine in valid_engines

    def test_native_always_uses_pdfplumber(self):
        """Páginas NATIVE sempre usam pdfplumber."""
        assert (
            COMPLEXITY_ENGINE_MAP[PageComplexity.NATIVE_CLEAN] == "pdfplumber"
        )
        assert (
            COMPLEXITY_ENGINE_MAP[PageComplexity.NATIVE_WITH_ARTIFACTS]
            == "pdfplumber"
        )

    def test_degraded_always_uses_marker(self):
        """Páginas degradadas usam Marker (engine mais robusto)."""
        assert (
            COMPLEXITY_ENGINE_MAP[PageComplexity.RASTER_DEGRADED] == "marker"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
