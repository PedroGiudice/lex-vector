"""Storage persistente para learning system (JSON-based)"""
import json
import logging
from pathlib import Path
from typing import Optional, Literal
from datetime import datetime

from .schemas import (
    ExtractionResult,
    FewShotExample,
    PerformanceMetrics,
    ValidationStatus
)

logger = logging.getLogger(__name__)


class LearningStorage:
    """
    Gerencia persistência de dados do learning system.

    Storage baseado em JSON files para simplicidade e portabilidade.
    Estrutura de diretórios:
        data/learning/
        ├── extractions/          # ExtractionResult por documento
        │   ├── doc_001.json
        │   └── doc_002.json
        ├── few_shot_examples/    # FewShotExample para prompts
        │   ├── peticao_inicial/
        │   ├── sentenca/
        │   └── ...
        ├── metrics/              # PerformanceMetrics por batch
        │   ├── batch_001.json
        │   └── batch_002.json
        └── metadata.json         # Metadados gerais (contadores, versões)
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Inicializa storage.

        Args:
            data_dir: Diretório base para storage (default: data/learning/)
        """
        if data_dir is None:
            # Default: agentes/legal-text-extractor/data/learning/
            data_dir = Path(__file__).parent.parent.parent / "data" / "learning"

        self.data_dir = Path(data_dir)
        self._ensure_directories()

        logger.info(f"LearningStorage initialized: {self.data_dir}")

    def _ensure_directories(self) -> None:
        """Cria estrutura de diretórios se não existir"""
        subdirs = [
            self.data_dir / "extractions",
            self.data_dir / "few_shot_examples",
            self.data_dir / "metrics",
            self.data_dir / "ground_truth"
        ]

        for subdir in subdirs:
            subdir.mkdir(parents=True, exist_ok=True)

        # Criar metadata.json se não existir
        metadata_file = self.data_dir / "metadata.json"
        if not metadata_file.exists():
            metadata_file.write_text(json.dumps({
                "created_at": datetime.utcnow().isoformat(),
                "version": "1.0",
                "total_extractions": 0,
                "total_examples": 0,
                "total_batches": 0
            }, indent=2))

    # ===== ExtractionResult Methods =====

    def save_extraction(self, result: ExtractionResult) -> None:
        """
        Salva resultado de extração.

        Args:
            result: ExtractionResult a ser salvo
        """
        file_path = self.data_dir / "extractions" / f"{result.document_id}.json"
        file_path.write_text(result.model_dump_json(indent=2))

        logger.debug(f"Extraction saved: {result.document_id}")
        self._increment_metadata("total_extractions")

    def load_extraction(self, document_id: str) -> Optional[ExtractionResult]:
        """
        Carrega resultado de extração.

        Args:
            document_id: ID do documento

        Returns:
            ExtractionResult ou None se não encontrado
        """
        file_path = self.data_dir / "extractions" / f"{document_id}.json"

        if not file_path.exists():
            logger.warning(f"Extraction not found: {document_id}")
            return None

        data = json.loads(file_path.read_text())
        return ExtractionResult(**data)

    def list_extractions(
        self,
        status: Optional[ValidationStatus] = None,
        limit: Optional[int] = None
    ) -> list[ExtractionResult]:
        """
        Lista extrações armazenadas.

        Args:
            status: Filtrar por status de validação
            limit: Limitar número de resultados

        Returns:
            Lista de ExtractionResult
        """
        extractions_dir = self.data_dir / "extractions"
        files = sorted(extractions_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

        results = []
        for file_path in files:
            if limit and len(results) >= limit:
                break

            data = json.loads(file_path.read_text())
            extraction = ExtractionResult(**data)

            if status is None or extraction.validation_status == status:
                results.append(extraction)

        logger.debug(f"Loaded {len(results)} extractions (status={status})")
        return results

    # ===== FewShotExample Methods =====

    def save_few_shot_example(self, example: FewShotExample) -> None:
        """
        Salva exemplo few-shot.

        Args:
            example: FewShotExample a ser salvo
        """
        # Organizar por tipo de seção
        section_dir = self.data_dir / "few_shot_examples" / example.section_type.value
        section_dir.mkdir(parents=True, exist_ok=True)

        file_path = section_dir / f"{example.example_id}.json"
        file_path.write_text(example.model_dump_json(indent=2))

        logger.debug(f"Few-shot example saved: {example.example_id}")
        self._increment_metadata("total_examples")

    def load_few_shot_examples(
        self,
        section_type: Optional[str] = None,
        min_quality: float = 0.0,
        limit: Optional[int] = None,
        sort_by: Literal["quality", "usage", "recent"] = "quality"
    ) -> list[FewShotExample]:
        """
        Carrega exemplos few-shot.

        Args:
            section_type: Filtrar por tipo de seção
            min_quality: Qualidade mínima (0.0-1.0)
            limit: Limitar número de resultados
            sort_by: Ordenar por quality_score, usage_count, ou created_at

        Returns:
            Lista de FewShotExample ordenada
        """
        examples_dir = self.data_dir / "few_shot_examples"

        # Determinar quais diretórios buscar
        if section_type:
            search_dirs = [examples_dir / section_type]
        else:
            search_dirs = [d for d in examples_dir.iterdir() if d.is_dir()]

        examples = []

        for section_dir in search_dirs:
            if not section_dir.exists():
                continue

            for file_path in section_dir.glob("*.json"):
                data = json.loads(file_path.read_text())
                example = FewShotExample(**data)

                if example.quality_score >= min_quality:
                    examples.append(example)

        # Ordenar
        if sort_by == "quality":
            examples.sort(key=lambda e: e.quality_score, reverse=True)
        elif sort_by == "usage":
            examples.sort(key=lambda e: e.usage_count, reverse=True)
        elif sort_by == "recent":
            examples.sort(key=lambda e: e.created_at, reverse=True)

        # Limitar
        if limit:
            examples = examples[:limit]

        logger.debug(
            f"Loaded {len(examples)} few-shot examples "
            f"(type={section_type}, min_quality={min_quality})"
        )
        return examples

    def update_example_usage(self, example_id: str, section_type: str) -> None:
        """
        Incrementa usage_count de um exemplo.

        Args:
            example_id: ID do exemplo
            section_type: Tipo de seção (para encontrar arquivo)
        """
        file_path = self.data_dir / "few_shot_examples" / section_type / f"{example_id}.json"

        if not file_path.exists():
            logger.warning(f"Example not found for usage update: {example_id}")
            return

        data = json.loads(file_path.read_text())
        example = FewShotExample(**data)
        example.usage_count += 1

        file_path.write_text(example.model_dump_json(indent=2))
        logger.debug(f"Example usage incremented: {example_id} (count={example.usage_count})")

    # ===== PerformanceMetrics Methods =====

    def save_metrics(self, metrics: PerformanceMetrics) -> None:
        """
        Salva métricas de performance.

        Args:
            metrics: PerformanceMetrics a ser salvo
        """
        file_path = self.data_dir / "metrics" / f"{metrics.batch_id}.json"
        file_path.write_text(metrics.model_dump_json(indent=2))

        logger.debug(f"Metrics saved: {metrics.batch_id} (F1={metrics.f1_score:.3f})")
        self._increment_metadata("total_batches")

    def load_metrics(self, batch_id: str) -> Optional[PerformanceMetrics]:
        """
        Carrega métricas de um batch.

        Args:
            batch_id: ID do batch

        Returns:
            PerformanceMetrics ou None se não encontrado
        """
        file_path = self.data_dir / "metrics" / f"{batch_id}.json"

        if not file_path.exists():
            logger.warning(f"Metrics not found: {batch_id}")
            return None

        data = json.loads(file_path.read_text())
        return PerformanceMetrics(**data)

    def list_metrics(
        self,
        prompt_version: Optional[str] = None,
        limit: Optional[int] = None
    ) -> list[PerformanceMetrics]:
        """
        Lista métricas armazenadas.

        Args:
            prompt_version: Filtrar por versão do prompt
            limit: Limitar número de resultados

        Returns:
            Lista de PerformanceMetrics ordenada por data (mais recente primeiro)
        """
        metrics_dir = self.data_dir / "metrics"
        files = sorted(metrics_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

        results = []
        for file_path in files:
            if limit and len(results) >= limit:
                break

            data = json.loads(file_path.read_text())
            metrics = PerformanceMetrics(**data)

            if prompt_version is None or metrics.prompt_version == prompt_version:
                results.append(metrics)

        logger.debug(f"Loaded {len(results)} metrics (version={prompt_version})")
        return results

    def get_latest_metrics(self) -> Optional[PerformanceMetrics]:
        """
        Retorna métricas mais recentes.

        Returns:
            PerformanceMetrics mais recente ou None
        """
        metrics_list = self.list_metrics(limit=1)
        return metrics_list[0] if metrics_list else None

    # ===== Metadata Methods =====

    def _increment_metadata(self, field: str) -> None:
        """Incrementa contador no metadata.json"""
        metadata_file = self.data_dir / "metadata.json"
        metadata = json.loads(metadata_file.read_text())
        metadata[field] = metadata.get(field, 0) + 1
        metadata_file.write_text(json.dumps(metadata, indent=2))

    def get_metadata(self) -> dict:
        """Retorna metadados gerais do storage"""
        metadata_file = self.data_dir / "metadata.json"
        return json.loads(metadata_file.read_text())
