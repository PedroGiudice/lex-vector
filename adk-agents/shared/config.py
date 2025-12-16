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

    # Primary - for reasoning, agentic tasks
    GEMINI_3_PRO = "gemini-3-pro-preview"

    # Long context - for large files
    GEMINI_25_PRO = "gemini-2.5-pro"      # 1M tokens, complex reasoning
    GEMINI_25_FLASH = "gemini-2.5-flash"  # 1M tokens, faster/cheaper

    # Embedding - for RAG, semantic search
    EMBEDDING = "gemini-embedding-001"


@dataclass(frozen=True)
class Thresholds:
    """Context size thresholds for model selection"""

    # Below this: use Gemini 3 Pro (best reasoning)
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
