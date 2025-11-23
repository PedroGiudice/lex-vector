#!/usr/bin/env python3
"""
TDD - Test de Integração Downloader -> Processador

HIPÓTESE: A conversão de PublicacaoRaw para dict está causando incompatibilidade
de campos entre downloader e processador.
"""

import sys
from pathlib import Path
from dataclasses import asdict

# Adicionar src/ ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from downloader import PublicacaoRaw
from processador_texto import processar_publicacao, validar_publicacao_processada


def test_publicacao_raw_to_dict_to_processador():
    """
    TEST: Simular exatamente o fluxo do teste de coleta focada.

    Fluxo:
    1. Downloader cria PublicacaoRaw
    2. Converter para dict com asdict()
    3. Passar para processar_publicacao()
    4. Validar resultado
    """
    print("=" * 80)
    print("TEST: PublicacaoRaw -> asdict() -> processar_publicacao()")
    print("=" * 80)

    # STEP 1: Criar PublicacaoRaw igual ao que o downloader faz
    pub_raw = PublicacaoRaw(
        id='465639846',
        hash_conteudo='a' * 64,
        numero_processo='10518252520258260000',
        numero_processo_fmt='1051825-25.2025.8.26.0000',
        tribunal='STJ',
        orgao_julgador='SPF COORDENADORIA DOS JUIZADOS ESPECIAIS',
        tipo_comunicacao='Intimação',
        classe_processual='HABEAS CORPUS',
        texto_html='<p><strong>HC 1051825/SP</strong></p><p>EMENTA: Teste...</p>',
        data_publicacao='2025-11-21',  # ← Downloader passa a data aqui
        destinatario_advogados=[],
        metadata={  # ← Mas data_disponibilizacao vai aqui dentro
            'data_disponibilizacao': '2025-11-19',
            'meio_circulacao': 'E',
            'caderno_processo': 'judicial'
        }
    )

    print("\n1. PublicacaoRaw (dataclass):")
    print(f"   data_publicacao: {pub_raw.data_publicacao}")
    print(f"   metadata: {pub_raw.metadata}")

    # STEP 2: Converter para dict (igual ao teste de coleta)
    raw_dict = asdict(pub_raw)

    print("\n2. asdict(PublicacaoRaw):")
    print(f"   Chaves: {list(raw_dict.keys())}")
    print(f"   data_publicacao: {raw_dict.get('data_publicacao')}")
    print(f"   data_disponibilizacao: {raw_dict.get('data_disponibilizacao')}")
    print(f"   metadata['data_disponibilizacao']: {raw_dict.get('metadata', {}).get('data_disponibilizacao')}")

    # STEP 3: Processar (o que processador_texto.py espera)
    print("\n3. O que processador_texto.py busca:")
    print(f"   raw_data.get('data_disponibilizacao'): {raw_dict.get('data_disponibilizacao')}")  # ← Vai dar None!
    print(f"   raw_data.get('siglaTribunal'): {raw_dict.get('siglaTribunal')}")  # ← Vai dar None! (campo errado)
    print(f"   raw_data.get('nomeOrgao'): {raw_dict.get('nomeOrgao')}")  # ← Vai dar None! (campo errado)

    # STEP 4: Tentar processar
    print("\n4. Processando...")
    pub_processada = processar_publicacao(raw_dict)

    print("\n5. Resultado processado:")
    print(f"   data_publicacao: {pub_processada.get('data_publicacao')}")
    print(f"   tribunal: {pub_processada.get('tribunal')}")
    print(f"   orgao_julgador: {pub_processada.get('orgao_julgador')}")

    # STEP 5: Validar
    print("\n6. Verificação de campos obrigatórios:")
    campos_obrigatorios = ['id', 'hash_conteudo', 'texto_html', 'texto_limpo', 'tipo_publicacao', 'fonte']

    for campo in campos_obrigatorios:
        valor = pub_processada.get(campo)
        vazio = valor is None or valor == ''
        status = "✅" if not vazio else "❌"
        print(f"   {status} {campo}: {'OK' if not vazio else 'VAZIO/None'} (valor: {str(valor)[:50] if valor else 'None'})")

    valido = validar_publicacao_processada(pub_processada)
    print(f"\n7. Validação final: {'✅ VÁLIDA' if valido else '❌ INVÁLIDA'}")

    if not valido:
        print("\n🐛 BUG AINDA PRESENTE!")
        print("   Algum campo obrigatório está vazio ou inválido (ver acima)")
        return False

    print("\n✅ BUG CORRIGIDO!")
    return True


if __name__ == '__main__':
    success = test_publicacao_raw_to_dict_to_processador()
    sys.exit(0 if success else 1)
