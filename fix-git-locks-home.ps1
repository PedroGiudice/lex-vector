#Requires -Version 5.1
<#
.SYNOPSIS
    Correção de locks Git e preparação para Claude Code via WSL2 (PC Home)

.DESCRIPTION
    Resolve problemas de lock files no Git e GitHub Desktop:
    - Remove .gitconfig.lock órfão
    - Remove outros lock files do Git
    - Reinstala Git LFS
    - Valida configuração Git
    - Prepara ambiente para instalação Claude Code via WSL2

.NOTES
    Author: Claude Code
    Date: 2025-11-15
    Related: fix-home-windows-permissions.ps1

.PARAMETER DiagnoseOnly
    Apenas diagnóstico, sem fazer alterações

.PARAMETER FixAll
    Executa todas as correções necessárias

.PARAMETER Verbose
    Output detalhado

.EXAMPLE
    .\fix-git-locks-home.ps1 -DiagnoseOnly
    Apenas diagnóstico

.EXAMPLE
    .\fix-git-locks-home.ps1 -FixAll
    Corrige todos os problemas detectados
#>

param(
    [switch]$DiagnoseOnly,
    [switch]$FixAll,
    [switch]$VerboseOutput
)

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

$ErrorActionPreference = 'Continue'
$Script:Issues = @()
$Script:Fixes = @()
$Script:CurrentUser = $env:USERNAME
$Script:UserProfile = $env:USERPROFILE

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
        Write-Host ("═" * 60) -ForegroundColor $colors[$Level]
    } else {
        Write-Host "$($symbols[$Level]) " -ForegroundColor $colors[$Level] -NoNewline
        Write-Host $Message
    }
}

function Get-BooleanIcon {
    param([bool]$Value)
    if ($Value) { return "✓" } else { return "✗" }
}

# =============================================================================
# DIAGNÓSTICO - GIT LOCKS
# =============================================================================

function Find-GitLockFiles {
    Write-Status "Procurando lock files do Git..." -Level Info

    $lockLocations = @(
        @{
            Path = Join-Path $Script:UserProfile ".gitconfig.lock"
            Type = "GlobalConfig"
            Critical = $true
        },
        @{
            Path = Join-Path $Script:UserProfile ".gitconfig"
            Type = "GlobalConfigMain"
            Critical = $true
        },
        @{
            Path = Join-Path $env:ProgramData "Git\config.lock"
            Type = "SystemConfig"
            Critical = $false
        }
    )

    $foundLocks = @()

    foreach ($location in $lockLocations) {
        if ($location.Path -match "\.lock$") {
            # Arquivo de lock
            if (Test-Path $location.Path) {
                Write-Status "LOCK ENCONTRADO: $($location.Path)" -Level Error
                $foundLocks += @{
                    Path = $location.Path
                    Type = $location.Type
                    Critical = $location.Critical
                    IsLock = $true
                }

                # Verificar idade do arquivo
                $lockFile = Get-Item $location.Path
                $age = (Get-Date) - $lockFile.LastWriteTime
                Write-Status "  Idade: $($age.TotalHours.ToString('0.0')) horas" -Level Warning
            }
        } else {
            # Arquivo principal (verificar se existe)
            if (Test-Path $location.Path) {
                Write-Status "Configuração encontrada: $($location.Path)" -Level Success
            } else {
                Write-Status "Configuração ausente: $($location.Path)" -Level Warning
                if ($location.Critical) {
                    $Script:Issues += "Arquivo crítico ausente: $($location.Path)"
                }
            }
        }
    }

    # Verificar locks em repositórios locais
    $gitRepos = @(
        "C:\claude-work\repos\Claude-Code-Projetos"
    )

    foreach ($repo in $gitRepos) {
        if (Test-Path $repo) {
            $gitDir = Join-Path $repo ".git"
            if (Test-Path $gitDir) {
                $repoLocks = Get-ChildItem -Path $gitDir -Filter "*.lock" -Recurse -ErrorAction SilentlyContinue

                if ($repoLocks.Count -gt 0) {
                    Write-Status "Locks encontrados em repositório: $repo" -Level Warning
                    foreach ($lock in $repoLocks) {
                        Write-Status "  - $($lock.FullName)" -Level Warning
                        $foundLocks += @{
                            Path = $lock.FullName
                            Type = "RepositoryLock"
                            Critical = $false
                            IsLock = $true
                        }
                    }
                }
            }
        }
    }

    return $foundLocks
}

