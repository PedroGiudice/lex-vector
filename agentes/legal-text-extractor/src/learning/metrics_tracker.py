"""Tracking de métricas de performance do sistema de extração"""
import logging
from typing import Optional, Literal
from datetime import datetime, timedelta

from .schemas import (
    ExtractionResult,
    PerformanceMetrics,
    ExtractedSection,
    GroundTruthSection,
    ValidationStatus
)
from .storage import LearningStorage

logger = logging.getLogger(__name__)


class MetricsTracker:
    """
    Calcula e rastreia métricas de performance do sistema.

    Métricas rastreadas:
    - Precision: TP / (TP + FP)
    - Recall: TP / (TP + FN)
    - F1 Score: 2 * (precision * recall) / (precision + recall)
    - Per-type metrics: breakdown por tipo de seção
    - Trends: evolução ao longo do tempo
    """

    def __init__(self, storage: Optional[LearningStorage] = None):
        """
        Inicializa tracker.

        Args:
            storage: LearningStorage instance (cria novo se None)
        """
        self.storage = storage or LearningStorage()
        logger.info("MetricsTracker initialized")

    def calculate_metrics_for_extraction(
        self,
        extraction: ExtractionResult
    ) -> Optional[PerformanceMetrics]:
        """
        Calcula métricas para uma única extração.

        Args:
            extraction: ExtractionResult com predicted e ground_truth

        Returns:
            PerformanceMetrics calculado ou None se não houver ground truth
        """
        if not extraction.ground_truth_sections:
            logger.warning(
                f"No ground truth for {extraction.document_id}, cannot calculate metrics"
            )
            return None

        batch_id = f"{extraction.document_id}_metrics"

        metrics = PerformanceMetrics.calculate(
            batch_id=batch_id,
            predicted=extraction.predicted_sections,
            ground_truth=extraction.ground_truth_sections,
            prompt_version=extraction.prompt_version
        )

        # Calcular per-type metrics
        metrics.per_type_metrics = self._calculate_per_type_metrics(
            extraction.predicted_sections,
            extraction.ground_truth_sections
        )

        # Salvar
        self.storage.save_metrics(metrics)

        logger.info(
            f"Metrics calculated for {extraction.document_id}: "
            f"P={metrics.precision:.2f}, R={metrics.recall:.2f}, F1={metrics.f1_score:.2f}"
        )

        return metrics

    def calculate_batch_metrics(
        self,
        batch_id: str,
        extractions: list[ExtractionResult]
    ) -> PerformanceMetrics:
        """
        Calcula métricas agregadas para um batch de extrações.

        Args:
            batch_id: ID do batch
            extractions: Lista de ExtractionResult com ground truth

        Returns:
            PerformanceMetrics agregado
        """
        # Filtrar apenas extrações com ground truth
        valid_extractions = [
            e for e in extractions
            if e.ground_truth_sections is not None
        ]

        if not valid_extractions:
            raise ValueError("No extractions with ground truth in batch")

        # Agregar todas as seções
        all_predicted = []
        all_ground_truth = []

        for extraction in valid_extractions:
            all_predicted.extend(extraction.predicted_sections)
            all_ground_truth.extend(extraction.ground_truth_sections)

        # Calcular métricas agregadas
        metrics = PerformanceMetrics.calculate(
            batch_id=batch_id,
            predicted=all_predicted,
            ground_truth=all_ground_truth,
            prompt_version=valid_extractions[0].prompt_version
        )

        # Atualizar total_documents
        metrics.total_documents = len(valid_extractions)

        # Calcular per-type metrics
        metrics.per_type_metrics = self._calculate_per_type_metrics(
            all_predicted,
            all_ground_truth
        )

        # Salvar
        self.storage.save_metrics(metrics)

        logger.info(
            f"Batch metrics calculated: {batch_id} "
            f"(docs={metrics.total_documents}, F1={metrics.f1_score:.2f})"
        )

        return metrics

    def _calculate_per_type_metrics(
        self,
        predicted: list[ExtractedSection],
        ground_truth: list[GroundTruthSection]
    ) -> dict[str, dict]:
        """
        Calcula métricas detalhadas por tipo de seção.

        Args:
            predicted: Seções preditas
            ground_truth: Seções ground truth

        Returns:
            Dict com métricas por tipo
        """
        # Agrupar por tipo
        pred_by_type = {}
        gt_by_type = {}

        for section in predicted:
            type_str = section.type.value
            if type_str not in pred_by_type:
                pred_by_type[type_str] = []
            pred_by_type[type_str].append(section)

        for section in ground_truth:
            type_str = section.type.value
            if type_str not in gt_by_type:
                gt_by_type[type_str] = []
            gt_by_type[type_str].append(section)

        # Calcular métricas para cada tipo
        per_type = {}

        all_types = set(list(pred_by_type.keys()) + list(gt_by_type.keys()))

        for section_type in all_types:
            pred_sections = pred_by_type.get(section_type, [])
            gt_sections = gt_by_type.get(section_type, [])

            # Contar matches (simplified: count only if same type)
            tp = min(len(pred_sections), len(gt_sections))
            fp = max(0, len(pred_sections) - len(gt_sections))
            fn = max(0, len(gt_sections) - len(pred_sections))

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

            per_type[section_type] = {
                "predicted": len(pred_sections),
                "ground_truth": len(gt_sections),
                "precision": round(precision, 3),
                "recall": round(recall, 3),
                "f1": round(f1, 3)
            }

        return per_type

    def get_performance_trend(
        self,
        prompt_version: Optional[str] = None,
        last_n_batches: int = 10
    ) -> dict:
        """
        Retorna tendência de performance ao longo do tempo.

        Args:
            prompt_version: Filtrar por versão do prompt
            last_n_batches: Número de batches mais recentes

        Returns:
            Dict com dados de tendência
        """
        metrics_list = self.storage.list_metrics(
            prompt_version=prompt_version,
            limit=last_n_batches
        )

        if not metrics_list:
            return {
                "trend": "no_data",
                "batches": 0,
                "avg_f1": 0.0
            }

        # Calcular média de F1
        avg_f1 = sum(m.f1_score for m in metrics_list) / len(metrics_list)

        # Determinar tendência (comparar primeiros vs últimos)
        if len(metrics_list) >= 3:
            first_half_f1 = sum(m.f1_score for m in metrics_list[len(metrics_list)//2:]) / (len(metrics_list) - len(metrics_list)//2)
            second_half_f1 = sum(m.f1_score for m in metrics_list[:len(metrics_list)//2]) / (len(metrics_list)//2)

            if second_half_f1 > first_half_f1 + 0.05:
                trend = "improving"
            elif second_half_f1 < first_half_f1 - 0.05:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "trend": trend,
            "batches": len(metrics_list),
            "avg_f1": round(avg_f1, 3),
            "latest_f1": round(metrics_list[0].f1_score, 3) if metrics_list else 0.0,
            "data_points": [
                {
                    "batch_id": m.batch_id,
                    "f1": round(m.f1_score, 3),
                    "computed_at": m.computed_at.isoformat()
                }
                for m in metrics_list
            ]
        }

    def should_improve_prompt(
        self,
        f1_threshold: float = 0.85,
        min_batches: int = 3
    ) -> tuple[bool, str]:
        """
        Determina se prompt deve ser atualizado baseado em performance.

        Args:
            f1_threshold: Threshold de F1 abaixo do qual deve melhorar
            min_batches: Mínimo de batches antes de decidir

        Returns:
            Tupla (should_improve: bool, reason: str)
        """
        trend = self.get_performance_trend(last_n_batches=min_batches)

        if trend["batches"] < min_batches:
            return False, f"Insufficient data ({trend['batches']} < {min_batches} batches)"

        # Critérios para melhoria:
        # 1. F1 abaixo do threshold
        if trend["avg_f1"] < f1_threshold:
            return True, f"Low F1 score ({trend['avg_f1']:.2f} < {f1_threshold})"

        # 2. Tendência de declínio
        if trend["trend"] == "declining":
            return True, f"Performance declining (trend={trend['trend']})"

        # 3. Muita variação (alta std dev)
        f1_scores = [dp["f1"] for dp in trend["data_points"]]
        if len(f1_scores) >= 3:
            import statistics
            std_dev = statistics.stdev(f1_scores)
            if std_dev > 0.15:
                return True, f"High variance (std={std_dev:.2f})"

        return False, f"Performance acceptable (F1={trend['avg_f1']:.2f}, trend={trend['trend']})"

    def generate_report(
        self,
        batch_id: Optional[str] = None,
        format: Literal["text", "json"] = "text"
    ) -> str:
        """
        Gera relatório de métricas.

        Args:
            batch_id: ID do batch (None = latest)
            format: Formato do relatório

        Returns:
            Relatório formatado
        """
        if batch_id:
            metrics = self.storage.load_metrics(batch_id)
        else:
            metrics = self.storage.get_latest_metrics()

        if not metrics:
            return "No metrics available"

        if format == "json":
            return metrics.model_dump_json(indent=2)

        # Formato texto
        lines = [
            "=" * 70,
            f"PERFORMANCE REPORT: {metrics.batch_id}",
            "=" * 70,
            f"Computed at: {metrics.computed_at.isoformat()}",
            f"Prompt version: {metrics.prompt_version}",
            f"Documents: {metrics.total_documents}",
            "",
            "GLOBAL METRICS:",
            f"  Precision:  {metrics.precision:.3f}",
            f"  Recall:     {metrics.recall:.3f}",
            f"  F1 Score:   {metrics.f1_score:.3f}",
            f"  Avg Confidence: {metrics.average_confidence:.3f}" if metrics.average_confidence else "",
            "",
            "CONFUSION MATRIX:",
            f"  True Positives:  {metrics.true_positives}",
            f"  False Positives: {metrics.false_positives}",
            f"  False Negatives: {metrics.false_negatives}",
            "",
        ]

        if metrics.per_type_metrics:
            lines.append("PER-TYPE METRICS:")
            for section_type, type_metrics in metrics.per_type_metrics.items():
                lines.append(f"  {section_type}:")
                lines.append(f"    Predicted: {type_metrics['predicted']}, Ground Truth: {type_metrics['ground_truth']}")
                lines.append(f"    P={type_metrics['precision']:.2f}, R={type_metrics['recall']:.2f}, F1={type_metrics['f1']:.2f}")

        lines.append("=" * 70)

        return "\n".join(lines)
