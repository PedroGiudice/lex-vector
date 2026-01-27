"""
Analisador de secoes baseado em heuristicas.

OBJETIVO: Organizar autos para facilitar compreensao por LLMs.
Zero dependencia de LLM - usa patterns regex.

Output padrao: Markdown + XML (otimizado para Claude e outros LLMs)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..core.intelligence.peca_patterns import SecaoPatternConfig, SecaoType, get_default_config
from ..core.intelligence.secao_detector import SecaoDetector
from .output_schemas import (
    DocumentoEstruturado,
    DocumentoMetadata,
    OutputFormat,
    Secao,
)

# Import Section legado para compatibilidade
from .section_analyzer import Section


@dataclass
class HeuristicSectionAnalyzer:
    """
    Analisa e organiza autos em secoes usando heuristicas.

    Features:
    - Zero dependencia de LLM
    - Patterns regex calibrados
    - Output Markdown+XML (padrao) ou JSON
    - Compativel com interface legada (list[Section])
    """

    config: SecaoPatternConfig = None
    analyzer_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if self.config is None:
            self.config = get_default_config()
        self._detector = SecaoDetector(config=self.config)

    def analyze(
        self,
        text: str,
        document_id: Optional[str] = None,
        sistema: Optional[str] = None,
    ) -> DocumentoEstruturado:
        """
        Analisa texto e retorna documento estruturado.

        Args:
            text: Texto do documento
            document_id: ID opcional (gerado se nao fornecido)
            sistema: Sistema judicial (PJE, ESAJ, etc) se conhecido

        Returns:
            DocumentoEstruturado pronto para exportacao
        """
        # Gerar doc_id se necessario
        if document_id is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            document_id = f"doc_{timestamp}_{text_hash}"

        # Detectar boundaries e segmentos
        _, segments = self._detector.detect_with_segments(text)

        # Converter segmentos para Secao
        secoes = []
        for seg in segments:
            # Inferir titulo da primeira linha do conteudo
            first_line = seg["content"].split("\n")[0].strip()[:100]
            titulo = first_line if first_line else f"Secao {seg['secao_type']}"

            secao = Secao(
                tipo=SecaoType(seg["secao_type"]) if seg["secao_type"] in [t.value for t in SecaoType] else SecaoType.OUTRO,
                titulo=titulo,
                conteudo=seg["content"],
                paginas=None,  # TODO: calcular se tiver info de pagina
                confianca=seg["confidence"],
                pattern_matched=seg.get("pattern_matched"),
            )
            secoes.append(secao)

        # Criar metadata
        metadata = DocumentoMetadata(
            doc_id=document_id,
            sistema=sistema,
            total_secoes=len(secoes),
            total_chars=len(text),
            extraido_em=datetime.utcnow(),
            analyzer_version=self.analyzer_version,
        )

        return DocumentoEstruturado(metadata=metadata, secoes=secoes)

    def analyze_to_format(
        self,
        text: str,
        output_format: OutputFormat = OutputFormat.MARKDOWN_XML,
        document_id: Optional[str] = None,
        sistema: Optional[str] = None,
    ) -> str:
        """
        Analisa e exporta diretamente para formato desejado.

        Args:
            text: Texto do documento
            output_format: Formato de saida (default: MARKDOWN_XML)
            document_id: ID opcional
            sistema: Sistema judicial se conhecido

        Returns:
            String no formato solicitado
        """
        doc = self.analyze(text, document_id, sistema)

        if output_format == OutputFormat.MARKDOWN_XML:
            return doc.to_markdown_xml()
        elif output_format == OutputFormat.JSON:
            import json
            return json.dumps(doc.to_json_structured(), ensure_ascii=False, indent=2)
        elif output_format == OutputFormat.TEXT:
            # Formato legado - texto puro
            return "\n\n---\n\n".join(s.conteudo for s in doc.secoes)
        elif output_format == OutputFormat.MARKDOWN:
            # Markdown sem XML
            lines = []
            lines.append(f"# Documento {doc.metadata.doc_id}")
            lines.append("")
            for secao in doc.secoes:
                lines.append(f"## {secao.titulo}")
                lines.append("")
                lines.append(secao.conteudo)
                lines.append("")
            return "\n".join(lines)
        else:
            raise ValueError(f"Formato nao suportado: {output_format}")

    def analyze_legacy(
        self,
        text: str,
        document_id: Optional[str] = None,
    ) -> list[Section]:
        """
        Analisa e retorna list[Section] para compatibilidade com exporters legados.

        Args:
            text: Texto do documento
            document_id: ID opcional

        Returns:
            list[Section] compativel com interface antiga
        """
        doc = self.analyze(text, document_id)

        sections = []
        current_pos = 0

        for secao in doc.secoes:
            # Encontrar posicao real no texto
            start_pos = text.find(secao.conteudo[:50], current_pos)
            if start_pos == -1:
                start_pos = current_pos
            end_pos = start_pos + len(secao.conteudo)

            section = Section(
                type=secao.tipo.value,
                content=secao.conteudo,
                start_pos=start_pos,
                end_pos=end_pos,
                confidence=secao.confianca,
            )
            sections.append(section)
            current_pos = end_pos

        return sections
