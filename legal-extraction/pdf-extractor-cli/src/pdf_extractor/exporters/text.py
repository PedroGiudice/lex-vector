"""
Exporter para formato texto simples (.txt).
"""

from pathlib import Path

from ..core.cleaner import CleaningResult
from .base import BaseExporter


class TextExporter(BaseExporter):
    """
    Exporta para texto simples (.txt).

    Formato:
    - Texto limpo
    - Opcionalmente inclui cabeçalho com metadados
    """

    def __init__(self, include_header: bool = False):
        """
        Args:
            include_header: Se True, inclui cabeçalho com estatísticas
        """
        self.include_header = include_header

    def export(self, result: CleaningResult, output_path: Path) -> None:
        """
        Exporta resultado para arquivo .txt.

        Args:
            result: CleaningResult do cleaner
            output_path: Caminho do arquivo de saída

        Raises:
            IOError: Se não conseguir escrever arquivo
        """
        self._ensure_parent_dir(output_path)

        content = ""

        # Cabeçalho opcional com metadados
        if self.include_header:
            content += self._generate_header(result)
            content += "\n" + ("=" * 80) + "\n\n"

        # Texto limpo
        content += result.text

        # Escreve arquivo
        try:
            output_path.write_text(content, encoding="utf-8")
        except Exception as e:
            raise IOError(f"Erro ao escrever arquivo {output_path}: {e}")

    def _generate_header(self, result: CleaningResult) -> str:
        """Gera cabeçalho com metadados"""
        stats = result.stats

        header = f"""DOCUMENTO PROCESSADO
Sistema Detectado: {stats.system_name} ({stats.system})
Confiança da Detecção: {stats.confidence}%
Tamanho Original: {stats.original_length:,} caracteres
Tamanho Final: {stats.final_length:,} caracteres
Redução: {stats.reduction_pct:.2f}%
Padrões Removidos: {len(stats.patterns_removed)}
"""
        return header


def export_txt(result: CleaningResult, output_path: Path, include_header: bool = False) -> None:
    """
    Função helper para exportar TXT rapidamente.

    Args:
        result: CleaningResult
        output_path: Caminho de saída
        include_header: Incluir cabeçalho com metadados

    Example:
        >>> from pdf_extractor.exporters.text import export_txt
        >>> export_txt(result, Path("output.txt"), include_header=True)
    """
    exporter = TextExporter(include_header=include_header)
    exporter.export(result, output_path)
