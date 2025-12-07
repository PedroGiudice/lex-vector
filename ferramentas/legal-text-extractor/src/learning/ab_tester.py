"""Sistema de A/B testing para comparar versões de prompts"""
import json
import logging
import random
from pathlib import Path
from typing import Optional, Literal
from datetime import datetime
from dataclasses import dataclass, asdict

from .schemas import ExtractionResult, PerformanceMetrics
from .prompt_versioner import PromptVersioner, PromptVersion
from .metrics_tracker import MetricsTracker
from .storage import LearningStorage

logger = logging.getLogger(__name__)


@dataclass
class ABTestResult:
    """Resultado de teste A/B individual"""
    document_id: str
    version_used: str  # "A" ou "B"
    extraction_result: ExtractionResult
    metrics: Optional[PerformanceMetrics] = None


@dataclass
class ABTest:
    """Teste A/B completo"""

    # Identificação
    test_id: str
    created_at: datetime

    # Versões sendo testadas
    version_a_id: str
    version_b_id: str

    # Configuração
    sample_size: int  # Número total de documentos a testar
    split_ratio: float = 0.5  # Proporção A vs B (default: 50/50)

    # Resultados
    results_a: list[ABTestResult] = None
    results_b: list[ABTestResult] = None

    # Status
    status: Literal["running", "completed", "cancelled"] = "running"
    completed_at: Optional[datetime] = None

    # Análise (preenchido após conclusão)
    winner: Optional[str] = None  # "A", "B", ou "tie"
    improvement_margin: Optional[float] = None  # Diferença de F1
    statistical_significance: Optional[bool] = None

    # Metadados
    notes: str = ""

    def __post_init__(self):
        if self.results_a is None:
            self.results_a = []
        if self.results_b is None:
            self.results_b = []
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if self.completed_at and isinstance(self.completed_at, str):
            self.completed_at = datetime.fromisoformat(self.completed_at)

    def to_dict(self) -> dict:
        """Serializa para dict (JSON-compatible)"""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()

        # Simplificar results (apenas IDs)
        data["results_a"] = [
            {
                "document_id": r.document_id,
                "version_used": r.version_used,
                "f1": r.metrics.f1_score if r.metrics else None
            }
            for r in self.results_a
        ]
        data["results_b"] = [
            {
                "document_id": r.document_id,
                "version_used": r.version_used,
                "f1": r.metrics.f1_score if r.metrics else None
            }
            for r in self.results_b
        ]

        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ABTest":
        """Deserializa de dict"""
        # Converter results simplificados de volta
        # (os ExtractionResult completos estão em storage separado)
        data["results_a"] = []
        data["results_b"] = []
        return cls(**data)


