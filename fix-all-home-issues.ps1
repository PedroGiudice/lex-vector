#Requires -Version 5.1
<#
.SYNOPSIS
    🛠️ CORREÇÃO MESTRE - Todos os problemas Windows (PC Home)

.DESCRIPTION
    Script MESTRE que unifica TODAS as correções necessárias para o ambiente Windows home:

    ✓ Git Locks órfãos (.gitconfig.lock)
    ✓ Ownership incorreto de arquivos
    ✓ Permissões NTFS inadequadas
    ✓ PATH corrompido
    ✓ Stale locks (.claude.json.*)
    ✓ Windows Defender bloqueando lock files
    ✓ Git LFS quebrado
    ✓ Paths com espaços (validação)

    Este script resolve DEFINITIVAMENTE todos os bloqueadores antes da instalação do Claude Code.

.NOTES
    Author: Legal-Braniac (Claude Code)
    Date: 2025-11-15
    Version: 1.0.0
    Environment: Windows 10/11 (PC Home - CMR Advogados)
    Related: fix-home-windows-permissions.ps1, fix-git-locks-home.ps1

.PARAMETER DiagnoseOnly
    Apenas diagnóstico completo, sem fazer alterações

.PARAMETER SkipDefender
    Pula adição de exclusão Defender (útil se não for Admin)

.PARAMETER Force
    Executa todas as correções sem confirmação

.PARAMETER Verbose
    Output detalhado de todas as operações

.EXAMPLE
    .\fix-all-home-issues.ps1 -DiagnoseOnly
    Diagnóstico completo (sem correções)

.EXAMPLE
    .\fix-all-home-issues.ps1
    Correção completa (usuário normal - sem Defender)

.EXAMPLE
    .\fix-all-home-issues.ps1 -Force
    Correção completa (Admin - COM Defender)
#>

param(
    [switch]$DiagnoseOnly,
    [switch]$SkipDefender,
    [switch]$Force,
    [switch]$VerboseOutput
)

# =============================================================================
# CONFIGURAÇÃO GLOBAL
# =============================================================================

$ErrorActionPreference = 'Continue'
$Script:StartTime = Get-Date

# State tracking
$Script:DiagnosticResults = @{}
$Script:FixResults = @{}
$Script:IssuesFound = @()
$Script:CriticalIssues = @()

# Environment
$Script:CurrentUser = $env:USERNAME
$Script:UserProfile = $env:USERPROFILE
$Script:IsAdmin = $false

# Arquivos críticos (100% genéricos)
$Script:CriticalFiles = @(
    (Join-Path $Script:UserProfile ".claude.json"),
    (Join-Path $Script:UserProfile ".claude"),
    (Join-Path $Script:UserProfile ".local"),
    (Join-Path $Script:UserProfile ".gitconfig")
)

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

function Write-Banner {
    param([string]$Text, [string]$Color = 'Cyan')

    $width = 70
    $padding = $width - $Text.Length - 2
    $leftPad = [Math]::Floor($padding / 2)
    $rightPad = [Math]::Ceiling($padding / 2)

    Write-Host ""
    Write-Host ("╔" + ("═" * ($width - 2)) + "╗") -ForegroundColor $Color
    Write-Host ("║" + (" " * $leftPad) + $Text + (" " * $rightPad) + "║") -ForegroundColor $Color
    Write-Host ("╚" + ("═" * ($width - 2)) + "╝") -ForegroundColor $Color
    Write-Host ""
}

function Write-Status {
    param(
        [string]$Message,
        [ValidateSet('Info', 'Success', 'Warning', 'Error', 'Section', 'Critical')]
        [string]$Level = 'Info'
    )

    $colors = @{
        'Info'     = 'Cyan'
        'Success'  = 'Green'
        'Warning'  = 'Yellow'
        'Error'    = 'Red'
        'Section'  = 'Magenta'
        'Critical' = 'Red'
    }

    $symbols = @{
        'Info'     = '[ℹ]'
        'Success'  = '[✓]'
        'Warning'  = '[!]'
        'Error'    = '[✗]'
        'Section'  = '═══'
        'Critical' = '[‼]'
    }

    if ($Level -eq 'Section') {
        Write-Host "`n$($symbols[$Level]) " -ForegroundColor $colors[$Level] -NoNewline
        Write-Host $Message -ForegroundColor $colors[$Level]
        Write-Host ("═" * 68) -ForegroundColor $colors[$Level]
    } else {
        Write-Host "$($symbols[$Level]) " -ForegroundColor $colors[$Level] -NoNewline
        Write-Host $Message
    }

    # Track critical issues
    if ($Level -eq 'Critical') {
        $Script:CriticalIssues += $Message
    } elseif ($Level -eq 'Error') {
        $Script:IssuesFound += $Message
    }
}

