"""Sistema de auto-melhoria de prompts usando Claude SDK"""
import os
import logging
from typing import Optional
from datetime import datetime
from dataclasses import dataclass

from anthropic import Anthropic, RateLimitError, APIError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from .schemas import ExtractionResult, ValidationStatus
from .prompt_versioner import PromptVersioner, PromptVersion
from .metrics_tracker import MetricsTracker
from .storage import LearningStorage

logger = logging.getLogger(__name__)


@dataclass
class ErrorAnalysis:
    """Análise de erros identificados em extrações"""

    # Contagens
    total_errors: int
    false_positives: int  # Seções identificadas incorretamente
    false_negatives: int  # Seções não identificadas

    # Padrões identificados
    missing_section_types: list[str]  # Tipos de seção frequentemente não detectados
    over_detected_types: list[str]    # Tipos de seção detectados em excesso

    # Exemplos de erros
    error_examples: list[dict]  # Lista de exemplos específicos de erro

    # Resumo
    summary: str
    recommendations: list[str]


class SelfImprover:
    """
    Sistema de auto-melhoria de prompts usando Claude SDK.

    Responsabilidades:
    - Analisar erros de extração
    - Gerar prompts melhorados usando meta-prompting
    - Decidir quando criar novas versões
    - Coordenar com PromptVersioner

    Workflow:
    1. Analisa resultados de extrações (successful vs failed)
    2. Identifica padrões de erro
    3. Usa Claude para gerar prompt melhorado (meta-prompting)
    4. Cria nova versão marcada como "testing"
    """

    # Meta-prompt template para melhorar prompts
    META_PROMPT_TEMPLATE = """Você é um especialista em engenharia de prompts. Sua tarefa é melhorar um prompt existente para extração de seções de documentos jurídicos brasileiros.

PROMPT ATUAL:
{current_prompt}

ANÁLISE DE ERROS IDENTIFICADOS:
{error_analysis}

MÉTRICAS ATUAIS:
- Precision: {precision:.2f}
- Recall: {recall:.2f}
- F1 Score: {f1:.2f}

PADRÕES DE ERRO:
{error_patterns}

INSTRUÇÕES:
1. Analise os erros identificados
2. Identifique fraquezas no prompt atual
3. Gere um prompt MELHORADO que corrija essas fraquezas

REQUISITOS:
- Manter estrutura clara e instruções específicas
- Adicionar exemplos dos tipos de seção problemáticos
- Melhorar critérios de identificação
- Manter formato de saída JSON
- Ser mais específico sobre markers de início/fim

IMPORTANTE:
- Retorne APENAS o novo prompt melhorado
- NÃO inclua explicações ou comentários
- O prompt deve ser autocontido e completo

NOVO PROMPT MELHORADO:"""

    def __init__(
        self,
        versioner: Optional[PromptVersioner] = None,
        metrics_tracker: Optional[MetricsTracker] = None,
        storage: Optional[LearningStorage] = None,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Inicializa SelfImprover.

        Args:
            versioner: PromptVersioner instance
            metrics_tracker: MetricsTracker instance
            storage: LearningStorage instance
            api_key: Claude API key
            model: Claude model a usar para meta-prompting
        """
        self.versioner = versioner or PromptVersioner()
        self.metrics_tracker = metrics_tracker or MetricsTracker(storage)
        self.storage = storage or LearningStorage()

        # Claude client para meta-prompting
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY não encontrada")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model

        logger.info(f"SelfImprover initialized: model={model}")

    def analyze_errors(
        self,
        extraction_results: list[ExtractionResult],
        min_errors: int = 3
    ) -> Optional[ErrorAnalysis]:
        """
        Analisa erros de uma lista de extrações.

        Args:
            extraction_results: Lista de ExtractionResult (com ground truth)
            min_errors: Mínimo de erros para análise ser válida

        Returns:
            ErrorAnalysis ou None se erros insuficientes
        """
        # Filtrar apenas extrações com ground truth
        validated = [
            r for r in extraction_results
            if r.ground_truth_sections is not None
        ]

        if not validated:
            logger.warning("Nenhuma extração validada para análise")
            return None

        # Calcular métricas para identificar erros
        all_predictions = []
        all_ground_truth = []

        for result in validated:
            all_predictions.extend(result.predicted_sections)
            all_ground_truth.extend(result.ground_truth_sections)

        # Identificar false positives e false negatives
        false_positives = 0
        false_negatives = 0
        missing_types = {}  # tipo -> count
        over_detected_types = {}  # tipo -> count
        error_examples = []

        # Para cada resultado, comparar predicted vs ground truth
        for result in validated:
            pred_types = [s.type.value for s in result.predicted_sections]
            gt_types = [s.type.value for s in result.ground_truth_sections]

            # FN: tipos em ground truth mas não em predicted
            for gt_type in gt_types:
                if gt_type not in pred_types:
                    false_negatives += 1
                    missing_types[gt_type] = missing_types.get(gt_type, 0) + 1

                    error_examples.append({
                        "type": "false_negative",
                        "section_type": gt_type,
                        "document_id": result.document_id
                    })

            # FP: tipos em predicted mas não em ground truth
            for pred_type in pred_types:
                if pred_type not in gt_types:
                    false_positives += 1
                    over_detected_types[pred_type] = over_detected_types.get(pred_type, 0) + 1

                    error_examples.append({
                        "type": "false_positive",
                        "section_type": pred_type,
                        "document_id": result.document_id
                    })

        total_errors = false_positives + false_negatives

        if total_errors < min_errors:
            logger.info(f"Erros insuficientes para análise: {total_errors} < {min_errors}")
            return None

        # Identificar top missing/over-detected types
        top_missing = sorted(missing_types.items(), key=lambda x: x[1], reverse=True)[:3]
        top_over = sorted(over_detected_types.items(), key=lambda x: x[1], reverse=True)[:3]

        # Gerar summary e recommendations
        summary = (
            f"Identificados {total_errors} erros em {len(validated)} documentos: "
            f"{false_positives} FP, {false_negatives} FN"
        )

        recommendations = []

        if top_missing:
            missing_str = ", ".join([f"{t} ({c}x)" for t, c in top_missing])
            recommendations.append(
                f"Melhorar detecção de: {missing_str}"
            )

        if top_over:
            over_str = ", ".join([f"{t} ({c}x)" for t, c in top_over])
            recommendations.append(
                f"Reduzir falsos positivos em: {over_str}"
            )

        if false_negatives > false_positives * 1.5:
            recommendations.append("Priorizar recall (muitas seções não detectadas)")
        elif false_positives > false_negatives * 1.5:
            recommendations.append("Priorizar precision (muitos falsos positivos)")

        analysis = ErrorAnalysis(
            total_errors=total_errors,
            false_positives=false_positives,
            false_negatives=false_negatives,
            missing_section_types=[t for t, _ in top_missing],
            over_detected_types=[t for t, _ in top_over],
            error_examples=error_examples[:10],  # Limitar a 10 exemplos
            summary=summary,
            recommendations=recommendations
        )

        logger.info(f"Error analysis complete: {summary}")
        return analysis

    @retry(
        retry=retry_if_exception_type((RateLimitError, APIError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def generate_improved_prompt(
        self,
        current_prompt: str,
        error_analysis: ErrorAnalysis,
        current_metrics: Optional[dict] = None
    ) -> str:
        """
        Gera prompt melhorado usando Claude (meta-prompting).

        Args:
            current_prompt: Prompt atual
            error_analysis: Análise de erros
            current_metrics: Métricas atuais (opcional)

        Returns:
            Novo prompt melhorado

        Raises:
            APIError: Se erro na API Claude
        """
        # Preparar dados para meta-prompt
        metrics = current_metrics or {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        # Formatar padrões de erro
        error_patterns = []

        if error_analysis.missing_section_types:
            error_patterns.append(
                f"Seções frequentemente NÃO detectadas: {', '.join(error_analysis.missing_section_types)}"
            )

        if error_analysis.over_detected_types:
            error_patterns.append(
                f"Seções com muitos FALSOS POSITIVOS: {', '.join(error_analysis.over_detected_types)}"
            )

        error_patterns.extend(error_analysis.recommendations)

        error_patterns_str = "\n".join(f"- {p}" for p in error_patterns)

        # Construir meta-prompt
        meta_prompt = self.META_PROMPT_TEMPLATE.format(
            current_prompt=current_prompt,
            error_analysis=error_analysis.summary,
            precision=metrics.get("precision", 0.0),
            recall=metrics.get("recall", 0.0),
            f1=metrics.get("f1", 0.0),
            error_patterns=error_patterns_str
        )

        logger.info("Generating improved prompt using Claude meta-prompting...")

        try:
            # Chamar Claude para gerar prompt melhorado
            message = self.client.messages.create(
                model=self.model,
                max_tokens=8192,  # Prompt pode ser longo
                temperature=0.3,  # Alguma criatividade, mas controlada
                messages=[{"role": "user", "content": meta_prompt}]
            )

            improved_prompt = message.content[0].text.strip()

            logger.info(f"Improved prompt generated: {len(improved_prompt)} chars")
            return improved_prompt

        except (RateLimitError, APIError) as e:
            logger.error(f"Failed to generate improved prompt: {e}")
            raise

    def should_create_new_version(
        self,
        f1_threshold: float = 0.85,
        min_batches: int = 3
    ) -> tuple[bool, str]:
        """
        Determina se deve criar nova versão do prompt.

        Args:
            f1_threshold: Threshold de F1 abaixo do qual deve melhorar
            min_batches: Mínimo de batches antes de decidir

        Returns:
            Tupla (should_create: bool, reason: str)
        """
        return self.metrics_tracker.should_improve_prompt(
            f1_threshold=f1_threshold,
            min_batches=min_batches
        )

    def create_improved_version(
        self,
        parent_version: str,
        extraction_results: list[ExtractionResult],
        description: str = "Auto-generated improved prompt"
    ) -> Optional[PromptVersion]:
        """
        Cria nova versão melhorada do prompt.

        Workflow:
        1. Analisa erros das extrações
        2. Carrega prompt atual
        3. Gera prompt melhorado com Claude
        4. Cria nova versão marcada como "testing"

        Args:
            parent_version: ID da versão pai
            extraction_results: Lista de extrações para análise
            description: Descrição da versão

        Returns:
            PromptVersion criado ou None se não foi possível
        """
        logger.info(f"Creating improved version based on {parent_version}...")

        # 1. Analisar erros
        error_analysis = self.analyze_errors(extraction_results)

        if error_analysis is None:
            logger.warning("Não foi possível analisar erros (dados insuficientes)")
            return None

        # 2. Carregar prompt atual
        current_version = self.versioner.load_version(parent_version)

        if current_version is None:
            raise ValueError(f"Parent version {parent_version} not found")

        # 3. Obter métricas atuais
        trend = self.metrics_tracker.get_performance_trend(
            prompt_version=parent_version,
            last_n_batches=5
        )

        current_metrics = {
            "precision": 0.0,
            "recall": 0.0,
            "f1": trend.get("avg_f1", 0.0)
        }

        # Tentar obter métricas mais detalhadas do último batch
        latest_metrics = self.storage.get_latest_metrics()
        if latest_metrics and latest_metrics.prompt_version == parent_version:
            current_metrics = {
                "precision": latest_metrics.precision,
                "recall": latest_metrics.recall,
                "f1": latest_metrics.f1_score
            }

        # 4. Gerar prompt melhorado
        try:
            improved_prompt = self.generate_improved_prompt(
                current_prompt=current_version.content,
                error_analysis=error_analysis,
                current_metrics=current_metrics
            )
        except Exception as e:
            logger.error(f"Failed to generate improved prompt: {e}")
            return None

        # 5. Criar nova versão
        new_version = self.versioner.create_version(
            content=improved_prompt,
            description=description + f" | {error_analysis.summary}",
            created_by="auto",
            parent_version=parent_version,
            tags=["auto-generated", "testing"] + error_analysis.missing_section_types[:2]
        )

        logger.info(
            f"Improved version created: {new_version.version_id} "
            f"(parent={parent_version}, status={new_version.status})"
        )

        return new_version

    def auto_improve_if_needed(
        self,
        extraction_results: list[ExtractionResult],
        f1_threshold: float = 0.85,
        min_batches: int = 3
    ) -> Optional[PromptVersion]:
        """
        Automaticamente melhora prompt se necessário.

        Este é o método principal para uso automático do sistema.

        Args:
            extraction_results: Lista de extrações recentes
            f1_threshold: Threshold de F1
            min_batches: Mínimo de batches

        Returns:
            Nova PromptVersion se criada, None caso contrário
        """
        # Verificar se deve melhorar
        should_improve, reason = self.should_create_new_version(
            f1_threshold=f1_threshold,
            min_batches=min_batches
        )

        if not should_improve:
            logger.info(f"Auto-improvement not needed: {reason}")
            return None

        logger.info(f"Auto-improvement triggered: {reason}")

        # Obter versão ativa atual
        current_version = self.versioner.get_active_version()

        # Criar versão melhorada
        new_version = self.create_improved_version(
            parent_version=current_version.version_id,
            extraction_results=extraction_results,
            description=f"Auto-improvement triggered: {reason}"
        )

        return new_version
