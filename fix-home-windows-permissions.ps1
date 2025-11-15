#Requires -Version 5.1
<#
.SYNOPSIS
    Correção unificada de permissões Windows para Claude Code (ambiente doméstico)

.DESCRIPTION
    Detecta e corrige TODOS os problemas de permissão em PC Windows doméstico:
    - Ownership incorreto (arquivos de outro usuário)
    - Permissões NTFS inadequadas
    - PATH corrompido
    - EPERM em lock files (.claude.json.lock)
    - Stale locks de sessões anteriores
    - Windows Defender bloqueando operações

    100% genérico - sem hardcoded paths, usa variáveis de ambiente.

.NOTES
    Author: Claude Code (via Legal-Braniac)
    Date: 2025-11-15
    Version: 1.0
    Related: DISASTER_HISTORY.md, CLAUDE.md, WINDOWS_PERMISSION_FIX.md

.PARAMETER FixOwnership
    Corrige ownership de arquivos críticos (takeown + icacls)

.PARAMETER FixPermissions
    Corrige ACLs (permissões NTFS) para FullControl do usuário atual

.PARAMETER FixPATH
    Limpa PATH corrompido (remove C:\Users\<user>, adiciona .local\bin)

.PARAMETER AddDefenderExclusion
    Adiciona exclusão Windows Defender (requer Admin)

.PARAMETER All
    Executa todas correções acima (exceto Defender se não for Admin)

.PARAMETER DiagnoseOnly
    Apenas diagnóstico, sem correções

.PARAMETER Verbose
    Output detalhado de diagnóstico

.EXAMPLE
    .\fix-home-windows-permissions.ps1 -DiagnoseOnly
    Apenas diagnóstico (não faz alterações)

.EXAMPLE
    .\fix-home-windows-permissions.ps1 -All
    Correção completa (sem Admin)

.EXAMPLE
    .\fix-home-windows-permissions.ps1 -All -AddDefenderExclusion
    Correção completa + Defender (REQUER Admin)

.EXAMPLE
    .\fix-home-windows-permissions.ps1 -FixOwnership -FixPermissions
    Apenas ownership e permissões
#>

param(
    [switch]$FixOwnership,
    [switch]$FixPermissions,
    [switch]$FixPATH,
    [switch]$AddDefenderExclusion,
    [switch]$All,
    [switch]$DiagnoseOnly,
    [switch]$VerboseOutput
)

# =============================================================================
# CONFIGURAÇÃO GLOBAL
# =============================================================================

$ErrorActionPreference = 'Continue'
$Script:DiagnosticResults = @{}
$Script:FixResults = @{}
$Script:CurrentUser = $env:USERNAME
$Script:UserProfile = $env:USERPROFILE

# Arquivos críticos (100% genéricos - sem hardcoded paths)
$Script:CriticalFiles = @(
    (Join-Path $Script:UserProfile ".claude.json"),
    (Join-Path $Script:UserProfile ".claude"),
    (Join-Path $Script:UserProfile ".local")
)

# Detectar projeto atual (dinâmico)
$Script:ProjectRoot = (Get-Location).Path
$Script:IsInClaudeProject = $Script:ProjectRoot -match 'Claude-Code-Projetos'

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

function Write-Status {
    param(
        [string]$Message,
        [ValidateSet('Info', 'Success', 'Warning', 'Error', 'Section')]
        [string]$Level = 'Info'
    )

    $colors = @{
        'Info'    = 'Cyan'
        'Success' = 'Green'
        'Warning' = 'Yellow'
        'Error'   = 'Red'
        'Section' = 'Magenta'
    }

    $symbols = @{
        'Info'    = '[i]'
        'Success' = '[✓]'
        'Warning' = '[!]'
        'Error'   = '[✗]'
        'Section' = '═══'
    }

    if ($Level -eq 'Section') {
        Write-Host "`n$($symbols[$Level]) " -ForegroundColor $colors[$Level] -NoNewline
        Write-Host $Message -ForegroundColor $colors[$Level]
        Write-Host ("═" * ($Message.Length + 5)) -ForegroundColor $colors[$Level]
    } else {
        Write-Host "$($symbols[$Level]) " -ForegroundColor $colors[$Level] -NoNewline
        Write-Host $Message
    }
}

