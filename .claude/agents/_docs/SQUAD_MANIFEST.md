# TUI Elite Squad - Manifest

**4 agentes especializados + 1 generalista para desenvolvimento TUI.**

---

## Arquitetura

```
                    ┌─────────────────────┐
                    │   Claude Principal  │
                    │    (Orquestrador)   │
                    └──────────┬──────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │tui-architect│────▶│tui-designer │────▶│tui-developer│
    │  (Planner)  │     │  (Stylist)  │     │  (Builder)  │
    └─────────────┘     └─────────────┘     └─────────────┘
                               │                   │
                               └─────────┬─────────┘
                                         │
                                         ▼
                               ┌─────────────────┐
                               │  tui-debugger   │
                               │  (Inspector)    │
                               └─────────────────┘

    ┌─────────────────────────────────────────────────────┐
    │                    tui-master                       │
    │           (Fallback - tarefas simples)              │
    └─────────────────────────────────────────────────────┘
```

---

## Shared Knowledge Base

**Localizacao:** `skills/tui-core/`

| Arquivo | Conteudo |
|---------|----------|
| `KNOWLEDGE_INDEX.md` | Indice central |
| `rules.md` | Anti-alucinacao TCSS |
| `tcss-reference.md` | Propriedades CSS |
| `patterns.md` | Padroes de codigo |
| `theme-guide.md` | Sistema de temas |
| `widget-catalog.md` | Catalogo widgets |
| `bug-patterns.md` | Bugs conhecidos |
| `debugging-guide.md` | Workflow debug |

**REGRA:** Todo agente DEVE ler o knowledge base antes de agir.

---

## Agentes

### tui-architect (Planner)

**Cor:** Azul
**Tools:** Read, Grep, Glob
**Output:** Diagramas ASCII, specs em Markdown

**Responsabilidades:**
- Analisar requisitos
- Desenhar hierarquia de widgets
- Definir message flow
- Criar specs para outros agentes

**Quando usar:**
- Novo projeto TUI
- Nova feature complexa
- Refatoracao arquitetural

**Handoff:** → tui-designer, tui-developer

---

### tui-designer (Stylist)

**Cor:** Magenta
**Tools:** Read, Write, Edit, Glob, Grep
**Output:** Arquivos .tcss, Theme definitions

**Responsabilidades:**
- Criar/editar estilos TCSS
- Definir temas
- Garantir consistencia visual

**Quando usar:**
- Estilizacao de widgets
- Criacao de temas
- Correcao de problemas visuais

**Handoff:** → tui-developer (classes CSS), tui-debugger (verificar)

---

### tui-developer (Builder)

**Cor:** Verde
**Tools:** Read, Write, Edit, MultiEdit, Bash, Grep, Glob
**Output:** Codigo Python (widgets, screens, workers, messages)

**Responsabilidades:**
- Implementar widgets
- Criar screens e navegacao
- Implementar workers assincronos
- Definir message contracts

**Quando usar:**
- Implementacao de features
- Correcao de bugs Python
- Integracao de APIs

**Handoff:** → tui-designer (estilos), tui-debugger (testes)

---

### tui-debugger (Inspector)

**Cor:** Amarelo
**Tools:** Read, Bash, Grep, Glob
**Output:** Relatorios de diagnostico

**Responsabilidades:**
- Diagnosticar problemas
- Executar verificacoes
- Inspecionar DOM e estilos
- Gerar relatorios

**Quando usar:**
- Algo nao funciona
- Verificacao pre-commit
- Auditoria de codigo

**Handoff:** → tui-developer (fixes Python), tui-designer (fixes CSS)

---

### tui-master (Fallback)

**Cor:** Cyan
**Tools:** Read, Write, Edit, MultiEdit, Bash, Grep, Glob
**Output:** Qualquer (codigo, estilos, debug)

**Responsabilidades:**
- Tarefas simples que nao justificam cadeia
- Tarefas que cruzam dominios
- Quando usuario pede explicitamente

**Quando usar:**
- Bug simples e obvio
- Pequena modificacao
- Usuario pede "faca tudo"

---

## Fluxo de Trabalho

### Feature Nova (Complexa)

```
1. tui-architect
   - Desenha hierarquia
   - Define specs
   - Handoff para designer e developer

2. tui-designer (paralelo com developer)
   - Cria .tcss
   - Define tema se necessario

3. tui-developer (paralelo com designer)
   - Implementa widgets
   - Cria messages/workers

4. tui-debugger
   - Verifica integracao
   - Testa com --dev
   - Reporta problemas

5. Loop: developer/designer corrigem → debugger verifica
```

### Bug Fix

```
1. tui-debugger
   - Diagnostica problema
   - Identifica causa
   - Reporta com sugestao

2. tui-developer OU tui-designer
   - Aplica fix baseado no relatorio

3. tui-debugger
   - Verifica correcao
```

### Tarefa Simples

```
1. tui-master
   - Faz tudo diretamente
   - Ou delega para especialista se necessario
```

---

## Decisao: Qual Agente Usar?

```
Tarefa e simples e obvia?
├── Sim → tui-master
└── Nao → Continua

Precisa de planejamento/arquitetura?
├── Sim → tui-architect primeiro
└── Nao → Continua

E sobre estilos/visual?
├── Sim → tui-designer
└── Nao → Continua

E sobre codigo Python?
├── Sim → tui-developer
└── Nao → Continua

E sobre debug/diagnostico?
├── Sim → tui-debugger
└── Nao → tui-master (fallback)
```

---

## Invocacao

```python
# Arquitetura
Task(subagent_type='tui-architect', prompt='...')

# Estilos
Task(subagent_type='tui-designer', prompt='...')

# Codigo
Task(subagent_type='tui-developer', prompt='...')

# Debug
Task(subagent_type='tui-debugger', prompt='...')

# Fallback
Task(subagent_type='tui-master', prompt='...')
```

---

## Importante

1. **Agentes sao stateless** - Cada invocacao e independente
2. **Handoffs sao sugestoes** - Claude principal decide
3. **Knowledge base e obrigatorio** - Todos devem ler
4. **Reiniciar sessao** - Novos agentes so ficam disponiveis apos restart
