# Subagentes - Guia Rapido

## O Que Sao Subagentes

Subagentes sao requisicoes separadas a Anthropic com:
1. **Contexto proprio** - Janela isolada, sem memoria compartilhada com a conversa principal
2. **System prompt dedicado** - Definido no corpo do arquivo markdown
3. **Prompt inicial** - O Claude principal escreve o prompt que vira a primeira mensagem do subagente
4. **Resultado sintetizado** - Ao terminar, retorna resumo para o Claude principal interpretar

> **Importante:** Subagentes NAO podem criar outros subagentes (sem aninhamento).

---

## Formato de Arquivo

Arquivos `.md` em `.claude/agents/` ou `~/.claude/agents/` com frontmatter YAML:

```yaml
---
name: nome-do-subagente        # Obrigatorio: identificador unico (lowercase, hifens)
description: Quando usar       # Obrigatorio: Claude usa isso para decidir delegacao
tools: Read, Edit, Bash        # Opcional: herda tudo se omitido
disallowedTools: Write         # Opcional: remove ferramentas especificas
model: sonnet                  # Opcional: sonnet (default), opus, haiku, inherit
permissionMode: default        # Opcional: default, acceptEdits, dontAsk, bypassPermissions
skills: skill-a, skill-b       # Opcional: skills injetadas no contexto
hooks:                         # Opcional: hooks especificos do subagente
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./validate.sh"
---

System prompt do subagente em markdown.
O corpo do arquivo define o comportamento.
```

---

## Campos do Frontmatter

| Campo | Obrig. | Descricao |
|-------|--------|-----------|
| `name` | Sim | Identificador unico (lowercase, hifens) |
| `description` | Sim | Quando Claude deve delegar para este subagente |
| `tools` | Nao | Ferramentas permitidas (herda todas se omitido) |
| `disallowedTools` | Nao | Ferramentas bloqueadas |
| `model` | Nao | `sonnet` (default), `opus`, `haiku`, `inherit` |
| `permissionMode` | Nao | `default`, `acceptEdits`, `dontAsk`, `bypassPermissions` |
| `skills` | Nao | Skills carregadas no contexto do subagente |
| `hooks` | Nao | Hooks que rodam durante execucao do subagente |

---

## Escopo e Prioridade

| Local | Escopo | Prioridade |
|-------|--------|-----------|
| `--agents` CLI | Sessao atual | 1 (maior) |
| `.claude/agents/` | Projeto | 2 |
| `~/.claude/agents/` | Usuario | 3 |
| Plugin `agents/` | Onde plugin ativo | 4 (menor) |

---

## Subagentes vs Skills vs Hooks

| Ferramenta | Proposito | Contexto |
|------------|-----------|----------|
| **Subagentes** | Tarefas isoladas, pesadas | Janela propria |
| **Skills** | Workflows reutilizaveis | Conversa principal |
| **Hooks** | Automacao de eventos | Background |

---

## Exemplos

### Subagente Minimo
```yaml
---
name: code-reviewer
description: Revisa codigo para qualidade e boas praticas
---

Voce revisa codigo focando em legibilidade e seguranca.
```

### Subagente Completo
```yaml
---
name: db-agent
description: Executa queries SQL read-only. Use para analise de dados.
tools: Bash, Read
model: haiku
permissionMode: dontAsk
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly.sh"
---

Voce e um analista de dados SQL.
Apenas queries SELECT sao permitidas.
```

---

## Comandos Uteis

```bash
/agents           # Interface interativa para gerenciar subagentes
/agents create    # Criar novo subagente
```

---

## Ciclo de Vida

1. Claude principal identifica tarefa que bate com `description`
2. Cria nova requisicao com system prompt do subagente
3. Subagente executa com ferramentas/permissoes proprias
4. Ao terminar, retorna resumo para Claude principal
5. Claude principal sintetiza e continua conversa
