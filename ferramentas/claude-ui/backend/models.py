"""Dataclasses e tipos para o backend."""
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime

class CLIState(Enum):
    """Estado atual do processo CLI."""
    DISCONNECTED = "disconnected"
    STARTING = "starting"
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    ERROR = "error"

class ContentType(Enum):
    """Tipo de bloco de conteúdo no output."""
    TEXT = "text"
    CODE = "code"
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    SYSTEM = "system"

@dataclass
class ContentBlock:
    """Bloco individual de conteúdo parseado."""
    type: ContentType
    content: str
    language: str = ""          # Para CODE blocks
    tool_name: str = ""         # Para TOOL_CALL blocks
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StatusLineData:
    """Dados estruturados da statusline do CLI."""
    model: str = ""
    model_display: str = ""
    current_dir: str = ""
    git_branch: str = ""
    git_dirty: bool = False
    git_ahead: int = 0
    git_behind: int = 0
    context_percent: float = 0.0
    context_tokens: int = 0
    context_limit: int = 0
    session_cost: float = 0.0
    session_messages: int = 0
    session_duration: str = ""
    raw_json: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Message:
    """Mensagem no histórico de chat."""
    role: str                   # "user" | "assistant" | "system"
    content: str                # Conteúdo raw
    blocks: List[ContentBlock] = field(default_factory=list)  # Conteúdo parseado
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Session:
    """Sessão de trabalho com o CLI."""
    id: str
    project_path: str
    created_at: datetime
    updated_at: datetime
    messages: List[Message] = field(default_factory=list)
    statusline: StatusLineData = field(default_factory=StatusLineData)
    metadata: Dict[str, Any] = field(default_factory=dict)
