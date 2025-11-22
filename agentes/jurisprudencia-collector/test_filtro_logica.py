#!/usr/bin/env python3
"""
Teste focado na LÓGICA do filtro (sem depender de API/data).

Cria publicações mock com tipos variados e testa se o filtro funciona corretamente.
"""

import sys
from pathlib import Path
from datetime import datetime
import logging
import sqlite3

# Adicionar src/ ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scheduler import processar_publicacoes, normalizar_tipo_publicacao
from downloader import PublicacaoRaw

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def criar_publicacao_mock(tipo: str, numero: int) -> PublicacaoRaw:
    """Cria publicação mock para teste."""
    import hashlib

    # Criar texto HTML que será reconhecido pela classificação
    if tipo == 'Acórdão':
        texto_html = f"""
        <p><strong>EMENTA:</strong> Teste de ementa do acórdão {numero}.</p>
        <p><strong>ACÓRDÃO:</strong> Por unanimidade, a Turma decidiu...</p>
        <p><strong>VOTO:</strong> O relator votou...</p>
        """
    elif tipo == 'Sentença':
        texto_html = f"""
        <p><strong>SENTENÇA</strong></p>
        <p>Sentença proferida pelo juiz {numero}.</p>
        <p>Julgo procedente o pedido...</p>
        """
    elif tipo == 'Decisão':
        texto_html = f"""
        <p><strong>DECISÃO MONOCRÁTICA</strong></p>
        <p>Decisão do relator {numero}.</p>
        <p>Indefiro o pedido...</p>
        """
    else:  # Intimação
        texto_html = f"""
        <p><strong>INTIMAÇÃO</strong></p>
        <p>Fica a parte intimada {numero}.</p>
        """

    conteudo = f'{tipo}-{numero}-{texto_html}'
    hash_conteudo = hashlib.sha256(conteudo.encode()).hexdigest()

    return PublicacaoRaw(
        id=f'mock-{tipo.lower()}-{numero}',
        hash_conteudo=hash_conteudo,
        numero_processo=f'1234567-89.2025.8.00.{numero:04d}',
        numero_processo_fmt=f'1234567-89.2025.8.00.{numero:04d}',
        tribunal='STJ',
        orgao_julgador=f'Turma {numero}',
        tipo_comunicacao='Edital',  # Forçar classificação por texto, não por tipo_comunicacao
        classe_processual='REsp',
        texto_html=texto_html,
        data_publicacao='2025-11-21',
        destinatario_advogados=[],
        metadata={'teste': True}
    )


def criar_banco_temporario() -> sqlite3.Connection:
    """Cria banco SQLite em memória para teste."""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Criar tabela publicacoes
    cursor.execute("""
        CREATE TABLE publicacoes (
            id                  TEXT PRIMARY KEY,
            hash_conteudo       TEXT NOT NULL UNIQUE,
            numero_processo     TEXT,
            numero_processo_fmt TEXT,
            tribunal            TEXT NOT NULL,
            orgao_julgador      TEXT,
            tipo_publicacao     TEXT NOT NULL,
            classe_processual   TEXT,
            assuntos            TEXT,
            texto_html          TEXT NOT NULL,
            texto_limpo         TEXT NOT NULL,
            ementa              TEXT,
            data_publicacao     TEXT NOT NULL,
            data_julgamento     TEXT,
            relator             TEXT,
            fonte               TEXT NOT NULL
        )
    """)

    conn.commit()
    logger.info("✅ Banco temporário criado")
    return conn


