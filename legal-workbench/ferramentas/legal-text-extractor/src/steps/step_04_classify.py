"""
Step 04: O Bibliotecário - Classificador Semântico com Gemini.

Este módulo reimplementa o Step 04 usando Gemini 2.5 Flash para:
1. Classificar peças processuais (12 categorias)
2. Limpar ruído contextual (SEM condensar)
3. Gerar output estruturado

Pipeline:
    final.md → Gemini (classificação) → Gemini (limpeza) → Outputs

Uso CLI:
    python -m src.steps.step_04_classify --input-md outputs/doc/final.md

Uso API:
    from src.steps.step_04_classify import GeminiBibliotecario
    bibliotecario = GeminiBibliotecario()
    result = bibliotecario.process("outputs/doc/final.md")
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TypedDict

import typer

# Imports relativos para compatibilidade
try:
    from src.gemini import GeminiClient, GeminiConfig
    from src.gemini.prompts import build_classification_prompt, build_cleaning_prompt
    from src.gemini.schemas import (
        ClassificationResult,
        CleanedSection,
        CleaningResult,
        PecaType,
        SectionClassification,
    )
except ImportError:
    # Fallback para imports absolutos quando rodando como script
    import sys
    from pathlib import Path as _Path

    sys.path.insert(0, str(_Path(__file__).parent.parent.parent))
    from src.gemini import GeminiClient, GeminiConfig
    from src.gemini.prompts import build_classification_prompt, build_cleaning_prompt
    from src.gemini.schemas import (
        ClassificationResult,
        CleanedSection,
        CleaningResult,
        PecaType,
        SectionClassification,
    )

logger = logging.getLogger(__name__)


class ProcessingOutput(TypedDict):
    """Output completo do processamento."""

    doc_id: str
    processed_at: str
    version: str
    classification: ClassificationResult
    cleaning: CleaningResult | None
    output_files: dict[str, str]


@dataclass
class BibliotecarioConfig:
    """Configuração do Bibliotecário."""

    # Gemini
    model: str = "gemini-2.5-flash"
    timeout_seconds: int = 300

    # Processamento
    skip_cleaning: bool = False
    generate_cleaned_md: bool = True

    # Validação
    min_confidence: float = 0.3


@dataclass
class GeminiBibliotecario:
    """
    Classificador e limpador de documentos jurídicos usando Gemini.

    Este é o orquestrador principal do Step 04. Ele:
    1. Recebe final.md do Step 03
    2. Envia para Gemini para classificação
    3. Opcionalmente envia para limpeza
    4. Valida outputs com Pydantic
    5. Gera arquivos de output

    Example:
        >>> bibliotecario = GeminiBibliotecario()
        >>> result = bibliotecario.process(Path("outputs/doc/final.md"))
        >>> print(f"Seções: {result['classification'].total_sections}")
    """

    config: BibliotecarioConfig = field(default_factory=BibliotecarioConfig)
    _client: GeminiClient | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Inicializa cliente Gemini."""
        gemini_config = GeminiConfig(
            model=self.config.model,
            timeout_seconds=self.config.timeout_seconds,
        )
        self._client = GeminiClient(config=gemini_config)

    def process(
        self,
        input_md: Path | str,
        output_dir: Path | str | None = None,
    ) -> ProcessingOutput:
        """
        Processa documento completo.

        Args:
            input_md: Caminho para final.md (output do Step 03)
            output_dir: Diretório para outputs (default: mesmo de input)

        Returns:
            ProcessingOutput com classificação e limpeza

        Raises:
            FileNotFoundError: Se input_md não existe
            RuntimeError: Se Gemini falhar na classificação
        """
        input_path = Path(input_md)

        if not input_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

        # Define output directory
        if output_dir is None:
            output_path = input_path.parent
        else:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

        # Extrai doc_id do nome do diretório
        doc_id = output_path.name

        logger.info(f"[Step 04] Processando: {input_path}")
        logger.info(f"[Step 04] Doc ID: {doc_id}")
        logger.info(f"[Step 04] Modelo: {self.config.model}")

        # Step 1: Classificação (obrigatória)
        classification = self._classify(input_path, doc_id)

        # Step 2: Limpeza (opcional)
        cleaning = None
        if not self.config.skip_cleaning:
            cleaning = self._clean(input_path, classification)

        # Step 3: Gerar outputs
        output_files = self._generate_outputs(output_path, classification, cleaning, input_path)

        logger.info(f"[Step 04] Concluído! {len(output_files)} arquivos gerados")

        return ProcessingOutput(
            doc_id=doc_id,
            processed_at=datetime.now().isoformat(),
            version="2.0.0",  # Nova versão com Gemini
            classification=classification,
            cleaning=cleaning,
            output_files=output_files,
        )

    def _classify(self, input_path: Path, doc_id: str) -> ClassificationResult:
        """
        Executa classificação via Gemini.

        Args:
            input_path: Caminho do arquivo final.md
            doc_id: ID do documento

        Returns:
            ClassificationResult validado

        Raises:
            RuntimeError: Se Gemini falhar
            ValueError: Se output não for JSON válido
        """
        logger.info("[Step 04] Fase 1: Classificação semântica via Gemini...")

        prompt = build_classification_prompt(doc_id)

        response = self._client.process_file(
            file_path=input_path,
            prompt=prompt,
            output_format="json",
        )

        if not response.success:
            raise RuntimeError(f"Gemini falhou na classificação: {response.error}")

        # Parse e valida JSON
        try:
            data = json.loads(response.text)
            logger.debug(f"JSON parseado: {len(data.get('sections', []))} seções")
        except json.JSONDecodeError as e:
            logger.error(f"Output não é JSON válido: {e}")
            logger.error(f"Response text (primeiros 500 chars): {response.text[:500]}")
            raise ValueError(f"Gemini retornou JSON inválido: {e}")

        # Converte para Pydantic models
        try:
            sections = []
            for s in data.get("sections", []):
                sections.append(
                    SectionClassification(
                        section_id=s["section_id"],
                        type=PecaType(s["type"]),
                        title=s.get("title", "Sem título")[:200],
                        start_page=s["start_page"],
                        end_page=s["end_page"],
                        confidence=s.get("confidence", 0.5),
                        reasoning=s.get("reasoning", "Sem justificativa")[:500],
                    )
                )

            result = ClassificationResult(
                doc_id=data.get("doc_id", doc_id),
                total_pages=data.get("total_pages", 0),
                total_sections=len(sections),
                sections=sections,
                summary=data.get("summary", "Documento jurídico")[:500],
            )

            logger.info(f"[Step 04] Classificação: {result.total_sections} seções identificadas")
            for s in result.sections:
                logger.info(
                    f"  - Seção {s.section_id}: {s.type.value} "
                    f"(págs {s.start_page}-{s.end_page}, conf={s.confidence:.2f})"
                )

            return result

        except Exception as e:
            logger.error(f"Erro ao criar ClassificationResult: {e}")
            logger.error(f"Data: {json.dumps(data, indent=2)[:1000]}")
            raise

    def _clean(self, input_path: Path, classification: ClassificationResult) -> CleaningResult:
        """
        Executa limpeza contextual via Gemini.

        Args:
            input_path: Caminho do arquivo
            classification: Resultado da classificação prévia

        Returns:
            CleaningResult (pode ter sections vazias se falhar)
        """
        logger.info("[Step 04] Fase 2: Limpeza contextual via Gemini...")

        # Prepara resumo da classificação para contexto
        classification_summary = "\n".join(
            [
                f"Seção {s.section_id}: {s.type.value} (páginas {s.start_page}-{s.end_page})"
                for s in classification.sections
            ]
        )

        prompt = build_cleaning_prompt(classification_summary)

        response = self._client.process_file(
            file_path=input_path,
            prompt=prompt,
            output_format="json",
        )

        if not response.success:
            logger.warning(f"Gemini falhou na limpeza: {response.error}")
            # Retorna resultado vazio mas não falha todo o processo
            return CleaningResult(
                doc_id=classification.doc_id,
                sections=[],
                total_chars_original=0,
                total_chars_cleaned=0,
                reduction_percent=0.0,
            )

        try:
            data = json.loads(response.text)

            sections = []
            for s in data.get("sections", []):
                sections.append(
                    CleanedSection(
                        section_id=s["section_id"],
                        type=PecaType(s["type"]),
                        content=s.get("content", ""),
                        noise_removed=s.get("noise_removed", [])[:5],
                    )
                )

            result = CleaningResult(
                doc_id=classification.doc_id,
                sections=sections,
                total_chars_original=data.get("total_chars_original", 0),
                total_chars_cleaned=data.get("total_chars_cleaned", 0),
                reduction_percent=data.get("reduction_percent", 0.0),
            )

            logger.info(
                f"[Step 04] Limpeza: {result.reduction_percent:.1f}% redução "
                f"({result.total_chars_original:,} → {result.total_chars_cleaned:,} chars)"
            )

            return result

        except Exception as e:
            logger.warning(f"Erro ao parsear limpeza: {e}")
            return CleaningResult(
                doc_id=classification.doc_id,
                sections=[],
                total_chars_original=0,
                total_chars_cleaned=0,
                reduction_percent=0.0,
            )

    def _generate_outputs(
        self,
        output_path: Path,
        classification: ClassificationResult,
        cleaning: CleaningResult | None,
        input_path: Path,
    ) -> dict[str, str]:
        """
        Gera arquivos de output.

        Args:
            output_path: Diretório de output
            classification: Resultado da classificação
            cleaning: Resultado da limpeza (pode ser None)
            input_path: Arquivo original para gerar tagged

        Returns:
            Dict com nomes e caminhos dos arquivos gerados
        """
        output_files = {}

        # 1. semantic_structure.json (sempre gerado)
        structure_path = output_path / "semantic_structure.json"
        structure_data = {
            "doc_id": classification.doc_id,
            "processed_at": datetime.now().isoformat(),
            "processor": "gemini-bibliotecario",
            "processor_version": "2.0.0",
            "model": self.config.model,
            "total_pages": classification.total_pages,
            "total_sections": classification.total_sections,
            "summary": classification.summary,
            "sections": [
                {
                    "section_id": s.section_id,
                    "type": s.type.value,
                    "title": s.title,
                    "start_page": s.start_page,
                    "end_page": s.end_page,
                    "confidence": s.confidence,
                    "reasoning": s.reasoning,
                }
                for s in classification.sections
            ],
        }

        with open(structure_path, "w", encoding="utf-8") as f:
            json.dump(structure_data, f, ensure_ascii=False, indent=2)
        output_files["semantic_structure.json"] = str(structure_path)
        logger.info(f"[Step 04] Gerado: {structure_path.name}")

        # 2. final_tagged.md (sempre gerado)
        tagged_md_path = output_path / "final_tagged.md"
        original_content = input_path.read_text(encoding="utf-8")
        tagged_content = self._build_tagged_markdown(original_content, classification)
        tagged_md_path.write_text(tagged_content, encoding="utf-8")
        output_files["final_tagged.md"] = str(tagged_md_path)
        logger.info(f"[Step 04] Gerado: {tagged_md_path.name}")

        # 3. final_cleaned.md (opcional, se limpeza foi executada com sucesso)
        if cleaning and cleaning.sections and self.config.generate_cleaned_md:
            cleaned_md_path = output_path / "final_cleaned.md"
            cleaned_content = self._build_cleaned_markdown(classification, cleaning)
            cleaned_md_path.write_text(cleaned_content, encoding="utf-8")
            output_files["final_cleaned.md"] = str(cleaned_md_path)
            logger.info(f"[Step 04] Gerado: {cleaned_md_path.name}")

        return output_files

    def _build_tagged_markdown(
        self,
        original_content: str,
        classification: ClassificationResult,
    ) -> str:
        """
        Adiciona tags semânticas ao markdown original.

        Transforma:
            ## [[PAGE_001]] [TYPE: NATIVE]

        Em:
            ## [[PAGE_001]] [TYPE: NATIVE] [SEMANTIC: PETICAO_INICIAL] [CONF: 0.95]
        """
        # Cria mapa de página → seção
        page_to_section: dict[int, SectionClassification] = {}
        for section in classification.sections:
            for page in range(section.start_page, section.end_page + 1):
                page_to_section[page] = section

        # Pattern para headers de página
        page_pattern = re.compile(
            r"(##\s*\[\[PAGE_(\d+)\]\]\s*\[TYPE:\s*\w+\])",
            re.IGNORECASE,
        )

        def replace_header(match: re.Match) -> str:
            original = match.group(1)
            page_num = int(match.group(2))

            if page_num in page_to_section:
                section = page_to_section[page_num]
                tagged = (
                    f"{original} [SEMANTIC: {section.type.value}] [CONF: {section.confidence:.2f}]"
                )

                # Marca início de seção
                if page_num == section.start_page:
                    tagged = f"\n---\n### SEÇÃO {section.section_id}: {section.type.value}\n> {section.title}\n\n{tagged}"

                return tagged

            return original

        return page_pattern.sub(replace_header, original_content)

    def _build_cleaned_markdown(
        self,
        classification: ClassificationResult,
        cleaning: CleaningResult,
    ) -> str:
        """Constrói markdown limpo a partir das seções limpas."""
        lines = [
            f"# {classification.doc_id}",
            "",
            "> Processado por Gemini Bibliotecário v2.0.0",
            f"> {classification.total_sections} seções | "
            f"{cleaning.reduction_percent:.1f}% redução de ruído",
            "",
            f"**Resumo:** {classification.summary}",
            "",
            "---",
            "",
        ]

        for section in cleaning.sections:
            lines.extend(
                [
                    f"## [{section.section_id}] {section.type.value}",
                    "",
                    section.content,
                    "",
                    "---",
                    "",
                ]
            )

        return "\n".join(lines)