class ABTester:
    """
    Sistema de A/B testing para comparar versões de prompts.

    Responsabilidades:
    - Criar testes A/B entre duas versões
    - Executar testes com split aleatório
    - Analisar resultados estatísticos
    - Promover versão vencedora
    - Fazer rollback se necessário

    Storage structure:
        data/learning/ab_tests/
        ├── test_001.json
        ├── test_002.json
        └── ...
    """

    def __init__(
        self,
        versioner: Optional[PromptVersioner] = None,
        metrics_tracker: Optional[MetricsTracker] = None,
        storage: Optional[LearningStorage] = None,
        tests_dir: Optional[Path] = None
    ):
        """
        Inicializa ABTester.

        Args:
            versioner: PromptVersioner instance
            metrics_tracker: MetricsTracker instance
            storage: LearningStorage instance
            tests_dir: Diretório para armazenar testes A/B
        """
        self.versioner = versioner or PromptVersioner()
        self.metrics_tracker = metrics_tracker or MetricsTracker(storage)
        self.storage = storage or LearningStorage()

        if tests_dir is None:
            tests_dir = Path(__file__).parent.parent.parent / "data" / "learning" / "ab_tests"

        self.tests_dir = Path(tests_dir)
        self.tests_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"ABTester initialized: tests_dir={self.tests_dir}")

    def create_test(
        self,
        version_a: str,
        version_b: str,
        sample_size: int = 10,
        split_ratio: float = 0.5,
        notes: str = ""
    ) -> ABTest:
        """
        Cria novo teste A/B.

        Args:
            version_a: ID da versão A (geralmente a atual/controle)
            version_b: ID da versão B (a nova/experimental)
            sample_size: Número de documentos a testar
            split_ratio: Proporção A vs B (0.5 = 50/50)
            notes: Notas sobre o teste

        Returns:
            ABTest criado

        Raises:
            ValueError: Se versões não existem
        """
        # Validar que versões existem
        v_a = self.versioner.load_version(version_a)
        v_b = self.versioner.load_version(version_b)

        if v_a is None:
            raise ValueError(f"Version A not found: {version_a}")
        if v_b is None:
            raise ValueError(f"Version B not found: {version_b}")

        # Gerar test_id único
        test_id = self._generate_test_id()

        # Criar teste
        test = ABTest(
            test_id=test_id,
            created_at=datetime.utcnow(),
            version_a_id=version_a,
            version_b_id=version_b,
            sample_size=sample_size,
            split_ratio=split_ratio,
            notes=notes
        )

        # Salvar
        self._save_test(test)

        logger.info(
            f"A/B test created: {test_id} ({version_a} vs {version_b}, n={sample_size})"
        )

        return test

    def run_test(
        self,
        test_id: str,
        documents: list[tuple[str, str]]  # List of (doc_id, doc_text)
    ) -> ABTest:
        """
        Executa teste A/B em documentos fornecidos.

        IMPORTANTE: Este método NÃO executa as extrações reais.
        Ele apenas registra qual versão deve ser usada para cada documento.

        As extrações devem ser feitas pelo SectionAnalyzer com
        get_version_for_document(doc_id).

        Args:
            test_id: ID do teste
            documents: Lista de (document_id, document_text)

        Returns:
            ABTest atualizado

        Raises:
            ValueError: Se teste não existe ou já completado
        """
        test = self.load_test(test_id)

        if test is None:
            raise ValueError(f"Test {test_id} not found")

        if test.status != "running":
            raise ValueError(f"Test {test_id} is not running (status={test.status})")

        # Limitar ao sample_size
        sample = documents[:test.sample_size]

        # Shuffle para randomizar
        random.shuffle(sample)

        # Split A/B baseado em split_ratio
        split_point = int(len(sample) * test.split_ratio)
        docs_a = sample[:split_point]
        docs_b = sample[split_point:]

        logger.info(
            f"Running A/B test {test_id}: "
            f"{len(docs_a)} docs for version A, {len(docs_b)} docs for version B"
        )

        # Registrar assignments (sem executar extrações)
        test.results_a = [
            ABTestResult(
                document_id=doc_id,
                version_used="A",
                extraction_result=None  # Será preenchido após extração
            )
            for doc_id, _ in docs_a
        ]

        test.results_b = [
            ABTestResult(
                document_id=doc_id,
                version_used="B",
                extraction_result=None  # Será preenchido após extração
            )
            for doc_id, _ in docs_b
        ]

        # Salvar assignments
        self._save_test(test)

        logger.info(
            f"A/B test {test_id} assignments saved. "
            f"Now run extractions with get_version_for_document()"
        )

        return test

    def get_version_for_document(self, test_id: str, document_id: str) -> Optional[str]:
        """
        Retorna qual versão deve ser usada para um documento no teste A/B.

        Args:
            test_id: ID do teste
            document_id: ID do documento

        Returns:
            version_id para usar ou None se documento não está no teste
        """
        test = self.load_test(test_id)

        if test is None:
            return None

        # Buscar em results_a
        for result in test.results_a:
            if result.document_id == document_id:
                return test.version_a_id

        # Buscar em results_b
        for result in test.results_b:
            if result.document_id == document_id:
                return test.version_b_id

        return None

    def record_result(
        self,
        test_id: str,
        document_id: str,
        extraction_result: ExtractionResult
    ) -> None:
        """
        Registra resultado de extração no teste A/B.

        Args:
            test_id: ID do teste
            document_id: ID do documento
            extraction_result: Resultado da extração
        """
        test = self.load_test(test_id)

        if test is None:
            raise ValueError(f"Test {test_id} not found")

        # Calcular métricas se houver ground truth
        metrics = None
        if extraction_result.ground_truth_sections:
            metrics = self.metrics_tracker.calculate_metrics_for_extraction(
                extraction_result
            )

        # Atualizar result apropriado
        updated = False

        for result in test.results_a:
            if result.document_id == document_id:
                result.extraction_result = extraction_result
                result.metrics = metrics
                updated = True
                break

        if not updated:
            for result in test.results_b:
                if result.document_id == document_id:
                    result.extraction_result = extraction_result
                    result.metrics = metrics
                    updated = True
                    break

        if not updated:
            logger.warning(
                f"Document {document_id} not found in test {test_id}"
            )
            return

        # Salvar
        self._save_test(test)

        logger.debug(f"Result recorded for {document_id} in test {test_id}")

    def analyze_results(
        self,
        test_id: str,
        min_results: int = 5
    ) -> Optional[dict]:
        """
        Analisa resultados do teste A/B.

        Args:
            test_id: ID do teste
            min_results: Mínimo de resultados em cada grupo

        Returns:
            Dict com análise ou None se dados insuficientes
        """
        test = self.load_test(test_id)

        if test is None:
            raise ValueError(f"Test {test_id} not found")

        # Filtrar apenas results com métricas
        results_a_valid = [r for r in test.results_a if r.metrics is not None]
        results_b_valid = [r for r in test.results_b if r.metrics is not None]

        if len(results_a_valid) < min_results or len(results_b_valid) < min_results:
            logger.warning(
                f"Insufficient results for analysis: "
                f"A={len(results_a_valid)}, B={len(results_b_valid)} (min={min_results})"
            )
            return None

        # Calcular médias
        avg_f1_a = sum(r.metrics.f1_score for r in results_a_valid) / len(results_a_valid)
        avg_precision_a = sum(r.metrics.precision for r in results_a_valid) / len(results_a_valid)
        avg_recall_a = sum(r.metrics.recall for r in results_a_valid) / len(results_a_valid)

        avg_f1_b = sum(r.metrics.f1_score for r in results_b_valid) / len(results_b_valid)
        avg_precision_b = sum(r.metrics.precision for r in results_b_valid) / len(results_b_valid)
        avg_recall_b = sum(r.metrics.recall for r in results_b_valid) / len(results_b_valid)

        # Calcular std dev (simplified)
        import statistics
        std_f1_a = statistics.stdev([r.metrics.f1_score for r in results_a_valid])
        std_f1_b = statistics.stdev([r.metrics.f1_score for r in results_b_valid])

        # Determinar vencedor
        improvement = avg_f1_b - avg_f1_a

        if abs(improvement) < 0.02:  # 2% threshold
            winner = "tie"
        elif improvement > 0:
            winner = "B"
        else:
            winner = "A"

        # Statistical significance (t-test simplificado)
        # Consideramos significante se diferença > 1.5 * (std_a + std_b) / 2
        pooled_std = (std_f1_a + std_f1_b) / 2
        significance_threshold = 1.5 * pooled_std
        is_significant = abs(improvement) > significance_threshold

        analysis = {
            "test_id": test_id,
            "version_a": {
                "id": test.version_a_id,
                "n": len(results_a_valid),
                "f1": round(avg_f1_a, 3),
                "precision": round(avg_precision_a, 3),
                "recall": round(avg_recall_a, 3),
                "std_f1": round(std_f1_a, 3)
            },
            "version_b": {
                "id": test.version_b_id,
                "n": len(results_b_valid),
                "f1": round(avg_f1_b, 3),
                "precision": round(avg_precision_b, 3),
                "recall": round(avg_recall_b, 3),
                "std_f1": round(std_f1_b, 3)
            },
            "winner": winner,
            "improvement": round(improvement, 3),
            "improvement_pct": round(improvement * 100, 1),
            "statistically_significant": is_significant
        }

        # Atualizar teste
        test.winner = winner
        test.improvement_margin = improvement
        test.statistical_significance = is_significant

        self._save_test(test)

        logger.info(
            f"A/B test {test_id} analyzed: winner={winner}, "
            f"improvement={improvement:.3f} (significant={is_significant})"
        )

        return analysis

    def complete_test(self, test_id: str) -> ABTest:
        """
        Marca teste como completo.

        Args:
            test_id: ID do teste

        Returns:
            ABTest atualizado
        """
        test = self.load_test(test_id)

        if test is None:
            raise ValueError(f"Test {test_id} not found")

        test.status = "completed"
        test.completed_at = datetime.utcnow()

        self._save_test(test)

        logger.info(f"A/B test {test_id} marked as completed")
        return test

    def promote_winner(
        self,
        test_id: str,
        min_improvement: float = 0.02
    ) -> Optional[str]:
        """
        Promove versão vencedora do teste A/B para ativa.

        Args:
            test_id: ID do teste
            min_improvement: Melhoria mínima para promoção (default: 2%)

        Returns:
            version_id promovido ou None se não promoveu
        """
        test = self.load_test(test_id)

        if test is None:
            raise ValueError(f"Test {test_id} not found")

        # Analisar resultados se ainda não foi feito
        if test.winner is None:
            analysis = self.analyze_results(test_id)
            if analysis is None:
                logger.warning("Cannot promote: insufficient data for analysis")
                return None

        # Verificar se há vencedor claro
        if test.winner == "tie":
            logger.info("Cannot promote: test resulted in tie")
            return None

        # Verificar melhoria mínima
        if abs(test.improvement_margin) < min_improvement:
            logger.info(
                f"Cannot promote: improvement {test.improvement_margin:.3f} "
                f"below threshold {min_improvement}"
            )
            return None

        # Determinar qual versão promover
        if test.winner == "B":
            promoted_version = test.version_b_id
        else:
            promoted_version = test.version_a_id

        # Promover versão
        self.versioner.set_active_version(promoted_version)

        # Atualizar status da versão para "promoted"
        version = self.versioner.load_version(promoted_version)
        version.status = "promoted"
        self.versioner._save_version(version)

        # Marcar teste como completo
        if test.status != "completed":
            self.complete_test(test_id)

        logger.info(
            f"Version {promoted_version} promoted to active "
            f"(improvement={test.improvement_margin:.3f})"
        )

        return promoted_version

    def rollback_if_worse(
        self,
        test_id: str,
        max_degradation: float = -0.02
    ) -> Optional[str]:
        """
        Faz rollback para versão A se B for pior.

        Args:
            test_id: ID do teste
            max_degradation: Degradação máxima tolerável (negativo)

        Returns:
            version_id para qual fez rollback ou None
        """
        test = self.load_test(test_id)

        if test is None:
            raise ValueError(f"Test {test_id} not found")

        # Analisar se necessário
        if test.improvement_margin is None:
            analysis = self.analyze_results(test_id)
            if analysis is None:
                return None

        # Se versão B pior que threshold, rollback para A
        if test.improvement_margin < max_degradation:
            logger.warning(
                f"Version B significantly worse (margin={test.improvement_margin:.3f}), "
                f"rolling back to version A"
            )

            # Ativar versão A
            self.versioner.set_active_version(test.version_a_id)

            # Marcar versão B como deprecated
            version_b = self.versioner.load_version(test.version_b_id)
            version_b.status = "deprecated"
            self.versioner._save_version(version_b)

            # Marcar teste como completo
            if test.status != "completed":
                self.complete_test(test_id)

            return test.version_a_id

        return None

    def load_test(self, test_id: str) -> Optional[ABTest]:
        """Carrega teste do storage"""
        test_file = self.tests_dir / f"{test_id}.json"

        if not test_file.exists():
            return None

        data = json.loads(test_file.read_text())
        return ABTest.from_dict(data)

    def list_tests(
        self,
        status: Optional[str] = None
    ) -> list[ABTest]:
        """
        Lista testes armazenados.

        Args:
            status: Filtrar por status

        Returns:
            Lista de ABTest ordenada por created_at
        """
        tests = []

        for test_file in self.tests_dir.glob("*.json"):
            data = json.loads(test_file.read_text())
            test = ABTest.from_dict(data)

            if status and test.status != status:
                continue

            tests.append(test)

        tests.sort(key=lambda t: t.created_at, reverse=True)
        return tests

    def _save_test(self, test: ABTest) -> None:
        """Salva teste em JSON"""
        test_file = self.tests_dir / f"{test.test_id}.json"
        test_file.write_text(json.dumps(test.to_dict(), indent=2))

    def _generate_test_id(self) -> str:
        """Gera ID único para teste"""
        existing = self.list_tests()
        numbers = []

        for test in existing:
            if test.test_id.startswith("test_"):
                try:
                    num = int(test.test_id.split("_")[1])
                    numbers.append(num)
                except (IndexError, ValueError):
                    continue

        next_num = max(numbers, default=0) + 1
        return f"test_{next_num:03d}"
