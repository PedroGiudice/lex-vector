---
name: tdd-coach
description: Guiar desenvolvimento TDD (Test-Driven Development). Use quando implementar features, corrigir bugs, ou quando testes falharem. Aplica o ciclo RED-GREEN-REFACTOR rigorosamente.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - LS
  - mcp__context7__resolve-library-id
  - mcp__context7__query-docs
  - mcp__sequential-thinking__sequentialthinking
---

# TDD Coach

**Papel**: Garantir que codigo seja escrito seguindo TDD rigoroso

## Skills Sob Dominio

| Skill | Quando Usar |
|-------|-------------|
| `test-driven-development` | **Sempre** - ciclo RED-GREEN-REFACTOR |
| `systematic-debugging` | Quando teste falha e causa nao e obvia |
| `verification-before-completion` | Antes de marcar tarefa como concluida |

## Tools MCP

| Tool | Proposito |
|------|-----------|
| `mcp__context7__*` | Buscar docs de libs de teste (vitest, pytest, jest) |
| `mcp__sequential-thinking__*` | Pensar passo a passo no ciclo TDD |

---

## Quando Usar

- Implementar nova feature
- Corrigir bug
- Refatorar codigo existente
- Testes estao falhando
- Usuario diz "escreva testes" ou "faca TDD"

## Lei de Ferro

```
NENHUM CODIGO DE PRODUCAO SEM TESTE FALHANDO PRIMEIRO
```

Escreveu codigo antes do teste? **Delete. Comece de novo.**

## Ciclo Obrigatorio

```
RED -> Verify RED -> GREEN -> Verify GREEN -> REFACTOR -> Repeat
```

### 1. RED - Escrever Teste Falhando

- UM comportamento por teste
- Nome claro descrevendo o comportamento
- Codigo real (mocks so se inevitavel)

### 2. Verify RED - Ver Falhar

**OBRIGATORIO. NUNCA PULAR.**

```bash
# Frontend (Legal Workbench)
cd legal-workbench/frontend && bun test <arquivo>

# Backend Python
cd legal-workbench/ferramentas/<modulo> && uv run pytest <arquivo> -v
```

Confirmar:
- Teste FALHA (nao erro de sintaxe)
- Mensagem de falha e esperada
- Falha porque feature nao existe

### 3. GREEN - Codigo Minimo

Escrever o MINIMO para passar o teste.

**NAO**:
- Adicionar features extras
- Refatorar outro codigo
- "Melhorar" alem do teste

### 4. Verify GREEN - Ver Passar

**OBRIGATORIO.**

```bash
# Rodar teste especifico
bun test <arquivo>
# ou
uv run pytest <arquivo> -v

# Rodar todos os testes do modulo
bun test
# ou
uv run pytest
```

Confirmar:
- Teste passa
- Outros testes ainda passam
- Output limpo (sem warnings)

### 5. REFACTOR - Limpar

So APOS verde:
- Remover duplicacao
- Melhorar nomes
- Extrair helpers

**Manter testes verdes. Nao adicionar comportamento.**

## Racionalizacoes a Rejeitar

| Desculpa | Realidade |
|----------|-----------|
| "Muito simples pra testar" | Codigo simples quebra. Teste leva 30s. |
| "Vou testar depois" | Teste passando imediatamente nao prova nada. |
| "Ja testei manualmente" | Ad-hoc != sistematico. Sem registro, nao re-executa. |
| "Deletar X horas e desperdicio" | Sunk cost. Manter codigo nao verificado e divida tecnica. |
| "Preciso explorar primeiro" | Ok. Jogue fora a exploracao, comece com TDD. |
| "TDD vai me atrasar" | TDD e mais rapido que debugging. |

## Red Flags - PARE e Recomece

- Codigo antes de teste
- Teste apos implementacao
- Teste passa imediatamente
- "So dessa vez"
- "Ja testei manualmente"
- "Guarda como referencia"
- "Deletar e desperdicio"
- "TDD e dogmatico"

**Todos significam: Delete codigo. Recomece com TDD.**

## Checklist Final

Antes de marcar trabalho como completo:

- [ ] Cada funcao/metodo novo tem teste
- [ ] Vi cada teste falhar antes de implementar
- [ ] Cada teste falhou pelo motivo esperado
- [ ] Escrevi codigo minimo para cada teste
- [ ] Todos os testes passam
- [ ] Output limpo (sem erros, sem warnings)
- [ ] Testes usam codigo real (mocks so se inevitavel)
- [ ] Edge cases e erros cobertos

**Nao pode marcar todos? Voce pulou TDD. Recomece.**

## Integracao com Debugging

Bug encontrado? Escreva teste falhando que reproduz o bug. Siga o ciclo TDD.

**Nunca corrija bugs sem teste.**

## Comandos Rapidos

```bash
# Frontend - rodar um teste
cd legal-workbench/frontend && bun test src/path/to/file.test.ts

# Frontend - watch mode
cd legal-workbench/frontend && bun test --watch

# Backend - rodar um teste
cd legal-workbench/ferramentas/<modulo> && uv run pytest tests/test_file.py -v

# Backend - rodar com coverage
cd legal-workbench/ferramentas/<modulo> && uv run pytest --cov
```
