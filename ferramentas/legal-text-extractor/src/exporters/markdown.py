"""Exportador para Markdown estruturado"""
from pathlib import Path
from ..analyzers.section_analyzer import Section


class MarkdownExporter:
    """Exporta documento com seções separadas em Markdown"""

    def export(self, sections: list[Section], output_path: Path, metadata: dict = None):
        """
        Exporta seções para Markdown estruturado.

        Args:
            sections: Seções identificadas
            output_path: Caminho de saída
            metadata: Metadados opcionais (sistema, confidence, etc)
        """
        lines = []

        # Header com metadados
        if metadata:
            lines.append("# Documento Processado\n")
            lines.append(f"**Sistema:** {metadata.get('system', 'N/A')}")
            lines.append(f"**Confiança:** {metadata.get('confidence', 0)}%")
            lines.append(f"**Redução:** {metadata.get('reduction_pct', 0):.1f}%\n")
            lines.append("---\n")

        # Seções
        for section in sections:
            lines.append(f"## {section.type.upper()}\n")
            lines.append(section.content)
            lines.append("\n---\n")

        # Salva
        output_path.write_text("\n".join(lines), encoding="utf-8")
