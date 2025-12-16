# CLAUDE.md - Legal Workbench

Regras específicas para desenvolvimento no Legal Workbench.

---

## Definition of Done (DoD)

**Uma tarefa SÓ está CONCLUÍDA quando:**

1. ✅ Backend testado e funcional (testes unitários passando)
2. ✅ Integração com UI/Streamlit verificada
3. ✅ Funcionalidade testável via `lw` (alias Streamlit)
4. ✅ Alterações não quebraram outros módulos

> **"Se não funciona na UI, não está pronto."**

---

## Regras Obrigatórias

### 0. UMA ÚNICA ARQUITETURA (CRÍTICO)

**NUNCA manter duas arquiteturas ou stacks concomitantemente.**

Esta regra existe porque:
- Múltiplos `docker-compose.yml` causam confusão sobre qual está ativo
- Portas conflitantes levam a comportamento inesperado
- Documentação fica desatualizada quando há duplicação
- Debugging se torna exponencialmente mais difícil

**Ao migrar de arquitetura:**
1. **DEPRECAR** explicitamente a arquitetura antiga (renomear para `*.deprecated`)
2. **MIGRAR** completamente antes de commitar
3. **REMOVER** arquivos obsoletos após validação
4. **ATUALIZAR** toda documentação relevante

**Se encontrar múltiplas stacks:**
1. PARAR imediatamente
2. Identificar qual é a arquitetura OFICIAL (North Star)
3. Consolidar antes de prosseguir com qualquer trabalho

> **"Uma arquitetura. Um docker-compose. Uma fonte de verdade."**

---

### 1. Docker Health Check PRIMEIRO

**ANTES de qualquer trabalho no Legal Workbench**, verificar status dos containers:

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench/docker
docker compose ps
```

**Todos os 6 serviços devem estar "healthy":**
- `lw-hub` (Streamlit) - porta 8501
- `lw-text-extractor` - porta 8001
- `lw-doc-assembler` - porta 8002
- `lw-stj-api` - porta 8003
- `lw-trello-mcp` - porta 8004
- `lw-redis` - porta 6379

**Se algum container não estiver healthy:**
1. Verificar logs: `docker logs <container_name>`
2. Reiniciar: `docker compose up -d`
3. Investigar causa raiz antes de prosseguir

> **Regra:** Não iniciar trabalho com infraestrutura quebrada.

### 2. UI-First Validation

Toda alteração em `ferramentas/` DEVE ser validada em `modules/`:

```
ferramentas/legal-text-extractor/  →  modules/text_extractor.py
ferramentas/legal-doc-assembler/   →  modules/doc_assembler.py
ferramentas/stj-dados-abertos/     →  modules/stj.py
ferramentas/trello-mcp/            →  modules/trello.py
```

**Checklist pós-alteração de backend:**
- [ ] Wrapper em `modules/` importa corretamente?
- [ ] `render()` executa sem exceção?
- [ ] Resultado aparece na UI?

### 3. Teste End-to-End Obrigatório

Antes de commitar alterações que afetam módulos:

```bash
# 1. Rodar Streamlit
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench
source .venv/bin/activate
streamlit run app.py

# 2. Testar CADA módulo alterado na UI
# 3. Verificar que módulos NÃO alterados continuam funcionando
```

### 4. Teste Empírico via Streamlit

**Regra:** Testes empíricos (com dados reais) SEMPRE via Streamlit.

- Testes unitários = verificam lógica isolada
- Testes empíricos = verificam fluxo completo do usuário
- **Ambos são necessários, mas empírico via UI é obrigatório**

### 5. Isolamento de Erros

Se um módulo quebrar:
1. **NÃO** commitar até corrigir
2. Verificar se a quebra afetou outros módulos
3. Rollback se necessário

### 6. Fixes Definitivos vs Hot-Fixes

**SEMPRE** priorizar correções e fixes definitivos. "Patches" ou "hot-fixes" devem ser usados **apenas** para:
- Situações emergenciais de produção
- Quando explicitamente solicitado pelo usuário

> **Princípio:** Resolver a causa raiz, não o sintoma.

---

## Estrutura do Projeto

```
legal-workbench/
├── app.py              # Entry point Streamlit
├── config.yaml         # Configuração de módulos
├── modules/            # Wrappers UI (Streamlit)
│   ├── text_extractor.py
│   ├── doc_assembler.py
│   ├── stj.py
│   └── trello.py
└── ferramentas/        # Backends independentes
    ├── legal-text-extractor/
    ├── legal-doc-assembler/
    ├── stj-dados-abertos/
    └── trello-mcp/
```

---

## Comandos Úteis

```bash
# Iniciar Legal Workbench
lw  # alias definido em ~/.bashrc

# Ou manualmente:
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench
source .venv/bin/activate
streamlit run app.py
```

---

## Workflow de Desenvolvimento

```
1. Alterar backend em ferramentas/
       ↓
2. Rodar testes unitários do backend
       ↓
3. Atualizar wrapper em modules/ (se necessário)
       ↓
4. Testar via `lw` (Streamlit)
       ↓
5. Verificar outros módulos não quebraram
       ↓
6. Commitar
```

---

## Regras de Frontend (OBRIGATÓRIO)

### 7. Sempre Usar Subagente Especializado

**QUALQUER tarefa de frontend DEVE usar um subagente especializado:**

| Tarefa | Subagente | Quando Usar |
|--------|-----------|-------------|
| FastHTML/HTMX | `fasthtml-bff-developer` | **SEMPRE** para FastHTML |
| React/TypeScript | `frontend-developer` | Componentes React |
| UI/Design | `ui-designer` | Layout, estética, cores |
| Review | `code-reviewer-superpowers` | Após implementação |

> **"Não importa quão simples pareça a tarefa - SEMPRE usar especialista."**

### 8. Clareza de Output ANTES de Implementar

**ANTES de escrever qualquer código frontend:**

1. ✅ Confirmar expectativa de UI com usuário (mockup/referência)
2. ✅ Definir interações HTMX (o que dispara o quê?)
3. ✅ Identificar endpoints backend necessários
4. ✅ Definir estados de erro e loading
5. ✅ Confirmar paleta de cores e estética

> **"Se não está 100% claro o que o usuário espera, PERGUNTE."**

### 9. FastHTML BFF Pattern (Novo Stack)

**Arquitetura aprovada para substituir Streamlit:**

```
Browser (HTMX) ←→ FastHTML BFF ←→ FastAPI Services (Docker)
                       ↑
               Tokens ficam AQUI
               Browser NUNCA vê
```

**Regras do BFF Pattern:**
- Tokens/secrets NUNCA no browser
- Componentes NUNCA chamam API diretamente
- Usar `services/*.py` para proxy de backend
- SSE para streaming de logs

**PoC de referência:** `poc-fasthtml-stj/`

---

*Última atualização: 2025-12-16*
