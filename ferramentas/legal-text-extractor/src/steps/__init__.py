"""
Pipeline de extracao em 4 estagios.

Estagio 1: step_01_layout.py (Cartografo) - Analise de layout e zoning
Estagio 2: step_02_vision.py (Saneador) - Processamento de imagem
Estagio 3: step_03_extract.py (Extrator) - Extracao de texto
Estagio 4: step_04_classify.py (Bibliotecario) - Classificacao semantica
"""

from .step_01_layout import LayoutAnalyzer
from .step_03_extract import TextExtractor
from .step_04_classify import SemanticClassifier

# VisionProcessor requer cv2 - import condicional
try:
    from .step_02_vision import VisionProcessor
except ImportError:
    VisionProcessor = None  # type: ignore

__all__ = ["LayoutAnalyzer", "VisionProcessor", "TextExtractor", "SemanticClassifier"]
