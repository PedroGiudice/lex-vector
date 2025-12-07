"""
Pipeline - Orchestrates complete PDF extraction workflow.

Components:
- PipelineOrchestrator: Main orchestrator integrating all extraction components
- PipelineResult: Structured result from complete extraction process

Usage:
    from src.pipeline import PipelineOrchestrator, PipelineResult

    # With learning (ContextStore active)
    orchestrator = PipelineOrchestrator(
        context_db_path=Path("data/context.db"),
        caso_info={"numero_cnj": "...", "sistema": "pje"}
    )

    # Without learning (one-off extraction)
    orchestrator = PipelineOrchestrator()

    # Process PDF
    result = orchestrator.process(Path("documento.pdf"))
    print(result.text)
    print(f"Learned {result.patterns_learned} patterns")
"""

from .orchestrator import PipelineOrchestrator, PipelineResult

__all__ = [
    "PipelineOrchestrator",
    "PipelineResult",
]
