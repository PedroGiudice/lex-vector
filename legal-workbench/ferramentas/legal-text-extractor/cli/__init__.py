"""
CLI tools for Legal Text Extractor

This module provides the unified CLI for the Legal Text Extractor.

Commands:
    lte process <arquivo>  - Processa um documento PDF
    lte stats              - Exibe estatisticas do Context Store
    lte batch <diretorio>  - Processamento em lote
    lte version            - Exibe versao

Usage after installation:
    pip install -e .
    lte --help
    lte process documento.pdf
    lte stats --db data/context.db
"""

from cli.main import __version__, app, main_entry

__all__ = ["app", "main_entry", "__version__"]