# =============================================================================
# DIAGNÓSTICO - GIT CONFIGURATION
# =============================================================================

function Test-GitConfiguration {
    Write-Status "Testando configuração Git..." -Level Info

    # Testar git config
    try {
        $userName = & git config --global user.name 2>&1
        $userEmail = & git config --global user.email 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Status "Git config funcionando: ✓" -Level Success
            Write-Status "  Nome: $userName" -Level Info
            Write-Status "  Email: $userEmail" -Level Info
            return $true
        } else {
            Write-Status "Git config FALHOU: $userName" -Level Error
            $Script:Issues += "Git config não funcional"
            return $false
        }
    } catch {
        Write-Status "Erro ao testar git config: $_" -Level Error
        $Script:Issues += "Git config error: $_"
        return $false
    }
}

function Test-GitLFS {
    Write-Status "Testando Git LFS..." -Level Info

    try {
        $lfsVersion = & git lfs version 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Status "Git LFS instalado: ✓" -Level Success
            Write-Status "  Versão: $lfsVersion" -Level Info

            # Testar instalação
            $lfsInstall = & git lfs install --force 2>&1

            if ($LASTEXITCODE -eq 0) {
                Write-Status "Git LFS install: ✓" -Level Success
                return $true
            } else {
                Write-Status "Git LFS install FALHOU: $lfsInstall" -Level Error
                $Script:Issues += "Git LFS install failed: $lfsInstall"
                return $false
            }
        } else {
            Write-Status "Git LFS não encontrado: $lfsVersion" -Level Warning
            return $false
        }
    } catch {
        Write-Status "Erro ao testar Git LFS: $_" -Level Error
        return $false
    }
}

# =============================================================================
# DIAGNÓSTICO - WSL2 READINESS
# =============================================================================

function Test-WSL2Readiness {
    Write-Status "Verificando prontidão para WSL2..." -Level Info

    $checks = @{
        WSLInstalled = $false
        WSL2Enabled = $false
        DistributionInstalled = $false
        VirtualizationEnabled = $false
    }

    # Verificar se WSL está instalado
    try {
        $wslVersion = & wsl --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $checks.WSLInstalled = $true
            Write-Status "WSL instalado: ✓" -Level Success
        } else {
            Write-Status "WSL não instalado" -Level Warning
        }
    } catch {
        Write-Status "WSL não disponível" -Level Warning
    }

    # Verificar WSL 2
    try {
        $wslList = & wsl --list --verbose 2>&1
        if ($wslList -match "VERSION 2") {
            $checks.WSL2Enabled = $true
            Write-Status "WSL 2 ativo: ✓" -Level Success
        }
        if ($wslList -match "Ubuntu|Debian|Alpine") {
            $checks.DistributionInstalled = $true
            Write-Status "Distribuição instalada: ✓" -Level Success
        }
    } catch {
        # Ignorar se WSL não estiver instalado
    }

    # Verificar virtualização
    try {
        $virtualization = Get-ComputerInfo | Select-Object -ExpandProperty HyperVisorPresent
        if ($virtualization) {
            $checks.VirtualizationEnabled = $true
            Write-Status "Virtualização habilitada: ✓" -Level Success
        } else {
            Write-Status "Virtualização desabilitada (necessário para WSL2)" -Level Warning
            $Script:Issues += "Virtualização precisa ser habilitada na BIOS"
        }
    } catch {
        Write-Status "Não foi possível verificar virtualização" -Level Warning
    }

    return $checks
}

# =============================================================================
# DIAGNÓSTICO - PATHS COM ESPAÇOS
# =============================================================================

function Test-PathsWithSpaces {
    Write-Status "Verificando paths com espaços..." -Level Info

    $problematicPaths = @()

    # Verificar user profile
    if ($Script:UserProfile -match " ") {
        Write-Status "User profile contém espaços: $Script:UserProfile" -Level Warning
        Write-Status "  Isso pode causar problemas com ferramentas Unix no WSL2" -Level Info
        $problematicPaths += @{
            Path = $Script:UserProfile
            Issue = "Espaços no caminho do perfil de usuário"
            Severity = "Medium"
            WSL2Impact = "Pode exigir escape de paths ou usar /mnt/c/Users/CMRADV~1/"
        }
    }

    # Verificar .claude
    $claudeDir = Join-Path $Script:UserProfile ".claude"
    if (Test-Path $claudeDir) {
        $fullPath = (Get-Item $claudeDir).FullName
        if ($fullPath -match " ") {
            $problematicPaths += @{
                Path = $fullPath
                Issue = "Espaços no caminho .claude"
                Severity = "High"
                WSL2Impact = "Claude Code pode ter problemas"
            }
        }
    }

    # Verificar repositórios Git
    if (Test-Path "C:\claude-work\repos") {
        Write-Status "Repositório em C:\claude-work\repos: ✓ (sem espaços)" -Level Success
    }

    return $problematicPaths
}

