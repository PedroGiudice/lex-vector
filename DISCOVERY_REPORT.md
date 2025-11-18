# DISCOVERY REPORT - Sistema de Monitoramento Multi-Agent

**Data:** 2025-11-18
**Fase:** 0 - Discovery & Análise
**Status:** ✅ Completo

---

## 📊 Sumário Executivo

O projeto **Claude-Code-Projetos** JÁ POSSUI uma infraestrutura significativa de monitoramento e hooks implementada, mas **incompleta** para um sistema full-featured de tracking multi-agent.

**Recomendação:** INTEGRAR o novo sistema de tracking com a infraestrutura existente, aproveitando hooks já configurados e expandindo funcionalidades.

---

## 🔍 Estrutura do Claude Code Encontrada

### Diretórios Claude Code

```
~/.claude/                          # Config global do Claude Code (runtime)
├── settings.json                   # Config global (só hook Stop configurado)
├── skills/                         # Skills oficiais
│   └── session-start-hook/
├── statusline/                     # Statusline global
│   └── last-used.json             # Tracking de last-used
└── stop-hook-git-check.sh         # Hook Stop existente

/home/user/Claude-Code-Projetos/.claude/   # Config do projeto
├── settings.local.json             # Permissions extensivas
├── hooks/                          # ⭐ SISTEMA DE HOOKS SOFISTICADO
│   ├── legal-braniac-loader.js    # (56KB) Supervisor agentes/skills
│   ├── prompt-enhancer.js         # (16KB) Prompt enhancement
│   ├── vibe-analyze-prompt.js     # (5KB) Vibe analysis
│   ├── context-collector.js       # (7KB) Context collection
│   ├── session-end-git-safety.js  # (8KB) Git safety
│   ├── hook-wrapper.js            # Hook execution wrapper
│   ├── lib/                       # Bibliotecas compartilhadas
│   └── docs/                      # Documentação dos hooks
├── statusline/                     # ⭐ STATUSLINES CUSTOMIZADAS
│   ├── enhanced-statusline.js     # Statusline enhanced
│   ├── professional-statusline.js # Statusline profissional
│   ├── hooks-status.json          # ⭐ TRACKING DE HOOKS
│   └── virtual-agents-state.json  # ⭐ TRACKING DE AGENTES (vazio)
├── statusline-deprecated-backup/
│   └── legal-braniac-statusline.js # (deprecated) Sistema anterior
└── agents/                         # Definições de agentes
    └── legal-braniac.md
```

---

## ✅ Dependências do Sistema

| Dependência | Status | Versão | Notas |
|-------------|--------|--------|-------|
| **Python 3** | ✅ OK | 3.11.14 | Instalado e funcional |
| **jq** | ✅ OK | 1.7 | Necessário para hooks bash |
| **Git** | ✅ OK | 2.43.0 | Instalado |
| **Node.js** | ✅ OK | v22.21.1 | Para hooks JavaScript |
| **Python sqlite3** | ✅ OK | Built-in | Módulo disponível |
| **sqlite3 CLI** | ⚠️ Faltando | N/A | Não essencial (Python sqlite3 suficiente) |

**Conclusão:** Todas as dependências essenciais estão disponíveis. ✅

---

## 🎯 Infraestrutura Existente de Monitoring

### 1. Sistema de Hooks (FUNCIONAL)

**Hooks implementados:**

| Hook | Arquivo | Função | Status |
|------|---------|--------|--------|
| `legal-braniac-loader` | legal-braniac-loader.js | Supervisor de agentes/skills | ✅ Ativo |
| `prompt-enhancer` | prompt-enhancer.js | Enhancement de prompts | ✅ Ativo |
| `vibe-analyze-prompt` | vibe-analyze-prompt.js | Análise de vibe | ✅ Ativo |
| `context-collector` | context-collector.js | Coleta de contexto | ✅ Ativo |
| `session-end-git-safety` | session-end-git-safety.js | Git safety check | ✅ Implementado |

**Dados do hooks-status.json (última execução):**

```json
{
  "legal-braniac-loader": {
    "status": "success",
    "timestamp": 1763428876703,
    "lastRun": "2025-11-18T01:21:16.703Z",
    "output": "🧠 Legal-Braniac: Supervisor ativo\n📋 Agentes (7): analise-dados-legal, desenvolvimento, +5\n🛠️ Skills (35): architecture-diagram-creator, article-extractor, +33"
  },
  "context-collector": {
    "status": "success",
    "timestamp": 1763428896443,
    "output": "⚠️ VALIDATIONS:\n⚠️ RULE_006: venv não ativo!"
  }
}
```

**Análise:** Hooks estão executando com sucesso e JÁ fazem tracking de:
- ✅ Agentes disponíveis (7 detectados)
- ✅ Skills disponíveis (35 detectados)
- ✅ Validações de ambiente (venv check)
- ✅ Timestamps de execução
- ✅ Status de sucesso/erro

