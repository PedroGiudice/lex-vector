"""
Schemas Pydantic para output estruturado do LTE.

Formato padrao: Markdown + XML tags
- YAML frontmatter para metadata
- Tags XML para separacao semantica de secoes
- Markdown interno para legibilidade

Este formato e otimizado para consumo por LLMs:
- Markdown e "nativo" para LLMs
- XML tags ajudam na compreensao e distincao de secoes
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SecaoType(str, Enum):
    """Tipos de secao para organizacao."""

    PETICAO = "peticao"
    DOCUMENTOS = "documentos"
    DECISAO = "decisao"
    PARECER = "parecer"
    ATA = "ata"
    OUTRO = "outro"


class Secao(BaseModel):
    """Uma secao do documento processado."""

    tipo: SecaoType = Field(description="Tipo da secao")
    titulo: str = Field(description="Titulo detectado ou inferido")
    conteudo: str = Field(description="Conteudo textual da secao")
    paginas: Optional[str] = Field(None, description="Range de paginas (ex: '1-15')")
    confianca: float = Field(ge=0.0, le=1.0, description="Confianca na deteccao")
    pattern_matched: Optional[str] = Field(None, description="Pattern que detectou esta secao")


class DocumentoMetadata(BaseModel):
    """Metadata do documento processado."""

    doc_id: str = Field(description="Identificador unico do documento")
    sistema: Optional[str] = Field(None, description="Sistema judicial detectado (PJE, ESAJ, etc)")
    total_secoes: int = Field(description="Numero total de secoes identificadas")
    total_chars: int = Field(description="Total de caracteres no documento")
    extraido_em: datetime = Field(default_factory=datetime.utcnow)
    analyzer_version: str = Field(default="1.0.0")
    formato_output: str = Field(default="markdown_xml")


class DocumentoEstruturado(BaseModel):
    """
    Documento processado com estrutura completa.

    Este modelo pode ser serializado para:
    - JSON (para APIs)
    - Markdown+XML (para LLMs - formato padrao)
    """

    metadata: DocumentoMetadata
    secoes: list[Secao]

    def to_markdown_xml(self) -> str:
        """
        Exporta para formato Markdown + XML.

        Formato otimizado para consumo por LLMs:
        - YAML frontmatter com metadata
        - Tags XML semanticas para secoes
        - Markdown interno para conteudo
        """
        lines = []

        # YAML frontmatter
        lines.append("---")
        lines.append(f"doc_id: {self.metadata.doc_id}")
        if self.metadata.sistema:
            lines.append(f"sistema: {self.metadata.sistema}")
        lines.append(f"total_secoes: {self.metadata.total_secoes}")
        lines.append(f"total_chars: {self.metadata.total_chars}")
        lines.append(f"extraido_em: {self.metadata.extraido_em.isoformat()}")
        lines.append(f"analyzer_version: {self.metadata.analyzer_version}")
        lines.append("---")
        lines.append("")

        # Secoes com tags XML
        for i, secao in enumerate(self.secoes, 1):
            # Atributos da tag
            attrs = [f'tipo="{secao.tipo.value}"']
            if secao.paginas:
                attrs.append(f'paginas="{secao.paginas}"')
            attrs.append(f'confianca="{secao.confianca:.2f}"')
            attrs_str = " ".join(attrs)

            # Tag de abertura
            lines.append(f"<secao {attrs_str}>")
            lines.append("")

            # Titulo em Markdown
            lines.append(f"# {secao.titulo}")
            lines.append("")

            # Conteudo
            lines.append(secao.conteudo.strip())
            lines.append("")

            # Tag de fechamento
            lines.append("</secao>")
            lines.append("")

        return "\n".join(lines)

    def to_json_structured(self) -> dict:
        """
        Exporta para JSON estruturado.

        Formato para APIs e integracao programatica.
        """
        return {
            "metadata": {
                "doc_id": self.metadata.doc_id,
                "sistema": self.metadata.sistema,
                "total_secoes": self.metadata.total_secoes,
                "total_chars": self.metadata.total_chars,
                "extraido_em": self.metadata.extraido_em.isoformat(),
                "analyzer_version": self.metadata.analyzer_version,
            },
            "secoes": [
                {
                    "tipo": s.tipo.value,
                    "titulo": s.titulo,
                    "conteudo": s.conteudo,
                    "paginas": s.paginas,
                    "confianca": s.confianca,
                    "pattern_matched": s.pattern_matched,
                }
                for s in self.secoes
            ],
            "summary": {
                "tipos_encontrados": list(set(s.tipo.value for s in self.secoes)),
                "confianca_media": sum(s.confianca for s in self.secoes) / len(self.secoes) if self.secoes else 0,
            },
        }


class OutputFormat(str, Enum):
    """Formatos de output disponiveis."""

    MARKDOWN_XML = "markdown_xml"  # Padrao - otimizado para LLMs
    JSON = "json"                  # Para APIs
    TEXT = "text"                  # Texto puro (legado)
    MARKDOWN = "markdown"          # Markdown puro (sem XML)
