# Sistema de Memória Episódica

Sistema de memória contextual para agentes LLM baseado em SQLite + embeddings opcionais.

**Data de Criação**: 2025-11-13
**Status**: ✅ Implementado e testado
**Integração**: Legal-Braniac via hooks

---

## Visão Geral

O sistema de memória episódica permite que agentes LLM armazenem e recuperem conhecimento de sessões anteriores:

- **Decisões arquiteturais** (ex: separação 3 camadas)
- **Bugs resolvidos** (ex: API DJEN filtro OAB)
- **Soluções de problemas** (ex: hooks Windows CLI)
- **Workarounds de APIs** (ex: paginação DJEN)
- **Contextos de projetos**
- **Lições aprendidas**

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│ Claude Code (SessionStart/UserPromptSubmit hooks)          │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ memory-integration.js (Node.js bridge)                      │
│   - Recupera memórias via Python CLI                        │
│   - Injeta contexto no SystemMessage                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ episodic_memory.py (Python backend)                         │
│   - SQLite: metadata, tags, TTL                             │
│   - Embeddings: sentence-transformers (opcional)            │
│   - Busca: tags, tipo, similaridade semântica               │
└─────────────────────────────────────────────────────────────┘
```

---

## Instalação

### 1. Dependências Básicas (Obrigatórias)

```bash
# Já incluído no Python 3.x padrão
# - sqlite3
# - json, logging, pathlib, datetime
```

### 2. Busca Semântica (Opcional)

```bash
pip install sentence-transformers
```

**Recomendação**: Usar em ambiente com GPU para performance. CPU é aceitável, mas lento.

**Tamanho do modelo**: ~90 MB (all-MiniLM-L6-v2)

---

## Uso Básico

### CLI do Sistema de Memória

#### 1. Armazenar Memória

```bash
python3 shared/memory/episodic_memory.py \
  --memory-dir shared/memory/data \
  --action store \
  --type bug_resolution \
  --title "API DJEN filtro OAB não funciona" \
  --content "Bug: parâmetro numeroOab é completamente ignorado pela API. Workaround: buscar todos os resultados e filtrar localmente via campo destinatarioadvogados." \
  --tags DJEN API bug workaround
```

**Tipos disponíveis**:
- `architectural_decision`
- `bug_resolution`
- `solution_pattern`
- `project_context`
- `lesson_learned`
- `api_workaround`
- `orchestration`

#### 2. Recuperar Memórias

**Busca por tags**:
```bash
python3 shared/memory/episodic_memory.py \
  --memory-dir shared/memory/data \
  --action recall \
  --tags DJEN API \
  --limit 10
```

**Busca por tipo**:
```bash
python3 shared/memory/episodic_memory.py \
  --memory-dir shared/memory/data \
  --action recall \
  --type bug_resolution \
  --limit 5
```

**Busca semântica** (requer embeddings):
```bash
python3 shared/memory/episodic_memory.py \
  --memory-dir shared/memory/data \
  --action recall \
  --query "Como resolver problemas com API do DJEN?" \
  --limit 5
```

#### 3. Estatísticas

```bash
python3 shared/memory/episodic_memory.py \
  --memory-dir shared/memory/data \
  --action stats
```

**Output**:
```
📊 Estatísticas de Memória:

Total de memórias: 12
Tipos diferentes: 4
Acessos totais: 47
Relevância média: 0.73
Embeddings: ✅ Ativados

Por tipo:
  - bug_resolution: 5
  - api_workaround: 3
  - architectural_decision: 2
  - solution_pattern: 2

Top tags:
  - DJEN: 8
  - API: 6
  - hooks: 3
  - windows: 3
```

#### 4. Exportar Memórias

```bash
python3 shared/memory/episodic_memory.py \
  --memory-dir shared/memory/data \
  --action export \
  --output memories_backup.json
```

---

## Integração com Claude Code

### Configuração em `.claude/settings.json`

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node .claude/hooks/memory-integration.js"
          }
        ]
      }
    ]
  }
}
```

**Comportamento**:
1. Na primeira prompt da sessão, o hook executa
2. Recupera memórias relevantes (tags: DJEN, API, hooks, windows, arquitetura)
3. Injeta contexto no SystemMessage
4. Fornece instruções de uso

**Run-Once Guard**: Hook executa apenas 1x por sessão (via env var `CLAUDE_MEMORY_INTEGRATION_LOADED`)

---

## Uso Programático (Python)

