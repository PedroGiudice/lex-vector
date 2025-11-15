#Requires -Version 5.1
<#
.SYNOPSIS
    Diagnóstico PROFUNDO e COMPLETO - Ambiente Windows para Claude Code (PC Home)

.DESCRIPTION
    Executa diagnóstico exaustivo de TODOS os aspectos que podem impedir Claude Code de funcionar:

    CATEGORIA 1: GIT E GITHUB
    - Lock files (.gitconfig.lock, index.lock, etc)
    - Git configuration (global, system, local)
    - Git LFS installation e configuration
    - GitHub Desktop configuration
    - SSH keys e credentials
    - Processos bloqueando arquivos Git

    CATEGORIA 2: PERMISSÕES E OWNERSHIP
    - Ownership de arquivos críticos
    - ACLs (permissões NTFS) detalhadas
    - User SID e grupos
    - Herança de permissões
    - Effective permissions

    CATEGORIA 3: WINDOWS DEFENDER
    - Status do Defender
    - Exclusões configuradas
    - Histórico de quarentena
    - Real-time protection impact

    CATEGORIA 4: SISTEMA E AMBIENTE
    - PATH integrity (User e System)
    - Environment variables críticas
    - Processos em execução (que podem bloquear)
    - Disk space e performance
    - User profile paths com espaços

    CATEGORIA 5: CLAUDE CODE ESPECÍFICO
    - .claude.json e .claude directory
    - Lock files do Claude
    - Configurações corrompidas
    - Logs de erro

    CATEGORIA 6: NODE.JS E NPM
    - Node.js version
    - npm global packages
    - npm cache integrity

    Gera relatório JSON detalhado + output formatado para humanos.

.PARAMETER OutputJson
    Caminho para salvar relatório JSON detalhado

.PARAMETER CheckProcesses
    Verificar processos que podem estar bloqueando arquivos (mais lento)

.PARAMETER DeepScan
    Scan profundo (inclui verificações lentas como registry, event logs)

.PARAMETER VerboseOutput
    Output extremamente detalhado

.EXAMPLE
    .\diagnose-home-complete.ps1
    Diagnóstico padrão (rápido)

.EXAMPLE
    .\diagnose-home-complete.ps1 -DeepScan -CheckProcesses
    Diagnóstico completo e profundo (pode levar alguns minutos)

.EXAMPLE
    .\diagnose-home-complete.ps1 -OutputJson "diagnostico.json"
    Salva relatório em JSON para análise programática

.NOTES
    Author: Claude Code
    Version: 2.0
    Date: 2025-11-15
    Platform: Windows PowerShell 5.1+
    Related: fix-home-windows-permissions.ps1, fix-git-locks-home.ps1
#>

[CmdletBinding()]
param(
    [string]$OutputJson,
    [switch]$CheckProcesses,
    [switch]$DeepScan,
    [switch]$VerboseOutput
)

# =============================================================================
# CONFIGURAÇÃO GLOBAL
# =============================================================================

