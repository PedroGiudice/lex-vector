#!/usr/bin/env python3
"""
TDD - Testes Unitários para Processador de Texto

Systematic debugging approach:
1. Test campo por campo (isolação)
2. Test com dados reais mínimos
3. Test com dados completos
"""

import sys
import uuid
import re
from pathlib import Path

# Adicionar src/ ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from processador_texto import processar_publicacao, validar_publicacao_processada


def test_validacao_campos_minimos():
    """TEST 1: Validação deve aceitar campos mínimos obrigatórios."""
    print("\n" + "=" * 80)
    print("TEST 1: Validação com campos mínimos")
    print("=" * 80)

    pub_minima = {
        'id': str(uuid.uuid4()),
        'hash_conteudo': 'a' * 64,  # Hash SHA256 válido (64 hex chars)
        'texto_html': '<p>Teste</p>',
        'texto_limpo': 'Teste',
        'tipo_publicacao': 'Intimação',
        'fonte': 'DJEN'
    }

    resultado = validar_publicacao_processada(pub_minima)
    print(f"Publicação mínima: {'✅ VÁLIDA' if resultado else '❌ INVÁLIDA'}")

    if not resultado:
        print("\n🐛 BUG ENCONTRADO: Validação rejeitou publicação com campos mínimos corretos!")
        print("Campos fornecidos:", list(pub_minima.keys()))
        return False

    print("✅ PASSOU: Validação aceita campos mínimos")
    return True


def test_validacao_campo_por_campo():
    """TEST 2: Isolar qual campo está falhando."""
    print("\n" + "=" * 80)
    print("TEST 2: Validação campo por campo (isolação)")
    print("=" * 80)

    campos_obrigatorios = [
        'id',
        'hash_conteudo',
        'texto_html',
        'texto_limpo',
        'tipo_publicacao',
        'fonte'
    ]

    pub_base = {
        'id': str(uuid.uuid4()),
        'hash_conteudo': 'a' * 64,
        'texto_html': '<p>Teste</p>',
        'texto_limpo': 'Teste',
        'tipo_publicacao': 'Intimação',
        'fonte': 'DJEN'
    }

    # Test removendo cada campo
    for campo in campos_obrigatorios:
        pub_teste = pub_base.copy()
        del pub_teste[campo]

        resultado = validar_publicacao_processada(pub_teste)
        esperado = False  # Deve falhar sem campo obrigatório

        status = "✅" if resultado == esperado else "❌"
        print(f"  {status} Sem campo '{campo}': {'REJEITADO' if not resultado else 'ACEITO'} (esperado: REJEITADO)")

    # Test com cada campo vazio
    for campo in campos_obrigatorios:
        pub_teste = pub_base.copy()
        pub_teste[campo] = ''  # String vazia

        resultado = validar_publicacao_processada(pub_teste)
        esperado = False  # Deve falhar com campo vazio

        status = "✅" if resultado == esperado else "❌"
        print(f"  {status} Campo '{campo}' vazio: {'REJEITADO' if not resultado else 'ACEITO'} (esperado: REJEITADO)")

    return True


def test_processador_com_dados_reais_minimos():
    """TEST 3: Processar dados mínimos da API DJEN."""
    print("\n" + "=" * 80)
    print("TEST 3: Processador com dados reais mínimos")
    print("=" * 80)

    # Dados mínimos que a API DJEN pode retornar
    raw_data_minima = {
        'texto': '<p>INTIMAÇÃO: Processo 1234567-89.2025.8.00.0000</p>',
        'tipoComunicacao': 'Intimação',
        'siglaTribunal': 'STJ',
        'data_disponibilizacao': '2025-11-20'
    }

    print("Dados de entrada (mínimos):")
    for k, v in raw_data_minima.items():
        print(f"  {k}: {v if len(str(v)) < 60 else str(v)[:60] + '...'}")

    pub_processada = processar_publicacao(raw_data_minima)

    print("\nDados processados:")
    for k, v in pub_processada.items():
        valor_print = str(v) if v is not None and len(str(v)) < 60 else (str(v)[:60] + '...' if v else 'None')
        print(f"  {k}: {valor_print}")

    # Verificar campos obrigatórios
    print("\nVerificação de campos obrigatórios:")
    campos_obrigatorios = ['id', 'hash_conteudo', 'texto_html', 'texto_limpo', 'tipo_publicacao', 'fonte']

    for campo in campos_obrigatorios:
        presente = campo in pub_processada
        valor = pub_processada.get(campo)
        vazio = valor is None or valor == ''

        status = "✅" if (presente and not vazio) else "❌"
        print(f"  {status} {campo}: {'OK' if (presente and not vazio) else 'FALTA/VAZIO'}")

    # Validar
    valido = validar_publicacao_processada(pub_processada)
    print(f"\nValidação final: {'✅ VÁLIDA' if valido else '❌ INVÁLIDA'}")

    if not valido:
        print("\n🐛 BUG ENCONTRADO: Processador não gera publicação válida com dados mínimos!")
        return False

    print("✅ PASSOU: Processador gera publicação válida com dados mínimos")
    return True


