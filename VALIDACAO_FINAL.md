# Validação Final - Setup Claude Code

Execute estes testes para confirmar que tudo está funcionando.

---

## ✅ Teste 1: PowerShell Profile Instalado (Windows)

```powershell
# Abra PowerShell Windows

# 1.1 Verificar se $PROFILE existe
Test-Path $PROFILE
# Esperado: True

# 1.2 Verificar conteúdo
cat $PROFILE | Select-String "Start-Claude"
# Esperado: Deve mostrar a função Start-Claude

# 1.3 Verificar alias scc
Get-Alias scc
# Esperado: CommandType=Alias, Definition=Start-Claude
```

**✅ PASS se:** Todos retornaram valores esperados
**❌ FAIL se:** Algum erro → Execute `Copy-Item .\powershell-profile.ps1 $PROFILE -Force`

---

## ✅ Teste 2: WSL Username Correto (Windows)

```powershell
# Verificar usuário WSL
wsl -- whoami
# Esperado: cmr-auto

# Verificar se bate com $PROFILE
cat $PROFILE | Select-String "WSL_USERNAME"
# Esperado: $WSL_USERNAME = "cmr-auto"
```

**✅ PASS se:** `cmr-auto` em ambos
**❌ FAIL se:** Diferente → Editar linha 39 do $PROFILE

---

## ✅ Teste 3: Claude Instalado no WSL (Windows)

```powershell
# Verificar caminho do Claude
wsl -- which claude
# Esperado: /opt/node22/bin/claude
# OU: /home/cmr-auto/.npm-global/bin/claude
# OU: /home/cmr-auto/.nvm/versions/node/vX.X.X/bin/claude

# Verificar versão
wsl -- claude --version
# Esperado: Claude Code 2.X.X (não deve travar)
```

**✅ PASS se:** Retornou caminho e versão
**❌ FAIL se:** "command not found" → Claude não instalado no WSL

**Se FAIL:** O caminho real é diferente de `$CLAUDE_PATH` no profile. Ajustar:

```powershell
# Editar $PROFILE
notepad $PROFILE

# Mudar linha 43 para o caminho correto retornado por "which claude"
$CLAUDE_PATH = "/caminho/correto/aqui"

# Salvar e recarregar
. $PROFILE
```

---

## ✅ Teste 4: Projeto Existe (WSL)

```bash
# No WSL

# 4.1 Navegar para projeto
cd /home/user/Claude-Code-Projetos

# 4.2 Verificar é repositório Git
git status
# Esperado: On branch claude/review-injected-context-... (ou outra branch)

# 4.3 Verificar estrutura
ls -la .claude/
# Esperado: Deve mostrar agents/, hooks/, settings.json
```

**✅ PASS se:** Todos comandos funcionaram
**❌ FAIL se:** "No such file or directory" → Projeto não está em `/home/user/`

---

## ✅ Teste 5: scc Funciona de Qualquer Diretório (Windows)

```powershell
# Ir para diretório problemático (com acentos/espaços)
cd "C:\Users\CRM Advogados\Documents"

# Executar scc
scc
```

**✅ PASS se:** Claude Code abre sem erro
**❌ FAIL se:** Erro `readdirent` → Profile não tem Push-Location (atualizar)

**Validação visual:** Claude Code deve abrir mostrando o projeto `/home/user/Claude-Code-Projetos`

---

## ✅ Teste 6: claude Funciona no WSL (WSL)

```bash
# No WSL bash

# Navegar para projeto
cd /home/user/Claude-Code-Projetos

# Executar claude (pode travar por alguns segundos - normal)
claude --version
# Esperado: Claude Code 2.X.X

# Se versão funciona, pode executar interativo
claude
```

**✅ PASS se:** Claude Code abre normalmente
**❌ FAIL se:** Trava indefinidamente → Ctrl+C e reportar

---

## 🎯 Resultado Final

### ✅ Todos os 6 testes PASS → Sistema OK!

Você pode usar:
- **Windows PowerShell:** `scc` de qualquer lugar
- **WSL bash:** `cd /home/user/Claude-Code-Projetos && claude`

### ❌ Algum teste FAIL

Reporte qual teste falhou e o erro exato.

---

## 📋 Resumo dos Comandos

| Ambiente | Comando | O que faz |
|----------|---------|-----------|
| **PowerShell** | `scc` | Abre Claude no projeto (qualquer diretório) |
| **PowerShell** | `gcp` | Abre bash WSL no projeto |
| **PowerShell** | `cenv` | Mostra info do ambiente |
| **PowerShell** | `pstatus` | Mostra status do projeto |
| **WSL** | `claude` | Abre Claude Code (do diretório atual) |

---

**Última atualização:** 2025-11-15
**Versão:** 1.0 - Validação Final
