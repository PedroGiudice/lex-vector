"""
Gestão de sessões de trabalho.

Responsabilidades:
- Criar/carregar/salvar sessões
- Manter histórico de mensagens
- Sincronizar com estrutura ~/.claude/projects/ do CLI nativo
- Listar sessões anteriores
"""
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import asdict
from .models import Session, Message, StatusLineData, ContentBlock, ContentType
from .exceptions import SessionNotFoundError

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Gerencia sessões de trabalho com persistência.

    Sessões são salvas em ~/.claude-ui/sessions/ como JSON.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Args:
            storage_dir: Diretório para salvar sessões.
                        Default: ~/.claude-ui/sessions/
        """
        self.storage_dir = storage_dir or Path.home() / ".claude-ui" / "sessions"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Session storage initialized at: {self.storage_dir}")

    def create_session(self, project_path: str) -> Session:
        """
        Cria nova sessão para um projeto.

        Args:
            project_path: Caminho do projeto

        Returns:
            Nova Session com ID único
        """
        now = datetime.now()
        session = Session(
            id=str(uuid.uuid4()),
            project_path=str(Path(project_path).resolve()),
            created_at=now,
            updated_at=now,
            messages=[],
            statusline=StatusLineData(),
            metadata={}
        )

        self.save_session(session)
        logger.info(f"Created new session: {session.id} for {project_path}")
        return session

    def get_session(self, session_id: str) -> Session:
        """
        Carrega sessão por ID.

        Args:
            session_id: ID da sessão

        Returns:
            Session carregada

        Raises:
            SessionNotFoundError: Se sessão não existe
        """
        session_file = self.storage_dir / f"{session_id}.json"

        if not session_file.exists():
            raise SessionNotFoundError(f"Session not found: {session_id}")

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return self._deserialize_session(data)

        except json.JSONDecodeError as e:
            raise SessionNotFoundError(f"Corrupted session file: {session_id}") from e

    def save_session(self, session: Session) -> None:
        """
        Salva sessão em disco.

        Args:
            session: Session a salvar
        """
        session.updated_at = datetime.now()
        session_file = self.storage_dir / f"{session.id}.json"

        try:
            data = self._serialize_session(session)

            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved session: {session.id}")

        except Exception as e:
            logger.error(f"Failed to save session {session.id}: {e}")
            raise

    def list_sessions(self, project_path: Optional[str] = None) -> List[Session]:
        """
        Lista sessões salvas.

        Args:
            project_path: Se fornecido, filtra por projeto

        Returns:
            Lista de sessões ordenadas por updated_at (mais recente primeiro)
        """
        sessions = []

        for session_file in self.storage_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                session = self._deserialize_session(data)

                # Filter by project if specified
                if project_path:
                    normalized_path = str(Path(project_path).resolve())
                    if session.project_path != normalized_path:
                        continue

                sessions.append(session)

            except Exception as e:
                logger.warning(f"Failed to load session {session_file}: {e}")
                continue

        # Sort by updated_at, most recent first
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """
        Deleta sessão.

        Args:
            session_id: ID da sessão

        Returns:
            True se deletou, False se não existia
        """
        session_file = self.storage_dir / f"{session_id}.json"

        if session_file.exists():
            session_file.unlink()
            logger.info(f"Deleted session: {session_id}")
            return True

        return False

    def add_message(self, session: Session, message: Message) -> None:
        """
        Adiciona mensagem à sessão e salva.

        Args:
            session: Sessão alvo
            message: Mensagem a adicionar
        """
        session.messages.append(message)
        self.save_session(session)
        logger.debug(f"Added message to session {session.id}: {message.role}")

    def update_statusline(self, session: Session, data: StatusLineData) -> None:
        """
        Atualiza statusline da sessão.

        Args:
            session: Sessão alvo
            data: Novos dados de statusline
        """
        session.statusline = data
        self.save_session(session)

    def get_native_sessions(self) -> List[Dict[str, Any]]:
        """
        Lista sessões do CLI nativo em ~/.claude/projects/.

        Útil para sincronização/import.

        Returns:
            Lista de dicionários com info das sessões nativas
        """
        native_dir = Path.home() / ".claude" / "projects"
        sessions = []

        if not native_dir.exists():
            return sessions

        for project_dir in native_dir.iterdir():
            if project_dir.is_dir():
                # Look for session files (typically .jsonl)
                for session_file in project_dir.glob("*.jsonl"):
                    sessions.append({
                        'project': project_dir.name,
                        'file': str(session_file),
                        'modified': datetime.fromtimestamp(session_file.stat().st_mtime),
                        'size': session_file.stat().st_size
                    })

        return sessions

    def _serialize_session(self, session: Session) -> Dict[str, Any]:
        """Converte Session para dicionário serializável."""
        return {
            'id': session.id,
            'project_path': session.project_path,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'messages': [self._serialize_message(m) for m in session.messages],
            'statusline': self._serialize_statusline(session.statusline),
            'metadata': session.metadata
        }

    def _deserialize_session(self, data: Dict[str, Any]) -> Session:
        """Converte dicionário para Session."""
        return Session(
            id=data['id'],
            project_path=data['project_path'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            messages=[self._deserialize_message(m) for m in data.get('messages', [])],
            statusline=self._deserialize_statusline(data.get('statusline', {})),
            metadata=data.get('metadata', {})
        )

    def _serialize_message(self, message: Message) -> Dict[str, Any]:
        """Converte Message para dicionário."""
        return {
            'role': message.role,
            'content': message.content,
            'blocks': [self._serialize_block(b) for b in message.blocks],
            'timestamp': message.timestamp.isoformat(),
            'metadata': message.metadata
        }

    def _deserialize_message(self, data: Dict[str, Any]) -> Message:
        """Converte dicionário para Message."""
        return Message(
            role=data['role'],
            content=data['content'],
            blocks=[self._deserialize_block(b) for b in data.get('blocks', [])],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {})
        )

    def _serialize_block(self, block: ContentBlock) -> Dict[str, Any]:
        """Converte ContentBlock para dicionário."""
        return {
            'type': block.type.value,
            'content': block.content,
            'language': block.language,
            'tool_name': block.tool_name,
            'timestamp': block.timestamp.isoformat(),
            'metadata': block.metadata
        }

    def _deserialize_block(self, data: Dict[str, Any]) -> ContentBlock:
        """Converte dicionário para ContentBlock."""
        return ContentBlock(
            type=ContentType(data['type']),
            content=data['content'],
            language=data.get('language', ''),
            tool_name=data.get('tool_name', ''),
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {})
        )

    def _serialize_statusline(self, statusline: StatusLineData) -> Dict[str, Any]:
        """Converte StatusLineData para dicionário."""
        return {
            'model': statusline.model,
            'model_display': statusline.model_display,
            'current_dir': statusline.current_dir,
            'git_branch': statusline.git_branch,
            'git_dirty': statusline.git_dirty,
            'git_ahead': statusline.git_ahead,
            'git_behind': statusline.git_behind,
            'context_percent': statusline.context_percent,
            'context_tokens': statusline.context_tokens,
            'context_limit': statusline.context_limit,
            'session_cost': statusline.session_cost,
            'session_messages': statusline.session_messages,
            'session_duration': statusline.session_duration,
            'raw_json': statusline.raw_json
        }

    def _deserialize_statusline(self, data: Dict[str, Any]) -> StatusLineData:
        """Converte dicionário para StatusLineData."""
        if not data:
            return StatusLineData()

        return StatusLineData(
            model=data.get('model', ''),
            model_display=data.get('model_display', ''),
            current_dir=data.get('current_dir', ''),
            git_branch=data.get('git_branch', ''),
            git_dirty=data.get('git_dirty', False),
            git_ahead=data.get('git_ahead', 0),
            git_behind=data.get('git_behind', 0),
            context_percent=data.get('context_percent', 0.0),
            context_tokens=data.get('context_tokens', 0),
            context_limit=data.get('context_limit', 0),
            session_cost=data.get('session_cost', 0.0),
            session_messages=data.get('session_messages', 0),
            session_duration=data.get('session_duration', ''),
            raw_json=data.get('raw_json', {})
        )
