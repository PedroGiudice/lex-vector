# Windows CLI Freezing - Diagnóstico e Correção

## 🚨 Problema

**Sintoma:** Claude Code CLI no Windows PowerShell congela durante inicialização, exigindo pressionar `Tab + Enter` 3 vezes para destravar.

**Causa Raiz:** Windows requer polling ativo de subprocessos, mas Claude Code CLI bloqueia durante a fase de inicialização síncrona antes do event loop estar ativo. Hooks que usam chamadas **síncronas bloqueantes** (`execSync()`, `readFileSync()`) causam deadlock.

## 🔍 Background Técnico

### Por Que Windows É Diferente

- **Linux/macOS:** Usa `kqueue`/`epoll` - notificação assíncrona de eventos do SO
- **Windows:** Requer polling ativo de handles de subprocessos - se o event loop não estiver rodando, subprocessos bloqueiam

### Hooks Problemáticos Identificados

1. **`memory-integration.js`**
   - Usa `execSync()` para executar comandos Python
   - Bloqueia event loop esperando subprocess terminar
   - Windows não consegue fazer polling → freeze

2. **`skill-activation-prompt.ts`**
   - Usa `fs.readFileSync(0, 'utf8')` para ler stdin sincronamente
   - Bloqueia aguardando entrada do usuário
   - Causa timeout e freeze no Windows CLI

### Hooks Seguros (ASYNC)

✅ **`session-context-hybrid.js`**
- Usa `fs.promises.readdir()` - totalmente assíncrono
- Timeout de 500ms via `Promise.race()`
- Run-once guard via variável de ambiente

✅ **`invoke-legal-braniac-hybrid.js`**
- Auto-descobre 7 agentes e 34+ skills
- Usa `await fs.readFile()` - assíncrono
- Run-once guard previne execução repetida

✅ **`venv-check.js`**
- Validação rápida e síncrona de arquivos
- Não usa subprocessos
- Seguro para Windows

## 🛠️ Solução Automática

### 1. Execute o Script de Correção

```powershell
# Navegue até o diretório do projeto
cd C:\claude-work\repos\Claude-Code-Projetos

# Execute o script
.\.claude\fix-windows-hooks.ps1
```

**O script automaticamente:**
- ✅ Detecta hooks bloqueantes (`memory-integration.js`, `skill-activation-prompt`)
- ✅ Cria backup do `settings.json` original
- ✅ Aplica configuração correta (apenas 3 hooks ASYNC)
- ✅ Valida JSON programaticamente
- ✅ Detecta e remove `settings.json` criado em local errado

### 2. Apenas Diagnóstico (Sem Modificar)

```powershell
.\.claude\fix-windows-hooks.ps1 -DiagnosisOnly
```

## 📋 Configuração Correta

Após a correção, seu `.claude/settings.json` deve conter:

```json
{
  "_comment": "Configuração HÍBRIDA de hooks - Solução para Windows CLI subprocess polling issue",
  "_docs": "https://github.com/DennisLiuCk/cc-toolkit/commit/09ab8674200a7bf9e31b0090f39ed12cbc3f6f5d",
  "_strategy": "Use SessionStart para Web/Linux, UserPromptSubmit para Windows CLI. Hooks híbridos previnem execução repetida via run-once guard.",

  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node .claude/hooks/session-context-hybrid.js"
          },
          {
            "type": "command",
            "command": "node .claude/hooks/invoke-legal-braniac-hybrid.js"
          },
          {
            "type": "command",
            "command": "node .claude/hooks/venv-check.js"
          }
        ]
      }
    ]
  }
}
```

**Chave da Solução:**
- ❌ Removido `SessionStart` (não funciona no Windows CLI)
- ✅ Apenas `UserPromptSubmit` com 3 hooks ASYNC
- ✅ Run-once guards previnem execução múltipla
- ✅ Nenhum `execSync()` ou `readFileSync()` bloqueante

## ⚠️ Problema Comum: settings.json no Local Errado

### Sintoma

Após executar o script, `/doctor` ainda reporta:

```
Invalid Settings
C:\Users\pedro\.claude\settings.json
  └ Invalid or malformed JSON
```