# =============================================================================
# CORREÇÃO - REMOVER LOCKS
# =============================================================================

function Remove-GitLocks {
    param([array]$Locks)

    Write-Status "Removendo lock files..." -Level Section

    $removed = 0
    $failed = 0

    foreach ($lock in $Locks) {
        if ($lock.IsLock) {
            Write-Status "Removendo: $($lock.Path)" -Level Info

            try {
                # Verificar se o arquivo existe (pode ter sido removido anteriormente)
                if (Test-Path $lock.Path) {
                    Remove-Item $lock.Path -Force -ErrorAction Stop
                    Write-Status "  Removido com sucesso" -Level Success
                    $removed++
                    $Script:Fixes += "Removido lock: $($lock.Path)"
                } else {
                    Write-Status "  Arquivo já não existe" -Level Info
                }
            } catch {
                Write-Status "  FALHA ao remover: $_" -Level Error
                $failed++
            }
        }
    }

    return @{
        Removed = $removed
        Failed = $failed
    }
}

# =============================================================================
# CORREÇÃO - REINSTALAR GIT LFS
# =============================================================================

function Repair-GitLFS {
    Write-Status "Reinstalando Git LFS..." -Level Section

    try {
        # Uninstall atual
        Write-Status "Desinstalando Git LFS..." -Level Info
        & git lfs uninstall 2>&1 | Out-Null

        # Reinstall
        Write-Status "Instalando Git LFS..." -Level Info
        $result = & git lfs install --force 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Status "Git LFS reinstalado com sucesso" -Level Success
            $Script:Fixes += "Git LFS reinstalado"
            return $true
        } else {
            Write-Status "Falha ao reinstalar Git LFS: $result" -Level Error
            return $false
        }
    } catch {
        Write-Status "Erro ao reinstalar Git LFS: $_" -Level Error
        return $false
    }
}

# =============================================================================
# MAIN
# =============================================================================

