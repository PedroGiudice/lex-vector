#!/usr/bin/env python3
"""Debug de validação - descobre por que publicações estão falhando."""

import sys
from pathlib import Path
from dataclasses import asdict

# Adicionar src/ ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from downloader import DJENDownloader
from processador_texto import processar_publicacao, validar_publicacao_processada

# Baixar UMA publicação do STJ
downloader = DJENDownloader(
    data_root=Path(__file__).parent / 'test_data',
    requests_per_minute=30,
    delay_seconds=2.0
)

print("Baixando 1 publicação do STJ...")
publicacoes = downloader.baixar_api(
    tribunal='STJ',
    data='2025-11-21',
    limit=1,
    max_pages=1
)

if not publicacoes:
    print("❌ Nenhuma publicação baixada")
    sys.exit(1)

pub_raw = publicacoes[0]
print(f"✅ Publicação baixada: {pub_raw.id}\n")

# Converter para dict
raw_dict = asdict(pub_raw)

print("=" * 80)
print("DADOS BRUTOS (raw_dict)")
print("=" * 80)
for key, value in raw_dict.items():
    if isinstance(value, str) and len(value) > 100:
        print(f"{key}: {value[:100]}... (truncado)")
    else:
        print(f"{key}: {value}")

# Processar
print("\n" + "=" * 80)
print("PROCESSANDO...")
print("=" * 80)
pub_processada = processar_publicacao(raw_dict)

print("\n" + "=" * 80)
print("DADOS PROCESSADOS (pub_processada)")
print("=" * 80)
for key, value in pub_processada.items():
    if isinstance(value, str) and len(value) > 100:
        print(f"{key}: {value[:100]}... (truncado)")
    else:
        print(f"{key}: {value}")

# Validar
print("\n" + "=" * 80)
print("VALIDAÇÃO")
print("=" * 80)

campos_obrigatorios = [
    'id',
    'hash_conteudo',
    'texto_html',
    'texto_limpo',
    'tipo_publicacao',
    'fonte'
]

print("Verificando campos obrigatórios:")
for campo in campos_obrigatorios:
    presente = campo in pub_processada
    vazio = pub_processada.get(campo) is None or pub_processada.get(campo) == ''

    status = "✅" if (presente and not vazio) else "❌"
    valor = pub_processada.get(campo, 'AUSENTE')

    if isinstance(valor, str) and len(valor) > 50:
        valor_print = f"{valor[:50]}..."
    else:
        valor_print = valor

    print(f"  {status} {campo}: {valor_print}")

print("\n" + "Validação final:", "✅ VÁLIDO" if validar_publicacao_processada(pub_processada) else "❌ INVÁLIDO")
