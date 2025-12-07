"""Sistema de versionamento de prompts"""
import logging
import hashlib
from pathlib import Path
from typing import Optional, Literal
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import yaml

logger = logging.getLogger(__name__)


@dataclass
class PromptVersion:
    """Versão de um prompt"""
    version_id: str  # v1, v2, v3, etc
    content: str     # Conteúdo do prompt
    created_at: datetime
    created_by: Literal["human", "auto"] = "human"
    parent_version: Optional[str] = None  # Versão que originou esta (se auto)

    # Metadata
    description: str = ""
    tags: list[str] = None

    # Performance (preenchido após testes)
    tests_count: int = 0
    avg_f1_score: Optional[float] = None
    avg_precision: Optional[float] = None
    avg_recall: Optional[float] = None

    # Status
    status: Literal["active", "testing", "deprecated", "promoted"] = "testing"

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)

    def to_dict(self) -> dict:
        """Converte para dict (JSON-serializable)"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "PromptVersion":
        """Cria instância a partir de dict"""
        return cls(**data)


class PromptVersioner:
    """
    Gerencia versionamento de prompts.

    Estrutura de storage:
        data/prompts/
        ├── versions/
        │   ├── v1.yaml
        │   ├── v2.yaml
        │   └── v3.yaml
        ├── changelog.md
        ├── active_version.txt
        └── metadata.json
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Inicializa versioner.

        Args:
            prompts_dir: Diretório para armazenar versões
        """
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent.parent.parent / "data" / "prompts"

        self.prompts_dir = Path(prompts_dir)
        self.versions_dir = self.prompts_dir / "versions"
        self.changelog_file = self.prompts_dir / "changelog.md"
        self.active_file = self.prompts_dir / "active_version.txt"
        self.metadata_file = self.prompts_dir / "metadata.json"

        self._ensure_structure()

        logger.info(f"PromptVersioner initialized: {self.prompts_dir}")

    def _ensure_structure(self) -> None:
        """Cria estrutura de diretórios se não existir"""
        self.versions_dir.mkdir(parents=True, exist_ok=True)

        if not self.changelog_file.exists():
            self.changelog_file.write_text("# Prompt Changelog\n\n")

        if not self.active_file.exists():
            self.active_file.write_text("v1")

        if not self.metadata_file.exists():
            self.metadata_file.write_text(json.dumps({
                "created_at": datetime.utcnow().isoformat(),
                "total_versions": 0,
                "latest_version": "v1"
            }, indent=2))

    def create_version(
        self,
        content: str,
        version_id: Optional[str] = None,
        description: str = "",
        created_by: Literal["human", "auto"] = "human",
        parent_version: Optional[str] = None,
        tags: Optional[list[str]] = None
    ) -> PromptVersion:
        """
        Cria nova versão de prompt.

        Args:
            content: Conteúdo do prompt
            version_id: ID da versão (auto-gerado se None)
            description: Descrição das mudanças
            created_by: Origem (human ou auto)
            parent_version: Versão pai (se derivado)
            tags: Tags para classificação

        Returns:
            PromptVersion criado
        """
        # Auto-gerar version_id se não fornecido
        if version_id is None:
            version_id = self._get_next_version_id()

        # Criar versão
        version = PromptVersion(
            version_id=version_id,
            content=content,
            created_at=datetime.utcnow(),
            created_by=created_by,
            parent_version=parent_version,
            description=description,
            tags=tags or []
        )

        # Salvar em YAML
        version_file = self.versions_dir / f"{version_id}.yaml"
        version_file.write_text(yaml.dump(version.to_dict(), allow_unicode=True))

        # Atualizar changelog
        self._append_to_changelog(version)

        # Atualizar metadata
        self._update_metadata(version_id)

        logger.info(f"Prompt version created: {version_id} (by {created_by})")
        return version

    def load_version(self, version_id: str) -> Optional[PromptVersion]:
        """
        Carrega versão específica.

        Args:
            version_id: ID da versão

        Returns:
            PromptVersion ou None se não encontrado
        """
        version_file = self.versions_dir / f"{version_id}.yaml"

        if not version_file.exists():
            logger.warning(f"Version not found: {version_id}")
            return None

        data = yaml.safe_load(version_file.read_text())
        return PromptVersion.from_dict(data)

    def list_versions(
        self,
        status: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> list[PromptVersion]:
        """
        Lista versões armazenadas.

        Args:
            status: Filtrar por status
            created_by: Filtrar por criador (human/auto)

        Returns:
            Lista de PromptVersion ordenada por created_at
        """
        versions = []

        for version_file in self.versions_dir.glob("*.yaml"):
            data = yaml.safe_load(version_file.read_text())
            version = PromptVersion.from_dict(data)

            # Aplicar filtros
            if status and version.status != status:
                continue
            if created_by and version.created_by != created_by:
                continue

            versions.append(version)

        # Ordenar por created_at (mais recente primeiro)
        versions.sort(key=lambda v: v.created_at, reverse=True)

        return versions

    def get_active_version(self) -> PromptVersion:
        """
        Retorna versão atualmente ativa.

        Returns:
            PromptVersion ativo
        """
        active_id = self.active_file.read_text().strip()
        version = self.load_version(active_id)

        if version is None:
            raise ValueError(f"Active version {active_id} not found")

        return version

    def set_active_version(self, version_id: str) -> None:
        """
        Define versão ativa.

        Args:
            version_id: ID da versão a ativar
        """
        # Verificar se versão existe
        version = self.load_version(version_id)
        if version is None:
            raise ValueError(f"Version {version_id} not found")

        # Atualizar active_version.txt
        self.active_file.write_text(version_id)

        # Atualizar status da versão
        version.status = "active"
        self._save_version(version)

        logger.info(f"Active version set to: {version_id}")

    def update_version_metrics(
        self,
        version_id: str,
        f1_score: float,
        precision: float,
        recall: float
    ) -> None:
        """
        Atualiza métricas de uma versão após testes.

        Args:
            version_id: ID da versão
            f1_score: F1 score obtido
            precision: Precision obtida
            recall: Recall obtido
        """
        version = self.load_version(version_id)
        if version is None:
            logger.warning(f"Cannot update metrics: version {version_id} not found")
            return

        # Atualizar com média incremental
        n = version.tests_count

        if version.avg_f1_score is None:
            version.avg_f1_score = f1_score
            version.avg_precision = precision
            version.avg_recall = recall
        else:
            version.avg_f1_score = (version.avg_f1_score * n + f1_score) / (n + 1)
            version.avg_precision = (version.avg_precision * n + precision) / (n + 1)
            version.avg_recall = (version.avg_recall * n + recall) / (n + 1)

        version.tests_count += 1

        self._save_version(version)

        logger.info(
            f"Metrics updated for {version_id}: "
            f"F1={version.avg_f1_score:.3f} (n={version.tests_count})"
        )

    def compare_versions(
        self,
        version_a: str,
        version_b: str
    ) -> dict:
        """
        Compara duas versões.

        Args:
            version_a: ID da primeira versão
            version_b: ID da segunda versão

        Returns:
            Dict com comparação
        """
        v_a = self.load_version(version_a)
        v_b = self.load_version(version_b)

        if v_a is None or v_b is None:
            raise ValueError("One or both versions not found")

        comparison = {
            "version_a": {
                "id": v_a.version_id,
                "f1": v_a.avg_f1_score,
                "precision": v_a.avg_precision,
                "recall": v_a.avg_recall,
                "tests": v_a.tests_count,
                "status": v_a.status
            },
            "version_b": {
                "id": v_b.version_id,
                "f1": v_b.avg_f1_score,
                "precision": v_b.avg_precision,
                "recall": v_b.avg_recall,
                "tests": v_b.tests_count,
                "status": v_b.status
            }
        }

        # Determinar vencedor (se ambos tiverem métricas)
        if v_a.avg_f1_score and v_b.avg_f1_score:
            if v_a.avg_f1_score > v_b.avg_f1_score + 0.02:  # 2% threshold
                comparison["winner"] = version_a
                comparison["margin"] = v_a.avg_f1_score - v_b.avg_f1_score
            elif v_b.avg_f1_score > v_a.avg_f1_score + 0.02:
                comparison["winner"] = version_b
                comparison["margin"] = v_b.avg_f1_score - v_a.avg_f1_score
            else:
                comparison["winner"] = "tie"
                comparison["margin"] = 0.0
        else:
            comparison["winner"] = "insufficient_data"

        return comparison

    def _get_next_version_id(self) -> str:
        """Gera próximo version_id sequencial"""
        existing_versions = [v.version_id for v in self.list_versions()]

        # Extrair números de versão (v1 -> 1, v2 -> 2, etc)
        version_numbers = []
        for vid in existing_versions:
            if vid.startswith('v') and vid[1:].isdigit():
                version_numbers.append(int(vid[1:]))

        next_number = max(version_numbers, default=0) + 1
        return f"v{next_number}"

    def _save_version(self, version: PromptVersion) -> None:
        """Salva versão em YAML"""
        version_file = self.versions_dir / f"{version.version_id}.yaml"
        version_file.write_text(yaml.dump(version.to_dict(), allow_unicode=True))

    def _append_to_changelog(self, version: PromptVersion) -> None:
        """Adiciona entrada ao changelog"""
        entry = [
            f"\n## {version.version_id} - {version.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"**Created by:** {version.created_by}",
        ]

        if version.parent_version:
            entry.append(f"**Parent version:** {version.parent_version}")

        entry.append(f"**Description:** {version.description or 'No description'}")

        if version.tags:
            entry.append(f"**Tags:** {', '.join(version.tags)}")

        entry.append("")

        with open(self.changelog_file, 'a') as f:
            f.write('\n'.join(entry))

    def _update_metadata(self, latest_version: str) -> None:
        """Atualiza metadata.json"""
        metadata = json.loads(self.metadata_file.read_text())
        metadata['total_versions'] = len(list(self.versions_dir.glob("*.yaml")))
        metadata['latest_version'] = latest_version
        metadata['last_updated'] = datetime.utcnow().isoformat()

        self.metadata_file.write_text(json.dumps(metadata, indent=2))