def test_filtro_logica():
    """
    Testa lógica do filtro com publicações mock.

    Cenário:
    - 20 Acórdãos
    - 30 Sentenças
    - 25 Decisões
    - 25 Intimações

    Total: 100 publicações

    Filtro ativado para apenas Acórdãos:
    - Esperado: 20 novas, 80 filtradas
    """
    logger.info("=" * 80)
    logger.info("TESTE DE LÓGICA DO FILTRO (Publicações Mock)")
    logger.info("=" * 80)

    # Criar publicações mock
    publicacoes_mock = []

    # 20 Acórdãos
    for i in range(1, 21):
        publicacoes_mock.append(criar_publicacao_mock('Acórdão', i))

    # 30 Sentenças
    for i in range(1, 31):
        publicacoes_mock.append(criar_publicacao_mock('Sentença', i))

    # 25 Decisões
    for i in range(1, 26):
        publicacoes_mock.append(criar_publicacao_mock('Decisão', i))

    # 25 Intimações
    for i in range(1, 26):
        publicacoes_mock.append(criar_publicacao_mock('Intimação', i))

    logger.info(f"📦 Criadas {len(publicacoes_mock)} publicações mock:")
    logger.info(f"   - 20 Acórdãos")
    logger.info(f"   - 30 Sentenças")
    logger.info(f"   - 25 Decisões")
    logger.info(f"   - 25 Intimações")

    # Criar banco temporário
    conn = criar_banco_temporario()

    # Testar COM filtro (apenas Acórdãos)
    logger.info("\n🔍 Testando filtro: apenas Acórdãos")
    stats = processar_publicacoes(
        conn=conn,
        publicacoes=publicacoes_mock,
        tribunal='STJ',
        tipos_desejados=['Acórdão']
    )

    logger.info(f"\n📊 Resultados:")
    logger.info(f"   Total processadas: {stats['total']}")
    logger.info(f"   Novas (Acórdãos): {stats['novas']}")
    logger.info(f"   Filtradas (outros tipos): {stats['filtrados']}")
    logger.info(f"   Duplicadas: {stats['duplicadas']}")
    logger.info(f"   Erros: {stats['erros']}")

    # Validações
    sucesso = True

    if stats['total'] != 100:
        logger.error(f"❌ Total esperado: 100, obtido: {stats['total']}")
        sucesso = False

    if stats['novas'] != 20:
        logger.error(f"❌ Novas esperado: 20 (Acórdãos), obtido: {stats['novas']}")
        sucesso = False

    if stats['filtrados'] != 80:
        logger.error(f"❌ Filtrados esperado: 80 (Sentenças+Decisões+Intimações), obtido: {stats['filtrados']}")
        sucesso = False

    if stats['duplicadas'] != 0:
        logger.error(f"❌ Duplicadas esperado: 0, obtido: {stats['duplicadas']}")
        sucesso = False

    if stats['erros'] != 0:
        logger.error(f"❌ Erros esperado: 0, obtido: {stats['erros']}")
        sucesso = False

    # Verificar banco de dados
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), tipo_publicacao FROM publicacoes GROUP BY tipo_publicacao")
    tipos_salvos = cursor.fetchall()

    logger.info(f"\n💾 Verificação do banco:")
    for count, tipo in tipos_salvos:
        logger.info(f"   {tipo}: {count} registros")

    if len(tipos_salvos) != 1 or tipos_salvos[0][1] != 'Acórdão' or tipos_salvos[0][0] != 20:
        logger.error(f"❌ Banco deveria ter apenas 20 Acórdãos, encontrado: {tipos_salvos}")
        sucesso = False

    conn.close()

    # Resultado final
    logger.info("\n" + "=" * 80)
    if sucesso:
        logger.info("✅ TESTE PASSOU! Filtro funcionando corretamente.")
        logger.info("=" * 80)
        return 0
    else:
        logger.error("❌ TESTE FALHOU! Verifique os logs acima.")
        logger.error("=" * 80)
        return 1


def test_filtro_multiplos_tipos():
    """
    Testa filtro com múltiplos tipos desejados.

    Cenário:
    - Filtrar Acórdãos E Sentenças
    - Bloquear Decisões E Intimações
    """
    logger.info("\n" + "=" * 80)
    logger.info("TESTE DE FILTRO COM MÚLTIPLOS TIPOS")
    logger.info("=" * 80)

    # Criar publicações mock
    publicacoes_mock = []

    for i in range(1, 11):
        publicacoes_mock.append(criar_publicacao_mock('Acórdão', i))

    for i in range(1, 11):
        publicacoes_mock.append(criar_publicacao_mock('Sentença', i))

    for i in range(1, 11):
        publicacoes_mock.append(criar_publicacao_mock('Decisão', i))

    for i in range(1, 11):
        publicacoes_mock.append(criar_publicacao_mock('Intimação', i))

    logger.info(f"📦 Criadas {len(publicacoes_mock)} publicações mock (10 de cada tipo)")

    # Criar banco temporário
    conn = criar_banco_temporario()

    # Testar COM filtro (Acórdãos E Sentenças)
    logger.info("\n🔍 Testando filtro: Acórdãos E Sentenças")
    stats = processar_publicacoes(
        conn=conn,
        publicacoes=publicacoes_mock,
        tribunal='STJ',
        tipos_desejados=['Acórdão', 'Sentença']
    )

    logger.info(f"\n📊 Resultados:")
    logger.info(f"   Novas: {stats['novas']} (esperado: 20)")
    logger.info(f"   Filtradas: {stats['filtrados']} (esperado: 20)")

    sucesso = (stats['novas'] == 20 and stats['filtrados'] == 20)

    conn.close()

    if sucesso:
        logger.info("\n✅ TESTE PASSOU! Filtro múltiplo funcionando.")
        return 0
    else:
        logger.error("\n❌ TESTE FALHOU! Filtro múltiplo com erro.")
        return 1


def main():
    """Executa todos os testes de lógica."""
    logger.info("🧪 INICIANDO TESTES DE LÓGICA DO FILTRO")
    logger.info("")

    # Teste 1: Filtro simples (apenas Acórdãos)
    resultado1 = test_filtro_logica()

    # Teste 2: Filtro múltiplo (Acórdãos + Sentenças)
    resultado2 = test_filtro_multiplos_tipos()

    # Resultado final
    if resultado1 == 0 and resultado2 == 0:
        logger.info("\n" + "=" * 80)
        logger.info("🎉 TODOS OS TESTES PASSARAM!")
        logger.info("=" * 80)
        return 0
    else:
        logger.error("\n" + "=" * 80)
        logger.error("❌ ALGUNS TESTES FALHARAM")
        logger.error("=" * 80)
        return 1


if __name__ == '__main__':
    sys.exit(main())
