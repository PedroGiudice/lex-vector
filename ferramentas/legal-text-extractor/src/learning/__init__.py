"""Learning system for continuous improvement of section extraction"""

# Core schemas
from .schemas import (
    ValidationStatus,
    SectionType,
    ExtractedSection,
    GroundTruthSection,
    ExtractionResult,
    FewShotExample,
    PerformanceMetrics
)

# Storage
from .storage import LearningStorage

# Pattern extraction
from .pattern_extractor import PatternExtractor

# Few-shot management
from .few_shot_manager import FewShotManager

# Metrics tracking
from .metrics_tracker import MetricsTracker

# Prompt versioning
from .prompt_versioner import PromptVersioner, PromptVersion

# Self-improvement (M3.2)
from .self_improver import SelfImprover, ErrorAnalysis

# A/B testing (M3.3)
from .ab_tester import ABTester, ABTest, ABTestResult

__all__ = [
    # Schemas
    "ValidationStatus",
    "SectionType",
    "ExtractedSection",
    "GroundTruthSection",
    "ExtractionResult",
    "FewShotExample",
    "PerformanceMetrics",
    # Storage
    "LearningStorage",
    # Pattern extraction
    "PatternExtractor",
    # Few-shot
    "FewShotManager",
    # Metrics
    "MetricsTracker",
    # Versioning
    "PromptVersioner",
    "PromptVersion",
    # Self-improvement
    "SelfImprover",
    "ErrorAnalysis",
    # A/B testing
    "ABTester",
    "ABTest",
    "ABTestResult",
]