function Main {
    Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                                                                ║" -ForegroundColor Cyan
    Write-Host "║     CORREÇÃO GIT LOCKS + PREPARAÇÃO WSL2 - CLAUDE CODE        ║" -ForegroundColor Cyan
    Write-Host "║                 PC Home (CMR Advogados)                        ║" -ForegroundColor Cyan
    Write-Host "║                                                                ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

    # AMBIENTE
    Write-Status "DETECÇÃO DE AMBIENTE" -Level Section
    Write-Status "Usuário: $Script:CurrentUser" -Level Info
    Write-Status "Profile: $Script:UserProfile" -Level Info

    # DIAGNÓSTICO COMPLETO
    Write-Status "DIAGNÓSTICO - GIT LOCKS" -Level Section
    $locks = Find-GitLockFiles

    Write-Status "`nDIAGNÓSTICO - GIT CONFIGURATION" -Level Section
    $gitConfigOK = Test-GitConfiguration
    $gitLFSOK = Test-GitLFS

    Write-Status "`nDIAGNÓSTICO - WSL2 READINESS" -Level Section
    $wsl2Checks = Test-WSL2Readiness

    Write-Status "`nDIAGNÓSTICO - PATHS COM ESPAÇOS" -Level Section
    $pathIssues = Test-PathsWithSpaces

    # RESUMO
    Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
    Write-Host "║                     RESUMO DO DIAGNÓSTICO                      ║" -ForegroundColor Yellow
    Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Yellow

    Write-Host "Git Locks Encontrados: " -NoNewline
    if ($locks.Count -gt 0) {
        Write-Host "$($locks.Count)" -ForegroundColor Red
    } else {
        Write-Host "0 (OK)" -ForegroundColor Green
    }

    Write-Host "Git Config Funcionando: " -NoNewline
    Write-Host (Get-BooleanIcon $gitConfigOK) -ForegroundColor $(if ($gitConfigOK) { "Green" } else { "Red" })

    Write-Host "Git LFS Funcionando: " -NoNewline
    Write-Host (Get-BooleanIcon $gitLFSOK) -ForegroundColor $(if ($gitLFSOK) { "Green" } else { "Red" })

    Write-Host "WSL2 Instalado: " -NoNewline
    Write-Host (Get-BooleanIcon $wsl2Checks.WSLInstalled) -ForegroundColor $(if ($wsl2Checks.WSLInstalled) { "Green" } else { "Yellow" })

    Write-Host "Virtualização Habilitada: " -NoNewline
    Write-Host (Get-BooleanIcon $wsl2Checks.VirtualizationEnabled) -ForegroundColor $(if ($wsl2Checks.VirtualizationEnabled) { "Green" } else { "Yellow" })

    Write-Host "Paths com Espaços: " -NoNewline
    if ($pathIssues.Count -gt 0) {
        Write-Host "$($pathIssues.Count)" -ForegroundColor Yellow
    } else {
        Write-Host "0 (OK)" -ForegroundColor Green
    }

    Write-Host "`nProblemas Detectados: $($Script:Issues.Count)" -ForegroundColor $(if ($Script:Issues.Count -gt 0) { "Red" } else { "Green" })

    # MODO DIAGNÓSTICO
    if ($DiagnoseOnly) {
        Write-Host "`n" -NoNewline
        Write-Status "Modo diagnóstico - nenhuma correção aplicada" -Level Info

        if ($locks.Count -gt 0 -or -not $gitConfigOK -or -not $gitLFSOK) {
            Write-Host "`nPara corrigir problemas Git, execute:" -ForegroundColor Yellow
            Write-Host "  .\fix-git-locks-home.ps1 -FixAll" -ForegroundColor Green
        }

        if (-not $wsl2Checks.WSLInstalled) {
            Write-Host "`nPara instalar WSL2:" -ForegroundColor Yellow
            Write-Host "  wsl --install" -ForegroundColor Green
            Write-Host "  (requer reinicialização)" -ForegroundColor Gray
        }

        return
    }

    # CORREÇÃO
    if ($FixAll) {
        Write-Status "`nINICIANDO CORREÇÕES" -Level Section

        # Remover locks
        if ($locks.Count -gt 0) {
            $lockResult = Remove-GitLocks -Locks $locks
            Write-Status "Locks removidos: $($lockResult.Removed)" -Level Success
        }

        # Reinstalar Git LFS se necessário
        if (-not $gitLFSOK) {
            Repair-GitLFS
        }

        # VALIDAÇÃO PÓS-CORREÇÃO
        Write-Status "`nVALIDAÇÃO PÓS-CORREÇÃO" -Level Section
        $gitConfigAfter = Test-GitConfiguration
        $gitLFSAfter = Test-GitLFS

        # RESULTADO FINAL
        Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
        Write-Host "║                      RESULTADO FINAL                           ║" -ForegroundColor Cyan
        Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

        Write-Host "Correções aplicadas: $($Script:Fixes.Count)" -ForegroundColor Green
        foreach ($fix in $Script:Fixes) {
            Write-Host "  ✓ $fix" -ForegroundColor Gray
        }

        if ($gitConfigAfter -and $gitLFSAfter) {
            Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
            Write-Host "║                                                                ║" -ForegroundColor Green
            Write-Host "║  ✓ GIT E GIT LFS FUNCIONANDO CORRETAMENTE!                    ║" -ForegroundColor Green
            Write-Host "║                                                                ║" -ForegroundColor Green
            Write-Host "║  Próximos passos:                                              ║" -ForegroundColor Green
            Write-Host "║  1. Instalar WSL2 (se necessário): wsl --install              ║" -ForegroundColor Green
            Write-Host "║  2. Instalar Claude Code no WSL2                               ║" -ForegroundColor Green
            Write-Host "║                                                                ║" -ForegroundColor Green
            Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green
        } else {
            Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
            Write-Host "║                                                                ║" -ForegroundColor Yellow
            Write-Host "║  ⚠ ALGUNS PROBLEMAS PERSISTEM                                  ║" -ForegroundColor Yellow
            Write-Host "║                                                                ║" -ForegroundColor Yellow
            Write-Host "║  Verifique os erros acima e tente executar como Admin         ║" -ForegroundColor Yellow
            Write-Host "║                                                                ║" -ForegroundColor Yellow
            Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Yellow
        }
    }
}

# EXECUTAR
Main
