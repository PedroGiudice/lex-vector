"""
Base abstrata para exporters.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from ..core.cleaner import CleaningResult


class BaseExporter(ABC):
    """
    Classe base abstrata para todos os exporters.

    Subclasses devem implementar export() para formatos específicos.
    """

    @abstractmethod
    def export(self, result: CleaningResult, output_path: Path) -> None:
        """
        Exporta resultado de limpeza para arquivo.

        Args:
            result: CleaningResult do DocumentCleaner
            output_path: Caminho do arquivo de saída

        Raises:
            IOError: Se houver erro ao escrever arquivo
        """
        pass

    def _ensure_parent_dir(self, output_path: Path) -> None:
        """Garante que diretório pai existe"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
