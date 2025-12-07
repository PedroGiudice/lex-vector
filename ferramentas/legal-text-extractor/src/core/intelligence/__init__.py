"""
Modulo de inteligencia para classificacao semantica de pecas processuais.

Componentes:
- definitions: Carrega e gerencia a taxonomia legal
- cleaning_rules: Padroes regex para limpeza avancada
- cleaner_advanced: Limpeza fina de texto juridico
- segmenter: Segmentacao de documentos em blocos logicos
- boundary_config: Configuracao adaptavel para deteccao de boundaries
- boundary_detector: Deteccao de boundaries entre documentos genericos
"""

from .definitions import TaxonomyLoader, LegalTaxonomy, get_taxonomy, reload_taxonomy
from .cleaning_rules import CLEANING_PATTERNS, CleaningRules
from .cleaner_advanced import AdvancedCleaner
from .segmenter import DocumentSegmenter
from .boundary_config import (
    BoundaryConfig,
    BoundaryPattern,
    DocumentClass,
    get_conservative_config,
    get_formal_document_config,
    get_compact_document_config,
    get_disabled_config,
)
from .boundary_detector import (
    BoundaryDetector,
    detect_boundaries_conservative,
    has_boundary_markers,
)

__all__ = [
    # Taxonomia
    "TaxonomyLoader",
    "LegalTaxonomy",
    "get_taxonomy",
    "reload_taxonomy",
    # Limpeza
    "CLEANING_PATTERNS",
    "CleaningRules",
    "AdvancedCleaner",
    # Segmentacao
    "DocumentSegmenter",
    # Boundary Detection
    "BoundaryConfig",
    "BoundaryPattern",
    "DocumentClass",
    "BoundaryDetector",
    "get_conservative_config",
    "get_formal_document_config",
    "get_compact_document_config",
    "get_disabled_config",
    "detect_boundaries_conservative",
    "has_boundary_markers",
]