# =============================================================================
# CLI (typer)
# =============================================================================

app = typer.Typer(
    name="step_04_classify",
    help="Step 04: Bibliotecário Semântico com Gemini",
)


@app.command()
def classify(
    input_md: Path = typer.Option(
        ...,
        "--input-md",
        "-i",
        help="Caminho para final.md (output do Step 03)",
    ),
    output_dir: Path = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Diretório para outputs (default: mesmo de input)",
    ),
    skip_cleaning: bool = typer.Option(
        False,
        "--skip-cleaning",
        help="Pula etapa de limpeza (só classifica)",
    ),
    model: str = typer.Option(
        "gemini-2.5-flash",
        "--model",
        "-m",
        help="Modelo Gemini (gemini-2.5-flash ou gemini-2.5-pro)",
    ),
) -> None:
    """
    Classifica documento jurídico usando Gemini.

    Este comando substitui a classificação baseada em regex por
    classificação semântica via LLM (Gemini 2.5 Flash/Pro).

    Exemplo:
        python -m src.steps.step_04_classify -i outputs/doc/final.md
        python -m src.steps.step_04_classify -i outputs/doc/final.md --skip-cleaning
        python -m src.steps.step_04_classify -i outputs/doc/final.md -m gemini-2.5-pro
    """
    if not input_md.exists():
        typer.echo(f"Erro: arquivo não encontrado: {input_md}", err=True)
        raise typer.Exit(1)

    config = BibliotecarioConfig(
        model=model,
        skip_cleaning=skip_cleaning,
    )

    bibliotecario = GeminiBibliotecario(config=config)

    typer.echo("[Step 04] Bibliotecário Semântico v2.0.0 (Gemini)")
    typer.echo(f"[Step 04] Input: {input_md}")
    typer.echo(f"[Step 04] Modelo: {model}")
    typer.echo(f"[Step 04] Limpeza: {'DESABILITADA' if skip_cleaning else 'HABILITADA'}")
    typer.echo("")

    try:
        result = bibliotecario.process(input_md, output_dir)

        typer.echo("")
        typer.echo("[Step 04] ✓ Processamento concluído!")
        typer.echo(f"  Doc ID: {result['doc_id']}")
        typer.echo(f"  Seções: {result['classification'].total_sections}")
        typer.echo(f"  Resumo: {result['classification'].summary[:100]}...")

        if result["cleaning"] and result["cleaning"].sections:
            typer.echo(f"  Redução: {result['cleaning'].reduction_percent:.1f}%")

        typer.echo("")
        typer.echo("[Step 04] Arquivos gerados:")
        for name, path in result["output_files"].items():
            typer.echo(f"  - {name}")

    except FileNotFoundError as e:
        typer.echo(f"Erro: {e}", err=True)
        raise typer.Exit(1)
    except RuntimeError as e:
        typer.echo(f"Erro Gemini: {e}", err=True)
        raise typer.Exit(2)
    except Exception as e:
        typer.echo(f"Erro inesperado: {e}", err=True)
        raise typer.Exit(3)


@app.command()
def version():
    """Mostra versão do Bibliotecário."""
    typer.echo("Bibliotecário Semântico v2.0.0")
    typer.echo("Engine: Gemini 2.5 Flash/Pro")
    typer.echo("Taxonomia: 12 categorias (ADR-001)")


if __name__ == "__main__":
    app()
