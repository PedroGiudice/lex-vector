# Plano: Script Unificado de Correção de Permissões Windows

## Objetivo
Criar script PowerShell que detecte e corrija **todos** os problemas de permissão no PC doméstico Windows, incluindo:
- Ownership incorreto (arquivos de outro usuário)
- Permissões NTFS inadequadas
- PATH corrompido
- EPERM em lock files
- Problemas de ambiente semi-corporativo

## Problemas Identificados (da Documentação)

### 1. EPERM em Lock Files (CRÍTICO)
**Fonte:** DISASTER_HISTORY.md DIA 4, WINDOWS_PERMISSION_FIX.md

**Sintoma:**
- Claude Code CLI congela ao iniciar
- Logs mostram `Failed to save config with lock: EPERM`
- Loop infinito de retry sem backoff

**Causa:**
- Windows Defender bloqueia criação de `.claude.json.lock`
- Permissões NTFS insuficientes em `$env:USERPROFILE\.claude.json`
- Ownership incorreto do arquivo

**Correção necessária:**
- Takeown + icacls para garantir propriedade
- ACLs com FullControl para usuário atual
- Exclusão Windows Defender (opcional, requer admin)

### 2. PATH Corrompido (ALTO)
**Fonte:** DISASTER_HISTORY.md DIA 2, CLAUDE.md

**Sintoma:**
- Claude Code trava
- VSCode abre arquivos de plugins automaticamente
- Node.js executáveis não encontrados ou versão errada

**Causa:**
- PATH contém `C:\Users\<usuario>` INTEIRO ao invés de apenas `.local\bin`
- Instalações globais contaminam ambiente

**Correção necessária:**
- Remover `C:\Users\<usuario>` do PATH
- Adicionar APENAS `C:\Users\<usuario>\.local\bin` (se não existir)
- Validar que diretórios no PATH existem

### 3. Ownership Incorreto (NOVO - ALTO)
**Fonte:** Input do usuário

**Sintoma:**
- PC de casa configurado pela mesma pessoa do trabalho
- Arquivos podem ter proprietário diferente do usuário atual
- Operações falham com "Access Denied" mesmo com permissões aparentemente corretas

**Causa:**
- Setup inicial feito por outro usuário (ex: admin corporativo)
- Arquivos em `C:\claude-work\repos\` com owner errado
- Arquivos em `$env:USERPROFILE\.claude*` com owner errado

**Correção necessária:**
- `takeown /f <arquivo> /r /d y` para diretórios críticos
- `icacls <arquivo> /setowner <usuario_atual>` como alternativa
- Recursivo em:
  - `C:\claude-work\repos\Claude-Code-Projetos\`
  - `$env:USERPROFILE\.claude.json`
  - `$env:USERPROFILE\.claude\` (se existir)
  - `$env:USERPROFILE\.local\` (se existir)

### 4. Permissões NTFS Inadequadas (MÉDIO)
**Fonte:** fix-claude-permissions.ps1

**Sintoma:**
- "Access Denied" ao ler/escrever arquivos
- EPERM ao criar diretórios temporários

**Causa:**
- ACLs restritivas herdadas de ambiente corporativo
- Usuário atual não tem FullControl

**Correção necessária:**
- `icacls <arquivo> /grant <usuario>:F` (F = FullControl)
- Aplicar recursivamente em diretórios críticos

### 5. Stale Locks (BAIXO)
**Fonte:** fix-claude-permissions.ps1

**Sintoma:**
- Claude Code não inicia (falha silenciosa)
- Locks antigos de sessões crashed

**Causa:**
- Arquivos `.claude.json.lock`, `.claude.json.tmp.*` não foram limpos

**Correção necessária:**
- Remover todos `.claude.json.*` em `$env:USERPROFILE`

### 6. Windows Defender Bloqueios (MÉDIO)
**Fonte:** diagnose-corporate-env.ps1, WINDOWS_PERMISSION_FIX.md

**Sintoma:**
- Delays intermitentes
- EPERM ocasional

**Causa:**
- Real-time protection escaneia `.claude.json` durante write operations

**Correção necessária:**
- `Add-MpPreference -ExclusionPath "$env:USERPROFILE\.claude.json"`
- Requer privilégios admin

## Estrutura do Script

### Nome: `fix-home-windows-permissions.ps1`

### Parâmetros

```powershell
param(
    [switch]$FixOwnership,           # Corrige ownership (takeown)
    [switch]$FixPermissions,         # Corrige ACLs
    [switch]$FixPATH,                # Limpa PATH corrompido
    [switch]$AddDefenderExclusion,   # Adiciona exclusão Defender (requer admin)
    [switch]$All,                    # Executa todas correções acima
    [switch]$DiagnoseOnly,           # Apenas diagnóstico, sem correções
    [switch]$Verbose                 # Output detalhado
)
```

### Fluxo de Execução

```
1. DETECÇÃO DE AMBIENTE
   ├─ Test-AdminPrivileges
   ├─ Get-CurrentUser
   ├─ Detect-CorporateEnvironment (score-based)
   └─ Display-EnvironmentSummary

