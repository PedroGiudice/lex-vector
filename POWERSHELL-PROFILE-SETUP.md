# PowerShell Profile - Guia Rápido de Instalação

## 🎯 O que é isso?

Um profile customizado do PowerShell que adiciona comandos úteis para trabalhar com WSL e Claude Code.

**Comandos que você ganha:**
- `scc` - Start Claude Code (abre Claude Code no projeto)
- `gcp` - Go to Claude Project (abre bash WSL no projeto)
- `gsync` - Git sync (pull + status)
- `cstatus` - Check status do ambiente
- `claude <args>` - Executar Claude Code via WSL sem prefixo

---

## 📦 Instalação Automática (RECOMENDADO)

### Passo 1: Baixe o repositório (se ainda não tem)

```powershell
# Clone ou baixe o repositório
git clone https://github.com/PedroGiudice/Claude-Code-Projetos.git
cd Claude-Code-Projetos
```

### Passo 2: Execute o instalador

```powershell
# Execute o script de instalação
.\install-powershell-profile.ps1
```

### Passo 3: Siga as instruções na tela

O script vai:
1. ✅ Detectar automaticamente onde está seu `$PROFILE`
2. ✅ Fazer backup do profile anterior (se existir)
3. ✅ Copiar o profile customizado
4. ✅ Abrir o arquivo no editor para você configurar o username WSL
5. ✅ Mostrar instruções claras do que fazer

### Passo 4: Configure username WSL

No arquivo que abriu, procure pela linha (por volta da linha 39):

```powershell
$wslUser = "cmr-auto"  # ← TROCAR ESTE VALOR!
```

**Como descobrir seu username:**
```bash
# No WSL Ubuntu
whoami
```

**Exemplo de mudança:**
```powershell
# Antes:
$wslUser = "cmr-auto"

# Depois (se seu username for "pedro"):
$wslUser = "pedro"
```

**Salve (Ctrl+S) e feche.**

### Passo 5: Configure ExecutionPolicy (se necessário)

```powershell
# Permitir execução de scripts locais
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Passo 6: Recarregue o profile

```powershell
# Aplicar mudanças
. $PROFILE
```

### Passo 7: Teste!

```powershell
# Ver status
cstatus

# Iniciar Claude Code
scc

# Abrir WSL bash no projeto
gcp
```

---

## 📝 Instalação Manual (se preferir)

### Passo 1: Localize seu profile

```powershell
# Ver onde está o profile
$PROFILE

# Exemplo de output:
# C:\Users\SeuNome\Documents\PowerShell\Microsoft.PowerShell_profile.ps1
```

### Passo 2: Abra o profile no editor

```powershell
# Criar diretório se não existir
$profileDir = Split-Path $PROFILE -Parent
New-Item -ItemType Directory -Path $profileDir -Force

# Abrir no editor (escolha um):
notepad $PROFILE       # Bloco de Notas
code $PROFILE          # VS Code
notepad++ $PROFILE     # Notepad++
```

### Passo 3: Copie o conteúdo

1. Abra o arquivo `powershell-profile.ps1` deste repositório
2. **Copie TODO o conteúdo**
3. **Cole** no arquivo `$PROFILE` que você abriu
4. **Configure o username WSL** (veja instruções acima)
5. **Salve** (Ctrl+S)

### Passo 4: Configure ExecutionPolicy

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Passo 5: Recarregue

```powershell
. $PROFILE
```

---

## 🔍 Localização do Profile por Sistema

O caminho do `$PROFILE` varia conforme sua configuração:

**Windows PowerShell 5.1:**
```
C:\Users\<username>\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1
```

**PowerShell Core 7+ (Windows):**
```
C:\Users\<username>\Documents\PowerShell\Microsoft.PowerShell_profile.ps1
```

**PowerShell Core 7+ (Linux/macOS):**
```
~/.config/powershell/Microsoft.PowerShell_profile.ps1
```

**Descobrir automaticamente:**
```powershell
# Sempre mostra o caminho correto para seu sistema
$PROFILE
```

---

## 🛠️ Troubleshooting

### Erro: "Execution of scripts is disabled"

**Causa:** ExecutionPolicy restritivo.

**Solução:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Erro: "wsl: command not found"

**Causa:** WSL não instalado ou não no PATH.

**Solução:**
1. Verifique se WSL está instalado: `wsl --version`
2. Se não estiver, siga o guia de instalação WSL

### Comandos não funcionam (scc, gcp, etc)

**Causa:** Profile não foi carregado.

**Solução:**
```powershell
# Recarregar profile
. $PROFILE

# Verificar se aliases existem
Get-Alias scc
Get-Alias gcp
```

### Erro: "Username not found in WSL"

**Causa:** Username configurado no profile está errado.

**Solução:**
1. No WSL: `whoami`
2. Abra o profile: `notepad $PROFILE`
3. Corrija a linha `$wslUser = "..."`
4. Salve e recarregue: `. $PROFILE`

---

## 📚 Comandos Disponíveis

| Comando | Alias | Descrição |
|---------|-------|-----------|
| `scc` | `Start-Claude` | Inicia Claude Code no projeto WSL |
| `gcp` | `Enter-ClaudeProject` | Abre bash WSL no projeto |
| `gsync` | `Sync-Git` | Executa git pull + git status |
| `cstatus` | `Get-ClaudeStatus` | Mostra status do ambiente (Git, Node, WSL) |
| `claude <args>` | - | Executa Claude Code via WSL (wrapper) |

**Exemplos:**

```powershell
# Iniciar Claude Code
scc

# Abrir terminal WSL no projeto
gcp

# Ver status
cstatus

# Git sync
gsync

# Executar Claude Code com argumentos
claude --help
claude --version
```

---

## ℹ️ Informações Adicionais

**Repositório:** https://github.com/PedroGiudice/Claude-Code-Projetos

**Arquivos:**
- `powershell-profile.ps1` - Profile customizado (conteúdo)
- `install-powershell-profile.ps1` - Instalador automático
- `POWERSHELL-PROFILE-SETUP.md` - Este guia

**Compatibilidade:**
- ✅ Windows 10/11
- ✅ PowerShell 5.1+
- ✅ PowerShell Core 7+
- ✅ WSL2 com Ubuntu

---

**Última atualização:** 2025-11-17
**Versão:** 1.0
