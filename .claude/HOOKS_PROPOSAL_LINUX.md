# 🪝 Proposta de Hooks Avançados - Linux/WSL

**Data:** 2025-11-15
**Ambiente:** Linux/WSL (Claude Code 2.0.42)
**Objetivo:** Aproveitar hooks nativos shell agora que estamos em ambiente Linux

---

## 📋 Status Atual

### Hooks Implementados (UserPromptSubmit)
✅ **session-context-hybrid.js** - Injeta contexto do projeto
✅ **invoke-legal-braniac-hybrid.js** - Orquestrador mestre
✅ **venv-check.js** - Valida venv Python ativo
✅ **git-status-watcher.js** - Avisa commits antigos (>1h)
✅ **data-layer-validator.js** - Valida separação CODE/ENV/DATA
✅ **dependency-drift-checker.js** - Detecta requirements.txt desatualizados
✅ **corporate-detector.js** - Detecta ambiente corporativo Windows

### Hook Wrapper
✅ **hook-wrapper.js** - Wrapper universal para tracking de execução

### Hooks Não Utilizados
⚠️ **skill-activation-prompt.sh** - Existe mas não está ativo no settings.json

---

## 🆕 Propostas de Novos Hooks

### 1. PostToolUse: Python Code Quality

**Nome:** `post-python-quality.sh`
**Trigger:** Após Edit/Write em arquivos `.py`
**Funcionalidades:**
- ✅ Validar sintaxe Python (`python -m py_compile`)
- ✅ Auto-formatar com Black (se instalado)
- ✅ Checar imports não utilizados (via `pyflakes`)
- ✅ Avisar se código está fora de venv (previne poluição global)
- ⚠️ Alertar se arquivo contém credenciais (regex: `api_key`, `password`, etc.)

**Benefícios:**
- Previne commits com syntax errors
- Mantém código formatado automaticamente
- Detecta secrets antes de commit

**Implementação:**
```bash
#!/bin/bash
# .claude/hooks/post-python-quality.sh

# Verificar se é arquivo Python
if [[ "$FILE_PATH" != *.py ]]; then
    echo '{"continue": true}'
    exit 0
fi

# 1. Validar sintaxe
if ! python3 -m py_compile "$FILE_PATH" 2>/dev/null; then
    echo '{"continue": false, "systemMessage": "❌ SYNTAX ERROR em '$FILE_PATH' - Corrija antes de continuar"}'
    exit 0
fi

# 2. Detectar secrets
if grep -qE "(api_key|password|secret|token)\s*=\s*['\"]" "$FILE_PATH"; then
    echo '{"continue": true, "systemMessage": "⚠️ AVISO: Possível credencial detectada em '$FILE_PATH' - Verificar antes de commit"}'
    exit 0
fi

# 3. Auto-formatar com Black (se disponível)
if command -v black &>/dev/null; then
    black "$FILE_PATH" --quiet 2>/dev/null
fi

echo '{"continue": true}'
```

---

### 2. PostToolUse: Git Auto-Add (Opcional)

**Nome:** `post-git-auto-add.sh`
**Trigger:** Após Edit/Write em qualquer arquivo
**Funcionalidades:**
- ✅ Auto `git add` em arquivos modificados (exceto .gitignore)
- ✅ Notificar quando staging area está pronta para commit
- ⚠️ Nunca adicionar arquivos sensíveis (.env, credentials.json)

**Benefícios:**
- Workflow mais rápido - menos comandos manuais
- Previne esquecimento de `git add`

**Configuração:** Opt-in (desabilitado por padrão)

**Implementação:**
```bash
#!/bin/bash
# .claude/hooks/post-git-auto-add.sh

# Verificar se git auto-add está habilitado
AUTO_ADD_ENABLED=${CLAUDE_GIT_AUTO_ADD:-false}

if [[ "$AUTO_ADD_ENABLED" != "true" ]]; then
    echo '{"continue": true}'
    exit 0
fi

# Verificar se arquivo está em .gitignore
if git check-ignore -q "$FILE_PATH"; then
    echo '{"continue": true}'
    exit 0
fi

# Verificar se é arquivo sensível
BASENAME=$(basename "$FILE_PATH")
if [[ "$BASENAME" =~ ^\.env|credentials|secrets|.*\.key$ ]]; then
    echo '{"continue": true, "systemMessage": "⚠️ Arquivo sensível não foi adicionado ao git: '$BASENAME'"}'
    exit 0
fi

# Git add
git add "$FILE_PATH" 2>/dev/null

# Contar arquivos staged
STAGED_COUNT=$(git diff --cached --name-only | wc -l)

if [ "$STAGED_COUNT" -gt 0 ]; then
    echo '{"continue": true, "systemMessage": "✅ '$FILE_PATH' adicionado ao staging ($STAGED_COUNT arquivos prontos para commit)"}'
else
    echo '{"continue": true}'
fi
```

---