```python
from pathlib import Path
from shared.memory.episodic_memory import EpisodicMemory, MemoryUnit, MemoryType

# Inicializar sistema
memory = EpisodicMemory(
    memory_dir=Path('./shared/memory/data'),
    enable_embeddings=True,  # Busca semântica
    default_ttl_days=None    # Sem expiração
)

# Armazenar memória
memory.store(MemoryUnit(
    type=MemoryType.BUG_RESOLUTION.value,
    title="API DJEN filtro OAB não funciona",
    content="Workaround: buscar todos + filtrar localmente",
    tags=["DJEN", "API", "bug", "workaround"],
    context={"project": "Legal-Braniac", "agent": "djen-tracker"}
))

# Recuperar memórias
results = memory.recall(
    tags=["DJEN", "API"],
    limit=10
)

for mem in results:
    print(f"{mem.title} - {mem.relevance_score:.2f}")

# Busca semântica
results = memory.recall_by_semantic_similarity(
    query="Como resolver problemas com API do DJEN?",
    limit=5
)

for mem, score in results:
    print(f"{mem.title} - Similaridade: {score:.3f}")

# Estatísticas
stats = memory.get_stats()
print(f"Total: {stats['total_memories']} memórias")
```

---

## Boas Práticas

### Quando Armazenar Memórias

**✅ Armazene:**
- Bugs críticos resolvidos (especialmente workarounds)
- Decisões arquiteturais importantes
- Padrões de solução bem-sucedidos
- APIs com comportamento não documentado
- Lições aprendidas de desastres (ex: DISASTER_HISTORY.md)

**❌ Não armazene:**
- Informações triviais ou temporárias
- Dados sensíveis (senhas, tokens)
- Contexto que muda frequentemente (ex: "última task executada")

### Tags Efetivas

**Boas tags**:
```python
tags=["DJEN", "API", "bug", "workaround", "pagination"]
```

**Tags ruins**:
```python
tags=["problema", "coisa", "importante"]  # Muito genéricas
```

**Convenções**:
- Nomes técnicos em maiúsculas: `DJEN`, `API`, `CLI`
- Categorias em minúsculas: `bug`, `workaround`, `hooks`
- Plataformas em minúsculas: `windows`, `linux`, `web`

### Títulos Descritivos

**Bom**:
```
"API DJEN filtro OAB não funciona (parâmetro ignorado)"
```

**Ruim**:
```
"Bug na API"
```

### Conteúdo Acionável

**Bom**:
```
Bug: parâmetro numeroOab é completamente ignorado pela API.

Workaround:
1. Buscar todos os resultados (sem filtro)
2. Filtrar localmente via campo destinatarioadvogados
3. Usar regex: /numeroOab:\s*(\d{4,7})/

Referência: agentes/djen-tracker/src/publicacoes_api.py:156
```

**Ruim**:
```
"A API tem um bug com OAB."
```

---

## Manutenção

### Cleanup de Memórias Expiradas

```bash
# Via Python
python3 -c "from pathlib import Path; \
from shared.memory.episodic_memory import EpisodicMemory; \
memory = EpisodicMemory(Path('shared/memory/data')); \
deleted = memory.cleanup_expired(); \
print(f'{deleted} memórias expiradas removidas')"
```

### Backup de Memórias

```bash
# Exportar para JSON
python3 shared/memory/episodic_memory.py \
  --memory-dir shared/memory/data \
  --action export \
  --output backups/memories_$(date +%Y%m%d).json

# Backup do banco SQLite
cp shared/memory/data/episodic_memory.db \
   backups/episodic_memory_$(date +%Y%m%d).db
```

### Reconstruir Embeddings

Se você instalar `sentence-transformers` depois de já ter memórias armazenadas:

```python
from pathlib import Path
from shared.memory.episodic_memory import EpisodicMemory

# Abrir memória SEM embeddings
old_memory = EpisodicMemory(Path('./shared/memory/data'), enable_embeddings=False)

# Exportar memórias
memories = old_memory.recall(limit=999999)

# Recriar memória COM embeddings
new_memory = EpisodicMemory(Path('./shared/memory/data_new'), enable_embeddings=True)

# Re-armazenar com embeddings
for mem in memories:
    new_memory.store(mem)

# Substituir banco
# mv shared/memory/data shared/memory/data_old
# mv shared/memory/data_new shared/memory/data
```

---

## Troubleshooting

### "sentence-transformers não instalado"

**Sintoma**: Warning ao habilitar embeddings

**Solução**:
```bash
pip install sentence-transformers
```

**Alternativa**: Usar sem embeddings (busca por tags/tipo funciona normalmente)

### "numpy não instalado"

**Sintoma**: Erro na busca semântica

**Solução**:
```bash
pip install numpy
```