function Test-AdminPrivileges {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-BooleanIcon {
    param([bool]$Value)
    if ($Value) { return "✓" } else { return "✗" }
}

function Write-ProgressBar {
    param(
        [int]$Current,
        [int]$Total,
        [string]$Activity
    )

    $percent = [Math]::Round(($Current / $Total) * 100)
    Write-Progress -Activity $Activity -Status "$percent% completo" -PercentComplete $percent
}

# =============================================================================
# DIAGNÓSTICO - AMBIENTE
# =============================================================================

function Test-Environment {
    Write-Status "DETECÇÃO DE AMBIENTE" -Level Section

    $Script:IsAdmin = Test-AdminPrivileges

    Write-Status "Usuário: $Script:CurrentUser" -Level Info
    Write-Status "Profile: $Script:UserProfile" -Level Info
    Write-Status "Privilégios Admin: $(Get-BooleanIcon $Script:IsAdmin)" -Level Info
    Write-Status "PowerShell Version: $($PSVersionTable.PSVersion)" -Level Info
    Write-Status "OS: $([System.Environment]::OSVersion.VersionString)" -Level Info

    # Verificar se path contém espaços
    if ($Script:UserProfile -match " ") {
        Write-Status "⚠ User profile contém espaços - pode causar problemas" -Level Warning
        $Script:IssuesFound += "User profile path contém espaços"
    }

    $Script:DiagnosticResults['Environment'] = @{
        User = $Script:CurrentUser
        IsAdmin = $Script:IsAdmin
        PSVersion = $PSVersionTable.PSVersion.ToString()
        HasSpacesInPath = ($Script:UserProfile -match " ")
    }
}

# =============================================================================
# DIAGNÓSTICO - GIT LOCKS (CRÍTICO)
# =============================================================================

function Find-GitLockFiles {
    Write-Status "DIAGNÓSTICO - GIT LOCKS" -Level Section

    $locks = @()

    # Verificar .gitconfig.lock (BLOQUEADOR CRÍTICO)
    $gitconfigLock = Join-Path $Script:UserProfile ".gitconfig.lock"
    if (Test-Path $gitconfigLock) {
        Write-Status "LOCK ÓRFÃO ENCONTRADO: .gitconfig.lock" -Level Critical

        $lockFile = Get-Item $gitconfigLock
        $age = (Get-Date) - $lockFile.LastWriteTime
        Write-Status "  Idade: $($age.TotalHours.ToString('0.0')) horas" -Level Warning
        Write-Status "  Bloqueando: Git config, GitHub Desktop, Git LFS" -Level Error

        $locks += @{
            Path = $gitconfigLock
            Type = "GitConfigLock"
            Critical = $true
            Age = $age
        }

        $Script:CriticalIssues += ".gitconfig.lock órfão (bloqueando Git)"
    } else {
        Write-Status ".gitconfig.lock: Não existe (OK)" -Level Success
    }

    # Verificar .gitconfig existe
    $gitconfig = Join-Path $Script:UserProfile ".gitconfig"
    if (Test-Path $gitconfig) {
        Write-Status ".gitconfig: Existe (OK)" -Level Success
    } else {
        Write-Status ".gitconfig: AUSENTE!" -Level Error
        $Script:IssuesFound += ".gitconfig ausente"
    }

    # Verificar outros locks Git
    $systemGitLock = Join-Path $env:ProgramData "Git\config.lock"
    if (Test-Path $systemGitLock) {
        Write-Status "Lock de sistema Git encontrado: $systemGitLock" -Level Warning
        $locks += @{
            Path = $systemGitLock
            Type = "SystemGitLock"
            Critical = $false
        }
    }

    # Verificar locks em repositórios
    $repoPath = "C:\claude-work\repos\Claude-Code-Projetos"
    if (Test-Path $repoPath) {
        $repoLocks = Get-ChildItem -Path (Join-Path $repoPath ".git") -Filter "*.lock" -Recurse -ErrorAction SilentlyContinue

        if ($repoLocks.Count -gt 0) {
            Write-Status "Locks em repositório: $($repoLocks.Count)" -Level Warning
            foreach ($lock in $repoLocks) {
                Write-Status "  - $($lock.Name)" -Level Info
                $locks += @{
                    Path = $lock.FullName
                    Type = "RepositoryLock"
                    Critical = $false
                }
            }
        }
    }

    $Script:DiagnosticResults['GitLocks'] = @{
        TotalFound = $locks.Count
        HasCriticalLock = ($locks | Where-Object { $_.Critical }).Count -gt 0
        Locks = $locks
    }

    return $locks
}

function Test-GitConfiguration {
    Write-Status "DIAGNÓSTICO - GIT CONFIGURATION" -Level Section

    $gitOK = $false
    $lfsOK = $false

    # Testar git config
    try {
        $userName = & git config --global user.name 2>&1
        $userEmail = & git config --global user.email 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Status "Git config: Funcionando ✓" -Level Success
            Write-Status "  Nome: $userName" -Level Info
            Write-Status "  Email: $userEmail" -Level Info
            $gitOK = $true
        } else {
            Write-Status "Git config: FALHOU ✗" -Level Error
            Write-Status "  Erro: $userName" -Level Error
            $Script:IssuesFound += "Git config não funcional"
        }
    } catch {
        Write-Status "Git config: ERRO $_" -Level Error
        $Script:IssuesFound += "Git config error"
    }

    # Testar Git LFS
    try {
        $lfsVersion = & git lfs version 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Status "Git LFS: Instalado ✓" -Level Success
            Write-Status "  Versão: $lfsVersion" -Level Info

            # Testar install
            $lfsInstall = & git lfs install --force 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Status "Git LFS install: OK ✓" -Level Success
                $lfsOK = $true
            } else {
                Write-Status "Git LFS install: FALHOU ✗" -Level Error
                $Script:IssuesFound += "Git LFS install failed"
            }
        } else {
            Write-Status "Git LFS: Não encontrado" -Level Warning
        }
    } catch {
        Write-Status "Git LFS: Erro $_" -Level Warning
    }

    $Script:DiagnosticResults['GitConfig'] = @{
        ConfigWorking = $gitOK
        LFSWorking = $lfsOK
        BothOK = ($gitOK -and $lfsOK)
    }

    return ($gitOK -and $lfsOK)
}

