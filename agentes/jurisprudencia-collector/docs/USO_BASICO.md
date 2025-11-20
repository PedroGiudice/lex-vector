# Guia de Uso Básico - Jurisprudência Collector

Exemplos práticos de como usar o sistema de coleta e processamento de jurisprudência.

## Pré-requisitos

Assumindo que você já completou a instalação em `INSTALACAO.md`:

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector
source .venv/bin/activate
```

## 1. Processamento de Publicação Simples

### 1.1 Exemplo Básico

```python
from src.processador_texto import processar_publicacao, validar_publicacao_processada

# Dados brutos da API DJEN (simulado)
raw_data = {
    'texto': '''
        <p><strong>EMENTA:</strong> Direito Civil. Responsabilidade Civil.
        Pessoa Jurídica de Direito Privado. Dano Moral. Indenização.</p>

        <p><strong>ACÓRDÃO</strong></p>
        <p>Vistos, relatados e discutidos os autos do recurso especial...</p>

        <p><strong>RELATOR:</strong> Ministro JOÃO SILVA</p>
    ''',
    'tipoComunicacao': 'Intimação',
    'numero_processo': '00012345620248210000',
    'numeroprocessocommascara': '0001234-56.2024.8.21.0000',
    'siglaTribunal': 'STJ',
    'nomeOrgao': '1ª Turma',
    'nomeClasse': 'Apelação',
    'data_disponibilizacao': '2025-11-20'
}

# Processar
pub = processar_publicacao(raw_data)

# Validar
if validar_publicacao_processada(pub):
    print("✅ Publicação válida!")
else:
    print("❌ Publicação inválida!")

# Acessar campos
print(f"ID: {pub['id']}")
print(f"Tipo: {pub['tipo_publicacao']}")
print(f"Tribunal: {pub['tribunal']}")
print(f"Ementa: {pub['ementa'][:100]}...")
print(f"Hash: {pub['hash_conteudo']}")
```

**Saída esperada:**

```
✅ Publicação válida!
ID: 8f3c9a1b-2d4e-4f6a-8b9c-1d2e3f4a5b6c
Tipo: Acórdão
Tribunal: STJ
Ementa: Direito Civil. Responsabilidade Civil. Pessoa Jurídica de Direito Privado...
Hash: a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1
```

### 1.2 Extrair Componentes Individuais

```python
from src.processador_texto import (
    extrair_ementa,
    extrair_relator,
    classificar_tipo,
    gerar_hash_sha256
)

texto = '''
EMENTA: Direito Processual Civil. Sentença de Embargos à Execução.

RELATOR: Ministro CARLOS COSTA

DECISÃO MONOCRÁTICA: Provido o recurso.
'''

# Extrair componentes
ementa = extrair_ementa(texto)
relator = extrair_relator(texto)
tipo = classificar_tipo('Edital', texto)
hash_val = gerar_hash_sha256(texto)

print(f"Ementa: {ementa}")
print(f"Relator: {relator}")
print(f"Tipo: {tipo}")
print(f"Hash: {hash_val}")
```

**Saída esperada:**

```
Ementa: Direito Processual Civil. Sentença de Embargos à Execução.
Relator: CARLOS COSTA
Tipo: Decisão
Hash: 9c47f1...
```

## 2. Baixar e Processar Publicações da API DJEN

### 2.1 Baixar Publicações do STJ (Últimos 7 dias)

```python
import requests
from datetime import datetime, timedelta
from src.processador_texto import processar_publicacao

def baixar_publicacoes_djen(tribunal='STJ', dias=7):
    """Baixa publicações da API DJEN."""

    # Datas
    data_fim = datetime.now().strftime('%Y-%m-%d')
    data_inicio = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')

    # URL da API
    url = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
    params = {
        'dataInicio': data_inicio,
        'dataFim': data_fim,
        'siglaTribunal': tribunal,
        'limit': 100,
        'offset': 0
    }

    print(f"Baixando publicações ({tribunal}, {data_inicio} a {data_fim})...")

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        items = data.get('items', [])

        print(f"✅ Total obtido: {len(items)} publicações")
        return items

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao baixar: {e}")
        return []