---

### 2. Tracking de Agentes (PARCIAL)

**Arquivo:** `.claude/statusline/virtual-agents-state.json`

```json
{
  "version": "2.0",
  "virtualAgents": [],        // ⚠️ VAZIO - não tracking agentes ativos
  "timestamp": 1763428876689,
  "ttl": 86400000,
  "session": "unknown",
  "metadata": {
    "totalAgents": 0,         // ⚠️ Zero agentes rastreados
    "promotionCandidates": 0
  }
}
```

**Status:** Estrutura existe mas **não está populada**. Sistema não está rastreando agentes ativos em tempo real.

---

### 3. Sistema de Statusline (MÚLTIPLAS OPÇÕES)

**Statuslines encontradas:**

| Arquivo | Localização | Status | Funcionalidade |
|---------|-------------|--------|----------------|
| `enhanced-statusline.js` | `.claude/statusline/` | ✅ Ativo | Statusline simplificado |
| `professional-statusline.js` | `.claude/statusline/` | ✅ Ativo | Statusline profissional |
| `legal-braniac-statusline.js` | `statusline-deprecated-backup/` | ⚠️ Deprecated | Sistema anterior (v3 com spinner) |

**Capacidades do legal-braniac-statusline.js (deprecated):**
- ✅ Discovery de agentes (`.claude/agents/*.md`)
- ✅ Discovery de skills
- ✅ Discovery de hooks
- ✅ Tracking de last-used (hooks/agents/skills)
- ✅ Métricas de prompt quality
- ✅ User vocabulary tracking
- ✅ Pattern confidence tracking
- ✅ Active agents tracking

**Nota:** O sistema deprecated tinha funcionalidades que **podem ser recuperadas** para o novo sistema.

---

### 4. Configuração de Settings

