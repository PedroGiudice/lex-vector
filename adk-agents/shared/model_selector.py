"""
Dynamic model selection based on context size.

Strategy:
- Gemini 3 Pro: Default for reasoning, agentic tasks (<50k tokens)
- Gemini 2.5 Flash: Fast processing for medium contexts (50k-200k tokens)
- Gemini 2.5 Pro: Complex reasoning on large contexts (>200k tokens)
"""
from pathlib import Path
from typing import Union
from .config import Config, Models, Thresholds


class ModelSelector:
    """
    Selects optimal Gemini model based on context size.

    Usage:
        selector = ModelSelector()
        model = selector.for_file("/path/to/large_file.py")
        model = selector.for_text(long_text)
        model = selector.for_tokens(150_000)
    """

    # Approximate tokens per character (conservative estimate)
    CHARS_PER_TOKEN = 4

    def __init__(self):
        self.models = Config.MODELS
        self.thresholds = Config.THRESHOLDS

    def for_tokens(self, token_count: int) -> str:
        """Select model based on token count."""
        if token_count < self.thresholds.SMALL_CONTEXT_TOKENS:
            return self.models.GEMINI_3_PRO
        elif token_count < self.thresholds.MEDIUM_CONTEXT_TOKENS:
            return self.models.GEMINI_25_FLASH
        else:
            return self.models.GEMINI_25_PRO

    def for_text(self, text: str) -> str:
        """Select model based on text length."""
        estimated_tokens = len(text) // self.CHARS_PER_TOKEN
        return self.for_tokens(estimated_tokens)

    def for_file(self, file_path: Union[str, Path]) -> str:
        """Select model based on file size."""
        path = Path(file_path)
        if not path.exists():
            return self.models.GEMINI_3_PRO

        file_size = path.stat().st_size
        estimated_tokens = file_size // self.CHARS_PER_TOKEN
        return self.for_tokens(estimated_tokens)

    def for_files(self, file_paths: list[Union[str, Path]]) -> str:
        """Select model based on total size of multiple files."""
        total_size = 0
        for path in file_paths:
            p = Path(path)
            if p.exists():
                total_size += p.stat().st_size

        estimated_tokens = total_size // self.CHARS_PER_TOKEN
        return self.for_tokens(estimated_tokens)


def get_model_for_context(
    text: str = None,
    file_path: Union[str, Path] = None,
    file_paths: list[Union[str, Path]] = None,
    token_count: int = None,
) -> str:
    """
    Convenience function for model selection.

    Args:
        text: Text content to analyze
        file_path: Single file path
        file_paths: List of file paths
        token_count: Direct token count

    Returns:
        Model ID string for use in Agent() constructor

    Example:
        model = get_model_for_context(file_path="large_codebase.py")
        agent = Agent(model=model, ...)
    """
    selector = ModelSelector()

    if token_count is not None:
        return selector.for_tokens(token_count)
    elif file_paths is not None:
        return selector.for_files(file_paths)
    elif file_path is not None:
        return selector.for_file(file_path)
    elif text is not None:
        return selector.for_text(text)
    else:
        # Default: use best reasoning model
        return Config.MODELS.GEMINI_3_PRO
