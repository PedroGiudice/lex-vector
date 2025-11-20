#!/usr/bin/env python3
"""
Exemplo de uso do schema de jurisprudência.
Demonstra operações CRUD e busca textual.
"""

import sqlite3
import hashlib
import uuid
from datetime import datetime
from pathlib import Path

def criar_banco(db_path: Path):
    """Cria banco de dados aplicando schema."""
    schema_path = Path(__file__).parent / "schema.sql"
    schema_sql = schema_path.read_text(encoding='utf-8')

    conn = sqlite3.connect(str(db_path))
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()

    print(f"✅ Banco criado: {db_path}")


def inserir_publicacao_exemplo(db_path: Path):
    """Insere publicação de exemplo."""

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Dados de exemplo (simulando acórdão do STJ)
    texto_html = """
    <div class="publicacao">
        <p><strong>ACÓRDÃO</strong></p>
        <p>Processo: 1234567-89.2024.8.00.0000</p>
        <p>Relator: Min. JOÃO SILVA</p>
        <p><strong>EMENTA:</strong> DIREITO CIVIL. RESPONSABILIDADE CIVIL.
        DANO MORAL. CONFIGURAÇÃO. QUANTUM INDENIZATÓRIO. PROPORCIONALIDADE.
        1. A responsabilidade civil pressupõe a ocorrência de dano, nexo causal
        e conduta culposa ou dolosa. 2. O valor da indenização deve observar
        os princípios da razoabilidade e proporcionalidade. 3. Recurso provido.</p>
        <p>Decisão: Por unanimidade, dar provimento ao recurso.</p>
    </div>
    """

    texto_limpo = """
    ACÓRDÃO
    Processo: 1234567-89.2024.8.00.0000
    Relator: Min. JOÃO SILVA

    EMENTA: DIREITO CIVIL. RESPONSABILIDADE CIVIL. DANO MORAL. CONFIGURAÇÃO.
    QUANTUM INDENIZATÓRIO. PROPORCIONALIDADE.

    1. A responsabilidade civil pressupõe a ocorrência de dano, nexo causal
    e conduta culposa ou dolosa.
    2. O valor da indenização deve observar os princípios da razoabilidade
    e proporcionalidade.
    3. Recurso provido.

    Decisão: Por unanimidade, dar provimento ao recurso.
    """

    # Gerar UUID e hash
    pub_id = str(uuid.uuid4())
    hash_conteudo = hashlib.sha256(texto_limpo.encode()).hexdigest()

    # Inserir publicação
    cursor.execute("""
        INSERT INTO publicacoes (
            id, hash_conteudo, numero_processo, numero_processo_fmt,
            tribunal, orgao_julgador, tipo_publicacao, classe_processual,
            assuntos, texto_html, texto_limpo, ementa,
            data_publicacao, data_julgamento, relator, fonte
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        pub_id,
        hash_conteudo,
        "12345678920248000000",
        "1234567-89.2024.8.00.0000",
        "STJ",
        "3ª Turma",
        "Acórdão",
        "Apelação Cível",
        '["Direito Civil", "Responsabilidade Civil", "Dano Moral"]',
        texto_html,
        texto_limpo,
        "DIREITO CIVIL. RESPONSABILIDADE CIVIL. DANO MORAL...",
        "2025-11-20",
        "2025-11-15",
        "Min. JOÃO SILVA",
        "DJEN"
    ))

    # Associar tema
    cursor.execute("SELECT id FROM temas WHERE nome = 'Direito Civil'")
    tema_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO publicacoes_temas (publicacao_id, tema_id, relevancia)
        VALUES (?, ?, ?)
    """, (pub_id, tema_id, 0.95))

    conn.commit()
    conn.close()

    print(f"✅ Publicação inserida: {pub_id}")
    return pub_id


