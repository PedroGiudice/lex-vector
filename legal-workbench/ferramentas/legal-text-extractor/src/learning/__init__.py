"""Learning system for continuous improvement of section extraction"""

# Core schemas
# A/B testing (M3.3)
from .ab_tester import ABTest, ABTester, ABTestResult

# Few-shot management
from .few_shot_manager import FewShotManager

# Metrics tracking
from .metrics_tracker import MetricsTracker

# Pattern extraction
from .pattern_extractor import PatternExtractor

# Prompt versioning
from .prompt_versioner import PromptVersion, PromptVersioner
from .schemas import (
    ExtractedSection,
    ExtractionResult,
    FewShotExample,
    GroundTruthSection,
    PerformanceMetrics,
    SectionType,
    ValidationStatus,
)

# Self-improvement (M3.2)
from .self_improver import ErrorAnalysis, SelfImprover

# Storage
from .storage import LearningStorage

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
