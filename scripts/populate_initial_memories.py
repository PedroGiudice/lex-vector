#!/usr/bin/env python3
"""
populate_initial_memories.py - Popula memórias iniciais do projeto

Armazena conhecimento crítico das sessões anteriores:
- Bugs do DJEN API
- Solução hooks Windows
- Decisões arquiteturais
- Workarounds descobertos
"""
import sys
from pathlib import Path

# Adicionar shared ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.memory.episodic_memory import EpisodicMemory, MemoryUnit, MemoryType

def main():
    # Inicializar sistema de memória
    memory_dir = project_root / 'shared' / 'memory' / 'data'
    memory = EpisodicMemory(memory_dir, enable_embeddings=False)

    print("📋 Populando memórias iniciais do projeto...\n")

    # ========================================================================
    # BUGS RESOLVIDOS
    # ========================================================================

    print("1. Bug: API DJEN filtro numeroOab ignorado")
    memory.store(MemoryUnit(
        type=MemoryType.BUG_RESOLUTION.value,
        title="DJEN API: numeroOab completamente ignorado",
        content="""Bug crítico descoberto em 2025-11-13:

**Problema**: Parâmetro numeroOab é completamente ignorado pela API do DJEN.

**Evidência**:
- Request: /api/v1/publicacoes?numeroOab=123456
- Response: Retorna TODAS as publicações, não filtradas por OAB

**Workaround**:
1. Buscar TODOS os resultados (sem filtro numeroOab)
2. Filtrar localmente via campo destinatarioadvogados
3. Usar regex para extrair OAB: /numeroOab:\\s*(\\d{4,7})/

**Implementação**: agentes/djen-tracker/src/publicacoes_api.py

**Impacto**: Filtragem local consome mais memória, mas é única solução funcional.

**Referência**: AUDITORIA_API_DJEN_2025-11-13.md (769 linhas)
""",
        tags=["DJEN", "API", "bug", "workaround", "numeroOab", "critico"],
        context={"discovered_date": "2025-11-13", "severity": "critical"}
    ))

    print("2. Bug: API DJEN limite de paginação 100 itens")
    memory.store(MemoryUnit(
        type=MemoryType.API_WORKAROUND.value,
        title="DJEN API: Limite de 100 itens por request",
        content="""Limitação da API DJEN descoberta em 2025-11-13:

**Problema**: API retorna máximo 100 itens por request, independente do parâmetro limit.

**Evidência**:
- Request: /api/v1/publicacoes?limit=1000
- Response: Retorna apenas 100 itens

**Solução**: Paginação incremental com offset

**Implementação**:
```python
def fetch_all_pages(params):
    offset = 0
    limit = 100
    all_results = []

    while True:
        params_page = {**params, 'offset': offset, 'limit': limit}
        response = api.get('/publicacoes', params=params_page)

        if not response or len(response) < limit:
            break

        all_results.extend(response)
        offset += limit

    return all_results
```

**Referência**: agentes/djen-tracker/src/publicacoes_api.py:fetch_all_pages()
""",
        tags=["DJEN", "API", "pagination", "limit", "workaround"],
        context={"discovered_date": "2025-11-13", "max_items": 100}
    ))

    # ========================================================================
    # SOLUÇÕES DE PROBLEMAS
    # ========================================================================

    print("3. Solução: Windows CLI hooks freeze")
    memory.store(MemoryUnit(
        type=MemoryType.SOLUTION_PATTERN.value,
        title="Windows CLI: SessionStart hooks freeze",
        content="""Solução definitiva para hooks no Windows CLI descoberta em 2025-11-13:

**Problema**: SessionStart hooks causam freeze/hang no Windows CLI

**Root Cause**:
SessionStart hooks executam durante fase de inicialização SÍNCRONA do Claude Code,
antes do event loop estar ativo. No Windows, isso impede subprocess signal polling correto.

**Evidência**:
> "Windows requires active polling for subprocess signals during initialization.
>  SessionStart hooks run during sync init phase which doesn't poll on Windows"
Fonte: cc-toolkit commit 09ab8674

**Solução**: Hooks híbridos com run-once guard

**Implementação**:
```javascript
function shouldSkip() {
  if (process.env.CLAUDE_SESSION_CONTEXT_LOADED === 'true') {
    return true;
  }
  process.env.CLAUDE_SESSION_CONTEXT_LOADED = 'true';
  return false;
}

function main() {
  if (shouldSkip()) {
    outputJSON({ continue: true, systemMessage: '' });
    return;
  }
  // Lógica normal do hook...
}
```

**Comportamento**:
- SessionStart (Web/Linux): executa 1x normalmente
- UserPromptSubmit (Windows CLI): executa apenas na 1ª invocação

**Arquivos criados**:
- .claude/hooks/session-context-hybrid.js
- .claude/hooks/invoke-legal-braniac-hybrid.js
- .claude/settings.hybrid.json
- .claude/WINDOWS_CLI_HOOKS_SOLUTION.md (400+ linhas)

**Referência**: https://github.com/DennisLiuCk/cc-toolkit/commit/09ab8674
""",
        tags=["windows", "CLI", "hooks", "freeze", "sessionstart", "userpromptsubmit", "workaround"],
        context={"discovered_date": "2025-11-13", "platform": "windows", "fix_type": "run-once-guard"}
    ))

    # ========================================================================
    # DECISÕES ARQUITETURAIS
    # ========================================================================

    print("4. Decisão: Separação 3 camadas Code/Environment/Data")
    memory.store(MemoryUnit(
        type=MemoryType.ARCHITECTURAL_DECISION.value,
        title="Separação 3 camadas: Code/Environment/Data (Inviolável)",
        content="""Decisão arquitetural CRÍTICA pós-desastre de 3 dias:

**LAYER 1: CODE** (C:/claude-work/repos/Claude-Code-Projetos/)
- Conteúdo: Python source files, configs, docs
- Version control: Git (MANDATORY)
- Portabilidade: git push/pull

**LAYER 2: ENVIRONMENT** (agentes/*/.venv/)
- Conteúdo: Python interpreter, installed packages
- Version control: NEVER (must be in .gitignore)
- Portabilidade: Recreated via requirements.txt

**LAYER 3: DATA** (E:/claude-code-data/)
- Conteúdo: Downloads, logs, outputs
- Version control: NEVER
- Portabilidade: Physical transport only

**BLOCKING RULE**:
- ❌ Code MUST NEVER be placed on E:/
- ❌ Data MUST NEVER be committed to Git
- ❌ .venv MUST NEVER be committed to Git

**Consequências de violação**:
Ver DISASTER_HISTORY.md - 3 dias de sistema inutilizável

**Implementação**:
- shared/utils/path_utils.py (centralização de paths)
- .gitignore (proteção contra commits acidentais)
- CLAUDE.md (instruções para agentes LLM)
""",
        tags=["arquitetura", "disaster", "git", "windows", "separacao-camadas", "critico"],
        context={"decided_date": "2025-11-07", "severity": "critical", "reason": "3-day disaster"}
    ))

    print("5. Decisão: Legal-Braniac Orchestrator")
    memory.store(MemoryUnit(
        type=MemoryType.ORCHESTRATION.value,
        title="Legal-Braniac: Meta-agent orchestrator",
        content="""Arquitetura de orquestração implementada em 2025-11-13:

**Conceito**: Meta-agent que coordena 6 agentes especializados + 34 skills

**Agentes coordenados**:
1. oab-watcher (OAB daily journal monitoring)
2. djen-tracker (Electronic Justice Daily)
3. legal-lens (Legal publications analysis)
4. oab-api (OAB certifications verification)
5. pdf-ingestion (PDF processing pipeline)
6. doc-analysis (Document deep analysis)

**Skills disponíveis**: 34 capabilities
- OCR: ocr-pro
- Parsing: deep-parser, parse-legal
- Recognition: sign-recognition
- +31 outras

**Auto-discovery**:
Hooks detectam automaticamente agentes/.claude/agents/*.md e skills/*/SKILL.md

**Hooks implementados**:
- .claude/hooks/invoke-legal-braniac-hybrid.js (auto-discovery)
- .claude/hooks/session-context-hybrid.js (project context injection)

**Compatibilidade**: Web, Linux, Windows CLI (via hybrid hooks)

**Referência**:
- README_SESSAO_2025-11-13.md
- .claude/agents/legal-braniac.md
""",
        tags=["legal-braniac", "orchestration", "agentes", "skills", "arquitetura"],
        context={"implemented_date": "2025-11-13", "agents_count": 6, "skills_count": 34}
    ))

    # ========================================================================
    # CONTEXTO DO PROJETO
    # ========================================================================

    print("6. Contexto: Filtro de jurisprudência pós-download")
    memory.store(MemoryUnit(
        type=MemoryType.PROJECT_CONTEXT.value,
        title="Caderno Filter: Filtro de jurisprudência multi-critério",
        content="""Feature implementada em 2025-11-13 para filtrar cadernos DJEN:

**Problema**: Após download massivo de cadernos, precisava filtrar por tema/estado/data

**Solução**: CadernoFilter com scoring multi-camadas

**Critérios de filtro**:
- Temas (ex: "execução fiscal", "ICMS")
- Tribunais (ex: "STF", "STJ", "TJSP")
- Data (início/fim)
- Instância (1ª, 2ª, superior)
- Palavras-chave custom

**Scoring system**:
- Temas: 40%
- Palavras-chave: 30%
- Instância: 20%
- Termos jurídicos: 10%

**Features**:
- Extração de texto PDF (pdfplumber + PyPDF2 fallback)
- Cache de textos extraídos (performance)
- Snippets relevantes com contexto (200 chars)
- Export JSON/TXT
- CLI completo

**Uso**:
```bash
python caderno_filter.py \\
  --cadernos-dir E:/djen-data/cadernos \\
  --temas "ICMS" "execução fiscal" \\
  --tribunais STF STJ TJSP \\
  --data-inicio 2025-01-01 \\
  --score-minimo 0.7 \\
  --output resultados.json
```

**Implementação**: agentes/djen-tracker/src/caderno_filter.py (669 linhas)
""",
        tags=["DJEN", "cadernos", "filter", "jurisprudencia", "pdf", "scoring"],
        context={"implemented_date": "2025-11-13", "lines_of_code": 669}
    ))

    # ========================================================================
    # ESTATÍSTICAS
    # ========================================================================

    print("\n" + "="*60)
    stats = memory.get_stats()
    print(f"✅ {stats['total_memories']} memórias armazenadas com sucesso!\n")

    print("📊 Estatísticas:")
    print(f"  - Tipos: {stats['types_count']}")
    print(f"  - Embeddings: {'✅ Ativados' if stats['embeddings_enabled'] else '❌ Desativados'}")
    print(f"\nPor tipo:")
    for tipo, count in stats['by_type'].items():
        print(f"  - {tipo}: {count}")
    print(f"\nTop tags:")
    for tag_info in stats['top_tags'][:5]:
        print(f"  - {tag_info['tag']}: {tag_info['count']}")

    print("\n" + "="*60)
    print("🎉 Memórias iniciais populadas com sucesso!")
    print("\nPróximo passo: Testar recall")
    print(f"  python3 {__file__.replace('populate_initial_memories.py', 'episodic_memory.py')} \\")
    print(f"    --memory-dir {memory_dir} \\")
    print(f"    --action recall \\")
    print(f"    --tags DJEN API \\")
    print(f"    --limit 5")

if __name__ == "__main__":
    main()