# Usar
items = baixar_publicacoes_djen(tribunal='STJ', dias=3)
```

**Saída esperada:**

```
Baixando publicações (STJ, 2025-11-17 a 2025-11-20)...
✅ Total obtido: 85 publicações
```

### 2.2 Processar Lote de Publicações

```python
def processar_lote(items):
    """Processa lote de publicações."""

    processadas = []
    erros = []

    for i, item in enumerate(items, 1):
        try:
            pub = processar_publicacao(item)
            processadas.append(pub)

            # Mostrar progresso a cada 10
            if i % 10 == 0:
                print(f"  Processadas {i}/{len(items)}...")

        except Exception as e:
            erros.append({
                'processo': item.get('numeroprocessocommascara', 'N/A'),
                'erro': str(e)
            })

    print(f"\n✅ Total processado: {len(processadas)}")
    print(f"❌ Erros: {len(erros)}")

    return processadas, erros

# Usar
items = baixar_publicacoes_djen()
processadas, erros = processar_lote(items)

# Exibir erros (se houver)
if erros:
    print("\nErros encontrados:")
    for erro in erros[:3]:  # Mostrar apenas os 3 primeiros
        print(f"  {erro['processo']}: {erro['erro']}")
```

**Saída esperada:**

```
  Processadas 10/85...
  Processadas 20/85...
  Processadas 30/85...

✅ Total processado: 85
❌ Erros: 0
```

## 3. Inserir no Banco de Dados

### 3.1 Inserir Publicação Individual

```python
import sqlite3
from src.processador_texto import processar_publicacao, validar_publicacao_processada

def inserir_publicacao(db_path, pub):
    """Insere publicação no banco."""

    # Conectar
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO publicacoes (
            id, hash_conteudo, numero_processo, numero_processo_fmt,
            tribunal, orgao_julgador, tipo_publicacao, classe_processual,
            texto_html, texto_limpo, ementa, data_publicacao, relator, fonte
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pub['id'],
            pub['hash_conteudo'],
            pub['numero_processo'],
            pub['numero_processo_fmt'],
            pub['tribunal'],
            pub['orgao_julgador'],
            pub['tipo_publicacao'],
            pub['classe_processual'],
            pub['texto_html'],
            pub['texto_limpo'],
            pub['ementa'],
            pub['data_publicacao'],
            pub['relator'],
            pub['fonte']
        ))

        conn.commit()
        return True

    except sqlite3.IntegrityError as e:
        # Duplicata (hash já existe)
        conn.rollback()
        return False

    finally:
        conn.close()

# Usar
pub = processar_publicacao(raw_data)
if validar_publicacao_processada(pub):
    if inserir_publicacao('jurisprudencia.db', pub):
        print("✅ Publicação inserida!")
    else:
        print("⚠️ Publicação já existe (duplicata)")
else:
    print("❌ Publicação inválida!")
```

### 3.2 Inserir Lote Completo

```python
def inserir_lote(db_path, publicacoes):
    """Insere lote de publicações."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    novas = 0
    duplicatas = 0
    erros = 0

    for pub in publicacoes:
        try:
            if not validar_publicacao_processada(pub):
                erros += 1
                continue

            cursor.execute("""
            INSERT OR IGNORE INTO publicacoes (
                id, hash_conteudo, numero_processo, numero_processo_fmt,
                tribunal, orgao_julgador, tipo_publicacao, classe_processual,
                texto_html, texto_limpo, ementa, data_publicacao, relator, fonte
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pub['id'], pub['hash_conteudo'], pub['numero_processo'],
                pub['numero_processo_fmt'], pub['tribunal'], pub['orgao_julgador'],
                pub['tipo_publicacao'], pub['classe_processual'],
                pub['texto_html'], pub['texto_limpo'], pub['ementa'],
                pub['data_publicacao'], pub['relator'], pub['fonte']
            ))

            # Verificar se foi inserida
            if cursor.rowcount > 0:
                novas += 1
            else:
                duplicatas += 1

        except Exception as e:
            erros += 1
            print(f"  ⚠️ Erro: {e}")

    conn.commit()
    conn.close()

    return {
        'novas': novas,
        'duplicatas': duplicatas,
        'erros': erros,
        'total': len(publicacoes)
    }

# Usar
resultado = inserir_lote('jurisprudencia.db', processadas)
print(f"\nResultado da inserção:")
print(f"  Novas: {resultado['novas']}")
print(f"  Duplicatas: {resultado['duplicatas']}")
print(f"  Erros: {resultado['erros']}")
```

**Saída esperada:**

```
Resultado da inserção:
  Novas: 42
  Duplicatas: 35
  Erros: 0
```

## 4. Consultar o Banco de Dados

### 4.1 Estatísticas Gerais

```python
import sqlite3

