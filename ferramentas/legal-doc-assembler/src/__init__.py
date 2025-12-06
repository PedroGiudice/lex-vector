"""
legal-doc-assembler: Core engine for generating legal documents from JSON data.

A deterministic Python library for rendering Brazilian legal documents using
docxtpl (Jinja2 for MS Word) with fault-tolerant template processing.
"""

__version__ = "1.0.0"
__author__ = "Claude Code Projetos"

from .normalizers import (
    normalize_whitespace,
    normalize_name,
    normalize_address,
    format_cpf,
    format_cnpj,
    format_cep,
    format_oab,
    normalize_punctuation,
    normalize_all,
)

from .engine import DocumentEngine

__all__ = [
    "DocumentEngine",
    "normalize_whitespace",
    "normalize_name",
    "normalize_address",
    "format_cpf",
    "format_cnpj",
    "format_cep",
    "format_oab",
    "normalize_punctuation",
    "normalize_all",
]