**~/.claude/settings.json (Global):**

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "~/.claude/stop-hook-git-check.sh"
      }]
    }]
  },
  "permissions": {
    "allow": ["Skill"]
  }
}
```

**Status:**
- ⚠️ NÃO tem statusline configurada
- ⚠️ Apenas hook "Stop" configurado
- ⚠️ Falta PrePrompt, PostResponse, PostToolUse hooks

**.claude/settings.local.json (Projeto):**
- ✅ Permissions extensivas configuradas (152 allow rules)
- ⚠️ NÃO sobrescreve hooks (herda do global)

---

## 📋 Gap Analysis - O Que Falta

### Funcionalidades Faltantes para Sistema Completo

| Funcionalidade | Status Atual | Necessário |
|----------------|--------------|------------|
| **Agent Tracking** | ⚠️ Estrutura existe, mas vazia | Implementar tracker populando virtual-agents-state.json |
| **Hook Tracking** | ✅ Parcial (hooks-status.json) | Expandir para métricas detalhadas |
| **Skill Tracking** | ❌ Não existe | Implementar detection e tracking |
| **Statusline Display** | ✅ Múltiplas opções | Escolher/configurar uma |
| **Database Persistence** | ❌ Não existe | Criar SQLite tracking.db |
| **PrePrompt Hook** | ❌ Não configurado | Adicionar para detecção de agents |
| **PostResponse Hook** | ❌ Não configurado | Adicionar para tracking de atividade |
| **PostToolUse Hook** | ❌ Não configurado | Adicionar para skill detection |
| **Dashboard Web** | ❌ Não existe | Opcional (Fase avançada) |

---

## 🎯 Recomendação de Abordagem

### Opção A: Integração Incremental (RECOMENDADA)

**Vantagens:**
- ✅ Aproveita infraestrutura existente (hooks, statuslines)
- ✅ Menos risco de quebrar sistema atual
- ✅ Validação progressiva
- ✅ Pode reutilizar código do deprecated legal-braniac-statusline

**Passos:**
1. Criar `simple_tracker.py` (do quick-start guide)
2. Integrar com `virtual-agents-state.json` existente
3. Expandir `hooks-status.json` para tracking completo
4. Configurar hooks faltantes (PrePrompt, PostResponse, PostToolUse)
5. Escolher statusline (professional-statusline.js ou criar novo)
6. Testar e validar

**Estimativa:** 2-3 horas

---

### Opção B: Implementação do Zero (Baseada em Quick-Start)

**Vantagens:**
- ✅ Controle total
- ✅ Código limpo e novo
- ✅ Seguindo exatamente o quick-start guide

**Desvantagens:**
- ❌ Ignora infraestrutura existente
- ❌ Pode conflitar com hooks atuais
- ❌ Mais trabalho de setup

**Estimativa:** 3-4 horas

---

### Opção C: Híbrida (Melhor de Ambos Mundos)

**Estratégia:**
1. Criar `simple_tracker.py` (novo, limpo)
2. Integrar com arquivos existentes:
   - Ler de `hooks-status.json`
   - Escrever para `virtual-agents-state.json`
   - Usar statuslines existentes como base
3. Adicionar hooks via settings.json SEM remover os existentes
4. Criar dashboard lendo tanto tracking.db quanto arquivos existentes

**Estimativa:** 2.5-3.5 horas

---

## 🚀 Plano de Ação Recomendado

### FASE 1: Setup Base (30 min)

1. ✅ **Criar simple_tracker.py** no diretório `.claude/monitoring/`
   - Database: `.claude/monitoring/tracking.db`
   - CLI commands: agent, hook, skill, status, statusline, cleanup
2. ✅ **Testar tracker** standalone
3. ✅ **Criar hooks de detecção** (detect_agents.sh, detect_skills.sh, log_hook.sh)

### FASE 2: Integração com Sistema Existente (45 min)

1. ✅ **Modificar simple_tracker.py** para:
   - Ler de `hooks-status.json`
   - Escrever para `virtual-agents-state.json`
   - Manter compatibilidade com sistema atual
2. ✅ **Configurar hooks** em `~/.claude/settings.json`:
   - Adicionar PrePrompt (agent detection)
   - Adicionar PostResponse (activity tracking)
   - Adicionar PostToolUse (skill detection)
   - **MANTER** hook Stop existente
3. ✅ **Testar hooks** não quebram sistema atual

### FASE 3: Statusline Display (30 min)

1. ✅ **Escolher base:**
   - Opção 1: Usar `professional-statusline.js` como base
   - Opção 2: Criar novo `statusline.sh` do quick-start
   - Opção 3: Recuperar funcionalidades do `legal-braniac-statusline.js`
2. ✅ **Integrar** com simple_tracker.py
3. ✅ **Configurar** em settings.json

### FASE 4: Validação End-to-End (45 min)

1. ✅ Testar detecção de agents
2. ✅ Testar tracking de hooks
3. ✅ Testar detecção de skills
4. ✅ Verificar statusline display
5. ✅ Testar performance (<500ms)

### FASE 5: Documentação (30 min)

1. ✅ Criar README.md do sistema
2. ✅ Documentar comandos
3. ✅ Troubleshooting guide
4. ✅ Atualizar CLAUDE.md com novo sistema

**Total Estimado:** 3 horas

---

## ⚠️ Riscos Identificados

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Conflito com hooks existentes | Média | Alto | Testar hooks isoladamente primeiro |
| Performance degradation | Baixa | Médio | Implementar caching, timeout guards |
| Database locking | Baixa | Médio | Usar WAL mode, connections curtas |
| Quebrar sistema atual | Baixa | Alto | Backup settings.json, teste incremental |

---

## 📝 Decisões Pendentes (Necessário Input do Usuário)

### 1. Qual Statusline Base Usar?

- [ ] **Opção A:** Usar `professional-statusline.js` existente como base
- [ ] **Opção B:** Criar novo `statusline.sh` do quick-start guide
- [ ] **Opção C:** Recuperar/refatorar `legal-braniac-statusline.js` (deprecated)
- [ ] **Opção D:** Integrar com ccstatusline (requer npm install)

**Recomendação:** Opção A (professional-statusline.js) ou C (refatorar legal-braniac)

### 2. Integração com Sistema Existente?

- [ ] **Opção A:** Integrar com `virtual-agents-state.json` e `hooks-status.json`
- [ ] **Opção B:** Criar tracking.db separado (isolado)
- [ ] **Opção C:** Híbrido (database novo + leitura de arquivos existentes)

**Recomendação:** Opção C (híbrido)

### 3. Hooks - Adicionar ou Substituir?

- [ ] **Adicionar** hooks PrePrompt/PostResponse/PostToolUse SEM remover existentes
- [ ] **Substituir** alguns hooks existentes com novos

**Recomendação:** Adicionar (menos risco)

---

## 📊 Métricas de Sucesso

### Critérios Obrigatórios (MVP)

- [ ] simple_tracker.py funciona e persiste dados
- [ ] Statusline exibe informações básicas (agents, hooks, skills)
- [ ] Pelo menos 3 hooks configurados e funcionando
- [ ] Sistema não quebra Claude Code
- [ ] Performance aceitável (<500ms para statusline)

### Critérios Desejáveis

- [ ] Integração completa com sistema existente
- [ ] Todos os hooks configurados
- [ ] Dashboard web (opcional)
- [ ] Documentação completa
- [ ] Testes automatizados

---

## 🎯 Próximo Passo

**AGUARDAR CONFIRMAÇÃO DO USUÁRIO:**

1. **Qual abordagem seguir?** (A, B ou C)
2. **Qual statusline usar?** (professional, novo, ou refatorar legal-braniac)
3. **Integração com arquivos existentes?** (Sim/Não)

Após decisão, proceder para **FASE 1: Setup Base** com implementação hands-on.

---

**Relatório gerado em:** 2025-11-18
**Analista:** Claude Sonnet 4.5
**Status:** ✅ Completo - Aguardando aprovação para próxima fase
