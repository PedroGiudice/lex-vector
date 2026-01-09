---
name: gemini-cli
description: Gemini CLI integration for context offloading. Use when calling gemini CLI, delegating large file analysis, summarizing code, or needing second opinions. Covers correct syntax, flags, environment variables, and common errors. Keywords: gemini, context offloading, large files, summarize, second opinion, gemini-assistant, gemini CLI.
---

# Gemini CLI: Context Offloading

**Para:** Claude Code
**Versão CLI:** 0.19.1
**Verificado:** 2026-01-09

Esta skill instrui como usar o Gemini CLI para context offloading. **NÃO ADIVINHE FLAGS** - use apenas o documentado aqui.

---

## Sintaxe

```bash
gemini [OPTIONS] "PROMPT_TEXT" [FILES...]
```

---

## Flags Disponíveis

| Flag | Tipo | Descrição |
|------|------|-----------|
| `-m, --model` | string | Modelo (ex: gemini-2.5-flash) |
| `-o, --output-format` | string | `text`, `json`, `stream-json` |
| `-y, --yolo` | boolean | Auto-aprovar ações |
| `--approval-mode` | string | `default`, `auto_edit`, `yolo` |
| `-s, --sandbox` | boolean | Rodar em sandbox |
| `-d, --debug` | boolean | Modo debug |
| `-r, --resume` | string | Retomar sessão |
| `-e, --extensions` | array | Lista de extensões |
| `--include-directories` | array | Diretórios adicionais |

### Flags que NÃO EXISTEM

- ~~`--no-stream`~~
- ~~`--sys-prompt`~~
- ~~`--token-limit`~~
- ~~`--fix`~~
- ~~`--auto-apply`~~

---

## Variável de Ambiente

```bash
export GEMINI_API_KEY="sua-chave"
```

**IMPORTANTE:** Use **apenas** `GEMINI_API_KEY`. Se `GOOGLE_API_KEY` também estiver setada, ela tem precedência.

---

## Padrões de Uso

### Análise de Arquivos (Recomendado)

Passe arquivos como argumentos - Gemini lê diretamente:

```bash
gemini -y "Analise a arquitetura" CLAUDE.md ARCHITECTURE.md src/**/*.ts
```

### Output Estruturado

```bash
gemini -y -o json "Liste problemas" src/*.py
```

### Dados via Pipe

```bash
git diff main | gemini -y "Explique mudanças"
```

---

## Context Offloading

Use Gemini quando:

| Situação | Usar Gemini? |
|----------|--------------|
| Arquivo > 500 linhas | ✅ Sim |
| Múltiplos arquivos | ✅ Sim |
| Diff grande | ✅ Sim |
| Logs extensos | ✅ Sim |
| Edição pequena | ❌ Claude direto |

### CORRETO
```bash
gemini -y "Analise" src/**/*.ts
```

### INCORRETO
```bash
content=$(cat src/**/*.ts)
gemini -y "Analise: $content"  # NÃO FAÇA ISSO
```

---

## Erros Comuns

| Erro | Causa | Solução |
|------|-------|---------|
| "Both API keys set" | GOOGLE + GEMINI | Usar apenas GEMINI_API_KEY |
| "Unknown argument" | Flag inexistente | Usar apenas flags desta skill |
| Auth error | Key inválida | Verificar Google Cloud |
| Timeout | Esperando input | Usar `-y` |

---

## Exemplo Completo

```bash
gemini -y -m gemini-2.5-flash "Você é um auditor. Analise:
1. Estrutura geral
2. Consistência doc/código
3. Problemas
4. Sugestões

Baseie-se APENAS no que leu." \
  CLAUDE.md ARCHITECTURE.md README.md
```
