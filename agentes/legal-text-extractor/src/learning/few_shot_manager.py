"""Gerenciamento de exemplos few-shot para prompts"""
import logging
import hashlib
from typing import Optional
from datetime import datetime

from .schemas import (
    ExtractionResult,
    FewShotExample,
    ExtractedSection,
    SectionType,
    ValidationStatus
)
from .storage import LearningStorage

logger = logging.getLogger(__name__)


class FewShotManager:
    """
    Gerencia biblioteca de exemplos few-shot para melhorar prompts.

    Responsabilidades:
    - Criar exemplos a partir de extrações aprovadas
    - Selecionar melhores exemplos para cada tipo de seção
    - Formatar exemplos para injeção em prompts
    - Rastrear uso e atualizar quality scores
    """

    def __init__(self, storage: Optional[LearningStorage] = None):
        """
        Inicializa manager.

        Args:
            storage: LearningStorage instance (cria novo se None)
        """
        self.storage = storage or LearningStorage()
        logger.info("FewShotManager initialized")

    def create_example_from_extraction(
        self,
        extraction: ExtractionResult,
        section: ExtractedSection
    ) -> FewShotExample:
        """
        Cria FewShotExample a partir de uma seção extraída e aprovada.

        Args:
            extraction: ExtractionResult aprovado
            section: Seção específica a usar como exemplo

        Returns:
            FewShotExample criado
        """
        # Gerar ID único baseado no conteúdo
        content_hash = hashlib.md5(section.content.encode()).hexdigest()[:8]
        example_id = f"{section.type.value}_{extraction.document_id}_{content_hash}"

        # Truncar texto se muito longo (max 5000 chars)
        input_text = section.content
        if len(input_text) > 5000:
            input_text = input_text[:5000] + "..."

        # Construir expected output (JSON que Claude deve retornar)
        expected_output = {
            "type": section.type.value,
            "start_marker": section.start_marker or input_text[:50],
            "end_marker": section.end_marker or input_text[-50:],
            "confidence": section.confidence,
            "summary": section.summary or f"Seção do tipo {section.type.value}"
        }

        # Quality score inicial baseado em confidence da extração
        quality_score = section.confidence

        example = FewShotExample(
            example_id=example_id,
            source_document_id=extraction.document_id,
            section_type=section.type,
            input_text=input_text,
            expected_output=expected_output,
            quality_score=quality_score,
            usage_count=0,
            tags=self._generate_tags(section)
        )

        logger.debug(f"Example created: {example_id} (quality={quality_score:.2f})")
        return example

    def add_approved_extraction_as_examples(
        self,
        extraction: ExtractionResult,
        max_examples_per_section: int = 3
    ) -> list[FewShotExample]:
        """
        Adiciona todas as seções de uma extração aprovada como exemplos.

        Args:
            extraction: ExtractionResult aprovado
            max_examples_per_section: Máximo de exemplos por tipo de seção

        Returns:
            Lista de FewShotExample criados
        """
        if extraction.validation_status != ValidationStatus.APPROVED:
            logger.warning(
                f"Extraction {extraction.document_id} não está aprovada "
                f"(status={extraction.validation_status})"
            )
            return []

        created_examples = []

        # Contar exemplos existentes por tipo
        existing_counts = {}
        for section_type in SectionType:
            existing = self.storage.load_few_shot_examples(
                section_type=section_type.value
            )
            existing_counts[section_type] = len(existing)

        # Criar exemplos para cada seção
        for section in extraction.predicted_sections:
            # Verificar limite de exemplos por tipo
            if existing_counts.get(section.type, 0) >= max_examples_per_section:
                logger.debug(
                    f"Skipping example creation for {section.type.value}: "
                    f"limit reached ({max_examples_per_section})"
                )
                continue

            example = self.create_example_from_extraction(extraction, section)
            self.storage.save_few_shot_example(example)
            created_examples.append(example)

            existing_counts[section.type] = existing_counts.get(section.type, 0) + 1

        logger.info(
            f"Created {len(created_examples)} few-shot examples from {extraction.document_id}"
        )
        return created_examples

    def get_best_examples(
        self,
        section_type: Optional[SectionType] = None,
        n: int = 3,
        strategy: str = "quality"
    ) -> list[FewShotExample]:
        """
        Retorna N melhores exemplos para um tipo de seção.

        Args:
            section_type: Tipo de seção (None = todos os tipos)
            n: Número de exemplos a retornar
            strategy: Estratégia de seleção ("quality", "balanced", "recent")

        Returns:
            Lista de FewShotExample selecionados
        """
        section_type_str = section_type.value if section_type else None

        if strategy == "quality":
            # Ordenar por quality_score
            examples = self.storage.load_few_shot_examples(
                section_type=section_type_str,
                min_quality=0.7,
                limit=n * 2,
                sort_by="quality"
            )

        elif strategy == "balanced":
            # Balance entre quality e usage (evitar overfitting)
            examples = self.storage.load_few_shot_examples(
                section_type=section_type_str,
                min_quality=0.5,
                sort_by="quality"
            )

            # Penalizar exemplos muito usados
            for example in examples:
                if example.usage_count > 10:
                    example.quality_score *= 0.8

            examples.sort(key=lambda e: e.quality_score, reverse=True)

        elif strategy == "recent":
            # Priorizar exemplos recentes
            examples = self.storage.load_few_shot_examples(
                section_type=section_type_str,
                min_quality=0.5,
                sort_by="recent"
            )

        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        selected = examples[:n]

        logger.debug(
            f"Selected {len(selected)} examples "
            f"(type={section_type_str}, strategy={strategy})"
        )

        return selected

    def format_for_prompt(
        self,
        examples: list[FewShotExample],
        format_style: str = "xml"
    ) -> str:
        """
        Formata exemplos para injeção em prompt.

        Args:
            examples: Lista de exemplos a formatar
            format_style: Estilo de formatação ("xml", "markdown")

        Returns:
            String formatada para incluir no prompt
        """
        if not examples:
            return ""

        if format_style == "xml":
            return self._format_xml(examples)
        elif format_style == "markdown":
            return self._format_markdown(examples)
        else:
            raise ValueError(f"Unknown format_style: {format_style}")

    def _format_xml(self, examples: list[FewShotExample]) -> str:
        """Formata exemplos em XML (compatível com Claude)"""
        formatted = []

        for i, example in enumerate(examples, 1):
            formatted.append(f"<example_{i}>")
            formatted.append(f"<input>")
            formatted.append(example.input_text[:500])  # Truncar para economia
            if len(example.input_text) > 500:
                formatted.append("...")
            formatted.append(f"</input>")
            formatted.append(f"<output>")
            formatted.append(str(example.expected_output))
            formatted.append(f"</output>")
            formatted.append(f"</example_{i}>")
            formatted.append("")

        return "\n".join(formatted)

    def _format_markdown(self, examples: list[FewShotExample]) -> str:
        """Formata exemplos em Markdown"""
        formatted = []

        for i, example in enumerate(examples, 1):
            formatted.append(f"### Exemplo {i}")
            formatted.append(f"**Tipo:** {example.section_type.value}")
            formatted.append(f"**Entrada:**")
            formatted.append("```")
            formatted.append(example.input_text[:500])
            if len(example.input_text) > 500:
                formatted.append("...")
            formatted.append("```")
            formatted.append(f"**Saída esperada:**")
            formatted.append("```json")
            formatted.append(str(example.expected_output))
            formatted.append("```")
            formatted.append("")

        return "\n".join(formatted)

    def mark_examples_as_used(self, example_ids: list[str]) -> None:
        """
        Marca exemplos como usados (incrementa usage_count).

        Args:
            example_ids: Lista de IDs de exemplos usados
        """
        for example_id in example_ids:
            # Descobrir section_type do exemplo para encontrar arquivo
            # (formato: {section_type}_{doc_id}_{hash})
            section_type_str = example_id.split('_')[0]

            try:
                self.storage.update_example_usage(example_id, section_type_str)
            except Exception as e:
                logger.warning(f"Failed to update usage for {example_id}: {e}")

    def _generate_tags(self, section: ExtractedSection) -> list[str]:
        """
        Gera tags para um exemplo baseado em características da seção.

        Args:
            section: Seção extraída

        Returns:
            Lista de tags
        """
        tags = []

        # Tag por tamanho
        length = len(section.content)
        if length < 500:
            tags.append("short")
        elif length > 2000:
            tags.append("long")
        else:
            tags.append("medium")

        # Tag por confidence
        if section.confidence >= 0.95:
            tags.append("high-confidence")
        elif section.confidence < 0.7:
            tags.append("low-confidence")

        # Tag por complexidade (heurística simples)
        if '\n\n' in section.content and section.content.count('\n') > 10:
            tags.append("complex")

        return tags