Nota: `sentence-transformers` já depende de numpy, então normalmente não ocorre.

### Hook não executa

**Sintoma**: Memórias não aparecem no SystemMessage

**Diagnóstico**:
```bash
# Testar hook manualmente
node .claude/hooks/memory-integration.js

# Verificar se Python backend funciona
python3 shared/memory/episodic_memory.py \
  --memory-dir shared/memory/data \
  --action stats
```

**Causas comuns**:
- Run-once guard já executou (env var `CLAUDE_MEMORY_INTEGRATION_LOADED='true'`)
- Banco de memórias vazio (sem memórias para recuperar)
- Timeout no Python subprocess (hook tem timeout de 5s)

### Performance lenta

**Sintoma**: Hook demora >5s para executar

**Causa**: Busca semântica em CPU sem otimização

**Soluções**:
1. Desabilitar embeddings no hook (usar apenas tags)
2. Reduzir `limit` de memórias recuperadas
3. Usar GPU para embeddings (se disponível)
4. Cache de embeddings (já implementado)

---

## Exemplos de Memórias do Projeto

### Bugs Resolvidos

```bash
python3 shared/memory/episodic_memory.py \
  --memory-dir shared/memory/data \
  --action store \
  --type bug_resolution \
  --title "DJEN API: numeroOab completamente ignorado" \
  --content "Bug crítico: parâmetro numeroOab é ignorado pela API. Workaround: buscar todos os resultados e filtrar localmente via destinatarioadvogados. Referência: agentes/djen-tracker/src/publicacoes_api.py" \
  --tags DJEN API bug workaround numeroOab
```

### Decisões Arquiteturais

```bash
python3 shared/memory/episodic_memory.py \
  --memory-dir shared/memory/data \
  --action store \
  --type architectural_decision \
  --title "Separação 3 camadas: Code/Environment/Data" \
  --content "Decisão crítica pós-desastre: código em C:/repos (Git), ambiente em .venv (não-Git), dados em E:/ (externo). NUNCA misturar. Ver DISASTER_HISTORY.md para contexto." \
  --tags arquitetura disaster windows separacao-camadas
```

### Workarounds de API

```bash
python3 shared/memory/episodic_memory.py \
  --memory-dir shared/memory/data \
  --action store \
  --type api_workaround \
  --title "DJEN API: Limite de 100 itens por request" \
  --content "Limitação: API retorna máximo 100 itens por request. Solução: usar paginação com offset. Exemplo: ?offset=0&limit=100, depois ?offset=100&limit=100. Implementado em agentes/djen-tracker/src/publicacoes_api.py:fetch_all_pages()" \
  --tags DJEN API pagination limit workaround
```

### Padrões de Solução

```bash
python3 shared/memory/episodic_memory.py \
  --memory-dir shared/memory/data \
  --action store \
  --type solution_pattern \
  --title "Windows CLI: SessionStart hooks freeze" \
  --content "Problema: SessionStart hooks executam antes do event loop, causando freeze no Windows. Solução: migrar para UserPromptSubmit com run-once guard via env var. Baseado em cc-toolkit commit 09ab8674. Implementação: .claude/hooks/*-hybrid.js" \
  --tags windows CLI hooks workaround sessionstart userpromptsubmit
```

---

## Roadmap

### Implementado ✅
- [x] Backend Python com SQLite
- [x] Embeddings opcionais (sentence-transformers)
- [x] Busca por tags, tipo, semântica
- [x] TTL e cleanup de memórias
- [x] Export/import JSON
- [x] CLI completo
- [x] Testes unitários
- [x] Hook de integração com Claude Code
- [x] Run-once guard para UserPromptSubmit

### Próximos Passos 🔄
- [ ] Auto-armazenamento de memórias pelo Legal-Braniac
- [ ] Recall automático baseado em contexto da task
- [ ] Scoring de relevância automático (ML)
- [ ] Integração com Legal-Braniac orchestration decisions
- [ ] UI web para visualização de memórias (opcional)

---

## Referências

- **Implementação**: `shared/memory/episodic_memory.py` (800+ linhas)
- **Testes**: `shared/memory/test_episodic_memory.py`
- **Hook**: `.claude/hooks/memory-integration.js`
- **Inspiração**:
  - [MemOrb](https://github.com/MemOrb/memorb) - SQLite + ChromaDB
  - [Memori](https://github.com/Memori/memori) - Open-source memory engine
  - [cc-toolkit](https://github.com/DennisLiuCk/cc-toolkit) - Claude Code hooks patterns

---

**Última atualização**: 2025-11-13
**Autor**: Legal-Braniac Orchestrator
**Status**: ✅ Production-ready