def buscar_fts(db_path: Path, query: str):
    """Busca usando FTS5."""

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.id,
            p.numero_processo_fmt,
            p.tribunal,
            p.tipo_publicacao,
            p.ementa,
            snippet(publicacoes_fts, 0, '<mark>', '</mark>', '...', 64) AS snippet,
            p.data_publicacao,
            rank
        FROM publicacoes_fts
        JOIN publicacoes p ON publicacoes_fts.rowid = p.rowid
        WHERE publicacoes_fts MATCH ?
        ORDER BY rank
        LIMIT 10
    """, (query,))

    resultados = cursor.fetchall()
    conn.close()

    print(f"\n🔍 Busca FTS: '{query}'")
    print("=" * 80)

    if not resultados:
        print("Nenhum resultado encontrado.")
        return

    for i, row in enumerate(resultados, 1):
        print(f"\n{i}. {row['tribunal']} - {row['tipo_publicacao']}")
        print(f"   Processo: {row['numero_processo_fmt']}")
        print(f"   Data: {row['data_publicacao']}")
        print(f"   Ementa: {row['ementa'][:100]}...")
        print(f"   Snippet: {row['snippet'][:150]}...")


def exibir_estatisticas(db_path: Path):
    """Exibe estatísticas do banco."""

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Stats gerais
    cursor.execute("SELECT * FROM v_stats")
    stats = cursor.fetchone()

    print("\n📊 ESTATÍSTICAS GERAIS")
    print("=" * 80)
    print(f"Total de publicações:    {stats['total_publicacoes']:,}")
    print(f"Tribunais únicos:        {stats['tribunais_unicos']}")
    print(f"Processos únicos:        {stats['processos_unicos']}")
    print(f"Data mais antiga:        {stats['data_mais_antiga']}")
    print(f"Data mais recente:       {stats['data_mais_recente']}")
    print(f"Total de acórdãos:       {stats['total_acordaos']:,}")
    print(f"Total de sentenças:      {stats['total_sentencas']:,}")
    print(f"Total de decisões:       {stats['total_decisoes']:,}")
    print(f"Tamanho médio do texto:  {stats['tamanho_medio_texto']:,} chars")

    # Distribuição por tribunal
    cursor.execute("SELECT * FROM v_publicacoes_por_tribunal")
    tribunais = cursor.fetchall()

    print("\n📋 PUBLICAÇÕES POR TRIBUNAL")
    print("=" * 80)
    print(f"{'Tribunal':<10} {'Total':>8} {'Acórdãos':>10} {'Sentenças':>10} {'Decisões':>10}")
    print("-" * 80)

    for trib in tribunais:
        print(f"{trib['tribunal']:<10} {trib['total']:>8,} "
              f"{trib['acordaos']:>10,} {trib['sentencas']:>10,} {trib['decisoes']:>10,}")

    # Temas
    cursor.execute("SELECT * FROM v_temas_ranking LIMIT 10")
    temas = cursor.fetchall()

    print("\n🏷️  TOP 10 TEMAS")
    print("=" * 80)
    print(f"{'Tema':<30} {'Publicações':>12} {'Relevância Média':>18}")
    print("-" * 80)

    for tema in temas:
        relevancia = tema['relevancia_media'] if tema['relevancia_media'] is not None else 0.0
        print(f"{tema['nome']:<30} {tema['total_publicacoes']:>12,} "
              f"{relevancia:>18.2f}")

    conn.close()


def exemplo_completo():
    """Executa exemplo completo de uso."""

    db_path = Path(__file__).parent / "jurisprudencia_exemplo.db"

    # Remover banco antigo se existir
    if db_path.exists():
        db_path.unlink()

    print("=" * 80)
    print("EXEMPLO DE USO DO SCHEMA DE JURISPRUDÊNCIA")
    print("=" * 80)

    # 1. Criar banco
    print("\n1️⃣  Criando banco de dados...")
    criar_banco(db_path)

    # 2. Inserir publicação
    print("\n2️⃣  Inserindo publicação de exemplo...")
    pub_id = inserir_publicacao_exemplo(db_path)

    # 3. Buscar por FTS
    print("\n3️⃣  Testando busca FTS5...")
    buscar_fts(db_path, "responsabilidade civil")

    # 4. Exibir estatísticas
    print("\n4️⃣  Exibindo estatísticas...")
    exibir_estatisticas(db_path)

    print("\n" + "=" * 80)
    print(f"✅ Banco de exemplo criado: {db_path}")
    print(f"📊 Tamanho do arquivo: {db_path.stat().st_size / 1024:.1f} KB")
    print("=" * 80)


if __name__ == "__main__":
    exemplo_completo()