# =============================================================================
# DIAGNÓSTICO - OWNERSHIP & PERMISSIONS
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
    Write-Status "DIAGNÓSTICO - OWNERSHIP" -Level Section

    $issues = @()

    foreach ($file in $Script:CriticalFiles) {
        if (-not (Test-Path $file)) {
            Write-Status "Não existe: $file (será criado se necessário)" -Level Info
            continue
        }

        $info = Get-FileOwnerInfo -Path $file

        if ($info.NeedsFixing) {
            $issues += @{
                Path = $file
                CurrentOwner = $info.Owner
                ExpectedOwner = $Script:CurrentUser
            }
            Write-Status "Owner incorreto: $file" -Level Error
            Write-Status "  Atual: $($info.Owner) | Esperado: $Script:CurrentUser" -Level Info
        } else {
            Write-Status "Owner OK: $file" -Level Success
        }
    }

    $Script:DiagnosticResults['Ownership'] = @{
        TotalChecked = $Script:CriticalFiles.Count
        IssuesFound = $issues.Count
        AllCorrect = ($issues.Count -eq 0)
        Issues = $issues
    }

    return $issues
}

function Test-FilePermissions {
    Write-Status "DIAGNÓSTICO - PERMISSÕES NTFS" -Level Section

    $issues = @()

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
                $issues += @{
                    Path = $file
                    Issue = "FullControl ausente"
                }
                Write-Status "Permissões insuficientes: $file" -Level Error
            } else {
                Write-Status "Permissões OK: $file" -Level Success
            }
        } catch {
            $issues += @{
                Path = $file
                Issue = "Erro: $_"
            }
            Write-Status "Erro ao verificar: $file" -Level Error
        }
    }

    $Script:DiagnosticResults['Permissions'] = @{
        TotalChecked = $Script:CriticalFiles.Count
        IssuesFound = $issues.Count
        AllCorrect = ($issues.Count -eq 0)
        Issues = $issues
    }

    return $issues
}

# =============================================================================
# DIAGNÓSTICO - PATH
# =============================================================================

function Test-PATHIntegrity {
    Write-Status "DIAGNÓSTICO - PATH" -Level Section

    $currentPATH = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $pathEntries = $currentPATH -split ';' | Where-Object { $_ -ne '' }

    $hasUserProfileRoot = $false
    $hasLocalBin = $false
    $invalidEntries = @()

    foreach ($entry in $pathEntries) {
        # Problema: C:\Users\<user> inteiro
        if ($entry -eq $Script:UserProfile) {
            $hasUserProfileRoot = $true
            Write-Status "CRÍTICO: PATH contém user profile inteiro!" -Level Critical
            $Script:CriticalIssues += "PATH corrompido (user profile root)"
        }

        # Verificar .local\bin
        $localBinPath = Join-Path $Script:UserProfile ".local\bin"
        if ($entry -eq $localBinPath) {
            $hasLocalBin = $true
        }

        # Entradas inválidas
        if ($entry -match [regex]::Escape($Script:UserProfile)) {
            if (-not (Test-Path $entry)) {
                $invalidEntries += $entry
                Write-Status "Entrada inválida no PATH: $entry" -Level Warning
            }
        }
    }

    if ($hasLocalBin) {
        Write-Status ".local\bin no PATH: ✓" -Level Success
    } else {
        Write-Status ".local\bin ausente do PATH" -Level Warning
        $Script:IssuesFound += ".local\bin não está no PATH"
    }

    $Script:DiagnosticResults['PATH'] = @{
        TotalEntries = $pathEntries.Count
        HasUserProfileRoot = $hasUserProfileRoot
        HasLocalBin = $hasLocalBin
        InvalidEntries = $invalidEntries
        IsCorrupted = ($hasUserProfileRoot -or (-not $hasLocalBin) -or ($invalidEntries.Count -gt 0))
    }

    return ($hasUserProfileRoot -or (-not $hasLocalBin))
}

