"""
Application configuration.

Loads settings from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


@dataclass
class Config:
    """Application configuration loaded from environment."""

    # App identity
    APP_NAME: str = os.getenv("APP_NAME", "Legal Workbench")
    APP_VERSION: str = os.getenv("APP_VERSION", "3.0.0")

    # Server
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    PORT: int = int(os.getenv("PORT", "5001"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    MODULES_DIR: Path = BASE_DIR / "modules"
    STATIC_DIR: Path = BASE_DIR / "static"

    # Theme
    DEFAULT_THEME: str = os.getenv("DEFAULT_THEME", "shared")

    # Backend services
    STJ_API_URL: str = os.getenv("STJ_API_URL", "http://localhost:8000")

    @classmethod
    def validate(cls) -> "Config":
        """Validate configuration and return instance."""
        config = cls()

        # Ensure required directories exist
        config.MODULES_DIR.mkdir(parents=True, exist_ok=True)
        config.STATIC_DIR.mkdir(parents=True, exist_ok=True)

        return config


# Global config instance
config = Config.validate()