def exibir_estatisticas(db_path):
    """Exibe estatísticas do banco."""

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Usar VIEW v_stats (definida no schema)
    cursor.execute("SELECT * FROM v_stats")
    stats = cursor.fetchone()

    print("📊 ESTATÍSTICAS GERAIS")
    print("="*50)
    print(f"Total de publicações: {stats['total_publicacoes']}")
    print(f"Tribunais únicos: {stats['tribunais_unicos']}")
    print(f"Processos únicos: {stats['processos_unicos']}")
    print(f"Acórdãos: {stats['total_acordaos']}")
    print(f"Sentenças: {stats['total_sentencas']}")
    print(f"Decisões: {stats['total_decisoes']}")
    print(f"Data mais antiga: {stats['data_mais_antiga']}")
    print(f"Data mais recente: {stats['data_mais_recente']}")

    conn.close()

exibir_estatisticas('jurisprudencia.db')
```

**Saída esperada:**

```
📊 ESTATÍSTICAS GERAIS
==================================================
Total de publicações: 1250
Tribunais únicos: 5
Processos únicos: 1100
Acórdãos: 450
Sentenças: 300
Decisões: 500
Data mais antiga: 2025-11-01
Data mais recente: 2025-11-20
```

### 4.2 Publicações por Tribunal

```python
def exibir_por_tribunal(db_path):
    """Exibe distribuição por tribunal."""

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Usar VIEW v_publicacoes_por_tribunal
    cursor.execute("SELECT * FROM v_publicacoes_por_tribunal LIMIT 10")

    print("🏛️ PUBLICAÇÕES POR TRIBUNAL")
    print("="*80)
    print(f"{'Tribunal':<8} {'Total':<8} {'Acórdãos':<10} {'Sentenças':<12} {'Decisões':<10}")
    print("-"*80)

    for row in cursor.fetchall():
        print(f"{row['tribunal']:<8} {row['total']:<8} {row['acordaos']:<10} "
              f"{row['sentencas']:<12} {row['decisoes']:<10}")

    conn.close()

exibir_por_tribunal('jurisprudencia.db')
```

**Saída esperada:**

```
🏛️ PUBLICAÇÕES POR TRIBUNAL
================================================================================
Tribunal Total    Acórdãos   Sentenças    Decisões
--------------------------------------------------------------------------------
TJSP     450      150        200          100
STJ      300      120        80           100
TJRJ     250      80         100          70
TRF3     150      50         50           50
TJMG     100      20         30           50
```

### 4.3 Publicações Recentes

```python
def exibir_recentes(db_path, dias=7):
    """Exibe publicações dos últimos N dias."""

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Usar VIEW v_publicacoes_recentes (últimos 30 dias por padrão)
    cursor.execute("""
    SELECT id, numero_processo_fmt, tribunal, tipo_publicacao,
           preview, data_publicacao
    FROM v_publicacoes_recentes
    LIMIT 5
    """)

    print(f"📅 PUBLICAÇÕES RECENTES (últimos {dias} dias)")
    print("="*100)

    for i, row in enumerate(cursor.fetchall(), 1):
        print(f"\n{i}. {row['tribunal']} | {row['tipo_publicacao']}")
        print(f"   Processo: {row['numero_processo_fmt']}")
        print(f"   Data: {row['data_publicacao']}")
        print(f"   Preview: {row['preview']}")

    conn.close()

exibir_recentes('jurisprudencia.db', dias=7)
```

**Saída esperada:**

```
📅 PUBLICAÇÕES RECENTES (últimos 7 dias)
====================================================================================================

1. STJ | Acórdão
   Processo: 0001234-56.2024.8.21.0000
   Data: 2025-11-20
   Preview: APELAÇÃO CRIMINAL - Crime de ameaça - Lei nº 1.518/97 - [...]

2. TJSP | Sentença
   Processo: 0002345-67.2024.8.26.0000
   Data: 2025-11-20
   Preview: APELAÇÃO CÍVEL - Indenização por dano moral - Responsabilidade [...]
