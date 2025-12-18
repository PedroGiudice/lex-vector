"""
Configuration for ADK agents.
Centralizes model IDs and thresholds.
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Models:
    """Available Gemini models (Dec 2025)"""

    # Latest - Gemini 3 Pro Preview (best reasoning, limited function calling)
    GEMINI_3_PRO_PREVIEW = "gemini-3-pro-preview"

    # Primary - for agentic tasks WITH function calling
    GEMINI_25_FLASH = "gemini-2.5-flash"  # 1M tokens, fast, supports tools
    GEMINI_25_PRO = "gemini-2.5-pro"      # 1M tokens, complex reasoning, supports tools

    # Aliases for clarity
    BEST_REASONING = "gemini-3-pro-preview"       # Best reasoning but limited tool support
    BEST_AGENTIC = "gemini-2.5-flash"             # Best for agents with tools
    BEST_LONG_CONTEXT = "gemini-2.5-pro"          # Best for large files + reasoning

    # Embedding - for RAG, semantic search
    EMBEDDING = "gemini-embedding-001"


@dataclass(frozen=True)
class Thresholds:
    """Context size thresholds for model selection"""

    # Below this: use faster model
    SMALL_CONTEXT_TOKENS = 50_000

    # 50k-200k: use Gemini 2.5 Flash (fast, long context)
    MEDIUM_CONTEXT_TOKENS = 200_000

    # Above 200k: use Gemini 2.5 Pro (best long context reasoning)
    # Up to 1M tokens supported


class Config:
    """Global configuration"""

    MODELS = Models()
    THRESHOLDS = Thresholds()

    @staticmethod
    def get_api_key() -> str:
        """Get Gemini API key from environment"""
        key = os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError(
                "GOOGLE_API_KEY not set. "
                "Get one at: https://aistudio.google.com/apikey"
            )
        return key

    @staticmethod
    def get_model_for_task(needs_tools: bool = True, context_size: int = 0) -> str:
        """
        Select the best model for a given task.

        Args:
            needs_tools: Whether the task requires function calling
            context_size: Approximate context size in tokens

        Returns:
            Model ID string
        """
        if needs_tools:
            # Gemini 3 Pro Preview has limited tool support, use 2.5 Flash for tools
            if context_size > Config.THRESHOLDS.MEDIUM_CONTEXT_TOKENS:
                return Config.MODELS.GEMINI_25_PRO
            return Config.MODELS.GEMINI_25_FLASH
        else:
            # No tools needed - use best reasoning model
            return Config.MODELS.GEMINI_3_PRO_PREVIEW