# =============================================================================
# DIAGNÓSTICO - STALE LOCKS
# =============================================================================

function Find-StaleLocks {
    Write-Status "DIAGNÓSTICO - STALE LOCKS (.claude.json.*)" -Level Section

    $claudeConfig = Join-Path $Script:UserProfile ".claude.json"
    $configDir = Split-Path $claudeConfig -Parent

    try {
        $locks = Get-ChildItem -Path $configDir -Filter ".claude.json.*" -ErrorAction SilentlyContinue

        if ($locks.Count -gt 0) {
            Write-Status "Encontrados $($locks.Count) stale lock(s)!" -Level Warning
            foreach ($lock in $locks) {
                $age = (Get-Date) - $lock.LastWriteTime
                Write-Status "  - $($lock.Name) (idade: $($age.TotalHours.ToString('0.0'))h)" -Level Info
            }
            $Script:IssuesFound += "$($locks.Count) stale locks encontrados"
        } else {
            Write-Status "Nenhum stale lock encontrado ✓" -Level Success
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
    Write-Status "DIAGNÓSTICO - WINDOWS DEFENDER" -Level Section

    try {
        $defender = Get-MpComputerStatus -ErrorAction Stop
        $prefs = Get-MpPreference -ErrorAction Stop

        $claudeConfig = Join-Path $Script:UserProfile ".claude.json"
        $isExcluded = $prefs.ExclusionPath -contains $claudeConfig

        Write-Status "Defender ativo: $($defender.AntivirusEnabled)" -Level Info
        Write-Status "Real-time protection: $($defender.RealTimeProtectionEnabled)" -Level Info
        Write-Status ".claude.json em exclusões: $(Get-BooleanIcon $isExcluded)" -Level $(if ($isExcluded) { "Success" } else { "Warning" })

        if ($defender.RealTimeProtectionEnabled -and (-not $isExcluded)) {
            Write-Status "⚠ Defender pode bloquear lock files!" -Level Warning
            $Script:IssuesFound += "Defender sem exclusão para .claude.json"
        }

        $Script:DiagnosticResults['Defender'] = @{
            Enabled = $defender.AntivirusEnabled
            RealTimeProtection = $defender.RealTimeProtectionEnabled
            ClaudeConfigExcluded = $isExcluded
            NeedsExclusion = ($defender.RealTimeProtectionEnabled -and (-not $isExcluded))
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
# DIAGNÓSTICO - LOCK CREATION TEST
# =============================================================================

function Test-LockCreation {
    Write-Status "DIAGNÓSTICO - TESTE DE CRIAÇÃO DE LOCKS" -Level Section

    $claudeConfig = Join-Path $Script:UserProfile ".claude.json"
    $testLock = "$claudeConfig.test-lock-$([guid]::NewGuid().ToString('N').Substring(0,8))"

    try {
        New-Item -ItemType Directory -Path $testLock -ErrorAction Stop | Out-Null
        Remove-Item $testLock -Force -ErrorAction Stop

        Write-Status "Teste de criação de lock: PASSOU ✓" -Level Success

        $Script:DiagnosticResults['LockCreation'] = @{
            CanCreateLock = $true
            TestPassed = $true
        }

        return $true
    } catch {
        Write-Status "Teste de criação de lock: FALHOU ✗" -Level Error
        Write-Status "  Erro: $_" -Level Error
        $Script:CriticalIssues += "Não consegue criar lock files (EPERM)"

        $Script:DiagnosticResults['LockCreation'] = @{
            CanCreateLock = $false
            Error = $_.Exception.Message
            TestPassed = $false
        }

        return $false
    }
}

# =============================================================================
# RESUMO DO DIAGNÓSTICO
# =============================================================================

function Write-DiagnosticSummary {
    Write-Banner "RESUMO DO DIAGNÓSTICO" "Yellow"

    $totalIssues = $Script:IssuesFound.Count
    $totalCritical = $Script:CriticalIssues.Count

    # Git Locks
    Write-Host "Git Locks Órfãos: " -NoNewline
    $gitLocks = $Script:DiagnosticResults['GitLocks'].TotalFound
    if ($gitLocks -gt 0) {
        Write-Host "$gitLocks" -ForegroundColor Red
    } else {
        Write-Host "0 (OK)" -ForegroundColor Green
    }

    # Git Config
    Write-Host "Git Config Funcionando: " -NoNewline
    $gitOK = $Script:DiagnosticResults['GitConfig'].BothOK
    Write-Host (Get-BooleanIcon $gitOK) -ForegroundColor $(if ($gitOK) { "Green" } else { "Red" })

    # Ownership
    Write-Host "Ownership Correto: " -NoNewline
    $ownershipOK = $Script:DiagnosticResults['Ownership'].AllCorrect
    Write-Host (Get-BooleanIcon $ownershipOK) -ForegroundColor $(if ($ownershipOK) { "Green" } else { "Red" })

    # Permissions
    Write-Host "Permissões Corretas: " -NoNewline
    $permsOK = $Script:DiagnosticResults['Permissions'].AllCorrect
    Write-Host (Get-BooleanIcon $permsOK) -ForegroundColor $(if ($permsOK) { "Green" } else { "Red" })

    # PATH
    Write-Host "PATH Íntegro: " -NoNewline
    $pathOK = -not $Script:DiagnosticResults['PATH'].IsCorrupted
    Write-Host (Get-BooleanIcon $pathOK) -ForegroundColor $(if ($pathOK) { "Green" } else { "Red" })

    # Stale Locks
    Write-Host "Stale Locks: " -NoNewline
    $staleLocks = $Script:DiagnosticResults['StaleLocks'].Found
    if ($staleLocks -gt 0) {
        Write-Host "$staleLocks" -ForegroundColor Yellow
    } else {
        Write-Host "0 (OK)" -ForegroundColor Green
    }

    # Defender
    Write-Host "Defender Configurado: " -NoNewline
    $defenderOK = -not $Script:DiagnosticResults['Defender'].NeedsExclusion
    Write-Host (Get-BooleanIcon $defenderOK) -ForegroundColor $(if ($defenderOK) { "Green" } else { "Yellow" })

    # Lock Creation
    Write-Host "Pode Criar Locks: " -NoNewline
    $lockOK = $Script:DiagnosticResults['LockCreation'].TestPassed
    Write-Host (Get-BooleanIcon $lockOK) -ForegroundColor $(if ($lockOK) { "Green" } else { "Red" })

    Write-Host "`n═══════════════════════════════════════════════════════════════════`n"

    # Resumo final
    if ($totalCritical -gt 0) {
        Write-Host "⚠ PROBLEMAS CRÍTICOS: $totalCritical" -ForegroundColor Red
        foreach ($issue in $Script:CriticalIssues) {
            Write-Host "  ‼ $issue" -ForegroundColor Red
        }
        Write-Host ""
    }

    if ($totalIssues -gt 0) {
        Write-Host "⚠ Problemas encontrados: $totalIssues" -ForegroundColor Yellow
        if ($VerboseOutput) {
            foreach ($issue in $Script:IssuesFound) {
                Write-Host "  ! $issue" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "✓ NENHUM PROBLEMA DETECTADO - SISTEMA OK!" -ForegroundColor Green
    }

    Write-Host ""
}

# =============================================================================
# CORREÇÃO - GIT LOCKS
# =============================================================================

function Remove-GitLocks {
    param([array]$Locks)

    Write-Status "CORREÇÃO - REMOVENDO GIT LOCKS" -Level Section

    $removed = 0
    $failed = 0

    foreach ($lock in $Locks) {
        Write-Status "Removendo: $($lock.Path)" -Level Info

        try {
            if (Test-Path $lock.Path) {
                Remove-Item $lock.Path -Force -ErrorAction Stop
                Write-Status "  Removido com sucesso ✓" -Level Success
                $removed++
            } else {
                Write-Status "  Já não existe" -Level Info
            }
        } catch {
            Write-Status "  FALHA: $_" -Level Error
            $failed++
        }
    }

    $Script:FixResults['GitLocks'] = @{
        Attempted = $Locks.Count
        Removed = $removed
        Failed = $failed
    }

    Write-Status "Git locks removidos: $removed/$($Locks.Count)" -Level Success
}

function Repair-GitLFS {
    Write-Status "CORREÇÃO - REINSTALANDO GIT LFS" -Level Section

    try {
        Write-Status "Desinstalando Git LFS..." -Level Info
        & git lfs uninstall 2>&1 | Out-Null

        Write-Status "Instalando Git LFS..." -Level Info
        $result = & git lfs install --force 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Status "Git LFS reinstalado com sucesso ✓" -Level Success
            $Script:FixResults['GitLFS'] = @{ Success = $true }
            return $true
        } else {
            Write-Status "Falha ao reinstalar Git LFS: $result" -Level Error
            $Script:FixResults['GitLFS'] = @{ Success = $false; Error = $result }
            return $false
        }
    } catch {
        Write-Status "Erro ao reinstalar Git LFS: $_" -Level Error
        $Script:FixResults['GitLFS'] = @{ Success = $false; Error = $_ }
        return $false
    }
}

# =============================================================================
# CORREÇÃO - OWNERSHIP
# =============================================================================

function Fix-FileOwnership {
    param([string]$Path, [bool]$Recursive = $false)

    Write-Status "Corrigindo ownership: $Path" -Level Info

    try {
        # takeown.exe
        $takeownArgs = @("/F", "`"$Path`"")
        if ($Recursive) {
            $takeownArgs += @("/R", "/D", "Y")
        }

        $result = & takeown.exe $takeownArgs 2>&1

        if ($LASTEXITCODE -eq 0) {
            # icacls para garantir permissões
            $icaclsArgs = @("`"$Path`"", "/grant", "$($Script:CurrentUser):F")
            if ($Recursive) {
                $icaclsArgs += "/T"
            }

            & icacls.exe $icaclsArgs | Out-Null

            Write-Status "  Ownership corrigido ✓" -Level Success
            return $true
        } else {
            Write-Status "  Falhou: $result" -Level Error
            return $false
        }
    } catch {
        Write-Status "  Erro: $_" -Level Error
        return $false
    }
}

function Repair-AllOwnership {
    Write-Status "CORREÇÃO - OWNERSHIP" -Level Section

    $issues = $Script:DiagnosticResults['Ownership'].Issues
    $fixed = 0
    $failed = 0

    foreach ($issue in $issues) {
        $isDir = Test-Path $issue.Path -PathType Container
        if (Fix-FileOwnership -Path $issue.Path -Recursive $isDir) {
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

    Write-Status "Ownership corrigido: $fixed/$($issues.Count)" -Level Success
}

# =============================================================================
# CORREÇÃO - PERMISSÕES
# =============================================================================

function Fix-FilePermissions {
    param([string]$Path)

    try {
        $icaclsArgs = @("`"$Path`"", "/grant", "$($Script:CurrentUser):F")

        if (Test-Path $Path -PathType Container) {
            $icaclsArgs += "/T"
        }

        & icacls.exe $icaclsArgs | Out-Null

        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        return $false
    } catch {
        return $false
    }
}

function Repair-AllPermissions {
    Write-Status "CORREÇÃO - PERMISSÕES" -Level Section

    $issues = $Script:DiagnosticResults['Permissions'].Issues
    $fixed = 0

    foreach ($issue in $issues) {
        if (Fix-FilePermissions -Path $issue.Path) {
            $fixed++
        }
    }

    $Script:FixResults['Permissions'] = @{
        Attempted = $issues.Count
        Fixed = $fixed
    }

    Write-Status "Permissões corrigidas: $fixed/$($issues.Count)" -Level Success
}

# =============================================================================
# CORREÇÃO - PATH
# =============================================================================

function Repair-PATHVariable {
    Write-Status "CORREÇÃO - PATH" -Level Section

    $currentPATH = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $pathEntries = $currentPATH -split ';' | Where-Object { $_ -ne '' }

    # Backup
    $backupPath = Join-Path $env:TEMP "PATH_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
    $currentPATH | Out-File $backupPath
    Write-Status "Backup do PATH: $backupPath" -Level Info

    # Filtrar
    $newEntries = @()
    $removed = @()

    foreach ($entry in $pathEntries) {
        # Remover user profile root
        if ($entry -eq $Script:UserProfile) {
            $removed += $entry
            Write-Status "Removido: $entry" -Level Warning
            continue
        }

        # Remover inválidos
        if ($entry -match [regex]::Escape($Script:UserProfile)) {
            if (-not (Test-Path $entry)) {
                $removed += $entry
                Write-Status "Removida entrada inválida: $entry" -Level Warning
                continue
            }
        }

        $newEntries += $entry
    }

    # Adicionar .local\bin
    $localBinPath = Join-Path $Script:UserProfile ".local\bin"
    if ($newEntries -notcontains $localBinPath) {
        if (-not (Test-Path $localBinPath)) {
            New-Item -ItemType Directory -Path $localBinPath -Force | Out-Null
            Write-Status "Criado: $localBinPath" -Level Success
        }
        $newEntries += $localBinPath
        Write-Status "Adicionado ao PATH: $localBinPath" -Level Success
    }

    # Aplicar
    $newPATH = $newEntries -join ';'
    [System.Environment]::SetEnvironmentVariable("Path", $newPATH, "User")

    Write-Status "PATH atualizado com sucesso ✓" -Level Success

    $Script:FixResults['PATH'] = @{
        BackupLocation = $backupPath
        EntriesRemoved = $removed.Count
        RemovedEntries = $removed
    }
}

# =============================================================================
# CORREÇÃO - STALE LOCKS
# =============================================================================

function Clear-AllStaleLocks {
    Write-Status "CORREÇÃO - STALE LOCKS" -Level Section

    $locks = $Script:DiagnosticResults['StaleLocks'].Locks
    $removed = 0

    foreach ($lock in $locks) {
        try {
            Remove-Item $lock.FullName -Force -Recurse -ErrorAction Stop
            Write-Status "Removido: $($lock.Name) ✓" -Level Success
            $removed++
        } catch {
            Write-Status "Falha ao remover $($lock.Name): $_" -Level Error
        }
    }

    $Script:FixResults['StaleLocks'] = @{
        Attempted = $locks.Count
        Removed = $removed
    }

    Write-Status "Stale locks removidos: $removed/$($locks.Count)" -Level Success
}

# =============================================================================
# CORREÇÃO - DEFENDER
# =============================================================================

function Add-ClaudeDefenderExclusion {
    Write-Status "CORREÇÃO - WINDOWS DEFENDER EXCLUSÃO" -Level Section

    if (-not $Script:IsAdmin) {
        Write-Status "⚠ Privilégios Admin necessários (pulando)" -Level Warning
        Write-Status "  Execute como Admin e use -Force para adicionar exclusão" -Level Info
        $Script:FixResults['Defender'] = @{
            Added = $false
            Reason = "Sem privilégios Admin"
        }
        return
    }

    try {
        $claudeConfig = Join-Path $Script:UserProfile ".claude.json"
        Add-MpPreference -ExclusionPath $claudeConfig -ErrorAction Stop
        Write-Status "Exclusão adicionada: $claudeConfig ✓" -Level Success

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
# VALIDAÇÃO PÓS-CORREÇÃO
# =============================================================================

function Invoke-PostFixValidation {
    Write-Status "VALIDAÇÃO PÓS-CORREÇÃO" -Level Section

    $allGood = $true

    # Testar Git config novamente
    Write-Status "Validando Git config..." -Level Info
    $gitValid = Test-GitConfiguration
    if (-not $gitValid) {
        Write-Status "  Git ainda com problemas ✗" -Level Error
        $allGood = $false
    } else {
        Write-Status "  Git funcionando ✓" -Level Success
    }

    # Testar criação de lock novamente
    Write-Status "Validando criação de locks..." -Level Info
    $lockValid = Test-LockCreation
    if (-not $lockValid) {
        Write-Status "  Ainda não consegue criar locks ✗" -Level Error
        $allGood = $false
    } else {
        Write-Status "  Lock creation OK ✓" -Level Success
    }

    # Verificar se ainda há locks órfãos
    Write-Status "Validando remoção de locks..." -Level Info
    $gitconfigLock = Join-Path $Script:UserProfile ".gitconfig.lock"
    if (Test-Path $gitconfigLock) {
        Write-Status "  .gitconfig.lock ainda existe ✗" -Level Error
        $allGood = $false
    } else {
        Write-Status "  Sem locks órfãos ✓" -Level Success
    }

    return $allGood
}

# =============================================================================
# RELATÓRIO FINAL
# =============================================================================

function Write-FinalReport {
    $duration = (Get-Date) - $Script:StartTime

    Write-Banner "RELATÓRIO FINAL" "Cyan"

    Write-Host "Tempo de execução: $($duration.TotalSeconds.ToString('0.0'))s" -ForegroundColor Gray
    Write-Host "`nCorreções aplicadas:`n" -ForegroundColor Yellow

    foreach ($category in $Script:FixResults.Keys) {
        Write-Host "[$category]" -ForegroundColor Yellow
        $data = $Script:FixResults[$category]
        foreach ($key in $data.Keys) {
            $value = $data[$key]
            if ($value -is [array]) {
                Write-Host "  $key`: $($value.Count) itens"
            } else {
                Write-Host "  $key`: $value"
            }
        }
        Write-Host ""
    }
}

# =============================================================================
# MAIN ORCHESTRATION
# =============================================================================

function Main {
    Write-Banner "🛠️ CORREÇÃO MESTRE - TODOS OS PROBLEMAS WINDOWS (PC HOME)" "Cyan"

    # 1. AMBIENTE
    Test-Environment

    # 2. DIAGNÓSTICO COMPLETO
    Write-Banner "DIAGNÓSTICO COMPLETO" "Magenta"

    Write-ProgressBar -Current 1 -Total 8 -Activity "Executando diagnóstico completo..."
    $gitLocks = Find-GitLockFiles

    Write-ProgressBar -Current 2 -Total 8 -Activity "Executando diagnóstico completo..."
    Test-GitConfiguration

    Write-ProgressBar -Current 3 -Total 8 -Activity "Executando diagnóstico completo..."
    Test-FileOwnership

    Write-ProgressBar -Current 4 -Total 8 -Activity "Executando diagnóstico completo..."
    Test-FilePermissions

    Write-ProgressBar -Current 5 -Total 8 -Activity "Executando diagnóstico completo..."
    Test-PATHIntegrity

    Write-ProgressBar -Current 6 -Total 8 -Activity "Executando diagnóstico completo..."
    $staleLocks = Find-StaleLocks

    Write-ProgressBar -Current 7 -Total 8 -Activity "Executando diagnóstico completo..."
    Test-DefenderStatus

    Write-ProgressBar -Current 8 -Total 8 -Activity "Executando diagnóstico completo..."
    Test-LockCreation

    Write-Progress -Activity "Diagnóstico completo" -Completed

    # 3. RESUMO
    Write-DiagnosticSummary

    # Verificar se há problemas
    $hasProblems = ($Script:IssuesFound.Count -gt 0) -or ($Script:CriticalIssues.Count -gt 0)

    if (-not $hasProblems) {
        Write-Banner "✓ SISTEMA OK - NENHUMA CORREÇÃO NECESSÁRIA" "Green"
        return
    }

    # 4. MODO DIAGNÓSTICO (sair se for apenas diagnóstico)
    if ($DiagnoseOnly) {
        Write-Host "`nPara corrigir todos os problemas, execute:" -ForegroundColor Yellow
        if ($Script:IsAdmin) {
            Write-Host "  .\fix-all-home-issues.ps1 -Force" -ForegroundColor Green
        } else {
            Write-Host "  .\fix-all-home-issues.ps1" -ForegroundColor Green
            Write-Host "`nPara correção completa (COM Defender), execute como Admin:" -ForegroundColor Yellow
            Write-Host "  Right-click PowerShell → Run as Administrator" -ForegroundColor Gray
            Write-Host "  .\fix-all-home-issues.ps1 -Force" -ForegroundColor Green
        }
        return
    }

    # 5. CONFIRMAÇÃO (se não for -Force)
    if (-not $Force) {
        Write-Host "`n⚠ ATENÇÃO: Este script vai fazer as seguintes alterações:" -ForegroundColor Yellow
        Write-Host "  • Remover lock files Git" -ForegroundColor Gray
        Write-Host "  • Corrigir ownership de arquivos" -ForegroundColor Gray
        Write-Host "  • Corrigir permissões NTFS" -ForegroundColor Gray
        Write-Host "  • Limpar variável PATH (com backup)" -ForegroundColor Gray
        Write-Host "  • Remover stale locks" -ForegroundColor Gray
        if ($Script:IsAdmin -and -not $SkipDefender) {
            Write-Host "  • Adicionar exclusão no Windows Defender" -ForegroundColor Gray
        }
        Write-Host ""

        $confirmation = Read-Host "Continuar? (S/N)"
        if ($confirmation -ne 'S' -and $confirmation -ne 's') {
            Write-Host "Operação cancelada pelo usuário." -ForegroundColor Yellow
            return
        }
    }

    # 6. APLICAR CORREÇÕES (ordem importa!)
    Write-Banner "APLICANDO CORREÇÕES" "Yellow"

    # Ordem de correção:
    # 1º - Git locks (desbloqueiam Git)
    # 2º - Ownership & Permissions (permitem operações)
    # 3º - PATH (ambiente correto)
    # 4º - Stale locks (limpeza)
    # 5º - Defender (proteção futura)

    if ($gitLocks.Count -gt 0) {
        Remove-GitLocks -Locks $gitLocks
    }

    if ($Script:DiagnosticResults['GitConfig'].BothOK -eq $false) {
        Repair-GitLFS
    }

    if ($Script:DiagnosticResults['Ownership'].IssuesFound -gt 0) {
        Repair-AllOwnership
    }

    if ($Script:DiagnosticResults['Permissions'].IssuesFound -gt 0) {
        Repair-AllPermissions
    }

    if ($Script:DiagnosticResults['PATH'].IsCorrupted) {
        Repair-PATHVariable
    }

    if ($staleLocks.Count -gt 0) {
        Clear-AllStaleLocks
    }

    if (-not $SkipDefender -and $Script:DiagnosticResults['Defender'].NeedsExclusion) {
        Add-ClaudeDefenderExclusion
    }

    # 7. VALIDAÇÃO PÓS-CORREÇÃO
    $allFixed = Invoke-PostFixValidation

    # 8. RELATÓRIO FINAL
    Write-FinalReport

    # 9. RESULTADO FINAL
    if ($allFixed) {
        Write-Banner "✓ CORREÇÕES CONCLUÍDAS COM SUCESSO!" "Green"
        Write-Host "Próximos passos:" -ForegroundColor Yellow
        Write-Host "  1. Testar GitHub Desktop (deve funcionar agora)" -ForegroundColor Gray
        Write-Host "  2. Testar Git LFS: git lfs version" -ForegroundColor Gray
        Write-Host "  3. Instalar Claude Code (ambiente pronto!)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Ambiente Windows completamente corrigido e pronto para uso! ✓" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Banner "⚠ ALGUNS PROBLEMAS PERSISTEM" "Yellow"
        Write-Host "Ações recomendadas:" -ForegroundColor Yellow
        Write-Host "  1. Execute como Administrador:" -ForegroundColor Gray
        Write-Host "     Right-click PowerShell → Run as Administrator" -ForegroundColor Gray
        Write-Host "     .\fix-all-home-issues.ps1 -Force" -ForegroundColor Green
        Write-Host ""
        Write-Host "  2. Se o problema persistir, verifique:" -ForegroundColor Gray
        Write-Host "     • Antivirus de terceiros bloqueando operações" -ForegroundColor Gray
        Write-Host "     • Políticas de grupo corporativas (GPO)" -ForegroundColor Gray
        Write-Host "     • Processos Git/GitHub Desktop em execução" -ForegroundColor Gray
        Write-Host ""
    }
}

# EXECUTAR
Main
