"""Exportador para JSON com metadados"""
import json
from pathlib import Path
from ..analyzers.section_analyzer import Section


class JSONExporter:
    """Exporta documento para JSON estruturado"""

    def export(self, sections: list[Section], output_path: Path, metadata: dict = None):
        """
        Exporta para JSON com seções + metadados.

        Args:
            sections: Seções identificadas
            output_path: Caminho de saída
            metadata: Metadados opcionais
        """
        data = {
            "metadata": metadata or {},
            "sections": [
                {
                    "type": s.type,
                    "content": s.content,
                    "start_pos": s.start_pos,
                    "end_pos": s.end_pos,
                    "confidence": s.confidence,
                    "word_count": len(s.content.split())
                }
                for s in sections
            ],
            "total_sections": len(sections),
            "total_words": sum(len(s.content.split()) for s in sections)
        }

        output_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
