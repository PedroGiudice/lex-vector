# Vibe-Log: Compatibilidade Claude Code Web

**Data:** 2025-11-23
**Status:** ✅ Resolvido
**Componentes:** vibe-log-safe-wrapper.sh, settings.json

---

## 🔴 Problema Original

**Sintoma:** Erro "AUTH TOKEN" ao usar vibe-log-cli no Claude Code Web

**Ambiente afetado:** Claude Code Web (ambiente ephemeral/containerizado)

**Erro exato:**
```
[2025-11-23T06:32:58.740Z] Auth check: No authentication token found
Error: No authentication token found
VibelogError: Not authenticated
```

---

## 🔍 Causa Raiz

### Diferenças Ambientais

| Aspecto | WSL2/Local | Claude Code Web |
|---------|------------|-----------------|
| Diretório home | Persistente | Ephemeral (reseta entre sessões) |
| `~/.vibe-log/.key` | ✅ Existe (32 bytes hex) | ❌ Não existe |
| Token OAuth | ✅ Configurado via browser | ❌ Impossível (sem browser) |
| Autenticação | ✅ `npx vibe-log-cli auth` | ❌ Não disponível |
| Persistência | ✅ Config persiste | ❌ Perde config ao fechar |

### Como vibe-log Autentica

```javascript
// vibe-log-cli/dist/index.js
async authenticate(options) {
  if (options.silent) {
    const token = await getToken(); // ← Lê de ~/.vibe-log/config.json
    if (!token) {
      throw new VibelogError("Not authenticated", "AUTH_REQUIRED");
    }
  }
}
```

**Processo de autenticação:**
1. `npx vibe-log-cli auth` → Abre browser (OAuth flow)
2. Salva token criptografado em `~/.vibe-log/config.json`
3. Gera chave de criptografia em `~/.vibe-log/.key` (32 bytes)
4. Hooks usam `npx vibe-log-cli send --silent` (requer token)

**No Claude Code Web:**
- ❌ Sem browser → Impossível fazer OAuth
- ❌ Sem persistência → Token não sobrevive entre sessões
- ❌ Sem variável de ambiente → vibe-log não suporta `VIBELOG_TOKEN`

---

## ✅ Solução Implementada

### Wrapper Bash com Detecção Automática

**Arquivo:** `.claude/hooks/vibe-log-safe-wrapper.sh`

**Comportamento:**
```bash
# Se autenticado (WSL2/local)
→ Executa: npx vibe-log-cli send --silent --hook-trigger=X

# Se NÃO autenticado (Claude Code Web)
→ Skip silenciosamente (exit 0)
```

**Lógica de detecção:**
1. Verificar se `~/.vibe-log/.key` existe
2. Verificar se `config.json` contém `"token"`
3. Se ambos OK → Executar vibe-log
4. Se qualquer falhar → Skip silencioso

### Mudanças em settings.json

**Antes (QUEBRADO no Web):**
```json
{
  "command": "npx vibe-log-cli send --silent --hook-trigger=sessionstart --hook-version=1.0.0"
}
```

**Depois (COMPATÍVEL):**
```json
{
  "command": ".claude/hooks/vibe-log-safe-wrapper.sh sessionstart"
}
```

---

## 🧪 Validação

### Teste 1: Claude Code Web (Sem Autenticação)

```bash
# Setup
rm -f ~/.vibe-log/.key  # Simular ambiente web

# Execução
.claude/hooks/vibe-log-safe-wrapper.sh sessionstart

# Resultado esperado
# - Sem output
# - Exit code: 0
# - Sem erros em hooks.log
```

✅ **Resultado:** Skip silencioso confirmado

### Teste 2: WSL2/Local (Com Autenticação)

```bash
# Setup
ls ~/.vibe-log/.key  # Arquivo existe (32 bytes)
grep '"token"' ~/.vibe-log/config.json  # Token configurado

# Execução
.claude/hooks/vibe-log-safe-wrapper.sh sessionstart

# Resultado esperado
# - Upload para vibe-log cloud
# - "Sessions uploaded successfully"
```

✅ **Resultado:** Upload funcional (quando autenticado)