2. DIAGNÓSTICO COMPLETO
   ├─ Test-FileOwnership (arquivos críticos)
   │  ├─ $env:USERPROFILE\.claude.json
   │  ├─ $env:USERPROFILE\.claude\
   │  ├─ C:\claude-work\repos\Claude-Code-Projetos\
   │  └─ $env:USERPROFILE\.local\
   │
   ├─ Test-FilePermissions (ACLs)
   │  └─ Mesmos arquivos acima
   │
   ├─ Test-PATHIntegrity
   │  ├─ Detecta C:\Users\<user> inteiro no PATH
   │  ├─ Valida .local\bin está presente
   │  └─ Remove entradas inválidas (diretórios não existentes)
   │
   ├─ Test-LockCreation
   │  └─ Tenta criar .claude.json.test-lock
   │
   ├─ Find-StaleLocks
   │  └─ Lista .claude.json.* files
   │
   └─ Test-DefenderStatus
      └─ Verifica exclusões existentes

3. EXIBIR DIAGNÓSTICO
   ├─ Tabela com problemas encontrados
   ├─ Severity (CRÍTICO/ALTO/MÉDIO/BAIXO)
   └─ Recomendações de correção

4. CORREÇÃO (se não for -DiagnoseOnly)
   ├─ Se -FixOwnership ou -All:
   │  ├─ Takeown de arquivos com owner incorreto
   │  └─ icacls /setowner se takeown falhar
   │
   ├─ Se -FixPermissions ou -All:
   │  ├─ icacls /grant <user>:F para cada arquivo
   │  └─ Herança desabilitada em arquivos críticos
   │
   ├─ Se -FixPATH ou -All:
   │  ├─ Backup PATH atual
   │  ├─ Remove C:\Users\<user> se presente
   │  ├─ Adiciona C:\Users\<user>\.local\bin se não existir
   │  └─ Remove entradas inválidas
   │
   ├─ Sempre (se -All):
   │  └─ Clear-StaleLocks
   │
   └─ Se -AddDefenderExclusion:
      └─ Add-MpPreference (requer admin)

5. VALIDAÇÃO PÓS-CORREÇÃO
   ├─ Re-run diagnóstico
   ├─ Test-LockCreation (CRÍTICO)
   ├─ Compare before/after
   └─ Display-SuccessSummary

6. RELATÓRIO FINAL
   ├─ Problemas encontrados: X
   ├─ Problemas corrigidos: Y
   ├─ Problemas pendentes: Z
   └─ Próximos passos (se admin necessário)
```

### Funções Principais

#### Diagnóstico

```powershell
function Get-FileOwnerInfo {
    param([string]$Path)
    # Retorna: Owner, IsCurrentUser, NeedsFixing
}

function Test-FileOwnership {
    # Verifica ownership de todos arquivos críticos
    # Retorna array de problemas encontrados
}

function Test-FilePermissions {
    # Verifica ACLs (FullControl para usuário atual?)
    # Retorna array de problemas encontrados
}

function Test-PATHIntegrity {
    # Analisa PATH
    # Retorna: HasCorruption, InvalidEntries, MissingLocalBin
}

function Test-LockCreation {
    # Tenta criar .claude.json.test-lock
    # Retorna: Success/Failure + Error details
}

function Find-StaleLocks {
    # Lista .claude.json.* files
    # Retorna array de locks antigos
}

function Detect-CorporateEnvironment {
    # Reutiliza lógica de diagnose-corporate-env.ps1
    # Retorna: Score, Classification, Indicators
}
```

#### Correção

```powershell
function Fix-FileOwnership {
    param(
        [string]$Path,
        [string]$NewOwner = $env:USERNAME
    )
    # Método 1: takeown.exe
    # Método 2: icacls /setowner (fallback)
    # Retorna: Success/Failure
}

