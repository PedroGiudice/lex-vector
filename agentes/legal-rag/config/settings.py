"""
agentes/legal-rag/config/settings.py

Gerenciamento de configurações do sistema RAG.
Carrega config.json e variáveis de ambiente.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class PathConfig:
    """Configuração de paths do sistema."""
    data_root: Path
    corpus_dir: Path
    vector_store_dir: Path
    cache_dir: Path
    logs_dir: Path

    @classmethod
    def from_dict(cls, config: Dict[str, str], base_dir: Optional[Path] = None) -> "PathConfig":
        """
        Cria PathConfig a partir de dicionário.

        Args:
            config: Dicionário com paths
            base_dir: Diretório base para paths relativos

        Returns:
            PathConfig instance
        """
        # Resolver data_root com variáveis de ambiente
        data_root_str = config.get("data_root", "")

        # Suportar variáveis de ambiente no formato ${VAR:-default}
        data_root_str = _resolve_env_vars(data_root_str)

        data_root = Path(data_root_str)

        # Criar outros paths
        corpus_dir = _resolve_path(config.get("corpus_dir", ""), data_root)
        vector_store_dir = _resolve_path(config.get("vector_store_dir", ""), data_root)
        cache_dir = _resolve_path(config.get("cache_dir", ""), data_root)
        logs_dir = _resolve_path(config.get("logs_dir", ""), data_root)

        return cls(
            data_root=data_root,
            corpus_dir=corpus_dir,
            vector_store_dir=vector_store_dir,
            cache_dir=cache_dir,
            logs_dir=logs_dir
        )

    def ensure_dirs(self):
        """Cria diretórios se não existirem."""
        for dir_path in [
            self.data_root,
            self.corpus_dir,
            self.vector_store_dir,
            self.cache_dir,
            self.logs_dir
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Diretório garantido: {dir_path}")


@dataclass
class Settings:
    """Configurações completas do sistema RAG."""

    # Project info
    project_name: str
    project_version: str
    project_description: str

    # Paths
    paths: PathConfig

    # Configurations
    vector_store: Dict[str, Any]
    embeddings: Dict[str, Any]
    chunking: Dict[str, Any]
    retrieval: Dict[str, Any]
    llm: Dict[str, Any]
    indexing: Dict[str, Any]
    normalization: Dict[str, Any]
    analysis: Dict[str, Any]
    cache: Dict[str, Any]
    logging: Dict[str, Any]
    performance: Dict[str, Any]

    # Lists
    tribunais_validos: list[str]
    areas_direito: list[str]

    # Templates
    prompt_templates: Dict[str, str]

    # Config file path (for reference)
    _config_file: Path = field(default=None, repr=False)

    @classmethod
    def load_from_file(cls, config_path: Optional[Path] = None) -> "Settings":
        """
        Carrega configurações do arquivo JSON.

        Args:
            config_path: Path para config.json. Se None, usa padrão.

        Returns:
            Settings instance

        Raises:
            FileNotFoundError: Se config não encontrado
            json.JSONDecodeError: Se JSON inválido
        """
        if config_path is None:
            # Tentar encontrar config.json no diretório do agente
            module_dir = Path(__file__).parent.parent
            config_path = module_dir / "config.json"

        if not config_path.exists():
            raise FileNotFoundError(
                f"Config file não encontrado: {config_path}\n"
                f"Crie um arquivo config.json ou especifique o path."
            )

        logger.info(f"Carregando configurações de: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        # Criar PathConfig
        paths = PathConfig.from_dict(config_data.get("paths", {}))

        # Extrair seções
        project = config_data.get("project", {})

        return cls(
            project_name=project.get("name", "legal-rag-system"),
            project_version=project.get("version", "1.0.0"),
            project_description=project.get("description", ""),
            paths=paths,
            vector_store=config_data.get("vector_store", {}),
            embeddings=config_data.get("embeddings", {}),
            chunking=config_data.get("chunking", {}),
            retrieval=config_data.get("retrieval", {}),
            llm=config_data.get("llm", {}),
            indexing=config_data.get("indexing", {}),
            normalization=config_data.get("normalization", {}),
            analysis=config_data.get("analysis", {}),
            cache=config_data.get("cache", {}),
            logging=config_data.get("logging", {}),
            performance=config_data.get("performance", {}),
            tribunais_validos=config_data.get("tribunais_validos", []),
            areas_direito=config_data.get("areas_direito", []),
            prompt_templates=config_data.get("prompt_templates", {}),
            _config_file=config_path
        )

    def get_anthropic_api_key(self) -> str:
        """
        Obtém API key da Anthropic de variável de ambiente.

        Returns:
            API key

        Raises:
            ValueError: Se API key não configurada
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY não configurada. "
                "Configure via: export ANTHROPIC_API_KEY=sua_chave"
            )

        return api_key

    def setup_logging(self):
        """Configura logging baseado nas settings."""
        from loguru import logger as loguru_logger
        import sys

        # Remover handlers padrão
        loguru_logger.remove()

        # Adicionar handler para stdout
        loguru_logger.add(
            sys.stdout,
            format=self.logging.get("format", "{message}"),
            level=self.logging.get("level", "INFO"),
            colorize=self.logging.get("colorize", True)
        )

        # Adicionar handler para arquivo
        log_file = self.paths.logs_dir / "legal-rag.log"
        loguru_logger.add(
            log_file,
            format=self.logging.get("format", "{message}"),
            level=self.logging.get("level", "INFO"),
            rotation=self.logging.get("rotation", "500 MB"),
            retention=self.logging.get("retention", "30 days"),
            compression="zip"
        )

        logger.info("Logging configurado")

    def validate(self) -> bool:
        """
        Valida configurações.

        Returns:
            True se válido

        Raises:
            ValueError: Se configuração inválida
        """
        # Validar LLM config
        if not self.llm.get("model"):
            raise ValueError("llm.model não configurado")

        # Validar embeddings
        if not self.embeddings.get("model_path"):
            raise ValueError("embeddings.model_path não configurado")

        # Validar retrieval weights
        retrieval_weights = (
            self.retrieval.get("dense_weight", 0) +
            self.retrieval.get("sparse_weight", 0)
        )
        if abs(retrieval_weights - 1.0) > 0.01:
            raise ValueError(
                f"retrieval weights devem somar 1.0, "
                f"mas somam {retrieval_weights}"
            )

        logger.info("Configurações validadas com sucesso")
        return True


