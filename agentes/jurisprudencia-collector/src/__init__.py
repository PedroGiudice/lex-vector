"""
Módulo de Processamento de Jurisprudência (DJEN).

Componentes principais:
- processador_texto: Limpeza HTML, extração de ementas, classificação
"""

from .processador_texto import (
    processar_publicacao,
    extrair_ementa,
    extrair_relator,
    classificar_tipo,
    gerar_hash_sha256,
    validar_publicacao_processada
)

__all__ = [
    'processar_publicacao',
    'extrair_ementa',
    'extrair_relator',
    'classificar_tipo',
    'gerar_hash_sha256',
    'validar_publicacao_processada'
]
