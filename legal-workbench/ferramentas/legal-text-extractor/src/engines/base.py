"""
Base interfaces and data structures for extraction engines.

This module provides:
- ExtractionResult: Standardized output from all engines
- ExtractionEngine: Abstract base class for all extraction implementations
- Resource checking utilities
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import psutil


@dataclass
class ExtractionResult:
    """
    Standardized result from any extraction engine.

    Attributes:
        text: Extracted text content
        pages: Number of pages processed
        engine_used: Name of the engine that performed extraction
        confidence: Confidence score (0.0-1.0) based on:
            - Text quality (character density, readability)
            - OCR confidence (if applicable)
            - Native text ratio (higher is better)
        metadata: Additional engine-specific metadata
        warnings: List of warnings during extraction
    """
    text: str
    pages: int
    engine_used: str
    confidence: float
    metadata: dict[str, any] = None
    warnings: list[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.warnings is None:
            self.warnings = []

        # Clamp confidence to valid range
        self.confidence = max(0.0, min(1.0, self.confidence))


class ExtractionEngine(ABC):
    """
    Abstract base class for all extraction engines.

    Each engine must implement:
    - extract(): Main extraction logic
    - is_available(): Runtime availability check

    Class attributes (must be set by subclasses):
    - name: Human-readable engine name
    - min_ram_gb: Minimum RAM required (0 if no constraint)
    - dependencies: List of required packages
    """

    name: str = "UnknownEngine"
    min_ram_gb: float = 0.0
    dependencies: list[str] = []

    @abstractmethod
    def extract(self, pdf_path: Path) -> ExtractionResult:
        """
        Extract text from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            ExtractionResult with extracted text and metadata

        Raises:
            FileNotFoundError: PDF file not found
            RuntimeError: Extraction failed
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if engine is available at runtime.

        Verifies:
        - Required packages are installed
        - System resources meet requirements

        Returns:
            True if engine can be used, False otherwise
        """
        pass

    def check_resources(self) -> tuple[bool, str]:
        """
        Check if system has sufficient resources.

        Returns:
            (available, reason) tuple:
            - available: True if resources are sufficient
            - reason: Human-readable explanation if unavailable
        """
        # Check RAM requirement
        if self.min_ram_gb > 0:
            available_gb = psutil.virtual_memory().available / (1024 ** 3)
            if available_gb < self.min_ram_gb:
                return (
                    False,
                    f"{self.name} requires {self.min_ram_gb}GB RAM, "
                    f"only {available_gb:.1f}GB available"
                )

        # Check dependencies
        missing = []
        for dep in self.dependencies:
            try:
                __import__(dep)
            except ImportError:
                missing.append(dep)

        if missing:
            return (
                False,
                f"{self.name} missing dependencies: {', '.join(missing)}"
            )

        return (True, "")

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"name={self.name!r} "
            f"min_ram={self.min_ram_gb}GB>"
        )