---

## 📊 Comportamento por Ambiente

### Claude Code Web (Ephemeral)

```
SessionStart Hook
    ↓
vibe-log-safe-wrapper.sh
    ↓
Verificar ~/.vibe-log/.key → NÃO existe
    ↓
Exit 0 (skip silencioso) ✅
    ↓
Nenhum erro em hooks.log
```

### WSL2/Local (Persistente)

```
SessionStart Hook
    ↓
vibe-log-safe-wrapper.sh
    ↓
Verificar ~/.vibe-log/.key → Existe ✅
Verificar config.json → Token presente ✅
    ↓
npx vibe-log-cli send --silent --hook-trigger=sessionstart
    ↓
Sessions uploaded to cloud ✅
```

---

## 🔄 Rollback (Se Necessário)

### Reverter para comportamento anterior

```bash
# Editar .claude/settings.json manualmente
# SessionStart e SessionEnd hooks:

# ANTES (wrapper safe):
"command": ".claude/hooks/vibe-log-safe-wrapper.sh sessionstart"

# DEPOIS (comportamento original):
"command": "npx vibe-log-cli send --silent --hook-trigger=sessionstart --hook-version=1.0.0"
```

**⚠️ AVISO:** Comportamento original FALHARÁ no Claude Code Web com erro de autenticação.

---

## 📚 Limitações Conhecidas

### Vibe-Log NÃO Funciona no Claude Code Web

**Por quê:**
- Ambiente ephemeral (sem persistência de `~/.vibe-log/`)
- Sem browser para OAuth flow
- Sem suporte para env var `VIBELOG_TOKEN`

**Soluções alternativas NÃO viáveis:**
- ❌ Copiar `.key` manualmente → Perde ao fechar sessão
- ❌ Usar token via env var → vibe-log não suporta
- ❌ Autenticação programática → Requer browser OAuth

**Solução VIÁVEL (implementada):**
- ✅ Graceful degradation via wrapper
- ✅ Funciona em ambos ambientes (web skip, local upload)
- ✅ Zero impacto em performance
- ✅ Zero erros em logs

---

## 🚀 Próximas Melhorias (Opcional)

### Ideia 1: Cache Local no Claude Code Web

**Conceito:** Armazenar análises vibe-log localmente mesmo sem upload

```bash
# Se não autenticado, salvar local em /tmp
if [ ! -f "$HOME/.vibe-log/.key" ]; then
  # Executar analyze-prompt local (sem upload)
  npx vibe-log-cli analyze-prompt --stdin --no-upload
fi
```

**Trade-off:**
- ✅ Gordon AI Coach funciona localmente
- ❌ Sem sincronização cloud (dados perdem ao fechar sessão)

### Ideia 2: Modo Offline Nativo (Feature Request)

**Proposta para vibe-log-cli:**
- Adicionar flag `--offline` que skip autenticação
- Armazenar análises localmente
- Sincronizar quando autenticado

**Status:** Feature não existe ainda (2025-11-23)

---

## 📝 Arquivos Modificados

1. **`.claude/hooks/vibe-log-safe-wrapper.sh`** (NOVO)
   - Wrapper bash com detecção de autenticação
   - Graceful skip se não autenticado

2. **`.claude/settings.json`**
   - SessionStart hook: linha 32
   - SessionEnd hook: linha 54
   - Mudado de `npx vibe-log-cli` direto para wrapper

3. **`.claude/hooks/docs/vibe-log-web-compatibility.md`** (NOVO)
   - Esta documentação

---

## ✅ Checklist de Validação

- [x] Wrapper criado e testado
- [x] Permissões executáveis configuradas (`chmod +x`)
- [x] settings.json atualizado (SessionStart + SessionEnd)
- [x] Teste no ambiente web (skip silencioso)
- [x] Teste no ambiente local (funcional quando autenticado)
- [x] Documentação criada
- [x] Zero erros em hooks.log
- [x] Zero impacto em performance

---

**Última atualização:** 2025-11-23
**Responsável:** Claude Code (Sonnet 4.5)
**Status:** ✅ Produção