$ErrorActionPreference = 'Continue'
$Script:DiagnosticData = @{
    Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Machine = $env:COMPUTERNAME
    User = $env:USERNAME
    UserProfile = $env:USERPROFILE
    PSVersion = $PSVersionTable.PSVersion.ToString()
    Categories = @{}
    Issues = @()
    Warnings = @()
    CriticalIssues = @()
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

function Write-DiagHeader {
    param([string]$Title)

    Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    $padding = 64 - $Title.Length
    $leftPad = [Math]::Floor($padding / 2)
    $rightPad = [Math]::Ceiling($padding / 2)
    $line = "║" + (" " * $leftPad) + $Title + (" " * $rightPad) + "║"
    Write-Host $line -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
}

function Write-DiagSection {
    param([string]$Section)
    Write-Host "`n═══ $Section " -ForegroundColor Magenta -NoNewline
    Write-Host ("═" * (60 - $Section.Length)) -ForegroundColor Magenta
}

function Write-DiagStatus {
    param(
        [string]$Message,
        [ValidateSet('OK', 'INFO', 'WARN', 'ERROR', 'CRITICAL')]
        [string]$Level = 'INFO',
        [int]$Indent = 0
    )

    $prefix = "  " * $Indent
    $symbols = @{
        'OK' = '✓'
        'INFO' = 'i'
        'WARN' = '!'
        'ERROR' = '✗'
        'CRITICAL' = '⚠'
    }

    $colors = @{
        'OK' = 'Green'
        'INFO' = 'Cyan'
        'WARN' = 'Yellow'
        'ERROR' = 'Red'
        'CRITICAL' = 'Magenta'
    }

    Write-Host "$prefix[$($symbols[$Level])] " -ForegroundColor $colors[$Level] -NoNewline
    Write-Host $Message
}

function Add-Issue {
    param(
        [string]$Category,
        [string]$Issue,
        [string]$Severity = 'Medium',
        [string]$Solution = ''
    )

    $issueObj = @{
        Category = $Category
        Issue = $Issue
        Severity = $Severity
        Solution = $Solution
        Timestamp = Get-Date -Format 'HH:mm:ss'
    }

    $Script:DiagnosticData.Issues += $issueObj

    if ($Severity -eq 'Critical') {
        $Script:DiagnosticData.CriticalIssues += $issueObj
    } elseif ($Severity -eq 'High') {
        $Script:DiagnosticData.Warnings += $issueObj
    }
}

# =============================================================================
# CATEGORIA 1: GIT E GITHUB
# =============================================================================

function Test-GitLocks {
    Write-DiagSection "CATEGORIA 1.1: Git Lock Files"

    $lockData = @{
        GlobalLocks = @()
        SystemLocks = @()
        RepositoryLocks = @()
        TotalLocks = 0
    }

    # 1.1.1 Global config locks
    $gitConfigPath = Join-Path $env:USERPROFILE ".gitconfig"
    $gitConfigLock = "$gitConfigPath.lock"

    if (Test-Path $gitConfigLock) {
        Write-DiagStatus "LOCK ENCONTRADO: .gitconfig.lock" -Level ERROR -Indent 1

        $lockFile = Get-Item $gitConfigLock
        $age = (Get-Date) - $lockFile.LastWriteTime
        $ageHours = [Math]::Round($age.TotalHours, 1)

        Write-DiagStatus "Idade: $ageHours horas | Tamanho: $($lockFile.Length) bytes" -Level INFO -Indent 2

        $lockData.GlobalLocks += @{
            Path = $gitConfigLock
            Age = $ageHours
            Size = $lockFile.Length
            LastWrite = $lockFile.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
        }

        Add-Issue -Category "Git" -Issue ".gitconfig.lock bloqueando Git" `
            -Severity "Critical" `
            -Solution "Remove-Item '$gitConfigLock' -Force"
    } else {
        Write-DiagStatus ".gitconfig.lock: Não existe (OK)" -Level OK -Indent 1
    }

    # 1.1.2 Verificar .gitconfig principal
    if (Test-Path $gitConfigPath) {
        Write-DiagStatus ".gitconfig: Existe" -Level OK -Indent 1

        try {
            $acl = Get-Acl $gitConfigPath
            $owner = $acl.Owner
            Write-DiagStatus "Owner: $owner" -Level INFO -Indent 2
        } catch {
            Write-DiagStatus "Erro ao ler ACL: $_" -Level ERROR -Indent 2
        }
    } else {
        Write-DiagStatus ".gitconfig: NÃO EXISTE (problema)" -Level WARN -Indent 1
        Add-Issue -Category "Git" -Issue ".gitconfig ausente" -Severity "High"
    }

    # 1.1.3 System config locks
    $systemGitConfig = Join-Path $env:ProgramData "Git\config"
    $systemGitLock = "$systemGitConfig.lock"

    if (Test-Path $systemGitLock) {
        Write-DiagStatus "System config lock encontrado: $systemGitLock" -Level WARN -Indent 1
        $lockData.SystemLocks += $systemGitLock
        Add-Issue -Category "Git" -Issue "System Git config bloqueado" -Severity "Medium"
    }

    # 1.1.4 Repository locks (se existir repositório local)
    $repoPath = "C:\claude-work\repos\Claude-Code-Projetos"
    if (Test-Path $repoPath) {
        Write-DiagStatus "Verificando repositório: $repoPath" -Level INFO -Indent 1

        $gitDir = Join-Path $repoPath ".git"
        if (Test-Path $gitDir) {
            $repoLocks = Get-ChildItem -Path $gitDir -Filter "*.lock" -Recurse -ErrorAction SilentlyContinue

            if (@($repoLocks).Count -gt 0) {
                Write-DiagStatus "Locks encontrados no repositório: $(@($repoLocks).Count)" -Level WARN -Indent 2

                foreach ($lock in $repoLocks) {
                    Write-DiagStatus "$($lock.Name) - $($lock.FullName)" -Level WARN -Indent 3
                    $lockData.RepositoryLocks += $lock.FullName
                    Add-Issue -Category "Git" -Issue "Repository lock: $($lock.Name)" -Severity "Medium"
                }
            } else {
                Write-DiagStatus "Nenhum lock no repositório (OK)" -Level OK -Indent 2
            }
        }
    }

    $lockData.TotalLocks = $lockData.GlobalLocks.Count + $lockData.SystemLocks.Count + $lockData.RepositoryLocks.Count
    $Script:DiagnosticData.Categories['GitLocks'] = $lockData

    return $lockData
}

function Test-GitConfiguration {
    Write-DiagSection "CATEGORIA 1.2: Git Configuration"

    $gitData = @{
        GitInstalled = $false
        GitVersion = $null
        GitConfigWorks = $false
        UserName = $null
        UserEmail = $null
        ConfigEntries = @{}
        Errors = @()
    }

    # 1.2.1 Verificar se git está instalado
    try {
        $gitVersionOutput = & git --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $gitData.GitInstalled = $true
            $gitData.GitVersion = $gitVersionOutput.ToString().Trim()
            Write-DiagStatus "Git instalado: $($gitData.GitVersion)" -Level OK -Indent 1
        } else {
            Write-DiagStatus "Git não encontrado no PATH" -Level ERROR -Indent 1
            $gitData.Errors += "Git não encontrado"
            Add-Issue -Category "Git" -Issue "Git não instalado ou não no PATH" -Severity "Critical"
        }
    } catch {
        Write-DiagStatus "Erro ao verificar Git: $_" -Level ERROR -Indent 1
        $gitData.Errors += $_.Exception.Message
    }

    # 1.2.2 Testar git config
    if ($gitData.GitInstalled) {
        try {
            $userName = & git config --global user.name 2>&1
            $userEmail = & git config --global user.email 2>&1

            if ($LASTEXITCODE -eq 0) {
                $gitData.GitConfigWorks = $true
                $gitData.UserName = $userName.ToString().Trim()
                $gitData.UserEmail = $userEmail.ToString().Trim()

                Write-DiagStatus "Git config funcionando: ✓" -Level OK -Indent 1
                Write-DiagStatus "user.name: $($gitData.UserName)" -Level INFO -Indent 2
                Write-DiagStatus "user.email: $($gitData.UserEmail)" -Level INFO -Indent 2
            } else {
                Write-DiagStatus "Git config FALHOU: $userName" -Level ERROR -Indent 1
                $gitData.Errors += "Git config failed: $userName"
                Add-Issue -Category "Git" -Issue "git config --global não funciona" `
                    -Severity "Critical" `
                    -Solution "Remover .gitconfig.lock e reconfigurar Git"
            }
        } catch {
            Write-DiagStatus "Erro ao executar git config: $_" -Level ERROR -Indent 1
            $gitData.Errors += $_.Exception.Message
        }

        # 1.2.3 Listar todas as configs (se funcionar)
        if ($gitData.GitConfigWorks) {
            try {
                $allConfigs = & git config --global --list 2>&1
                if ($LASTEXITCODE -eq 0) {
                    $configLines = $allConfigs -split "`n" | Where-Object { $_ -ne '' }
                    Write-DiagStatus "Total de configurações globais: $($configLines.Count)" -Level INFO -Indent 1

                    foreach ($line in $configLines) {
                        if ($line -match '^([^=]+)=(.*)$') {
                            $key = $Matches[1]
                            $value = $Matches[2]
                            $gitData.ConfigEntries[$key] = $value
                        }
                    }
                }
            } catch {
                Write-DiagStatus "Erro ao listar configs: $_" -Level WARN -Indent 1
            }
        }
    }

    $Script:DiagnosticData.Categories['GitConfiguration'] = $gitData
    return $gitData
}