### Causa

O script foi executado de **`C:\Users\pedro>`** em vez de **`C:\claude-work\repos\Claude-Code-Projetos`**, criando `settings.json` no diretório do usuário.

### Solução

**Opção 1: Automática** (recomendada)
```powershell
# Execute o script novamente - agora com detecção automática de diretório
cd C:\claude-work\repos\Claude-Code-Projetos
.\.claude\fix-windows-hooks.ps1
# O script irá detectar e oferecer remover o arquivo no local errado
```

**Opção 2: Manual**
```powershell
# Remover arquivo criado incorretamente
Remove-Item "$env:USERPROFILE\.claude\settings.json" -Force

# Remover diretório .claude se vazio
Remove-Item "$env:USERPROFILE\.claude" -Force
```

## ✅ Validação

Após a correção:

```powershell
# 1. Verificar sem erros
claude doctor

# 2. Iniciar Claude CLI
claude

# 3. Verificar comportamento
# ✅ Deve iniciar normalmente
# ✅ NÃO deve congelar
# ✅ NÃO deve precisar de Tab + Enter
```

## 🔗 Referências

### GitHub Issues

- **#9542** - Windows SessionStart hooks freeze CLI
- **#10615** - Windows subprocess polling issue
- **#160** - Additional Windows CLI freezing reports

### Commits Relevantes

- **moai-adk** commit `09ab867` - Run-once guard pattern
- **DennisLiuCk/cc-toolkit** - Hybrid hooks solution

### Documentação Interna

- `.claude/settings.hybrid.json` - Configuração de referência com comentários explicativos
- `.claude/hooks/session-context-hybrid.js` - Exemplo de hook ASYNC com timeout
- `.claude/hooks/invoke-legal-braniac-hybrid.js` - Orquestrador com run-once guard

## 🧪 Detalhes Técnicos - Por Que SessionStart Não Funciona no Windows CLI

### Ordem de Execução (Windows CLI)

1. **Processo principal inicia** → Python subprocess spawned
2. **SessionStart hooks executam** → ANTES do event loop estar ativo
3. **Hook chama `execSync()`** → Precisa de polling para subprocess terminar
4. **Polling bloqueado** → Event loop ainda não iniciou
5. **DEADLOCK** → Processo congela aguardando subprocess que nunca termina

### Por Que UserPromptSubmit Funciona

1. **Processo principal inicia** → Event loop ATIVO
2. **Usuário envia prompt** → Trigger de `UserPromptSubmit`
3. **Hook executa assincronamente** → Event loop pode fazer polling
4. **Subprocess termina normalmente** → Sem freeze

### Web vs CLI Behavior

| Comportamento | Web | Windows CLI | Linux CLI |
|---------------|-----|-------------|-----------|
| SessionStart com subprocess | ✅ Funciona | ❌ Freeze | ✅ Funciona (kqueue) |
| UserPromptSubmit com subprocess | ✅ Funciona | ✅ Funciona | ✅ Funciona |
| Hooks síncronos puros (sem subprocess) | ✅ Funciona | ✅ Funciona | ✅ Funciona |

## 📝 Histórico de Versões

### v2.1 (2025-11-13)
- ✨ Adicionada detecção automática do diretório do projeto
- ✨ Adicionada funcionalidade de limpeza para settings.json em local errado
- ✨ Script agora busca o projeto em locais comuns se não encontrado no diretório atual
- 🐛 Corrigido problema de script executado de `C:\Users\pedro>` em vez do diretório do projeto

### v2.0 (2025-11-12)
- ✨ Removidos hooks bloqueantes `memory-integration.js` e `skill-activation-prompt`
- ✨ Implementado padrão hybrid hooks (SessionStart para Web, UserPromptSubmit para CLI)
- ✨ Adicionado run-once guard pattern
- 🐛 Corrigido freeze no Windows CLI

### v1.0 (Inicial)
- ❌ Usava SessionStart com hooks síncronos - causava freeze no Windows

---

**Última atualização:** 2025-11-13
**Mantido por:** PedroGiudice
**Status:** ✅ Solução validada e testada no Windows PowerShell
