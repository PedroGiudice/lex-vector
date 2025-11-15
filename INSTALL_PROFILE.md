# Instalar PowerShell Profile - Windows

## Problema
O comando `scc` não funciona porque o PowerShell profile não está carregado.

## Solução (Execute no PowerShell do Windows)

### 1. Copiar o profile para o local correto

```powershell
# Abra PowerShell como usuário normal (não Admin)
cd C:\claude-work\repos\Claude-Code-Projetos

# Verificar localização do $PROFILE
echo $PROFILE
# Saída esperada: C:\Users\CRM Advogados\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1

# Criar diretório se não existir
New-Item -ItemType Directory -Force -Path (Split-Path $PROFILE)

# Copiar o profile
Copy-Item .\powershell-profile.ps1 $PROFILE -Force
```

### 2. Permitir execução de scripts (se necessário)

```powershell
# Verificar política atual
Get-ExecutionPolicy

# Se retornar "Restricted", ajustar:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Recarregar o profile

```powershell
# Fechar e reabrir PowerShell
# OU
. $PROFILE
```

### 4. Verificar instalação

```powershell
# Deve mostrar mensagem de boas-vindas com lista de comandos
# Comandos disponíveis:
#   scc       - Start Claude Code in project directory
#   gcp       - Open bash WSL in project
#   owsl      - Open WSL (login shell)
#   gsync     - Git pull + status
#   cstatus   - Check Claude Code installation
#   cenv      - Show environment info
#   pstatus   - Show project status
```

## Troubleshooting

### "scc: command not found" no WSL
Isso é **esperado**! O `scc` é um comando **PowerShell** (Windows), não WSL.

**Correto:**
- No **Windows PowerShell**: `scc` ✅
- No **WSL bash**: `claude` ✅

### Erro: "readdirent Documents/CÓPIA DO PEN DRIVE/..."

**Causa:** Claude Code tentava indexar o diretório Windows atual antes de navegar para WSL.

**Solução aplicada (v1.1):** O comando `scc` agora muda para diretório seguro antes de iniciar:
```powershell
# Agora funciona de qualquer diretório (inclusive com caracteres especiais)
cd "C:\Users\CRM Advogados\Documents\CÓPIA DO PEN DRIVE"
scc  # ✅ Funciona! Muda para USERPROFILE antes de chamar WSL
```

**Como funciona internamente:**
1. `Push-Location $env:USERPROFILE` - Vai para diretório seguro
2. `wsl -- bash -c "cd $PROJECT_DIR && exec $CLAUDE_PATH"` - Executa Claude no WSL
3. `Pop-Location` - Restaura diretório original

Se ainda ocorrer erro, verifique se o profile está atualizado:
```powershell
cat $PROFILE | Select-String "PROJECT_DIR"
# Deve retornar: $PROJECT_DIR = "/home/user/Claude-Code-Projetos"
```

### Claude não inicia

**Verificar caminho do Claude no WSL:**
```powershell
wsl -- bash -c "which claude"
# Esperado: /home/cmr-auto/.npm-global/bin/claude
# OU: /home/cmr-auto/.nvm/versions/node/v24.11.1/bin/claude
```

Se retornar caminho diferente, ajustar `$CLAUDE_PATH` no profile:
```powershell
# Editar $PROFILE
notepad $PROFILE

# Alterar linha:
$CLAUDE_PATH = "/caminho/correto/retornado/acima"
```

## Validação Final

```powershell
# 1. Verificar profile carregado
Test-Path $PROFILE
# Deve retornar: True

# 2. Verificar comandos disponíveis
Get-Alias scc
# Deve retornar: CommandType = Alias, Definition = Start-Claude

# 3. Testar comando
scc
# Deve abrir Claude Code no projeto WSL
```

---

**Última atualização:** 2025-11-15