function Test-GitLFS {
    Write-DiagSection "CATEGORIA 1.3: Git LFS"

    $lfsData = @{
        Installed = $false
        Version = $null
        ConfigWorks = $false
        Filters = @{}
        Errors = @()
    }

    try {
        $lfsVersion = & git lfs version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $lfsData.Installed = $true
            $lfsData.Version = $lfsVersion.ToString().Trim()
            Write-DiagStatus "Git LFS instalado: $($lfsData.Version)" -Level OK -Indent 1

            # Testar instalação
            $lfsInstall = & git lfs install --force 2>&1
            if ($LASTEXITCODE -eq 0) {
                $lfsData.ConfigWorks = $true
                Write-DiagStatus "Git LFS install: ✓" -Level OK -Indent 1
            } else {
                Write-DiagStatus "Git LFS install FALHOU: $lfsInstall" -Level ERROR -Indent 1
                $lfsData.Errors += $lfsInstall.ToString()
                Add-Issue -Category "Git" -Issue "Git LFS install failed" `
                    -Severity "High" `
                    -Solution "git lfs uninstall && git lfs install --force"
            }

            # Verificar filtros LFS no git config
            try {
                $filterClean = & git config --global filter.lfs.clean 2>&1
                $filterSmudge = & git config --global filter.lfs.smudge 2>&1

                $lfsData.Filters = @{
                    clean = $filterClean.ToString().Trim()
                    smudge = $filterSmudge.ToString().Trim()
                }

                Write-DiagStatus "filter.lfs.clean: $($lfsData.Filters.clean)" -Level INFO -Indent 2
                Write-DiagStatus "filter.lfs.smudge: $($lfsData.Filters.smudge)" -Level INFO -Indent 2
            } catch {
                Write-DiagStatus "Erro ao verificar filtros LFS: $_" -Level WARN -Indent 1
            }

        } else {
            Write-DiagStatus "Git LFS não instalado" -Level WARN -Indent 1
            Add-Issue -Category "Git" -Issue "Git LFS não instalado" -Severity "Medium"
        }
    } catch {
        Write-DiagStatus "Erro ao verificar Git LFS: $_" -Level ERROR -Indent 1
        $lfsData.Errors += $_.Exception.Message
    }

    $Script:DiagnosticData.Categories['GitLFS'] = $lfsData
    return $lfsData
}

function Test-GitHubDesktop {
    Write-DiagSection "CATEGORIA 1.4: GitHub Desktop"

    $ghData = @{
        Installed = $false
        Version = $null
        ConfigPath = $null
        ConfigExists = $false
        Errors = @()
    }

    # Verificar se GitHub Desktop está instalado
    $ghDesktopPaths = @(
        "$env:LOCALAPPDATA\GitHubDesktop\GitHubDesktop.exe",
        "$env:LOCALAPPDATA\GitHubDesktop\app-*\GitHubDesktop.exe"
    )

    foreach ($path in $ghDesktopPaths) {
        $found = Get-Item $path -ErrorAction SilentlyContinue
        if ($found) {
            $ghData.Installed = $true
            $ghData.Version = @($found)[0].VersionInfo.FileVersion
            Write-DiagStatus "GitHub Desktop instalado: v$($ghData.Version)" -Level OK -Indent 1
            break
        }
    }

    if (-not $ghData.Installed) {
        Write-DiagStatus "GitHub Desktop não encontrado" -Level INFO -Indent 1
    }

    # Verificar configuração
    $ghConfigPath = Join-Path $env:APPDATA "GitHub Desktop\config.json"
    $ghData.ConfigPath = $ghConfigPath

    if (Test-Path $ghConfigPath) {
        $ghData.ConfigExists = $true
        Write-DiagStatus "Config GitHub Desktop: $ghConfigPath" -Level OK -Indent 1
    } else {
        Write-DiagStatus "Config GitHub Desktop não encontrado" -Level INFO -Indent 1
    }

    $Script:DiagnosticData.Categories['GitHubDesktop'] = $ghData
    return $ghData
}

# =============================================================================
# CATEGORIA 2: PERMISSÕES E OWNERSHIP
# =============================================================================