### 3. PostToolUse: Requirements.txt Sync

**Nome:** `post-requirements-sync.sh`
**Trigger:** Após Edit/Write em `requirements.txt`
**Funcionalidades:**
- ✅ Sugerir `pip install -r requirements.txt` se venv ativo
- ✅ Avisar quais dependências foram adicionadas/removidas
- ✅ Checar se há dependências com versão pinada vs `>=`

**Benefícios:**
- Sincronização automática de dependências
- Evita "funciona na minha máquina"

**Implementação:**
```bash
#!/bin/bash
# .claude/hooks/post-requirements-sync.sh

# Verificar se é requirements.txt
if [[ "$FILE_PATH" != *requirements.txt ]]; then
    echo '{"continue": true}'
    exit 0
fi

# Verificar se venv está ativo
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo '{"continue": true, "systemMessage": "⚠️ requirements.txt atualizado, mas venv não está ativo. Ative com: source .venv/bin/activate"}'
    exit 0
fi

# Sugerir instalação
echo '{"continue": true, "systemMessage": "📦 requirements.txt atualizado! Execute: pip install -r requirements.txt"}'
```

---

### 4. PostToolUse: Markdown Lint (Documentação)

**Nome:** `post-markdown-lint.sh`
**Trigger:** Após Edit/Write em arquivos `.md`
**Funcionalidades:**
- ✅ Verificar links quebrados (regex simples)
- ✅ Validar formatação de títulos (`#`, `##`, etc.)
- ✅ Alertar sobre TODOs não resolvidos

**Benefícios:**
- Documentação sempre consistente
- Previne links quebrados

**Implementação:**
```bash
#!/bin/bash
# .claude/hooks/post-markdown-lint.sh

if [[ "$FILE_PATH" != *.md ]]; then
    echo '{"continue": true}'
    exit 0
fi

# Contar TODOs
TODO_COUNT=$(grep -c "TODO\|FIXME\|XXX" "$FILE_PATH" 2>/dev/null || echo 0)

if [ "$TODO_COUNT" -gt 0 ]; then
    echo '{"continue": true, "systemMessage": "📝 '$FILE_PATH' contém '$TODO_COUNT' TODOs pendentes"}'
else
    echo '{"continue": true}'
fi
```

---

### 5. UserPromptSubmit: Skill Activation (Reativar)

**Nome:** `skill-activation-prompt.sh` (já existe!)
**Trigger:** Antes de processar prompt do usuário
**Funcionalidades:**
- ✅ Detectar menções a skills no prompt
- ✅ Ativar skills automaticamente se disponíveis
- ✅ Sugerir skills relacionados ao contexto

**Status:** Arquivo existe mas não está ativo no `settings.json`

**Ação:** Reativar adicionando ao UserPromptSubmit

---

### 6. PostToolUse: Bash Command Logger

**Nome:** `post-bash-logger.sh`
**Trigger:** Após execução de comandos Bash
**Funcionalidades:**
- ✅ Registrar comandos perigosos (`rm -rf`, `chmod 777`, etc.)
- ✅ Criar log de auditoria (`.claude/logs/bash-history.log`)
- ⚠️ Alertar sobre comandos destrutivos

**Benefícios:**
- Auditoria de ações
- Previne acidentes

**Implementação:**
```bash
#!/bin/bash
# .claude/hooks/post-bash-logger.sh

# Comandos perigosos para monitorar
DANGEROUS_PATTERNS="rm -rf|chmod 777|dd if=|mkfs|fdisk|parted"

# Ler comando executado (passado via stdin)
COMMAND=$(cat)

# Verificar se comando é perigoso
if echo "$COMMAND" | grep -qE "$DANGEROUS_PATTERNS"; then
    # Registrar em log
    echo "[$(date -Iseconds)] DANGEROUS: $COMMAND" >> .claude/logs/bash-history.log

    echo '{"continue": true, "systemMessage": "⚠️ Comando potencialmente perigoso executado: '"$COMMAND"'"}'
else
    echo '{"continue": true}'
fi
```

---

### 7. SessionStart: Project Health Check

**Nome:** `session-health-check.sh`
**Trigger:** Ao iniciar sessão Claude Code
**Funcionalidades:**
- ✅ Verificar se repositório está limpo (sem uncommitted changes antigos)
- ✅ Checar se dependências estão atualizadas
- ✅ Validar estrutura de diretórios (CODE/ENV/DATA)
- ✅ Reportar status de agentes Python (venvs criados?)

**Benefícios:**
- Visibilidade imediata de problemas
- Previne trabalho em ambiente inconsistente

---

