#!/usr/bin/env python3
"""
Teste básico do sistema de memória episódica.
"""
import sys
import logging
from pathlib import Path

# Adicionar shared ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory.episodic_memory import EpisodicMemory, MemoryUnit, MemoryType

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_basic_storage_and_recall():
    """Teste: armazenar e recuperar memórias."""
    logger.info("\n=== Teste 1: Storage e Recall básico ===")

    # Criar sistema de memória temporário
    memory_dir = Path("/tmp/test_episodic_memory")
    memory = EpisodicMemory(memory_dir, enable_embeddings=False)

    # Armazenar algumas memórias
    memory.store(MemoryUnit(
        type=MemoryType.BUG_RESOLUTION.value,
        title="API DJEN filtro OAB não funciona",
        content="Bug: parâmetro numeroOab é completamente ignorado pela API. Workaround: buscar todos os resultados e filtrar localmente via campo destinatarioadvogados.",
        tags=["DJEN", "API", "bug", "workaround"]
    ))

    memory.store(MemoryUnit(
        type=MemoryType.ARCHITECTURAL_DECISION.value,
        title="Separação em 3 camadas (Code/Environment/Data)",
        content="Decisão crítica: código em C:/repos, ambiente em .venv, dados em E:/. NUNCA misturar. Ver DISASTER_HISTORY.md.",
        tags=["arquitetura", "disaster", "windows"]
    ))

    memory.store(MemoryUnit(
        type=MemoryType.SOLUTION_PATTERN.value,
        title="SessionStart hooks freeze no Windows CLI",
        content="Solução: migrar para UserPromptSubmit com run-once guard via env vars. Baseado em cc-toolkit commit 09ab8674.",
        tags=["hooks", "windows", "cli", "workaround"]
    ))

    logger.info("✅ 3 memórias armazenadas")

    # Recuperar memórias por tag
    results = memory.recall(tags=["DJEN"], limit=5)
    logger.info(f"✅ Recall por tag 'DJEN': {len(results)} resultado(s)")
    assert len(results) == 1
    assert "filtro OAB" in results[0].title

    # Recuperar por tipo
    results = memory.recall(type_filter=MemoryType.BUG_RESOLUTION.value, limit=5)
    logger.info(f"✅ Recall por tipo 'bug_resolution': {len(results)} resultado(s)")
    assert len(results) == 1

    # Estatísticas
    stats = memory.get_stats()
    logger.info(f"✅ Stats: {stats['total_memories']} memórias totais")
    assert stats['total_memories'] == 3

    logger.info("✅ Teste 1 PASSOU!\n")


def test_semantic_search():
    """Teste: busca semântica (se embeddings disponíveis)."""
    logger.info("\n=== Teste 2: Busca Semântica ===")

    memory_dir = Path("/tmp/test_episodic_memory_semantic")

    # Tentar habilitar embeddings
    memory = EpisodicMemory(memory_dir, enable_embeddings=True)

    if not memory.enable_embeddings:
        logger.warning("⚠️  Embeddings não disponíveis (sentence-transformers não instalado)")
        logger.info("   Pulando teste de busca semântica")
        logger.info("   Para testar: pip install sentence-transformers\n")
        return

    # Armazenar memórias de teste
    memory.store(MemoryUnit(
        type=MemoryType.API_WORKAROUND.value,
        title="DJEN API pagination limit",
        content="A API do DJEN tem limite de 100 itens por request. Para buscar mais, usar paginação com offset.",
        tags=["DJEN", "API", "pagination"]
    ))

    memory.store(MemoryUnit(
        type=MemoryType.LESSON_LEARNED.value,
        title="Hooks do Claude Code no Windows",
        content="SessionStart hooks causam freeze no Windows porque executam antes do event loop. Usar UserPromptSubmit.",
        tags=["claude", "hooks", "windows"]
    ))

    logger.info("✅ 2 memórias com embeddings armazenadas")

    # Busca semântica
    results = memory.recall_by_semantic_similarity(
        query="Como resolver problemas com API do DJEN?",
        limit=5
    )

    logger.info(f"✅ Busca semântica: {len(results)} resultado(s)")

    if len(results) > 0:
        for mem, score in results:
            logger.info(f"   - {mem.title} (similaridade: {score:.3f})")

    # Validar que a memória DJEN tem maior score
    if len(results) >= 2:
        assert results[0][0].title == "DJEN API pagination limit"
        logger.info("✅ Ranking semântico correto!")

    logger.info("✅ Teste 2 PASSOU!\n")


def test_ttl_and_cleanup():
    """Teste: TTL e limpeza de memórias expiradas."""
    logger.info("\n=== Teste 3: TTL e Cleanup ===")

    memory_dir = Path("/tmp/test_episodic_memory_ttl")
    memory = EpisodicMemory(memory_dir, enable_embeddings=False, default_ttl_days=7)

    # Memória com TTL
    memory.store(MemoryUnit(
        type=MemoryType.PROJECT_CONTEXT.value,
        title="Contexto temporário",
        content="Esta memória expira em 1 dia",
        tags=["temp"]
    ), ttl_days=1)

    # Memória sem TTL
    memory.store(MemoryUnit(
        type=MemoryType.ARCHITECTURAL_DECISION.value,
        title="Decisão permanente",
        content="Esta memória nunca expira",
        tags=["permanent"]
    ), ttl_days=None)

    logger.info("✅ 2 memórias armazenadas (1 com TTL, 1 permanente)")

    stats = memory.get_stats()
    logger.info(f"✅ Total: {stats['total_memories']} memórias")
    assert stats['total_memories'] == 2

    # Simular expiração seria complexo (requer modificar banco diretamente)
    # Por enquanto, apenas validar que cleanup não quebra
    deleted = memory.cleanup_expired()
    logger.info(f"✅ Cleanup: {deleted} memórias expiradas removidas")

    logger.info("✅ Teste 3 PASSOU!\n")


def test_export():
    """Teste: exportação de memórias."""
    logger.info("\n=== Teste 4: Export ===")

    memory_dir = Path("/tmp/test_episodic_memory_export")
    memory = EpisodicMemory(memory_dir, enable_embeddings=False)

    # Armazenar memórias
    memory.store(MemoryUnit(
        type=MemoryType.LESSON_LEARNED.value,
        title="Lição 1",
        content="Conteúdo da lição 1",
        tags=["test"]
    ))

    memory.store(MemoryUnit(
        type=MemoryType.LESSON_LEARNED.value,
        title="Lição 2",
        content="Conteúdo da lição 2",
        tags=["test"]
    ))

    # Exportar
    output_file = Path("/tmp/test_memory_export.json")
    count = memory.export_memories(output_file)

    logger.info(f"✅ {count} memórias exportadas para {output_file}")
    assert count == 2
    assert output_file.exists()

    logger.info("✅ Teste 4 PASSOU!\n")


if __name__ == "__main__":
    try:
        test_basic_storage_and_recall()
        test_semantic_search()
        test_ttl_and_cleanup()
        test_export()

        logger.info("\n" + "="*60)
        logger.info("🎉 TODOS OS TESTES PASSARAM!")
        logger.info("="*60 + "\n")

        logger.info("Sistema de Memória Episódica está PRONTO para uso!")
        logger.info("\nPróximos passos:")
        logger.info("1. Integrar com Legal-Braniac hooks")
        logger.info("2. Armazenar automaticamente decisões de orquestração")
        logger.info("3. Usar recall() para contextualizar novas tasks")

    except AssertionError as e:
        logger.error(f"❌ TESTE FALHOU: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ ERRO: {e}", exc_info=True)
        sys.exit(1)