def _resolve_env_vars(value: str) -> str:
    """
    Resolve variáveis de ambiente no formato ${VAR:-default}.

    Args:
        value: String com possíveis variáveis

    Returns:
        String com variáveis resolvidas

    Example:
        >>> _resolve_env_vars("${HOME}/data")
        '/home/user/data'
        >>> _resolve_env_vars("${MISSING:-/default/path}")
        '/default/path'
    """
    import re

    # Padrão: ${VAR} ou ${VAR:-default}
    pattern = r'\$\{([^}:]+)(?::-([^}]+))?\}'

    def replacer(match):
        var_name = match.group(1)
        default_value = match.group(2) if match.group(2) else ""

        return os.getenv(var_name, default_value)

    return re.sub(pattern, replacer, value)


def _resolve_path(path_str: str, base: Path) -> Path:
    """
    Resolve path substituindo ${DATA_ROOT} e variáveis de ambiente.

    Args:
        path_str: String do path
        base: Path base para substituir ${DATA_ROOT}

    Returns:
        Path resolvido
    """
    # Substituir ${DATA_ROOT}
    path_str = path_str.replace("${DATA_ROOT}", str(base))

    # Resolver outras variáveis de ambiente
    path_str = _resolve_env_vars(path_str)

    return Path(path_str)


# Singleton global para configurações
_settings: Optional[Settings] = None


def get_settings(config_path: Optional[Path] = None, reload: bool = False) -> Settings:
    """
    Obtém singleton de configurações.

    Args:
        config_path: Path opcional para config.json
        reload: Se True, recarrega configurações

    Returns:
        Settings instance
    """
    global _settings

    if _settings is None or reload:
        _settings = Settings.load_from_file(config_path)
        _settings.validate()
        _settings.paths.ensure_dirs()

    return _settings


if __name__ == "__main__":
    # Teste
    import sys
    from loguru import logger as loguru_logger

    # Setup logging básico
    loguru_logger.remove()
    loguru_logger.add(sys.stdout, level="INFO")

    # Carregar settings
    settings = get_settings()

    print(f"\n{'='*60}")
    print(f"Projeto: {settings.project_name} v{settings.project_version}")
    print(f"Descrição: {settings.project_description}")
    print(f"{'='*60}\n")

    print("Paths:")
    print(f"  Data root: {settings.paths.data_root}")
    print(f"  Corpus: {settings.paths.corpus_dir}")
    print(f"  Vector store: {settings.paths.vector_store_dir}")
    print(f"  Cache: {settings.paths.cache_dir}")
    print(f"  Logs: {settings.paths.logs_dir}")

    print("\nEmbeddings:")
    print(f"  Model: {settings.embeddings.get('model_path')}")
    print(f"  Dimension: {settings.embeddings.get('embedding_dim')}")
    print(f"  Max length: {settings.embeddings.get('max_seq_length')}")

    print("\nRetrieval:")
    print(f"  Strategy: {settings.retrieval.get('strategy')}")
    print(f"  Dense weight: {settings.retrieval.get('dense_weight')}")
    print(f"  Sparse weight: {settings.retrieval.get('sparse_weight')}")

    print("\nLLM:")
    print(f"  Model: {settings.llm.get('model')}")
    print(f"  Max tokens: {settings.llm.get('max_tokens')}")
    print(f"  Temperature: {settings.llm.get('temperature')}")

    print("\nTribunais suportados:")
    print(f"  Total: {len(settings.tribunais_validos)}")
    print(f"  Exemplos: {', '.join(settings.tribunais_validos[:10])}")

    print("\nÁreas do direito:")
    print(f"  Total: {len(settings.areas_direito)}")
    print(f"  Exemplos: {', '.join(settings.areas_direito[:5])}")

    print(f"\n{'='*60}\n")
    print("✓ Configurações carregadas com sucesso!")