function Fix-FilePermissions {
    param([string]$Path)
    # icacls /grant <user>:F
    # Retorna: Success/Failure
}

function Fix-PATHVariable {
    # Backup PATH
    # Remove C:\Users\<user> (se existe)
    # Adiciona .local\bin (se não existe)
    # Remove entradas inválidas
    # Retorna: ChangesMade, BackupPath
}

function Clear-StaleLocks {
    # Remove .claude.json.* files
    # Retorna: RemovedCount
}

function Add-DefenderExclusion {
    # Add-MpPreference (requer admin)
    # Retorna: Success/Failure
}
```

#### Utilidades

```powershell
function Test-AdminPrivileges { }
function Write-Status { }  # Colorized output
function Write-DiagnosticTable { }
function Write-SuccessSummary { }
function Backup-EnvironmentVariable { }
```

## Locais Críticos a Verificar

### Arquivos Claude Code

```powershell
$ClaudeFiles = @(
    "$env:USERPROFILE\.claude.json",
    "$env:USERPROFILE\.claude",  # Directory (se existir)
    "$env:USERPROFILE\.local"    # Directory (se existir)
)
```

### Diretórios do Projeto

```powershell
# Detectar dinamicamente (pode estar em qualquer lugar)
$ProjectRoot = (Get-Location).Path
if ($ProjectRoot -match 'Claude-Code-Projetos') {
    # Verificar ownership recursivo
}
```

### PATH Específico

```powershell
$PATHEntriesToCheck = @(
    "$env:USERPROFILE",           # DEVE SER REMOVIDO (se presente)
    "$env:USERPROFILE\.local\bin" # DEVE ESTAR PRESENTE
)
```

## Casos de Uso

### Caso 1: Diagnóstico Rápido

```powershell
.\fix-home-windows-permissions.ps1 -DiagnoseOnly
```

**Output esperado:**
- Tabela com problemas encontrados
- Score corporativo
- Recomendações

### Caso 2: Correção Completa (Sem Admin)

```powershell
.\fix-home-windows-permissions.ps1 -All
```

**Executa:**
- Ownership fix
- Permissions fix
- PATH cleanup
- Stale locks removal

**Pula:**
- Defender exclusion (requer admin)

### Caso 3: Correção Completa (Com Admin)

```powershell
# PowerShell como Administrador
.\fix-home-windows-permissions.ps1 -All -AddDefenderExclusion
```

**Executa tudo, incluindo:**
- Defender exclusion

### Caso 4: Apenas Ownership

```powershell
.\fix-home-windows-permissions.ps1 -FixOwnership
```

**Útil quando:**
- Sabe que problema é ownership específico
- Quer evitar mudanças no PATH

### Caso 5: Apenas PATH

```powershell
.\fix-home-windows-permissions.ps1 -FixPATH
```

**Útil quando:**
- Claude Code trava (sintoma de PATH corrompido)
- Não quer alterar permissões de arquivos

## Compatibilidade

- **PowerShell:** 5.1+ (Desktop)
- **OS:** Windows 10/11
- **Privilégios:** Funciona sem admin (exceto Defender exclusion)
- **Encoding:** UTF-8 com BOM (compatibilidade Windows)
- **Sintaxe:** 100% PowerShell nativo (sem bashismos)

## Requisitos de Genericidade

✅ **ZERO hardcoded paths** - Usa apenas:
- `$env:USERPROFILE`
- `$env:USERNAME`
- `(Get-Location).Path` (dinâmico)
- `Join-Path` (cross-subdirectory)

✅ **ZERO hardcoded usernames** - Detecta automaticamente

✅ **ZERO hardcoded drives** - Funciona em qualquer drive

## Validação Pós-Implementação

1. Executar em ambiente limpo (VM)
2. Executar em ambiente com ownership corrompido
3. Executar em ambiente com PATH corrompido
4. Verificar que não quebra em ambiente já correto
5. Testar com/sem privilégios admin

## Próximos Passos

1. ✅ Planejamento completo (este documento)
2. ⏳ Implementar script PowerShell
3. ⏳ Testar sintaxe (sem execução)
4. ⏳ Gerar documentação de uso
5. ⏳ Commit + push para branch

---

**Criado:** 2025-11-15
**Versão:** 1.0
**Status:** PLANEJAMENTO COMPLETO