## 🔧 Configuração Proposta (settings.json)

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node .claude/hooks/hook-wrapper.js .claude/hooks/session-context-hybrid.js"
          },
          {
            "type": "command",
            "command": "node .claude/hooks/hook-wrapper.js .claude/hooks/invoke-legal-braniac-hybrid.js"
          },
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/skill-activation-prompt.sh",
            "_note": "NOVO: Reativado - detecta e ativa skills automaticamente"
          },
          {
            "type": "command",
            "command": "node .claude/hooks/hook-wrapper.js .claude/hooks/venv-check.js"
          },
          {
            "type": "command",
            "command": "node .claude/hooks/hook-wrapper.js .claude/hooks/git-status-watcher.js"
          },
          {
            "type": "command",
            "command": "node .claude/hooks/hook-wrapper.js .claude/hooks/data-layer-validator.js"
          },
          {
            "type": "command",
            "command": "node .claude/hooks/hook-wrapper.js .claude/hooks/dependency-drift-checker.js"
          },
          {
            "type": "command",
            "command": "node .claude/hooks/hook-wrapper.js .claude/hooks/corporate-detector.js"
          }
        ]
      }
    ],

    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/post-python-quality.sh",
            "_note": "NOVO: Valida sintaxe Python + detecta secrets"
          },
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/post-requirements-sync.sh",
            "_note": "NOVO: Sugere pip install após editar requirements.txt"
          },
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/post-markdown-lint.sh",
            "_note": "NOVO: Valida documentação Markdown"
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/post-bash-logger.sh",
            "_note": "NOVO: Registra comandos perigosos em auditoria"
          }
        ]
      }
    ],

    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/session-health-check.sh",
            "_note": "NOVO: Verifica saúde do projeto ao iniciar sessão"
          }
        ]
      }
    ]
  }
}
```

---

## 📊 Priorização

### 🔥 Alta Prioridade (Implementar Agora)
1. **post-python-quality.sh** - Validação crítica para agentes Python
2. **post-requirements-sync.sh** - Sincronização de dependências
3. **skill-activation-prompt.sh** - Reativar (já existe)

### 🚀 Média Prioridade (Próxima Sprint)
4. **post-bash-logger.sh** - Auditoria de comandos
5. **session-health-check.sh** - Health check ao iniciar

### 💡 Baixa Prioridade (Opcional)
6. **post-git-auto-add.sh** - Opt-in (pode ser invasivo)
7. **post-markdown-lint.sh** - Nice to have

---

## 🧪 Testes Recomendados

### Teste 1: Python Quality
```bash
# Criar arquivo Python com erro de sintaxe
echo "def test(" > /tmp/test_syntax_error.py

# Simular edição
FILE_PATH=/tmp/test_syntax_error.py .claude/hooks/post-python-quality.sh

# Resultado esperado: {"continue": false, "systemMessage": "❌ SYNTAX ERROR..."}
```

### Teste 2: Requirements Sync
```bash
# Editar requirements.txt
echo "requests==2.31.0" > agentes/oab-watcher/requirements.txt

# Simular hook
FILE_PATH=agentes/oab-watcher/requirements.txt .claude/hooks/post-requirements-sync.sh

# Resultado esperado: Sugestão de pip install
```

### Teste 3: Bash Logger
```bash
# Simular comando perigoso
echo "rm -rf /tmp/test" | .claude/hooks/post-bash-logger.sh

# Verificar log
cat .claude/logs/bash-history.log
```

---

## 🎯 Benefícios Esperados

### Qualidade de Código
- ✅ Zero syntax errors em Python
- ✅ Código sempre formatado (Black)
- ✅ Secrets detectados antes de commit

### Workflow
- ✅ Dependências sempre sincronizadas
- ✅ Menos comandos manuais (auto-add opcional)
- ✅ Skills ativados automaticamente

### Segurança
- ✅ Auditoria de comandos perigosos
- ✅ Validação de estrutura CODE/ENV/DATA
- ✅ Detecção de credenciais

### Visibilidade
- ✅ Status line com hooks em tempo real
- ✅ Health check ao iniciar sessão
- ✅ Tracking de execução via hook-wrapper

---

## 📁 Arquivos a Criar

```
.claude/hooks/
├── post-python-quality.sh          # NOVO
├── post-requirements-sync.sh       # NOVO
├── post-markdown-lint.sh           # NOVO
├── post-bash-logger.sh             # NOVO
├── post-git-auto-add.sh            # NOVO (opcional)
├── session-health-check.sh         # NOVO
└── skill-activation-prompt.sh      # JÁ EXISTE - apenas reativar

.claude/logs/
└── bash-history.log                # NOVO (gerado automaticamente)
```

---

## 🚀 Próximos Passos

1. **Revisar proposta** - Aprovar/ajustar hooks sugeridos
2. **Implementar Alta Prioridade** - Criar os 3 hooks prioritários
3. **Testar isoladamente** - Validar cada hook antes de integrar
4. **Atualizar settings.json** - Adicionar PostToolUse/SessionStart
5. **Documentar** - Atualizar README com novos hooks
6. **Monitorar** - Usar status line para acompanhar execução

---

**Pronto para implementar?** Aguardando aprovação para criar os hooks! 🚀