```

## 5. Busca Textual (FTS5)

### 5.1 Buscar por Termo

```python
def buscar_por_termo(db_path, termo, limit=10):
    """Busca publicações usando FTS5."""

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        p.id,
        p.numero_processo_fmt,
        p.tribunal,
        p.tipo_publicacao,
        p.data_publicacao,
        snippet(publicacoes_fts, 1, '<mark>', '</mark>', '...', 64) AS ementa_snippet
    FROM publicacoes_fts
    JOIN publicacoes p ON publicacoes_fts.rowid = p.rowid
    WHERE publicacoes_fts MATCH ?
    ORDER BY rank
    LIMIT ?
    """, (termo, limit))

    resultados = cursor.fetchall()
    print(f"🔍 Busca por: '{termo}'")
    print(f"Encontrados: {len(resultados)}")
    print("="*80)

    for i, row in enumerate(resultados, 1):
        print(f"\n{i}. {row['tribunal']} | {row['tipo_publicacao']}")
        print(f"   Processo: {row['numero_processo_fmt']}")
        print(f"   Data: {row['data_publicacao']}")
        print(f"   Ementa: {row['ementa_snippet']}")

    conn.close()

# Usar
buscar_por_termo('jurisprudencia.db', 'responsabilidade civil', limit=5)
```

**Saída esperada:**

```
🔍 Busca por: 'responsabilidade civil'
Encontrados: 12
================================================================================

1. STJ | Acórdão
   Processo: 0001234-56.2024.8.21.0000
   Data: 2025-11-20
   Ementa: DIREITO CIVIL. <mark>RESPONSABILIDADE CIVIL</mark>. Dano moral...
```

## 6. Executar Teste Completo com API Real

O projeto inclui script pronto para testar com dados reais:

```bash
# Com venv ativado
python test_processador_stj.py

# Resultado esperado (exemplo):
# ============================================================================
# VALIDAÇÃO DO PROCESSADOR DE TEXTO - STJ
# ============================================================================
#
# Baixando publicações do STJ (2025-11-13 a 2025-11-20)...
# Total obtido: 100 publicações
#
# Acórdãos encontrados: 17 (17.0% do total)
# Taxa de extração de ementa: 100.0% (esperado: ~90%)
# Taxa de extração de relator: 5.9%
#
# ✅ Taxa de extração de ementa APROVADA (>= 85%)
```

## 7. Script Completo de Exemplo

Crie um arquivo `exemplo_completo.py`:

```python
#!/usr/bin/env python3
"""Exemplo completo: Baixar, processar e inserir publicações."""

import sys
import sqlite3
import requests
from datetime import datetime, timedelta
from src.processador_texto import (
    processar_publicacao,
    validar_publicacao_processada
)

def main():
    print("🚀 EXEMPLO COMPLETO: Jurisprudência Collector")
    print("="*80)

    # 1. Baixar
    print("\n1️⃣  Baixando publicações do STJ...")
    url = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
    params = {
        'dataInicio': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
        'dataFim': datetime.now().strftime('%Y-%m-%d'),
        'siglaTribunal': 'STJ',
        'limit': 50
    }

    response = requests.get(url, params=params, timeout=30)
    items = response.json().get('items', [])
    print(f"   ✅ Obtidas {len(items)} publicações")

    # 2. Processar
    print("\n2️⃣  Processando publicações...")
    processadas = []
    for item in items:
        try:
            pub = processar_publicacao(item)
            if validar_publicacao_processada(pub):
                processadas.append(pub)
        except Exception as e:
            print(f"   ⚠️ Erro ao processar: {e}")
    print(f"   ✅ Processadas {len(processadas)} publicações válidas")

    # 3. Inserir
    print("\n3️⃣  Inserindo no banco...")
    conn = sqlite3.connect('jurisprudencia.db')
    cursor = conn.cursor()

    novas = 0
    duplicatas = 0

    for pub in processadas:
        try:
            cursor.execute("""
            INSERT OR IGNORE INTO publicacoes (
                id, hash_conteudo, numero_processo, numero_processo_fmt,
                tribunal, orgao_julgador, tipo_publicacao, classe_processual,
                texto_html, texto_limpo, ementa, data_publicacao, relator, fonte
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pub['id'], pub['hash_conteudo'], pub['numero_processo'],
                pub['numero_processo_fmt'], pub['tribunal'], pub['orgao_julgador'],
                pub['tipo_publicacao'], pub['classe_processual'],
                pub['texto_html'], pub['texto_limpo'], pub['ementa'],
                pub['data_publicacao'], pub['relator'], pub['fonte']
            ))

            if cursor.rowcount > 0:
                novas += 1
            else:
                duplicatas += 1
        except Exception as e:
            print(f"   ⚠️ Erro ao inserir: {e}")

    conn.commit()
    conn.close()
    print(f"   ✅ Novas: {novas}, Duplicatas: {duplicatas}")

    # 4. Resumo
    print("\n" + "="*80)
    print(f"✅ SUCESSO! Processadas {novas} publicações novas.")
    print("="*80)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ ERRO: {e}")
        sys.exit(1)
```

Execute com:

```bash
python exemplo_completo.py
```

---

**Próximo:** Veja `CONFIGURACAO.md` para customizações avançadas.

**Data de última atualização:** 2025-11-20
