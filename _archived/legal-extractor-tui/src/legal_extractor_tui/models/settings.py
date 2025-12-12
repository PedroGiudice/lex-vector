"""Application settings models.

Pydantic models for UI and pipeline settings with environment support.
"""

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class UISettings(BaseModel):
    """User interface configuration.

    Attributes:
        theme: Theme name ('vibe' or 'terminal')
        show_sidebar: Whether to display sidebar by default
        show_timestamps: Whether to show timestamps in logs
    """
    theme: str = Field(default="vibe", pattern="^(vibe|terminal)$")
    show_sidebar: bool = Field(default=True)
    show_timestamps: bool = Field(default=True)


class PipelineSettings(BaseModel):
    """Pipeline execution configuration.

    Attributes:
        timeout_s: Default timeout for pipeline steps (seconds)
        stop_on_error: Whether to stop pipeline on first error
    """
    timeout_s: int = Field(default=60, ge=1)
    stop_on_error: bool = Field(default=True)


class AppSettings(BaseSettings):
    """Application-wide settings with environment variable support.

    Environment variables can override settings:
        - TUI_THEME: Override UI theme
        - TUI_SHOW_SIDEBAR: Override sidebar visibility
        - TUI_PIPELINE_TIMEOUT: Override pipeline timeout

    Attributes:
        ui: UI-related settings
        pipeline: Pipeline execution settings
    """
    model_config = SettingsConfigDict(
        env_prefix="TUI_",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    ui: UISettings = Field(default_factory=UISettings)
    pipeline: PipelineSettings = Field(default_factory=PipelineSettings)

    @classmethod
    def load(cls) -> "AppSettings":
        """Load settings from environment and defaults.

        Returns:
            AppSettings instance with merged configuration
        """
        return cls()
