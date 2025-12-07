"""
Captura e parse de dados da statusline do Claude Code CLI.

O CLI pode ser configurado para emitir JSON estruturado com informações
da sessão (model, tokens, git, etc.). Este módulo intercepta e parseia
esses dados.
"""
import json
import re
import logging
from typing import Optional, Dict, Any
from .models import StatusLineData

logger = logging.getLogger(__name__)


class StatusLineParser:
    """
    Parser para dados de statusline do CLI.

    O Claude Code emite dados de statusline em formato JSON via hook configurável.
    Exemplo de JSON recebido:

    {
        "model": {"name": "claude-sonnet-4-20250514", "display_name": "Claude Sonnet 4"},
        "workspace": {"current_dir": "/home/user/project"},
        "git": {"branch": "main", "dirty": false, "ahead": 0, "behind": 0},
        "context": {"percent": 45.2, "tokens": 12000, "limit": 128000},
        "session": {"cost": 0.05, "messages": 10, "duration": "00:15:32"}
    }
    """

    # Known keys that indicate this is statusline JSON
    STATUSLINE_KEYS = {'model', 'workspace', 'git', 'context', 'session'}

    # Pattern to find JSON in mixed output
    JSON_PATTERN = re.compile(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}')

    def __init__(self):
        """Initialize the parser."""
        self._last_data: Optional[StatusLineData] = None

    def parse_json(self, json_str: str) -> Optional[StatusLineData]:
        """
        Parse JSON de statusline em StatusLineData.

        Args:
            json_str: String JSON do CLI

        Returns:
            StatusLineData populado ou None se parse falhar
        """
        try:
            data = json.loads(json_str)

            if not isinstance(data, dict):
                return None

            result = StatusLineData()
            result.raw_json = data

            # Parse model info
            if 'model' in data:
                model_data = data['model']
                result.model = model_data.get('name', '')
                result.model_display = model_data.get('display_name', result.model)

            # Parse workspace info
            if 'workspace' in data:
                workspace = data['workspace']
                result.current_dir = workspace.get('current_dir', '')

            # Parse git info
            if 'git' in data:
                git_data = data['git']
                result.git_branch = git_data.get('branch', '')
                result.git_dirty = git_data.get('dirty', False)
                result.git_ahead = git_data.get('ahead', 0)
                result.git_behind = git_data.get('behind', 0)

            # Parse context info
            if 'context' in data:
                ctx = data['context']
                result.context_percent = float(ctx.get('percent', 0.0))
                result.context_tokens = int(ctx.get('tokens', 0))
                result.context_limit = int(ctx.get('limit', 0))

            # Parse session info
            if 'session' in data:
                session = data['session']
                result.session_cost = float(session.get('cost', 0.0))
                result.session_messages = int(session.get('messages', 0))
                result.session_duration = session.get('duration', '')

            self._last_data = result
            logger.debug(f"Parsed statusline: model={result.model}, context={result.context_percent}%")
            return result

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse statusline JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing statusline: {e}")
            return None

    def is_statusline_json(self, line: str) -> bool:
        """
        Detecta se linha contém JSON de statusline.

        Heurística: começa com { e contém chaves conhecidas.
        """
        line = line.strip()

        if not line.startswith('{'):
            return False

        try:
            data = json.loads(line)
            if not isinstance(data, dict):
                return False

            # Check if it has any known statusline keys
            return bool(self.STATUSLINE_KEYS & set(data.keys()))

        except json.JSONDecodeError:
            return False

    def extract_from_output(self, output: str) -> Optional[StatusLineData]:
        """
        Extrai statusline data de output misto.

        Útil quando statusline JSON vem misturado com outro output.

        Args:
            output: Output que pode conter JSON misturado com texto

        Returns:
            StatusLineData se encontrado, None caso contrário
        """
        # Try to find JSON objects in the output
        for match in self.JSON_PATTERN.finditer(output):
            json_str = match.group()

            if self.is_statusline_json(json_str):
                result = self.parse_json(json_str)
                if result:
                    return result

        # Also try line by line (JSON might be on its own line)
        for line in output.split('\n'):
            line = line.strip()
            if self.is_statusline_json(line):
                result = self.parse_json(line)
                if result:
                    return result

        return None

    def get_last_data(self) -> Optional[StatusLineData]:
        """
        Retorna último StatusLineData parseado com sucesso.

        Returns:
            Último StatusLineData ou None
        """
        return self._last_data

    def clear(self) -> None:
        """Limpa dados armazenados."""
        self._last_data = None

    def parse_partial(self, data: Dict[str, Any]) -> StatusLineData:
        """
        Parse dados parciais de statusline (já deserializados).

        Útil quando dados vêm de fonte que não é JSON string.

        Args:
            data: Dicionário com dados parciais

        Returns:
            StatusLineData com campos preenchidos
        """
        result = StatusLineData()
        result.raw_json = data

        # Direct mappings for flat structures
        result.model = data.get('model', '')
        result.model_display = data.get('model_display', result.model)
        result.current_dir = data.get('current_dir', data.get('cwd', ''))
        result.git_branch = data.get('git_branch', data.get('branch', ''))
        result.git_dirty = data.get('git_dirty', data.get('dirty', False))
        result.git_ahead = int(data.get('git_ahead', data.get('ahead', 0)))
        result.git_behind = int(data.get('git_behind', data.get('behind', 0)))
        result.context_percent = float(data.get('context_percent', data.get('percent', 0.0)))
        result.context_tokens = int(data.get('context_tokens', data.get('tokens', 0)))
        result.context_limit = int(data.get('context_limit', data.get('limit', 0)))
        result.session_cost = float(data.get('session_cost', data.get('cost', 0.0)))
        result.session_messages = int(data.get('session_messages', data.get('messages', 0)))
        result.session_duration = data.get('session_duration', data.get('duration', ''))

        self._last_data = result
        return result

    def format_summary(self, data: Optional[StatusLineData] = None) -> str:
        """
        Formata StatusLineData em string legível.

        Args:
            data: StatusLineData a formatar (ou usa último parseado)

        Returns:
            String formatada
        """
        data = data or self._last_data
        if not data:
            return "No statusline data available"

        parts = []

        if data.model_display:
            parts.append(f"Model: {data.model_display}")

        if data.current_dir:
            parts.append(f"Dir: {data.current_dir}")

        if data.git_branch:
            git_status = data.git_branch
            if data.git_dirty:
                git_status += "*"
            if data.git_ahead:
                git_status += f" ↑{data.git_ahead}"
            if data.git_behind:
                git_status += f" ↓{data.git_behind}"
            parts.append(f"Git: {git_status}")

        if data.context_limit:
            parts.append(f"Context: {data.context_percent:.1f}% ({data.context_tokens:,}/{data.context_limit:,})")

        if data.session_cost > 0:
            parts.append(f"Cost: ${data.session_cost:.4f}")

        if data.session_duration:
            parts.append(f"Duration: {data.session_duration}")

        return " | ".join(parts)