def test_processador_com_dados_reais_completos():
    """TEST 4: Processar dados completos da API DJEN."""
    print("\n" + "=" * 80)
    print("TEST 4: Processador com dados reais completos")
    print("=" * 80)

    # Dados completos simulando resposta real da API DJEN
    raw_data_completa = {
        'id': '465639846',
        'texto': '''
        <html>
        <body>
        <p><strong>HC 1051825/SP</strong></p>
        <p><strong>HABEAS CORPUS</strong></p>
        <p><strong>EMENTA:</strong> APELAÇÃO CRIMINAL - Crime de ameaça - Artigo 147 do Código Penal
        - Sentença condenatória - Recurso defensivo - Pleito absolutório - Impossibilidade -
        Autoria e materialidade comprovadas - Provas testemunhais e documentais robustas.</p>
        <p><strong>DECISÃO:</strong> Por unanimidade, negou-se provimento ao recurso.</p>
        <p><strong>RELATOR:</strong> MINISTRO PRESIDENTE DO STJ</p>
        </body>
        </html>
        ''',
        'tipoComunicacao': 'Intimação',
        'numero_processo': '10518252520258260000',
        'numeroprocessocommascara': '1051825-25.2025.8.26.0000',
        'siglaTribunal': 'STJ',
        'nomeOrgao': 'SPF COORDENADORIA DOS JUIZADOS ESPECIAIS E ANEXOS',
        'nomeClasse': 'HABEAS CORPUS',
        'data_disponibilizacao': '2025-11-19',
        'destinatario_advogados': []
    }

    print("Dados de entrada (completos):")
    for k, v in raw_data_completa.items():
        valor_print = str(v) if len(str(v)) < 80 else str(v)[:80] + '...'
        print(f"  {k}: {valor_print}")

    pub_processada = processar_publicacao(raw_data_completa)

    print("\nDados processados:")
    for k, v in pub_processada.items():
        if v is None:
            valor_print = 'None'
        elif isinstance(v, str) and len(v) > 80:
            valor_print = v[:80] + '...'
        else:
            valor_print = str(v)
        print(f"  {k}: {valor_print}")

    # Verificar campos obrigatórios
    print("\nVerificação de campos obrigatórios:")
    campos_obrigatorios = ['id', 'hash_conteudo', 'texto_html', 'texto_limpo', 'tipo_publicacao', 'fonte']

    todos_ok = True
    for campo in campos_obrigatorios:
        presente = campo in pub_processada
        valor = pub_processada.get(campo)
        vazio = valor is None or valor == ''

        ok = presente and not vazio
        status = "✅" if ok else "❌"
        print(f"  {status} {campo}: {'OK' if ok else 'FALTA/VAZIO'}")

        if not ok:
            todos_ok = False

    # Validar
    valido = validar_publicacao_processada(pub_processada)
    print(f"\nValidação final: {'✅ VÁLIDA' if valido else '❌ INVÁLIDA'}")

    if not valido:
        print("\n🐛 BUG ENCONTRADO: Processador não gera publicação válida com dados completos!")
        print("\nCampos problemáticos:")
        for campo in campos_obrigatorios:
            valor = pub_processada.get(campo)
            if valor is None or valor == '':
                print(f"  ❌ {campo}: {valor}")
        return False

    # Verificar extração de ementa
    ementa = pub_processada.get('ementa')
    if ementa:
        print(f"\n✅ Ementa extraída: {ementa[:100]}...")
    else:
        print("\n⚠️  Ementa não extraída (pode ser normal se não for acórdão)")

    print("✅ PASSOU: Processador gera publicação válida com dados completos")
    return True


def run_all_tests():
    """Executa todos os testes em sequência."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 25 + "TDD - TESTES UNITÁRIOS" + " " * 31 + "║")
    print("╚" + "=" * 78 + "╝")

    tests = [
        ("Validação com campos mínimos", test_validacao_campos_minimos),
        ("Validação campo por campo", test_validacao_campo_por_campo),
        ("Processador com dados mínimos", test_processador_com_dados_reais_minimos),
        ("Processador com dados completos", test_processador_com_dados_reais_completos),
    ]

    resultados = []

    for nome, test_func in tests:
        try:
            resultado = test_func()
            resultados.append((nome, resultado))
        except Exception as e:
            print(f"\n❌ ERRO no teste '{nome}': {e}")
            import traceback
            traceback.print_exc()
            resultados.append((nome, False))

    # Resumo
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 32 + "RESUMO" + " " * 40 + "║")
    print("╚" + "=" * 78 + "╝")

    passou = sum(1 for _, r in resultados if r)
    total = len(resultados)

    for nome, resultado in resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"{status}: {nome}")

    print(f"\nTotal: {passou}/{total} testes passaram")

    if passou == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        return True
    else:
        print(f"\n❌ {total - passou} teste(s) falharam")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
