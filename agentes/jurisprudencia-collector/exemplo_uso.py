#!/usr/bin/env python3
"""
Exemplo de uso do processador_texto.py com dados reais do STJ.

Demonstra:
1. Download de publicação via API DJEN
2. Processamento com processador_texto
3. Validação de campos
4. Formato pronto para inserção no banco
"""

import requests
from src.processador_texto import processar_publicacao, validar_publicacao_processada


def obter_publicacao_stj():
    """Obtém uma publicação real do STJ."""
    url = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
    params = {
        'dataInicio': '2025-11-15',
        'dataFim': '2025-11-20',
        'siglaTribunal': 'STJ',
        'limit': 20
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    items = data.get('items', [])

    # Retornar primeiro acórdão encontrado
    for item in items:
        if 'ementa' in item.get('texto', '').lower():
            return item

    # Fallback: retornar primeiro item
    return items[0] if items else None


def main():
    print("="*80)
    print("EXEMPLO DE USO: processador_texto.py")
    print("="*80)

    # 1. Obter dados brutos
    print("\n1. Baixando publicação do STJ...")
    raw_data = obter_publicacao_stj()

    if not raw_data:
        print("❌ Nenhuma publicação obtida")
        return

    print(f"✅ Publicação obtida: {raw_data.get('numeroprocessocommascara', 'N/A')}")
    print(f"   Tipo original: {raw_data.get('tipoComunicacao', 'N/A')}")
    print(f"   Tribunal: {raw_data.get('siglaTribunal', 'N/A')}")

    # 2. Processar publicação
    print("\n2. Processando publicação...")
    pub_processada = processar_publicacao(raw_data)

    # 3. Validar
    print("\n3. Validando publicação processada...")
    if validar_publicacao_processada(pub_processada):
        print("✅ Validação OK")
    else:
        print("❌ Validação FALHOU")

    # 4. Mostrar resultado
    print("\n4. Dados processados (prontos para banco):")
    print("-"*80)
    print(f"ID (UUID):              {pub_processada['id']}")
    print(f"Hash SHA256:            {pub_processada['hash_conteudo'][:32]}...")
    print(f"Número processo:        {pub_processada['numero_processo_fmt']}")
    print(f"Tribunal:               {pub_processada['tribunal']}")
    print(f"Órgão julgador:         {pub_processada['orgao_julgador']}")
    print(f"Tipo classificado:      {pub_processada['tipo_publicacao']}")
    print(f"Classe processual:      {pub_processada['classe_processual']}")
    print(f"Data publicação:        {pub_processada['data_publicacao']}")
    print(f"Relator:                {pub_processada['relator'] or 'Não encontrado'}")
    print(f"Fonte:                  {pub_processada['fonte']}")

    # Ementa (se houver)
    if pub_processada['ementa']:
        print(f"\nEmenta extraída ({len(pub_processada['ementa'])} caracteres):")
        print("-"*80)
        ementa_preview = pub_processada['ementa'][:400]
        print(ementa_preview + ('...' if len(pub_processada['ementa']) > 400 else ''))

    # Texto limpo (preview)
    print(f"\nTexto limpo (preview - {len(pub_processada['texto_limpo'])} caracteres totais):")
    print("-"*80)
    texto_preview = pub_processada['texto_limpo'][:300]
    print(texto_preview + '...')

    # 5. Exemplo de inserção no banco (SQL)
    print("\n5. Exemplo de inserção no SQLite:")
    print("-"*80)
    print("""
INSERT INTO publicacoes (
    id, hash_conteudo, numero_processo, numero_processo_fmt,
    tribunal, orgao_julgador, tipo_publicacao, classe_processual,
    texto_html, texto_limpo, ementa, data_publicacao, relator, fonte
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)

    print("\nParâmetros:")
    params = (
        pub_processada['id'],
        pub_processada['hash_conteudo'],
        pub_processada['numero_processo'],
        pub_processada['numero_processo_fmt'],
        pub_processada['tribunal'],
        pub_processada['orgao_julgador'],
        pub_processada['tipo_publicacao'],
        pub_processada['classe_processual'],
        pub_processada['texto_html'],
        pub_processada['texto_limpo'],
        pub_processada['ementa'],
        pub_processada['data_publicacao'],
        pub_processada['relator'],
        pub_processada['fonte']
    )

    for i, param in enumerate(params, 1):
        if isinstance(param, str) and len(param) > 50:
            print(f"  {i:2}. {param[:47]}... ({len(param)} caracteres)")
        else:
            print(f"  {i:2}. {param}")

    print("\n" + "="*80)
    print("✅ EXEMPLO CONCLUÍDO")
    print("="*80)


if __name__ == '__main__':
    main()
