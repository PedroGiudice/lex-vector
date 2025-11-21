#!/usr/bin/env python3
"""
Script de validação do processador de texto com dados reais do STJ.

Testa:
1. Taxa de sucesso de extração de ementa (~90% esperado)
2. Taxa de sucesso de extração de relator
3. Classificação correta de tipos de publicação
4. Validação de hash SHA256
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from src.processador_texto import (
    processar_publicacao,
    extrair_ementa,
    extrair_relator,
    classificar_tipo,
    validar_publicacao_processada
)


def baixar_publicacoes_stj(data_inicio: str, data_fim: str, limit: int = 100) -> list:
    """Baixa publicações do STJ via API DJEN."""
    url = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
    params = {
        'dataInicio': data_inicio,
        'dataFim': data_fim,
        'siglaTribunal': 'STJ',
        'limit': limit
    }

    print(f"Baixando publicações do STJ ({data_inicio} a {data_fim})...")
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    items = data.get('items', [])
    print(f"Total obtido: {len(items)} publicações")

    return items


def analisar_acordaos(items: list) -> list:
    """Filtra apenas acórdãos (com ementa)."""
    acordaos = []
    for item in items:
        texto = item.get('texto', '').lower()
        if 'ementa' in texto:
            acordaos.append(item)
    return acordaos


def testar_taxa_extracao_ementa(items: list):
    """Testa taxa de sucesso de extração de ementa."""
    print("\n" + "="*80)
    print("TESTE 1: EXTRAÇÃO DE EMENTA")
    print("="*80)

    sucessos = 0
    falhas = 0
    ementas_extraidas = []

    for item in items:
        texto_html = item.get('texto', '')
        ementa = extrair_ementa(texto_html)

        if ementa:
            sucessos += 1
            ementas_extraidas.append({
                'processo': item.get('numeroprocessocommascara', 'N/A'),
                'ementa_preview': ementa[:150] + '...' if len(ementa) > 150 else ementa,
                'tamanho': len(ementa)
            })
        else:
            falhas += 1

    total = sucessos + falhas
    taxa = (sucessos / total * 100) if total > 0 else 0

    print(f"Total analisado: {total}")
    print(f"Sucessos: {sucessos}")
    print(f"Falhas: {falhas}")
    print(f"Taxa de sucesso: {taxa:.1f}%")

    # Mostrar exemplos
    print("\nExemplos de ementas extraídas (primeiras 3):")
    for i, exemplo in enumerate(ementas_extraidas[:3], 1):
        print(f"\n{i}. Processo: {exemplo['processo']}")
        print(f"   Tamanho: {exemplo['tamanho']} caracteres")
        print(f"   Preview: {exemplo['ementa_preview']}")

    return taxa


def testar_extracao_relator(items: list):
    """Testa taxa de sucesso de extração de relator."""
    print("\n" + "="*80)
    print("TESTE 2: EXTRAÇÃO DE RELATOR")
    print("="*80)

    sucessos = 0
    falhas = 0
    relatores = []

    for item in items:
        texto_html = item.get('texto', '')
        relator = extrair_relator(texto_html)

        if relator:
            sucessos += 1
            relatores.append(relator)
        else:
            falhas += 1

    total = sucessos + falhas
    taxa = (sucessos / total * 100) if total > 0 else 0

    print(f"Total analisado: {total}")
    print(f"Sucessos: {sucessos}")
    print(f"Falhas: {falhas}")
    print(f"Taxa de sucesso: {taxa:.1f}%")

    # Mostrar relatores únicos
    relatores_unicos = list(set(relatores))
    print(f"\nRelatores únicos encontrados: {len(relatores_unicos)}")
    print("\nExemplos (primeiros 5):")
    for i, relator in enumerate(relatores_unicos[:5], 1):
        print(f"{i}. {relator}")

    return taxa


def testar_classificacao_tipo(items: list):
    """Testa classificação de tipos de publicação."""
    print("\n" + "="*80)
    print("TESTE 3: CLASSIFICAÇÃO DE TIPO")
    print("="*80)

    tipos_contados = {}

    for item in items:
        tipo_original = item.get('tipoComunicacao', 'N/A')
        texto = item.get('texto', '')
        tipo_classificado = classificar_tipo(tipo_original, texto)

        if tipo_classificado not in tipos_contados:
            tipos_contados[tipo_classificado] = 0
        tipos_contados[tipo_classificado] += 1

    print("Distribuição de tipos classificados:")
    for tipo, count in sorted(tipos_contados.items(), key=lambda x: x[1], reverse=True):
        porcentagem = (count / len(items) * 100)
        print(f"  {tipo}: {count} ({porcentagem:.1f}%)")


def testar_processamento_completo(items: list):
    """Testa processamento completo de publicações."""
    print("\n" + "="*80)
    print("TESTE 4: PROCESSAMENTO COMPLETO")
    print("="*80)

    sucessos = 0
    falhas = 0
    hashes_unicos = set()

    for item in items:
        try:
            pub_processada = processar_publicacao(item)

            # Validar publicação
            if validar_publicacao_processada(pub_processada):
                sucessos += 1
                hashes_unicos.add(pub_processada['hash_conteudo'])
            else:
                falhas += 1
                print(f"  ⚠️ Validação falhou para processo {item.get('numeroprocessocommascara', 'N/A')}")

        except Exception as e:
            falhas += 1
            print(f"  ❌ Erro ao processar: {e}")

    total = sucessos + falhas
    taxa = (sucessos / total * 100) if total > 0 else 0

    print(f"Total processado: {total}")
    print(f"Sucessos: {sucessos}")
    print(f"Falhas: {falhas}")
    print(f"Taxa de sucesso: {taxa:.1f}%")
    print(f"Hashes únicos: {len(hashes_unicos)}")
    print(f"Duplicatas detectadas: {sucessos - len(hashes_unicos)}")


def main():
    """Executa bateria de testes."""
    print("="*80)
    print("VALIDAÇÃO DO PROCESSADOR DE TEXTO - STJ")
    print("="*80)

    # Baixar dados dos últimos 7 dias
    data_fim = datetime.now().strftime('%Y-%m-%d')
    data_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    try:
        # Baixar publicações
        items = baixar_publicacoes_stj(data_inicio, data_fim, limit=200)

        if not items:
            print("❌ Nenhuma publicação obtida. Encerrando.")
            return 1

        # Filtrar acórdãos
        acordaos = analisar_acordaos(items)
        print(f"\nAcórdãos encontrados: {len(acordaos)} ({len(acordaos)/len(items)*100:.1f}% do total)")

        # Executar testes
        taxa_ementa = testar_taxa_extracao_ementa(acordaos)
        taxa_relator = testar_extracao_relator(acordaos)
        testar_classificacao_tipo(items)
        testar_processamento_completo(items)

        # Resumo final
        print("\n" + "="*80)
        print("RESUMO FINAL")
        print("="*80)
        print(f"Total de publicações analisadas: {len(items)}")
        print(f"Acórdãos identificados: {len(acordaos)} ({len(acordaos)/len(items)*100:.1f}%)")
        print(f"Taxa de extração de ementa: {taxa_ementa:.1f}% (esperado: ~90%)")
        print(f"Taxa de extração de relator: {taxa_relator:.1f}%")

        if taxa_ementa >= 85:
            print("\n✅ Taxa de extração de ementa APROVADA (>= 85%)")
        else:
            print(f"\n⚠️ Taxa de extração de ementa ABAIXO DO ESPERADO (esperado: >= 85%, obtido: {taxa_ementa:.1f}%)")

        return 0

    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