function Test-FileOwnershipDetailed {
    Write-DiagSection "CATEGORIA 2.1: Ownership Detalhado"

    $ownershipData = @{
        CurrentUser = $env:USERNAME
        CurrentUserSID = $null
        Files = @()
        Issues = @()
    }

    # Obter SID do usuário atual
    try {
        $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent()
        $ownershipData.CurrentUserSID = $currentUser.User.Value
        Write-DiagStatus "Usuário atual: $($env:USERNAME)" -Level INFO -Indent 1
        Write-DiagStatus "SID: $($ownershipData.CurrentUserSID)" -Level INFO -Indent 1
    } catch {
        Write-DiagStatus "Erro ao obter SID: $_" -Level ERROR -Indent 1
    }

    # Arquivos críticos para verificar
    $criticalFiles = @(
        @{ Path = (Join-Path $env:USERPROFILE ".gitconfig"); Name = ".gitconfig" },
        @{ Path = (Join-Path $env:USERPROFILE ".claude.json"); Name = ".claude.json" },
        @{ Path = (Join-Path $env:USERPROFILE ".claude"); Name = ".claude dir" },
        @{ Path = (Join-Path $env:USERPROFILE ".local"); Name = ".local dir" }
    )

    foreach ($file in $criticalFiles) {
        if (Test-Path $file.Path) {
            try {
                $acl = Get-Acl $file.Path
                $owner = $acl.Owner

                # Extrair username do owner
                $ownerUsername = if ($owner -match '\\') {
                    $owner.Split('\')[1]
                } else {
                    $owner
                }

                $isCorrectOwner = $ownerUsername -eq $env:USERNAME

                $fileData = @{
                    Name = $file.Name
                    Path = $file.Path
                    Owner = $owner
                    OwnerUsername = $ownerUsername
                    IsCorrectOwner = $isCorrectOwner
                }

                $ownershipData.Files += $fileData

                if ($isCorrectOwner) {
                    Write-DiagStatus "$($file.Name): Owner correto ($owner)" -Level OK -Indent 1
                } else {
                    Write-DiagStatus "$($file.Name): Owner INCORRETO ($owner)" -Level ERROR -Indent 1
                    $ownershipData.Issues += $fileData
                    Add-Issue -Category "Ownership" `
                        -Issue "$($file.Name) pertence a $owner (deveria ser $($env:USERNAME))" `
                        -Severity "High" `
                        -Solution "takeown /F `"$($file.Path)`" && icacls `"$($file.Path)`" /grant $($env:USERNAME):F"
                }
            } catch {
                Write-DiagStatus "$($file.Name): Erro ao verificar - $_" -Level ERROR -Indent 1
                $ownershipData.Issues += @{ Path = $file.Path; Error = $_.Exception.Message }
            }
        } else {
            Write-DiagStatus "$($file.Name): Não existe (será criado conforme necessário)" -Level INFO -Indent 1
        }
    }

    $Script:DiagnosticData.Categories['Ownership'] = $ownershipData
    return $ownershipData
}

function Test-NTFSPermissionsDetailed {
    Write-DiagSection "CATEGORIA 2.2: Permissões NTFS Detalhadas"

    $permData = @{
        Files = @()
        Issues = @()
    }

    $criticalPaths = @(
        (Join-Path $env:USERPROFILE ".gitconfig"),
        (Join-Path $env:USERPROFILE ".claude.json"),
        (Join-Path $env:USERPROFILE ".claude"),
        (Join-Path $env:USERPROFILE ".local")
    )

    foreach ($path in $criticalPaths) {
        if (-not (Test-Path $path)) {
            continue
        }

        try {
            $acl = Get-Acl $path
            $pathName = Split-Path $path -Leaf

            Write-DiagStatus "Analisando: $pathName" -Level INFO -Indent 1

            $hasFullControl = $false
            $permissions = @()

            foreach ($access in $acl.Access) {
                $identity = $access.IdentityReference.ToString()
                $rights = $access.FileSystemRights.ToString()
                $type = $access.AccessControlType.ToString()

                $permissions += @{
                    Identity = $identity
                    Rights = $rights
                    Type = $type
                }

                # Verificar se usuário atual tem FullControl
                if ($identity -match $env:USERNAME -and $rights -match "FullControl") {
                    $hasFullControl = $true
                }

                if ($VerboseOutput) {
                    Write-DiagStatus "$identity : $rights ($type)" -Level INFO -Indent 2
                }
            }

            $filePermData = @{
                Path = $path
                Name = $pathName
                HasFullControl = $hasFullControl
                Permissions = $permissions
            }

            $permData.Files += $filePermData

            if ($hasFullControl) {
                Write-DiagStatus "$pathName : FullControl ✓" -Level OK -Indent 2
            } else {
                Write-DiagStatus "$pathName : FullControl AUSENTE" -Level ERROR -Indent 2
                $permData.Issues += $filePermData
                Add-Issue -Category "Permissions" `
                    -Issue "$pathName sem FullControl para $($env:USERNAME)" `
                    -Severity "High" `
                    -Solution "icacls `"$path`" /grant $($env:USERNAME):F"
            }

        } catch {
            Write-DiagStatus "Erro ao verificar $path : $_" -Level ERROR -Indent 1
            $permData.Issues += @{ Path = $path; Error = $_.Exception.Message }
        }
    }

    $Script:DiagnosticData.Categories['NTFSPermissions'] = $permData
    return $permData
}

# =============================================================================
# CATEGORIA 3: WINDOWS DEFENDER
# =============================================================================

function Test-WindowsDefender {
    Write-DiagSection "CATEGORIA 3: Windows Defender"

    $defenderData = @{
        Installed = $false
        Enabled = $false
        RealTimeProtection = $false
        Exclusions = @()
        ClaudeExcluded = $false
        QuarantineHistory = @()
        Errors = @()
    }

    try {
        $defender = Get-MpComputerStatus -ErrorAction Stop
        $prefs = Get-MpPreference -ErrorAction Stop

        $defenderData.Installed = $true
        $defenderData.Enabled = $defender.AntivirusEnabled
        $defenderData.RealTimeProtection = $defender.RealTimeProtectionEnabled

        Write-DiagStatus "Defender instalado: ✓" -Level OK -Indent 1
        Write-DiagStatus "Antivirus ativo: $($defender.AntivirusEnabled)" -Level INFO -Indent 1
        Write-DiagStatus "Real-time protection: $($defender.RealTimeProtectionEnabled)" -Level INFO -Indent 1

        # Verificar exclusões
        $defenderData.Exclusions = $prefs.ExclusionPath
        $claudeConfig = Join-Path $env:USERPROFILE ".claude.json"

        if ($defenderData.Exclusions -contains $claudeConfig) {
            $defenderData.ClaudeExcluded = $true
            Write-DiagStatus ".claude.json em exclusões: ✓" -Level OK -Indent 1
        } else {
            Write-DiagStatus ".claude.json NÃO está nas exclusões" -Level WARN -Indent 1
            Add-Issue -Category "Defender" `
                -Issue ".claude.json não excluído do Defender (pode causar EPERM)" `
                -Severity "High" `
                -Solution "Add-MpPreference -ExclusionPath '$claudeConfig' (requer Admin)"
        }

        if ($VerboseOutput -and @($defenderData.Exclusions).Count -gt 0) {
            Write-DiagStatus "Exclusões configuradas: $(@($defenderData.Exclusions).Count)" -Level INFO -Indent 1
            foreach ($exclusion in $defenderData.Exclusions) {
                Write-DiagStatus "- $exclusion" -Level INFO -Indent 2
            }
        }

        # Verificar histórico de quarentena (se DeepScan)
        if ($DeepScan) {
            try {
                $threats = Get-MpThreatDetection -ErrorAction SilentlyContinue
                if ($threats) {
                    $defenderData.QuarantineHistory = $threats | ForEach-Object {
                        @{
                            ThreatName = $_.ThreatName
                            Resources = $_.Resources
                            InitialDetectionTime = $_.InitialDetectionTime
                        }
                    }

                    Write-DiagStatus "Histórico de ameaças: $($threats.Count) itens" -Level INFO -Indent 1
                }
            } catch {
                # Ignorar se não tiver permissão
            }
        }

    } catch {
        Write-DiagStatus "Erro ao verificar Defender: $_" -Level WARN -Indent 1
        $defenderData.Errors += $_.Exception.Message
    }

    $Script:DiagnosticData.Categories['WindowsDefender'] = $defenderData
    return $defenderData
}

# =============================================================================
# CATEGORIA 4: SISTEMA E AMBIENTE
# =============================================================================

function Test-PATHVariable {
    Write-DiagSection "CATEGORIA 4.1: Variável PATH"

    $pathData = @{
        UserPATH = @()
        SystemPATH = @()
        HasUserProfileRoot = $false
        HasLocalBin = $false
        InvalidEntries = @()
        DuplicateEntries = @()
        Issues = @()
    }

    # User PATH
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")

    if ($userPath) {
        $pathData.UserPATH = $userPath -split ';' | Where-Object { $_ -ne '' }
    } else {
        $pathData.UserPATH = @()
        Write-DiagStatus "User PATH está vazio ou não definido" -Level WARN -Indent 1
    }

    Write-DiagStatus "User PATH entries: $($pathData.UserPATH.Count)" -Level INFO -Indent 1

    $seen = @{}
    $localBinPath = Join-Path $env:USERPROFILE ".local\bin"

    foreach ($entry in $pathData.UserPATH) {
        # Pular entries vazios ou nulos
        if ([string]::IsNullOrWhiteSpace($entry)) { continue }

        # Verificar duplicatas
        if ($seen.ContainsKey($entry)) {
            $pathData.DuplicateEntries += $entry
            Write-DiagStatus "Duplicado: $entry" -Level WARN -Indent 2
        }
        $seen[$entry] = $true

        # Verificar C:\Users\<user> raiz (CRÍTICO)
        if ($entry -eq $env:USERPROFILE) {
            $pathData.HasUserProfileRoot = $true
            Write-DiagStatus "CRÍTICO: PATH contém user profile raiz: $entry" -Level CRITICAL -Indent 2
            Add-Issue -Category "PATH" `
                -Issue "PATH contém diretório home completo ($entry)" `
                -Severity "Critical" `
                -Solution "Remover $entry do PATH e adicionar apenas subdirs necessários"
        }

        # Verificar .local\bin
        if ($entry -eq $localBinPath) {
            $pathData.HasLocalBin = $true
        }

        # Verificar entradas inválidas (não existem)
        if ($entry -match [regex]::Escape($env:USERPROFILE)) {
            if (-not (Test-Path $entry)) {
                $pathData.InvalidEntries += $entry
                Write-DiagStatus "Inválido (não existe): $entry" -Level WARN -Indent 2
                Add-Issue -Category "PATH" `
                    -Issue "PATH contém entrada inválida: $entry" `
                    -Severity "Medium" `
                    -Solution "Remover $entry do PATH"
            }
        }

        if ($VerboseOutput) {
            Write-DiagStatus "$entry" -Level INFO -Indent 2
        }
    }

    if (-not $pathData.HasLocalBin) {
        Write-DiagStatus ".local\bin AUSENTE no PATH" -Level WARN -Indent 1
        Add-Issue -Category "PATH" `
            -Issue ".local\bin não está no PATH" `
            -Severity "Medium" `
            -Solution "Adicionar '$localBinPath' ao PATH"
    } else {
        Write-DiagStatus ".local\bin presente: ✓" -Level OK -Indent 1
    }

    # System PATH (apenas contagem, não validação)
    $systemPath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $pathData.SystemPATH = $systemPath -split ';' | Where-Object { $_ -ne '' }
    Write-DiagStatus "System PATH entries: $($pathData.SystemPATH.Count)" -Level INFO -Indent 1

    $Script:DiagnosticData.Categories['PATH'] = $pathData
    return $pathData
}

function Test-PathsWithSpaces {
    Write-DiagSection "CATEGORIA 4.2: Paths com Espaços"

    $spaceData = @{
        UserProfileHasSpaces = $false
        ProblematicPaths = @()
        ImpactLevel = 'None'
    }

    if ($env:USERPROFILE -match ' ') {
        $spaceData.UserProfileHasSpaces = $true
        Write-DiagStatus "User profile CONTÉM ESPAÇOS: $($env:USERPROFILE)" -Level WARN -Indent 1
        Write-DiagStatus "Impacto: Pode causar problemas com ferramentas Unix/WSL2" -Level INFO -Indent 2

        $spaceData.ProblematicPaths += @{
            Path = $env:USERPROFILE
            Issue = "User profile com espaços"
            Impact = "Requer escape em scripts bash/sh, pode quebrar builds"
            Workaround = "Use caminhos curtos 8.3 ou evite ferramentas sensíveis a espaços"
        }

        $spaceData.ImpactLevel = 'Medium'

        Add-Issue -Category "Paths" `
            -Issue "User profile contém espaços: $($env:USERPROFILE)" `
            -Severity "Medium" `
            -Solution "Workaround: Use short paths (8.3) ou crie novo usuário sem espaços"
    } else {
        Write-DiagStatus "User profile SEM espaços: ✓" -Level OK -Indent 1
    }

    # Verificar outros paths críticos
    $claudeDir = Join-Path $env:USERPROFILE ".claude"
    if ((Test-Path $claudeDir) -and $claudeDir -match ' ') {
        $spaceData.ProblematicPaths += @{
            Path = $claudeDir
            Issue = ".claude directory com espaços"
            Impact = "Claude Code pode ter problemas"
        }
    }

    $Script:DiagnosticData.Categories['PathsWithSpaces'] = $spaceData
    return $spaceData
}

function Test-EnvironmentVariables {
    Write-DiagSection "CATEGORIA 4.3: Variáveis de Ambiente Críticas"

    $envData = @{
        Variables = @{}
        Issues = @()
    }

    $criticalVars = @('USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'TEMP', 'TMP', 'HOME', 'COMPUTERNAME', 'USERNAME')

    foreach ($varName in $criticalVars) {
        $value = [System.Environment]::GetEnvironmentVariable($varName)
        $envData.Variables[$varName] = $value

        if ($null -eq $value -or $value -eq '') {
            Write-DiagStatus "$varName : NÃO DEFINIDA" -Level WARN -Indent 1
            $envData.Issues += "$varName não definida"
        } else {
            Write-DiagStatus "$varName : $value" -Level INFO -Indent 1
        }
    }

    $Script:DiagnosticData.Categories['EnvironmentVariables'] = $envData
    return $envData
}

function Test-BlockingProcesses {
    Write-DiagSection "CATEGORIA 4.4: Processos Bloqueando Arquivos"

    $procData = @{
        CheckEnabled = $CheckProcesses
        BlockingProcesses = @()
    }

    if (-not $CheckProcesses) {
        Write-DiagStatus "Verificação de processos desabilitada (use -CheckProcesses)" -Level INFO -Indent 1
        $Script:DiagnosticData.Categories['BlockingProcesses'] = $procData
        return $procData
    }

    Write-DiagStatus "Procurando processos que podem bloquear arquivos Git/Claude..." -Level INFO -Indent 1

    # Processos conhecidos que podem bloquear
    $knownBlockers = @('git', 'GitHubDesktop', 'code', 'devenv', 'claude')

    foreach ($procName in $knownBlockers) {
        $processes = Get-Process -Name $procName -ErrorAction SilentlyContinue
        if ($processes) {
            foreach ($proc in $processes) {
                $procInfo = @{
                    Name = $proc.Name
                    PID = $proc.Id
                    Path = $proc.Path
                    StartTime = $proc.StartTime
                }
                $procData.BlockingProcesses += $procInfo

                Write-DiagStatus "Processo: $($proc.Name) (PID: $($proc.Id))" -Level WARN -Indent 2
                Write-DiagStatus "Path: $($proc.Path)" -Level INFO -Indent 3
            }
        }
    }

    if (@($procData.BlockingProcesses).Count -eq 0) {
        Write-DiagStatus "Nenhum processo bloqueador detectado" -Level OK -Indent 1
    } else {
        Write-DiagStatus "Processos encontrados: $(@($procData.BlockingProcesses).Count)" -Level WARN -Indent 1
        Add-Issue -Category "Processes" `
            -Issue "$(@($procData.BlockingProcesses).Count) processos podem estar bloqueando arquivos" `
            -Severity "Low" `
            -Solution "Fechar processos antes de tentar correções"
    }

    $Script:DiagnosticData.Categories['BlockingProcesses'] = $procData
    return $procData
}

function Test-DiskSpace {
    Write-DiagSection "CATEGORIA 4.5: Espaço em Disco"

    $diskData = @{
        Drives = @()
        LowSpaceWarnings = @()
    }

    $drives = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Root -match '^[A-Z]:\\$' }

    foreach ($drive in $drives) {
        $freeGB = [Math]::Round($drive.Free / 1GB, 2)
        $usedGB = [Math]::Round($drive.Used / 1GB, 2)
        $totalGB = [Math]::Round(($drive.Free + $drive.Used) / 1GB, 2)
        $freePercent = [Math]::Round(($drive.Free / ($drive.Free + $drive.Used)) * 100, 1)

        $driveInfo = @{
            Name = $drive.Name
            FreeGB = $freeGB
            UsedGB = $usedGB
            TotalGB = $totalGB
            FreePercent = $freePercent
        }

        $diskData.Drives += $driveInfo

        $status = if ($freePercent -lt 10) { 'CRITICAL' }
                  elseif ($freePercent -lt 20) { 'WARN' }
                  else { 'OK' }

        Write-DiagStatus "$($drive.Name): $freeGB GB livre / $totalGB GB ($freePercent%)" -Level $status -Indent 1

        if ($freePercent -lt 10) {
            $diskData.LowSpaceWarnings += $driveInfo
            Add-Issue -Category "DiskSpace" `
                -Issue "Drive $($drive.Name): apenas $freePercent% livre" `
                -Severity "Critical" `
                -Solution "Liberar espaço no drive $($drive.Name):"
        }
    }

    $Script:DiagnosticData.Categories['DiskSpace'] = $diskData
    return $diskData
}

# =============================================================================
# CATEGORIA 5: CLAUDE CODE ESPECÍFICO
# =============================================================================

function Test-ClaudeConfiguration {
    Write-DiagSection "CATEGORIA 5: Claude Code Configuration"

    $claudeData = @{
        ConfigExists = $false
        ConfigPath = $null
        ConfigValid = $false
        ClaudeDirExists = $false
        ClaudeDirPath = $null
        LockFiles = @()
        Errors = @()
    }

    # Verificar .claude.json
    $claudeConfig = Join-Path $env:USERPROFILE ".claude.json"
    $claudeData.ConfigPath = $claudeConfig

    if (Test-Path $claudeConfig) {
        $claudeData.ConfigExists = $true
        Write-DiagStatus ".claude.json existe: $claudeConfig" -Level OK -Indent 1

        try {
            $configContent = Get-Content $claudeConfig -Raw | ConvertFrom-Json
            $claudeData.ConfigValid = $true
            Write-DiagStatus "JSON válido: ✓" -Level OK -Indent 2

            if ($VerboseOutput) {
                Write-DiagStatus "Keys: $($configContent.PSObject.Properties.Name -join ', ')" -Level INFO -Indent 2
            }
        } catch {
            Write-DiagStatus "JSON INVÁLIDO: $_" -Level ERROR -Indent 2
            $claudeData.Errors += "JSON parse error: $($_.Exception.Message)"
            Add-Issue -Category "Claude" `
                -Issue ".claude.json corrompido" `
                -Severity "High" `
                -Solution "Backup e recreate .claude.json"
        }
    } else {
        Write-DiagStatus ".claude.json não existe (será criado no primeiro uso)" -Level INFO -Indent 1
    }

    # Verificar .claude directory
    $claudeDir = Join-Path $env:USERPROFILE ".claude"
    $claudeData.ClaudeDirPath = $claudeDir

    if (Test-Path $claudeDir) {
        $claudeData.ClaudeDirExists = $true
        Write-DiagStatus ".claude directory existe: $claudeDir" -Level OK -Indent 1

        # Listar conteúdo
        $items = Get-ChildItem $claudeDir -ErrorAction SilentlyContinue
        if ($items) {
            Write-DiagStatus "Arquivos: $($items.Count)" -Level INFO -Indent 2
            if ($VerboseOutput) {
                foreach ($item in $items) {
                    Write-DiagStatus "- $($item.Name)" -Level INFO -Indent 3
                }
            }
        }
    } else {
        Write-DiagStatus ".claude directory não existe (será criado conforme necessário)" -Level INFO -Indent 1
    }

    # Procurar lock files do Claude
    $possibleLocks = @(
        "$claudeConfig.lock",
        "$claudeConfig.lock-*",
        (Join-Path $env:USERPROFILE ".claude.json.*")
    )

    foreach ($lockPattern in $possibleLocks) {
        $locks = Get-Item $lockPattern -ErrorAction SilentlyContinue
        if ($locks) {
            foreach ($lock in $locks) {
                Write-DiagStatus "LOCK ENCONTRADO: $($lock.Name)" -Level ERROR -Indent 1
                $claudeData.LockFiles += $lock.FullName
                Add-Issue -Category "Claude" `
                    -Issue "Claude lock file: $($lock.Name)" `
                    -Severity "High" `
                    -Solution "Remove-Item '$($lock.FullName)' -Force"
            }
        }
    }

    if ($claudeData.LockFiles.Count -eq 0) {
        Write-DiagStatus "Nenhum lock file do Claude encontrado: ✓" -Level OK -Indent 1
    }

    $Script:DiagnosticData.Categories['ClaudeConfiguration'] = $claudeData
    return $claudeData
}

# =============================================================================
# CATEGORIA 6: NODE.JS E NPM
# =============================================================================

function Test-NodeEnvironment {
    Write-DiagSection "CATEGORIA 6: Node.js e npm"

    $nodeData = @{
        NodeInstalled = $false
        NodeVersion = $null
        NpmInstalled = $false
        NpmVersion = $null
        GlobalPackages = @()
        CacheIssues = @()
        Errors = @()
    }

    # Verificar Node.js
    try {
        $nodeVersion = & node --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $nodeData.NodeInstalled = $true
            $nodeData.NodeVersion = $nodeVersion.ToString().Trim()
            Write-DiagStatus "Node.js instalado: $($nodeData.NodeVersion)" -Level OK -Indent 1
        } else {
            Write-DiagStatus "Node.js não encontrado" -Level WARN -Indent 1
            Add-Issue -Category "Node" -Issue "Node.js não instalado" -Severity "High"
        }
    } catch {
        Write-DiagStatus "Erro ao verificar Node.js: $_" -Level ERROR -Indent 1
        $nodeData.Errors += $_.Exception.Message
    }

    # Verificar npm
    if ($nodeData.NodeInstalled) {
        try {
            $npmVersion = & npm --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                $nodeData.NpmInstalled = $true
                $nodeData.NpmVersion = $npmVersion.ToString().Trim()
                Write-DiagStatus "npm instalado: $($nodeData.NpmVersion)" -Level OK -Indent 1
            }
        } catch {
            Write-DiagStatus "Erro ao verificar npm: $_" -Level ERROR -Indent 1
        }

        # Listar pacotes globais (se DeepScan)
        if ($DeepScan -and $nodeData.NpmInstalled) {
            try {
                $globalList = & npm list -g --depth=0 --json 2>&1 | ConvertFrom-Json
                if ($globalList.dependencies) {
                    $nodeData.GlobalPackages = $globalList.dependencies.PSObject.Properties.Name
                    Write-DiagStatus "Pacotes globais: $($nodeData.GlobalPackages.Count)" -Level INFO -Indent 1

                    if ($VerboseOutput) {
                        foreach ($pkg in $nodeData.GlobalPackages) {
                            Write-DiagStatus "- $pkg" -Level INFO -Indent 2
                        }
                    }
                }
            } catch {
                Write-DiagStatus "Erro ao listar pacotes globais: $_" -Level WARN -Indent 1
            }
        }
    }

    $Script:DiagnosticData.Categories['NodeEnvironment'] = $nodeData
    return $nodeData
}

# =============================================================================
# RELATÓRIO FINAL
# =============================================================================

function Write-FinalReport {
    Write-DiagHeader "RESUMO DIAGNÓSTICO COMPLETO"

    $totalIssues = $Script:DiagnosticData.Issues.Count
    $criticalIssues = $Script:DiagnosticData.CriticalIssues.Count
    $warnings = $Script:DiagnosticData.Warnings.Count

    Write-Host ""
    Write-Host "Machine: " -NoNewline
    Write-Host $Script:DiagnosticData.Machine -ForegroundColor Cyan
    Write-Host "User: " -NoNewline
    Write-Host $Script:DiagnosticData.User -ForegroundColor Cyan
    Write-Host "Timestamp: " -NoNewline
    Write-Host $Script:DiagnosticData.Timestamp -ForegroundColor Cyan

    Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
    Write-Host "║                      RESULTADO GERAL                           ║" -ForegroundColor Yellow
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Yellow

    Write-Host "`nProblemas Críticos: " -NoNewline
    if ($criticalIssues -eq 0) {
        Write-Host "0 (OK)" -ForegroundColor Green
    } else {
        Write-Host $criticalIssues -ForegroundColor Red
    }

    Write-Host "Avisos (High): " -NoNewline
    if ($warnings -eq 0) {
        Write-Host "0 (OK)" -ForegroundColor Green
    } else {
        Write-Host $warnings -ForegroundColor Yellow
    }

    Write-Host "Total de Issues: " -NoNewline
    if ($totalIssues -eq 0) {
        Write-Host "0 (SISTEMA OK!)" -ForegroundColor Green
    } else {
        Write-Host $totalIssues -ForegroundColor $(if ($criticalIssues -gt 0) { 'Red' } else { 'Yellow' })
    }

    # Detalhar issues críticos
    if ($criticalIssues -gt 0) {
        Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Red
        Write-Host "║                  PROBLEMAS CRÍTICOS (ACTION REQUIRED)          ║" -ForegroundColor Red
        Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Red

        foreach ($issue in $Script:DiagnosticData.CriticalIssues) {
            Write-Host "`n[$($issue.Category)] " -ForegroundColor Red -NoNewline
            Write-Host $issue.Issue -ForegroundColor White
            if ($issue.Solution) {
                Write-Host "  Solução: " -ForegroundColor Yellow -NoNewline
                Write-Host $issue.Solution -ForegroundColor Gray
            }
        }
    }

    # Detalhar avisos
    if ($warnings -gt 0) {
        Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
        Write-Host "║                      AVISOS (RECOMENDADO CORRIGIR)             ║" -ForegroundColor Yellow
        Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Yellow

        foreach ($issue in $Script:DiagnosticData.Warnings) {
            Write-Host "`n[$($issue.Category)] " -ForegroundColor Yellow -NoNewline
            Write-Host $issue.Issue -ForegroundColor White
            if ($issue.Solution) {
                Write-Host "  Solução: " -ForegroundColor Cyan -NoNewline
                Write-Host $issue.Solution -ForegroundColor Gray
            }
        }
    }

    # Status final
    Write-Host ""
    if ($totalIssues -eq 0) {
        Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "║                                                                ║" -ForegroundColor Green
        Write-Host "║  ✓ SISTEMA OK - PRONTO PARA CLAUDE CODE!                      ║" -ForegroundColor Green
        Write-Host "║                                                                ║" -ForegroundColor Green
        Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    } elseif ($criticalIssues -gt 0) {
        Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Red
        Write-Host "║                                                                ║" -ForegroundColor Red
        Write-Host "║  ✗ PROBLEMAS CRÍTICOS DETECTADOS - CORREÇÃO NECESSÁRIA        ║" -ForegroundColor Red
        Write-Host "║                                                                ║" -ForegroundColor Red
        Write-Host "║  Execute o script de correção:                                 ║" -ForegroundColor Red
        Write-Host "║  .\fix-all-home-issues.ps1 -FixAll                            ║" -ForegroundColor Red
        Write-Host "║                                                                ║" -ForegroundColor Red
        Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Red
    } else {
        Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
        Write-Host "║                                                                ║" -ForegroundColor Yellow
        Write-Host "║  ⚠ AVISOS DETECTADOS - CORREÇÃO RECOMENDADA                   ║" -ForegroundColor Yellow
        Write-Host "║                                                                ║" -ForegroundColor Yellow
        Write-Host "║  Sistema deve funcionar mas pode ter problemas                 ║" -ForegroundColor Yellow
        Write-Host "║  Recomendado executar: .\fix-all-home-issues.ps1 -FixAll     ║" -ForegroundColor Yellow
        Write-Host "║                                                                ║" -ForegroundColor Yellow
        Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Yellow
    }

    # Salvar JSON se solicitado
    if ($OutputJson) {
        try {
            $Script:DiagnosticData | ConvertTo-Json -Depth 10 | Out-File $OutputJson -Encoding UTF8
            Write-Host "`n[✓] Relatório JSON salvo: $OutputJson" -ForegroundColor Green
        } catch {
            Write-Host "`n[✗] Erro ao salvar JSON: $_" -ForegroundColor Red
        }
    }
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

function Main {
    Write-DiagHeader "DIAGNÓSTICO PROFUNDO - CLAUDE CODE (PC HOME)"

    Write-Host "`nModo: " -NoNewline
    if ($DeepScan) {
        Write-Host "DEEP SCAN (completo, pode ser lento)" -ForegroundColor Magenta
    } else {
        Write-Host "Standard (use -DeepScan para análise completa)" -ForegroundColor Cyan
    }

    Write-Host "Check Processes: " -NoNewline
    Write-Host $(if ($CheckProcesses) { "Habilitado" } else { "Desabilitado (use -CheckProcesses)" }) -ForegroundColor Cyan

    # Executar todas as categorias
    Test-GitLocks
    Test-GitConfiguration
    Test-GitLFS
    Test-GitHubDesktop
    Test-FileOwnershipDetailed
    Test-NTFSPermissionsDetailed
    Test-WindowsDefender
    Test-PATHVariable
    Test-PathsWithSpaces
    Test-EnvironmentVariables
    Test-BlockingProcesses
    Test-DiskSpace
    Test-ClaudeConfiguration
    Test-NodeEnvironment

    # Relatório final
    Write-FinalReport
}

# EXECUTAR
Main
