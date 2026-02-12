"""Módulo de integração com Gemini."""

from .client import GeminiClient, GeminiConfig, GeminiResponse
from .schemas import (
    ClassificationResult,
    CleanedSection,
    CleaningResult,
    PecaType,
    SectionClassification,
)

__all__ = [
    "GeminiClient",
    "GeminiConfig",
    "GeminiResponse",
    "PecaType",
    "SectionClassification",
    "ClassificationResult",
    "CleanedSection",
    "CleaningResult",
]