function Test-AdminPrivileges {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-BooleanIcon {
    param([bool]$Value)
    return if ($Value) { "✓" } else { "✗" }
}

function Write-DiagnosticTable {
    param($Results)

    Write-Host "`n╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                      RESULTADO DO DIAGNÓSTICO                     ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

    foreach ($category in $Results.Keys) {
        $data = $Results[$category]
        Write-Host "[$category]" -ForegroundColor Yellow

        foreach ($key in $data.Keys) {
            $value = $data[$key]

            if ($value -is [bool]) {
                $icon = Get-BooleanIcon $value
                $color = if ($value) { "Green" } else { "Red" }
                Write-Host "  $key`: " -NoNewline
                Write-Host $icon -ForegroundColor $color
            } elseif ($value -is [array]) {
                Write-Host "  $key`: $($value.Count) itens"
                if ($VerboseOutput -and $value.Count -gt 0) {
                    $value | ForEach-Object { Write-Host "    - $_" -ForegroundColor Gray }
                }
            } else {
                Write-Host "  $key`: $value"
            }
        }
        Write-Host ""
    }
}

# =============================================================================
# DIAGNÓSTICO - OWNERSHIP
# =============================================================================

function Get-FileOwnerInfo {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return @{
            Exists = $false
            Owner = $null
            IsCurrentUser = $false
            NeedsFixing = $false
        }
    }

    try {
        $acl = Get-Acl $Path -ErrorAction Stop
        $owner = $acl.Owner

        # Extrair username (pode vir como DOMAIN\User ou MACHINE\User)
        $ownerUsername = if ($owner -match '\\') {
            $owner.Split('\')[1]
        } else {
            $owner
        }

        $isCurrentUser = $ownerUsername -eq $Script:CurrentUser

        return @{
            Exists = $true
            Owner = $owner
            OwnerUsername = $ownerUsername
            IsCurrentUser = $isCurrentUser
            NeedsFixing = -not $isCurrentUser
        }
    } catch {
        return @{
            Exists = $true
            Owner = "ERRO: $_"
            IsCurrentUser = $false
            NeedsFixing = $true
        }
    }
}

function Test-FileOwnership {
    Write-Status "Verificando ownership de arquivos críticos..." -Level Info

    $ownershipIssues = @()

    foreach ($file in $Script:CriticalFiles) {
        $info = Get-FileOwnerInfo -Path $file

        if ($info.Exists -and $info.NeedsFixing) {
            $ownershipIssues += @{
                Path = $file
                CurrentOwner = $info.Owner
                ExpectedOwner = $Script:CurrentUser
            }

            Write-Status "Owner incorreto: $file" -Level Warning
            Write-Status "  Atual: $($info.Owner) | Esperado: $Script:CurrentUser" -Level Info
        } elseif ($info.Exists) {
            Write-Status "Owner correto: $file ($($info.Owner))" -Level Success
        } else {
            Write-Status "Não existe: $file (será criado se necessário)" -Level Info
        }
    }

    # Verificar projeto Claude Code (se estamos dentro dele)
    if ($Script:IsInClaudeProject) {
        Write-Status "Verificando ownership do projeto: $Script:ProjectRoot" -Level Info

        $projectInfo = Get-FileOwnerInfo -Path $Script:ProjectRoot
        if ($projectInfo.Exists -and $projectInfo.NeedsFixing) {
            $ownershipIssues += @{
                Path = $Script:ProjectRoot
                CurrentOwner = $projectInfo.Owner
                ExpectedOwner = $Script:CurrentUser
                IsDirectory = $true
            }
            Write-Status "Owner incorreto no projeto raiz!" -Level Error
        }
    }

    $Script:DiagnosticResults['Ownership'] = @{
        TotalChecked = $Script:CriticalFiles.Count
        IssuesFound = $ownershipIssues.Count
        AllCorrect = $ownershipIssues.Count -eq 0
        Issues = $ownershipIssues
    }

    return $ownershipIssues
}

# =============================================================================
# DIAGNÓSTICO - PERMISSÕES NTFS
# =============================================================================

function Test-FilePermissions {
    Write-Status "Verificando permissões NTFS..." -Level Info

    $permissionIssues = @()

    foreach ($file in $Script:CriticalFiles) {
        if (-not (Test-Path $file)) {
            continue
        }

        try {
            $acl = Get-Acl $file -ErrorAction Stop
            $hasFullControl = $false

            foreach ($access in $acl.Access) {
                if ($access.IdentityReference -match $Script:CurrentUser) {
                    if ($access.FileSystemRights -match "FullControl") {
                        $hasFullControl = $true
                        break
                    }
                }
            }

            if (-not $hasFullControl) {
                $permissionIssues += @{
                    Path = $file
                    Issue = "FullControl ausente para $Script:CurrentUser"
                }
                Write-Status "Permissões insuficientes: $file" -Level Warning
            } else {
                Write-Status "Permissões corretas: $file" -Level Success
            }

        } catch {
            $permissionIssues += @{
                Path = $file
                Issue = "Erro ao ler ACL: $_"
            }
            Write-Status "Erro ao verificar: $file" -Level Error
        }
    }

    $Script:DiagnosticResults['Permissions'] = @{
        TotalChecked = $Script:CriticalFiles.Count
        IssuesFound = $permissionIssues.Count
        AllCorrect = $permissionIssues.Count -eq 0
        Issues = $permissionIssues
    }

    return $permissionIssues
}

# =============================================================================
# DIAGNÓSTICO - PATH
# =============================================================================

function Test-PATHIntegrity {
    Write-Status "Analisando variável PATH..." -Level Info

    $currentPATH = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $pathEntries = $currentPATH -split ';' | Where-Object { $_ -ne '' }

    $issues = @()
    $hasUserProfileRoot = $false
    $hasLocalBin = $false
    $invalidEntries = @()

    foreach ($entry in $pathEntries) {
        # Problema 1: C:\Users\<user> INTEIRO (sem subdir)
        if ($entry -eq $Script:UserProfile) {
            $hasUserProfileRoot = $true
            $issues += "PATH contém diretório home inteiro: $entry"
            Write-Status "CRÍTICO: PATH contém $entry (deve ser removido!)" -Level Error
        }

        # Verificar .local\bin
        $localBinPath = Join-Path $Script:UserProfile ".local\bin"
        if ($entry -eq $localBinPath) {
            $hasLocalBin = $true
        }

        # Problema 2: Entradas inválidas (diretório não existe)
        if ($entry -match [regex]::Escape($Script:UserProfile)) {
            if (-not (Test-Path $entry)) {
                $invalidEntries += $entry
                Write-Status "Entrada inválida (não existe): $entry" -Level Warning
            }
        }
    }

    if (-not $hasLocalBin) {
        $issues += ".local\bin ausente no PATH"
        Write-Status ".local\bin não está no PATH (será adicionado)" -Level Warning
    }

    $Script:DiagnosticResults['PATH'] = @{
        TotalEntries = $pathEntries.Count
        HasUserProfileRoot = $hasUserProfileRoot
        HasLocalBin = $hasLocalBin
        InvalidEntries = $invalidEntries
        IssuesFound = $issues.Count
        IsCorrupted = $hasUserProfileRoot -or (-not $hasLocalBin)
        Issues = $issues
    }

    return $issues
}

# =============================================================================
# DIAGNÓSTICO - LOCK FILES
# =============================================================================

function Test-LockCreation {
    Write-Status "Testando criação de lock files..." -Level Info

    $claudeConfig = Join-Path $Script:UserProfile ".claude.json"
    $testLock = "$claudeConfig.test-lock"

    try {
        New-Item -ItemType Directory -Path $testLock -ErrorAction Stop | Out-Null
        Remove-Item $testLock -Force -ErrorAction Stop

        Write-Status "Lock creation test: PASSOU" -Level Success

        $Script:DiagnosticResults['LockCreation'] = @{
            CanCreateLock = $true
            HasEPERMIssue = $false
            TestPassed = $true
        }

        return $true
    } catch {
        Write-Status "Lock creation test: FALHOU" -Level Error
        Write-Status "  Erro: $_" -Level Error

        $Script:DiagnosticResults['LockCreation'] = @{
            CanCreateLock = $false
            HasEPERMIssue = $_.Exception.Message -match "EPERM|denied|access"
            Error = $_.Exception.Message
            TestPassed = $false
        }

        return $false
    }
}

function Find-StaleLocks {
    Write-Status "Procurando stale locks..." -Level Info

    $claudeConfig = Join-Path $Script:UserProfile ".claude.json"
    $configDir = Split-Path $claudeConfig -Parent

    try {
        $locks = Get-ChildItem -Path $configDir -Filter ".claude.json.*" -ErrorAction SilentlyContinue

        if ($locks.Count -gt 0) {
            Write-Status "Encontrados $($locks.Count) stale lock(s)" -Level Warning
            foreach ($lock in $locks) {
                Write-Status "  - $($lock.Name)" -Level Info
            }
        } else {
            Write-Status "Nenhum stale lock encontrado" -Level Success
        }

        $Script:DiagnosticResults['StaleLocks'] = @{
            Found = $locks.Count
            Locks = $locks
        }

        return $locks
    } catch {
        $Script:DiagnosticResults['StaleLocks'] = @{
            Found = 0
            Error = $_
        }
        return @()
    }
}

# =============================================================================
# DIAGNÓSTICO - WINDOWS DEFENDER
# =============================================================================

function Test-DefenderStatus {
    Write-Status "Verificando Windows Defender..." -Level Info

    try {
        $defender = Get-MpComputerStatus -ErrorAction Stop
        $prefs = Get-MpPreference -ErrorAction Stop

        $claudeConfig = Join-Path $Script:UserProfile ".claude.json"
        $isExcluded = $prefs.ExclusionPath -contains $claudeConfig

        Write-Status "Defender ativo: $($defender.AntivirusEnabled)" -Level Info
        Write-Status "Real-time protection: $($defender.RealTimeProtectionEnabled)" -Level Info
        Write-Status ".claude.json em exclusões: $(Get-BooleanIcon $isExcluded)" -Level $(if ($isExcluded) { "Success" } else { "Warning" })

        $Script:DiagnosticResults['Defender'] = @{
            Enabled = $defender.AntivirusEnabled
            RealTimeProtection = $defender.RealTimeProtectionEnabled
            ClaudeConfigExcluded = $isExcluded
            NeedsExclusion = $defender.RealTimeProtectionEnabled -and (-not $isExcluded)
        }

    } catch {
        Write-Status "Não foi possível verificar Defender: $_" -Level Warning
        $Script:DiagnosticResults['Defender'] = @{
            Enabled = $false
            Error = $_
        }
    }
}

# =============================================================================
# CORREÇÃO - OWNERSHIP
# =============================================================================

function Fix-FileOwnership {
    param(
        [string]$Path,
        [bool]$Recursive = $false
    )

    Write-Status "Corrigindo ownership: $Path" -Level Info

    try {
        # Método 1: takeown.exe (preferido)
        $takeownArgs = @("/F", "`"$Path`"")
        if ($Recursive) {
            $takeownArgs += @("/R", "/D", "Y")
        }

        $result = & takeown.exe $takeownArgs 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Status "  takeown.exe: Sucesso" -Level Success

            # Agora garantir que ACLs também estejam corretos
            $icaclsArgs = @("`"$Path`"", "/grant", "$($Script:CurrentUser):F")
            if ($Recursive) {
                $icaclsArgs += "/T"
            }

            & icacls.exe $icaclsArgs | Out-Null

            return $true
        } else {
            Write-Status "  takeown.exe falhou: $result" -Level Warning

            # Método 2: icacls /setowner (fallback)
            $icaclsArgs = @("`"$Path`"", "/setowner", $Script:CurrentUser)
            if ($Recursive) {
                $icaclsArgs += "/T"
            }

            & icacls.exe $icaclsArgs | Out-Null

            if ($LASTEXITCODE -eq 0) {
                Write-Status "  icacls /setowner: Sucesso" -Level Success
                return $true
            } else {
                Write-Status "  icacls /setowner também falhou" -Level Error
                return $false
            }
        }

    } catch {
        Write-Status "  Erro ao corrigir ownership: $_" -Level Error
        return $false
    }
}

function Repair-AllOwnership {
    Write-Status "CORREÇÃO DE OWNERSHIP" -Level Section

    $issues = $Script:DiagnosticResults['Ownership'].Issues
    $fixed = 0
    $failed = 0

    foreach ($issue in $issues) {
        $isDir = Test-Path $issue.Path -PathType Container
        $success = Fix-FileOwnership -Path $issue.Path -Recursive $isDir

        if ($success) {
            $fixed++
        } else {
            $failed++
        }
    }

    $Script:FixResults['Ownership'] = @{
        Attempted = $issues.Count
        Fixed = $fixed
        Failed = $failed
    }

    Write-Status "Ownership corrigido: $fixed/$($issues.Count)" -Level $(if ($failed -eq 0) { "Success" } else { "Warning" })
}

# =============================================================================
# CORREÇÃO - PERMISSÕES
# =============================================================================

function Fix-FilePermissions {
    param([string]$Path)

    Write-Status "Corrigindo permissões: $Path" -Level Info

    try {
        # Garantir FullControl para usuário atual
        $icaclsArgs = @("`"$Path`"", "/grant", "$($Script:CurrentUser):F")

        if (Test-Path $Path -PathType Container) {
            $icaclsArgs += "/T"  # Recursivo para diretórios
        }

        & icacls.exe $icaclsArgs | Out-Null

        if ($LASTEXITCODE -eq 0) {
            Write-Status "  icacls: Sucesso" -Level Success
            return $true
        } else {
            Write-Status "  icacls falhou" -Level Error
            return $false
        }

    } catch {
        Write-Status "  Erro ao corrigir permissões: $_" -Level Error
        return $false
    }
}

function Repair-AllPermissions {
    Write-Status "CORREÇÃO DE PERMISSÕES" -Level Section

    $issues = $Script:DiagnosticResults['Permissions'].Issues
    $fixed = 0
    $failed = 0

    foreach ($issue in $issues) {
        $success = Fix-FilePermissions -Path $issue.Path

        if ($success) {
            $fixed++
        } else {
            $failed++
        }
    }

    $Script:FixResults['Permissions'] = @{
        Attempted = $issues.Count
        Fixed = $fixed
        Failed = $failed
    }

    Write-Status "Permissões corrigidas: $fixed/$($issues.Count)" -Level $(if ($failed -eq 0) { "Success" } else { "Warning" })
}

# =============================================================================
# CORREÇÃO - PATH
# =============================================================================

function Repair-PATHVariable {
    Write-Status "CORREÇÃO DO PATH" -Level Section

    $currentPATH = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $pathEntries = $currentPATH -split ';' | Where-Object { $_ -ne '' }

    # Backup
    $backupPath = Join-Path $env:TEMP "PATH_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
    $currentPATH | Out-File $backupPath
    Write-Status "Backup do PATH: $backupPath" -Level Info

    # Filtrar entradas
    $newEntries = @()
    $removed = @()

    foreach ($entry in $pathEntries) {
        # Remover C:\Users\<user> (raiz do perfil)
        if ($entry -eq $Script:UserProfile) {
            $removed += $entry
            Write-Status "Removido: $entry" -Level Warning
            continue
        }

        # Remover entradas inválidas (não existem)
        if ($entry -match [regex]::Escape($Script:UserProfile)) {
            if (-not (Test-Path $entry)) {
                $removed += $entry
                Write-Status "Removida entrada inválida: $entry" -Level Warning
                continue
            }
        }

        $newEntries += $entry
    }

    # Adicionar .local\bin se não existir
    $localBinPath = Join-Path $Script:UserProfile ".local\bin"
    if ($newEntries -notcontains $localBinPath) {
        # Criar diretório se não existir
        if (-not (Test-Path $localBinPath)) {
            New-Item -ItemType Directory -Path $localBinPath -Force | Out-Null
            Write-Status "Criado diretório: $localBinPath" -Level Success
        }

        $newEntries += $localBinPath
        Write-Status "Adicionado ao PATH: $localBinPath" -Level Success
    }

    # Aplicar novo PATH
    $newPATH = $newEntries -join ';'
    [System.Environment]::SetEnvironmentVariable("Path", $newPATH, "User")

    Write-Status "PATH atualizado com sucesso!" -Level Success
    Write-Status "  Entradas removidas: $($removed.Count)" -Level Info
    Write-Status "  Backup salvo em: $backupPath" -Level Info

    $Script:FixResults['PATH'] = @{
        BackupLocation = $backupPath
        EntriesRemoved = $removed.Count
        RemovedEntries = $removed
        LocalBinAdded = $newEntries -contains $localBinPath
    }
}

# =============================================================================
# CORREÇÃO - STALE LOCKS
# =============================================================================

function Clear-AllStaleLocks {
    Write-Status "LIMPEZA DE STALE LOCKS" -Level Section

    $locks = $Script:DiagnosticResults['StaleLocks'].Locks
    $removed = 0
    $failed = 0

    foreach ($lock in $locks) {
        try {
            Remove-Item $lock.FullName -Force -Recurse -ErrorAction Stop
            Write-Status "Removido: $($lock.Name)" -Level Success
            $removed++
        } catch {
            Write-Status "Falha ao remover $($lock.Name): $_" -Level Error
            $failed++
        }
    }

    $Script:FixResults['StaleLocks'] = @{
        Attempted = $locks.Count
        Removed = $removed
        Failed = $failed
    }

    Write-Status "Locks removidos: $removed/$($locks.Count)" -Level $(if ($failed -eq 0) { "Success" } else { "Warning" })
}

# =============================================================================
# CORREÇÃO - DEFENDER
# =============================================================================

function Add-ClaudeDefenderExclusion {
    Write-Status "ADICIONANDO EXCLUSÃO WINDOWS DEFENDER" -Level Section

    if (-not (Test-AdminPrivileges)) {
        Write-Status "Privilégios de Admin necessários (pulando)" -Level Warning
        $Script:FixResults['Defender'] = @{
            Added = $false
            Reason = "Sem privilégios Admin"
        }
        return
    }

    try {
        $claudeConfig = Join-Path $Script:UserProfile ".claude.json"
        Add-MpPreference -ExclusionPath $claudeConfig -ErrorAction Stop
        Write-Status "Exclusão adicionada: $claudeConfig" -Level Success

        $Script:FixResults['Defender'] = @{
            Added = $true
            Path = $claudeConfig
        }

    } catch {
        Write-Status "Falha ao adicionar exclusão: $_" -Level Error
        $Script:FixResults['Defender'] = @{
            Added = $false
            Error = $_
        }
    }
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

function Main {
    Write-Host "`n╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                                                                   ║" -ForegroundColor Cyan
    Write-Host "║        CORREÇÃO DE PERMISSÕES WINDOWS - CLAUDE CODE               ║" -ForegroundColor Cyan
    Write-Host "║        Ambiente Doméstico (Home PC)                               ║" -ForegroundColor Cyan
    Write-Host "║                                                                   ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

    # Detecção de ambiente
    Write-Status "DETECÇÃO DE AMBIENTE" -Level Section
    Write-Status "Usuário: $Script:CurrentUser" -Level Info
    Write-Status "Profile: $Script:UserProfile" -Level Info
    Write-Status "Admin: $(Get-BooleanIcon (Test-AdminPrivileges))" -Level Info
    Write-Status "Projeto Claude: $(Get-BooleanIcon $Script:IsInClaudeProject)" -Level Info
    if ($Script:IsInClaudeProject) {
        Write-Status "  Local: $Script:ProjectRoot" -Level Info
    }

    # DIAGNÓSTICO
    Write-Status "DIAGNÓSTICO COMPLETO" -Level Section
    Test-FileOwnership
    Test-FilePermissions
    Test-PATHIntegrity
    Test-LockCreation
    Find-StaleLocks
    Test-DefenderStatus

    # Exibir resultados
    Write-DiagnosticTable -Results $Script:DiagnosticResults

    # Determinar se há problemas
    $hasIssues = $false
    $hasIssues = $hasIssues -or ($Script:DiagnosticResults['Ownership'].IssuesFound -gt 0)
    $hasIssues = $hasIssues -or ($Script:DiagnosticResults['Permissions'].IssuesFound -gt 0)
    $hasIssues = $hasIssues -or ($Script:DiagnosticResults['PATH'].IsCorrupted)
    $hasIssues = $hasIssues -or ($Script:DiagnosticResults['StaleLocks'].Found -gt 0)
    $hasIssues = $hasIssues -or (-not $Script:DiagnosticResults['LockCreation'].TestPassed)

    if (-not $hasIssues) {
        Write-Host "`n╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "║                                                                   ║" -ForegroundColor Green
        Write-Host "║  ✓ NENHUM PROBLEMA DETECTADO - SISTEMA OK!                        ║" -ForegroundColor Green
        Write-Host "║                                                                   ║" -ForegroundColor Green
        Write-Host "╚═══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green
        return
    }

    # CORREÇÃO (se não for DiagnoseOnly)
    if ($DiagnoseOnly) {
        Write-Host "`n" -NoNewline
        Write-Status "Modo diagnóstico - nenhuma correção aplicada" -Level Info
        Write-Host "`nPara corrigir, execute:" -ForegroundColor Yellow
        Write-Host "  .\fix-home-windows-permissions.ps1 -All" -ForegroundColor Green
        Write-Host "`nOu com Admin (para Defender):" -ForegroundColor Yellow
        Write-Host "  .\fix-home-windows-permissions.ps1 -All -AddDefenderExclusion" -ForegroundColor Green
        return
    }

    # Determinar o que corrigir
    $shouldFixOwnership = $All -or $FixOwnership
    $shouldFixPermissions = $All -or $FixPermissions
    $shouldFixPATH = $All -or $FixPATH
    $shouldFixDefender = $All -or $AddDefenderExclusion

    Write-Host "`n╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
    Write-Host "║                      INICIANDO CORREÇÕES                          ║" -ForegroundColor Yellow
    Write-Host "╚═══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Yellow

    # Aplicar correções
    if ($shouldFixOwnership -and $Script:DiagnosticResults['Ownership'].IssuesFound -gt 0) {
        Repair-AllOwnership
    }

    if ($shouldFixPermissions -and $Script:DiagnosticResults['Permissions'].IssuesFound -gt 0) {
        Repair-AllPermissions
    }

    if ($shouldFixPATH -and $Script:DiagnosticResults['PATH'].IsCorrupted) {
        Repair-PATHVariable
    }

    # Sempre limpar stale locks se houver
    if ($Script:DiagnosticResults['StaleLocks'].Found -gt 0) {
        Clear-AllStaleLocks
    }

    if ($shouldFixDefender -and $Script:DiagnosticResults['Defender'].NeedsExclusion) {
        Add-ClaudeDefenderExclusion
    }

    # VALIDAÇÃO PÓS-CORREÇÃO
    Write-Status "VALIDAÇÃO PÓS-CORREÇÃO" -Level Section
    $lockTestAfter = Test-LockCreation

    # RELATÓRIO FINAL
    Write-Host "`n╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                      RELATÓRIO FINAL                              ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

    foreach ($category in $Script:FixResults.Keys) {
        Write-Host "[$category]" -ForegroundColor Yellow
        $data = $Script:FixResults[$category]
        foreach ($key in $data.Keys) {
            Write-Host "  $key`: $($data[$key])"
        }
        Write-Host ""
    }

    # Resultado final
    if ($lockTestAfter) {
        Write-Host "╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "║                                                                   ║" -ForegroundColor Green
        Write-Host "║  ✓ CORREÇÕES APLICADAS COM SUCESSO!                               ║" -ForegroundColor Green
        Write-Host "║                                                                   ║" -ForegroundColor Green
        Write-Host "║  Claude Code deve funcionar agora.                                ║" -ForegroundColor Green
        Write-Host "║  Execute: claude                                                  ║" -ForegroundColor Green
        Write-Host "║                                                                   ║" -ForegroundColor Green
        Write-Host "╚═══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green
    } else {
        Write-Host "╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
        Write-Host "║                                                                   ║" -ForegroundColor Yellow
        Write-Host "║  ⚠ ALGUNS PROBLEMAS PERSISTEM                                     ║" -ForegroundColor Yellow
        Write-Host "║                                                                   ║" -ForegroundColor Yellow
        Write-Host "║  Tente executar como Administrador:                               ║" -ForegroundColor Yellow
        Write-Host "║  Right-click PowerShell → Run as Administrator                    ║" -ForegroundColor Yellow
        Write-Host "║  Então: .\fix-home-windows-permissions.ps1 -All -AddDefenderExclusion ║" -ForegroundColor Yellow
        Write-Host "║                                                                   ║" -ForegroundColor Yellow
        Write-Host "╚═══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Yellow
    }
}

# RUN
Main
