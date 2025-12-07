"""
Step 04: O Bibliotecario - Classificador Semantico de Pecas Processuais.

Pipeline:
1. Carrega final.md (output do Step 03)
2. Aplica limpeza avancada (cleaner_advanced)
3. Segmenta em blocos logicos (segmenter)
4. Gera semantic_structure.json
5. Atualiza final.md com tags semanticas

Uso CLI:
    python -m src.steps.step_04_classify --input-md outputs/doc/final.md
    python -m src.steps.step_04_classify --output-dir outputs/doc

Uso API:
    from src.steps.step_04_classify import SemanticClassifier
    classifier = SemanticClassifier()
    result = classifier.classify("outputs/doc/final.md")
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TypedDict

import typer

# Adiciona src ao path para imports relativos
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.intelligence.cleaner_advanced import AdvancedCleaner, CleaningStats
from src.core.intelligence.definitions import get_taxonomy, reload_taxonomy
from src.core.intelligence.segmenter import (
    DocumentSegmenter,
    PageClassification,
    SectionInfo,
    SegmentationResult,
)


class ClassificationOutput(TypedDict):
    """Estrutura do output JSON."""

    doc_id: str
    processed_at: str
    version: str
    total_pages: int
    total_sections: int
    pages: list[PageClassification]
    sections: list[SectionInfo]
    cleaning_stats: dict | None
    taxonomy_version: str


@dataclass
class ClassifierConfig:
    """Configuracao do classificador."""

    apply_cleaning: bool = True
    include_masking: bool = False
    generate_tagged_md: bool = True
    min_confidence: float = 0.3


@dataclass
class SemanticClassifier:
    """
    Classificador semantico de documentos juridicos.

    Orquestra limpeza avancada e segmentacao para produzir
    estrutura semantica de um documento processual.
    """

    config: ClassifierConfig = field(default_factory=ClassifierConfig)

    # Componentes (lazy initialization)
    _cleaner: AdvancedCleaner | None = field(default=None, repr=False)
    _segmenter: DocumentSegmenter | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Inicializa componentes."""
        self._cleaner = AdvancedCleaner(
            include_masking=self.config.include_masking,
            preserve_structure=True,
        )
        self._segmenter = DocumentSegmenter(
            min_confidence=self.config.min_confidence,
        )

    def classify(
        self,
        input_md: Path | str,
        output_dir: Path | str | None = None,
    ) -> ClassificationOutput:
        """
        Classifica um documento e gera outputs.

        Args:
            input_md: Caminho para final.md
            output_dir: Diretorio para outputs (default: mesmo de input)

        Returns:
            ClassificationOutput com resultados
        """
        input_path = Path(input_md)

        if not input_path.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {input_path}")

        # Define output directory
        if output_dir is None:
            output_path = input_path.parent
        else:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

        # Extrai doc_id do path
        doc_id = output_path.name

        # Le conteudo
        markdown_content = input_path.read_text(encoding="utf-8")

        # Step 1: Limpeza avancada
        cleaning_stats = None
        if self.config.apply_cleaning:
            cleaned_content = self._cleaner.clean_markdown(markdown_content)
            # TODO: Implementar tracking de stats por pagina
        else:
            cleaned_content = markdown_content

        # Step 2: Segmentacao
        segmentation = self._segmenter.segment(cleaned_content, doc_id=doc_id)

        # Step 3: Monta output
        taxonomy = get_taxonomy()
        output = ClassificationOutput(
            doc_id=doc_id,
            processed_at=datetime.now().isoformat(),
            version="1.0.0",
            total_pages=segmentation["total_pages"],
            total_sections=segmentation["total_sections"],
            pages=segmentation["pages"],
            sections=segmentation["sections"],
            cleaning_stats=cleaning_stats,
            taxonomy_version=taxonomy.version,
        )

        # Step 4: Salva semantic_structure.json
        json_output_path = output_path / "semantic_structure.json"
        self._save_json(output, json_output_path)

        # Step 5: Gera MD taggeado
        if self.config.generate_tagged_md:
            tagged_md = self._generate_tagged_markdown(cleaned_content, segmentation)
            tagged_md_path = output_path / "final_tagged.md"
            tagged_md_path.write_text(tagged_md, encoding="utf-8")

        return output

    def _save_json(self, output: ClassificationOutput, path: Path) -> None:
        """Salva output como JSON formatado."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

    def _generate_tagged_markdown(
        self,
        markdown_content: str,
        segmentation: SegmentationResult,
    ) -> str:
        """
        Gera markdown com tags semanticas.

        Transforma:
            ## [[PAGE_001]] [TYPE: NATIVE]

        Em:
            ## [[PAGE_001]] [TYPE: NATIVE] [SEMANTIC: PETICAO_INICIAL] [CONF: 0.85]

        Args:
            markdown_content: Conteudo original
            segmentation: Resultado da segmentacao

        Returns:
            Markdown com tags semanticas
        """
        # Cria mapa de pagina -> classificacao
        page_map = {p["page"]: p for p in segmentation["pages"]}

        # Pattern para identificar headers de pagina
        page_pattern = re.compile(
            r"(##\s*\[\[PAGE_(\d+)\]\]\s*\[TYPE:\s*\w+\])",
            re.IGNORECASE,
        )

        def replace_header(match: re.Match) -> str:
            """Adiciona tags semanticas ao header."""
            original = match.group(1)
            page_num = int(match.group(2))

            if page_num in page_map:
                page_info = page_map[page_num]
                semantic_type = page_info["type"]
                confidence = page_info["confidence"]

                # Adiciona tags
                tagged = f"{original} [SEMANTIC: {semantic_type}] [CONF: {confidence}]"

                # Marca inicio de secao se aplicavel
                if page_info["is_section_start"]:
                    tagged = f"\n---\n### INICIO DE SECAO: {semantic_type}\n{tagged}"

                return tagged

            return original

        return page_pattern.sub(replace_header, markdown_content)


# =============================================================================
# CLI (typer)
# =============================================================================

app = typer.Typer(
    name="step_04_classify",
    help="Step 04: Classificador Semantico (O Bibliotecario)",
)


@app.command()
def classify(
    input_md: Path = typer.Option(
        None,
        "--input-md",
        "-i",
        help="Caminho para final.md",
    ),
    output_dir: Path = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Diretorio para outputs (default: mesmo de input)",
    ),
    no_clean: bool = typer.Option(
        False,
        "--no-clean",
        help="Desabilita limpeza avancada",
    ),
    mask_pii: bool = typer.Option(
        False,
        "--mask-pii",
        help="Mascara CPF/CNPJ/Email/Telefone",
    ),
    no_tagged_md: bool = typer.Option(
        False,
        "--no-tagged-md",
        help="Nao gera final_tagged.md",
    ),
    min_confidence: float = typer.Option(
        0.3,
        "--min-confidence",
        "-c",
        help="Confianca minima para classificacao (0.0-1.0)",
    ),
) -> None:
    """
    Classifica documento juridico e gera estrutura semantica.

    Exemplo:
        python -m src.steps.step_04_classify -i outputs/doc/final.md
    """
    # Valida input
    if input_md is None:
        typer.echo("Erro: --input-md e obrigatorio", err=True)
        raise typer.Exit(1)

    if not input_md.exists():
        typer.echo(f"Erro: arquivo nao encontrado: {input_md}", err=True)
        raise typer.Exit(1)

    # Configura
    config = ClassifierConfig(
        apply_cleaning=not no_clean,
        include_masking=mask_pii,
        generate_tagged_md=not no_tagged_md,
        min_confidence=min_confidence,
    )

    classifier = SemanticClassifier(config=config)

    typer.echo(f"[Step 04] Processando: {input_md}")
    typer.echo(f"[Step 04] Limpeza: {'SIM' if config.apply_cleaning else 'NAO'}")
    typer.echo(f"[Step 04] Mascaramento PII: {'SIM' if config.include_masking else 'NAO'}")

    try:
        result = classifier.classify(input_md, output_dir)

        typer.echo(f"\n[Step 04] Concluido!")
        typer.echo(f"  - Doc ID: {result['doc_id']}")
        typer.echo(f"  - Total paginas: {result['total_pages']}")
        typer.echo(f"  - Total secoes: {result['total_sections']}")
        typer.echo(f"  - Taxonomia: v{result['taxonomy_version']}")

        # Resumo de secoes
        typer.echo("\n[Step 04] Secoes identificadas:")
        for section in result["sections"]:
            typer.echo(
                f"  {section['section_id']}. {section['type']} "
                f"(pags {section['start_page']}-{section['end_page']}, "
                f"conf={section['confidence']})"
            )

        # Outputs gerados
        out_dir = output_dir or input_md.parent
        typer.echo(f"\n[Step 04] Outputs gerados em: {out_dir}")
        typer.echo(f"  - semantic_structure.json")
        if config.generate_tagged_md:
            typer.echo(f"  - final_tagged.md")

    except Exception as e:
        typer.echo(f"Erro: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def validate_taxonomy(
    taxonomy_path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Caminho para legal_taxonomy.json (default: assets/)",
    ),
) -> None:
    """Valida arquivo de taxonomia."""
    try:
        if taxonomy_path:
            taxonomy = reload_taxonomy(taxonomy_path)
        else:
            taxonomy = get_taxonomy()

        typer.echo(f"Taxonomia valida!")
        typer.echo(f"  - Versao: {taxonomy.version}")
        typer.echo(f"  - Descricao: {taxonomy.description}")
        typer.echo(f"  - Categorias: {len(taxonomy.categories)}")

        for cat_name in taxonomy.all_categories():
            cat = taxonomy.categories[cat_name]
            typer.echo(
                f"    - {cat_name}: {len(cat['synonyms'])} sinonimos, "
                f"prioridade={cat['priority']}"
            )

    except Exception as e:
        typer.echo(f"Erro: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
