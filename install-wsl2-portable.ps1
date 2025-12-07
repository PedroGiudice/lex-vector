<#
.SYNOPSIS
    Script PORTATIL para instalacao do WSL2 em qualquer PC Windows.

.DESCRIPTION
    Este script foi projetado para funcionar em QUALQUER PC Windows:
    - Compativel com PowerShell 5.1 (padrao do Windows)
    - Sem caminhos absolutos
    - Fases separadas para lidar com reinicializacoes
    - Foco apenas em WSL2 (ambiente de desenvolvimento depois)

.PARAMETER Phase
    Fase da instalacao:
    - Check    : Verificar pre-requisitos
    - Enable   : Habilitar recursos WSL (requer restart)
    - Install  : Instalar Ubuntu (apos restart)
    - Validate : Verificar se tudo funcionou
    - Full     : Executar todas as fases em sequencia

.NOTES
    Versao: 2.0.0
    Autor: PedroGiudice
    Compatibilidade: Windows 10 build 19041+, Windows 11, PowerShell 5.1+

.EXAMPLE
    .\install-wsl2-portable.ps1 -Phase Check
    Verifica se o PC atende os requisitos

.EXAMPLE
    .\install-wsl2-portable.ps1 -Phase Enable
    Habilita recursos WSL (requer restart apos)

.EXAMPLE
    .\install-wsl2-portable.ps1 -Phase Install
    Instala Ubuntu-24.04 (executar APOS restart)

.EXAMPLE
    .\install-wsl2-portable.ps1 -Phase Full
    Executa todas as fases em sequencia
#>

param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("Check", "Enable", "Install", "Validate", "Full")]
    [string]$Phase = "Check"
)

# ============================================
# CONFIGURACAO
# ============================================

$ErrorActionPreference = "Continue"
$UBUNTU_DISTRO = "Ubuntu-24.04"

# ============================================
# FUNCOES AUXILIARES
# ============================================

function Write-Status {
    param(
        [string]$Message,
        [ValidateSet("Info", "Success", "Warning", "Error", "Header")]
        [string]$Type = "Info"
    )

    $timestamp = Get-Date -Format "HH:mm:ss"

    switch ($Type) {
        "Info"    { Write-Host "[$timestamp] [INFO]    $Message" -ForegroundColor Cyan }
        "Success" { Write-Host "[$timestamp] [OK]      $Message" -ForegroundColor Green }
        "Warning" { Write-Host "[$timestamp] [AVISO]   $Message" -ForegroundColor Yellow }
        "Error"   { Write-Host "[$timestamp] [ERRO]    $Message" -ForegroundColor Red }
        "Header"  {
            Write-Host ""
            Write-Host "============================================" -ForegroundColor Magenta
            Write-Host " $Message" -ForegroundColor Magenta
            Write-Host "============================================" -ForegroundColor Magenta
        }
    }
}

function Test-IsAdmin {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal(
        [Security.Principal.WindowsIdentity]::GetCurrent()
    )
    return $currentPrincipal.IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator
    )
}

function Get-WindowsBuild {
    $os = Get-CimInstance -ClassName Win32_OperatingSystem
    return [int]$os.BuildNumber
}

function Get-PSVersion {
    return $PSVersionTable.PSVersion
}

# ============================================
# FASE: CHECK - Verificar Pre-requisitos
# ============================================

function Invoke-CheckPhase {
    Write-Status "FASE: CHECK - Verificando Pre-requisitos" -Type Header

    $allPassed = $true

    # 1. Verificar Admin
    Write-Status "Verificando privilegios de administrador..." -Type Info
    if (Test-IsAdmin) {
        Write-Status "Executando como Administrador" -Type Success
    }
    else {
        Write-Status "NAO esta executando como Administrador!" -Type Error
        Write-Status "Clique direito no PowerShell -> 'Executar como administrador'" -Type Warning
        $allPassed = $false
    }

    # 2. Verificar Versao Windows
    Write-Status "Verificando versao do Windows..." -Type Info
    $build = Get-WindowsBuild
    if ($build -ge 19041) {
        Write-Status "Windows Build $build (minimo: 19041)" -Type Success
    }
    else {
        Write-Status "Windows Build $build - INCOMPATIVEL (minimo: 19041)" -Type Error
        Write-Status "Atualize o Windows para uma versao mais recente" -Type Warning
        $allPassed = $false
    }

    # 3. Verificar PowerShell
    Write-Status "Verificando versao do PowerShell..." -Type Info
    $psVer = Get-PSVersion
    Write-Status "PowerShell $($psVer.Major).$($psVer.Minor)" -Type Success

    # 4. Verificar se Virtualizacao esta habilitada
    Write-Status "Verificando suporte a virtualizacao..." -Type Info
    try {
        $hyperv = Get-CimInstance -ClassName Win32_ComputerSystem
        if ($hyperv.HypervisorPresent) {
            Write-Status "Hypervisor detectado (virtualizacao OK)" -Type Success
        }
        else {
            # Pode ainda funcionar, apenas aviso
            Write-Status "Hypervisor nao detectado - pode precisar habilitar no BIOS" -Type Warning
            Write-Status "Se a instalacao falhar, habilite VT-x/AMD-V no BIOS" -Type Warning
        }
    }
    catch {
        Write-Status "Nao foi possivel verificar virtualizacao" -Type Warning
    }

    # 5. Verificar se WSL ja esta instalado
    Write-Status "Verificando estado atual do WSL..." -Type Info
    try {
        $wslStatus = wsl --status 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Status "WSL ja esta instalado no sistema" -Type Success

            # Verificar distribuicoes
            $distros = wsl --list --quiet 2>&1
            if ($distros -match $UBUNTU_DISTRO) {
                Write-Status "$UBUNTU_DISTRO ja esta instalado!" -Type Success
            }
            else {
                Write-Status "$UBUNTU_DISTRO NAO encontrado - sera instalado" -Type Info
            }
        }
        else {
            Write-Status "WSL nao esta instalado - sera configurado" -Type Info
        }
    }
    catch {
        Write-Status "WSL nao esta instalado - sera configurado" -Type Info
    }

    # Resultado
    Write-Host ""
    if ($allPassed) {
        Write-Status "Todos os pre-requisitos atendidos!" -Type Success
        Write-Host ""
        Write-Host "Proximo passo:" -ForegroundColor Yellow
        Write-Host "  .\install-wsl2-portable.ps1 -Phase Enable" -ForegroundColor White
        Write-Host ""
    }
    else {
        Write-Status "Alguns pre-requisitos NAO foram atendidos" -Type Error
        Write-Host "Corrija os erros acima antes de continuar" -ForegroundColor Red
    }

    return $allPassed
}

# ============================================
# FASE: ENABLE - Habilitar Recursos WSL
# ============================================

function Invoke-EnablePhase {
    Write-Status "FASE: ENABLE - Habilitando Recursos WSL" -Type Header

    # Verificar admin
    if (-not (Test-IsAdmin)) {
        Write-Status "Esta fase REQUER privilegios de administrador!" -Type Error
        Write-Status "Clique direito no PowerShell -> 'Executar como administrador'" -Type Warning
        return $false
    }

    $needsRestart = $false

    # 1. Habilitar WSL
    Write-Status "Habilitando Microsoft-Windows-Subsystem-Linux..." -Type Info
    try {
        $result = dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
        if ($LASTEXITCODE -eq 0) {
            Write-Status "WSL habilitado" -Type Success
        }
        elseif ($LASTEXITCODE -eq 3010) {
            Write-Status "WSL habilitado - REQUER RESTART" -Type Warning
            $needsRestart = $true
        }
        else {
            Write-Status "Erro ao habilitar WSL (codigo: $LASTEXITCODE)" -Type Error
            return $false
        }
    }
    catch {
        Write-Status "Excecao ao habilitar WSL: $($_.Exception.Message)" -Type Error
        return $false
    }

    # 2. Habilitar Plataforma de VM
    Write-Status "Habilitando VirtualMachinePlatform..." -Type Info
    try {
        $result = dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
        if ($LASTEXITCODE -eq 0) {
            Write-Status "VirtualMachinePlatform habilitado" -Type Success
        }
        elseif ($LASTEXITCODE -eq 3010) {
            Write-Status "VirtualMachinePlatform habilitado - REQUER RESTART" -Type Warning
            $needsRestart = $true
        }
        else {
            Write-Status "Erro ao habilitar VirtualMachinePlatform (codigo: $LASTEXITCODE)" -Type Error
            return $false
        }
    }
    catch {
        Write-Status "Excecao ao habilitar VirtualMachinePlatform: $($_.Exception.Message)" -Type Error
        return $false
    }

    # 3. Definir WSL2 como padrao
    Write-Status "Definindo WSL2 como versao padrao..." -Type Info
    try {
        wsl --set-default-version 2 2>&1 | Out-Null
        Write-Status "WSL2 definido como padrao" -Type Success
    }
    catch {
        Write-Status "Aviso: Nao foi possivel definir WSL2 como padrao agora" -Type Warning
        Write-Status "Isso sera configurado apos o restart" -Type Warning
    }

    # Resultado
    Write-Host ""
    if ($needsRestart) {
        Write-Host "========================================" -ForegroundColor Yellow
        Write-Host " RESTART NECESSARIO!" -ForegroundColor Yellow
        Write-Host "========================================" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Os recursos foram habilitados, mas voce precisa:" -ForegroundColor White
        Write-Host ""
        Write-Host "  1. REINICIAR o computador" -ForegroundColor Cyan
        Write-Host "  2. Apos reiniciar, abrir PowerShell como Admin" -ForegroundColor Cyan
        Write-Host "  3. Executar:" -ForegroundColor Cyan
        Write-Host "     .\install-wsl2-portable.ps1 -Phase Install" -ForegroundColor White
        Write-Host ""

        $response = Read-Host "Deseja reiniciar agora? (S/N)"
        if ($response -eq "S" -or $response -eq "s") {
            Write-Status "Reiniciando em 10 segundos..." -Type Warning
            Start-Sleep -Seconds 10
            Restart-Computer -Force
        }
    }
    else {
        Write-Status "Recursos habilitados sem necessidade de restart!" -Type Success
        Write-Host ""
        Write-Host "Proximo passo:" -ForegroundColor Yellow
        Write-Host "  .\install-wsl2-portable.ps1 -Phase Install" -ForegroundColor White
        Write-Host ""
    }

    return $true
}

# ============================================
# FASE: INSTALL - Instalar Ubuntu
# ============================================

function Invoke-InstallPhase {
    Write-Status "FASE: INSTALL - Instalando $UBUNTU_DISTRO" -Type Header

    # 1. Verificar se WSL esta funcionando
    Write-Status "Verificando se WSL esta funcionando..." -Type Info
    try {
        $wslStatus = wsl --status 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Status "WSL nao esta pronto. Execute primeiro: -Phase Enable e reinicie" -Type Error
            return $false
        }
        Write-Status "WSL esta operacional" -Type Success
    }
    catch {
        Write-Status "Erro ao verificar WSL" -Type Error
        return $false
    }

    # 2. Garantir WSL2 como padrao
    Write-Status "Garantindo WSL2 como versao padrao..." -Type Info
    wsl --set-default-version 2 2>&1 | Out-Null
    Write-Status "WSL2 configurado como padrao" -Type Success

    # 3. Verificar se Ubuntu ja existe
    Write-Status "Verificando se $UBUNTU_DISTRO ja esta instalado..." -Type Info
    $distros = wsl --list --quiet 2>&1
    if ($distros -match $UBUNTU_DISTRO) {
        Write-Status "$UBUNTU_DISTRO ja esta instalado!" -Type Warning

        $response = Read-Host "Deseja REINSTALAR? Isso APAGARA todos os dados! (S/N)"
        if ($response -eq "S" -or $response -eq "s") {
            Write-Status "Removendo instalacao existente..." -Type Warning
            wsl --unregister $UBUNTU_DISTRO 2>&1 | Out-Null
            Write-Status "Instalacao anterior removida" -Type Success
        }
        else {
            Write-Status "Mantendo instalacao existente" -Type Info
            Write-Host ""
            Write-Host "Proximo passo:" -ForegroundColor Yellow
            Write-Host "  .\install-wsl2-portable.ps1 -Phase Validate" -ForegroundColor White
            return $true
        }
    }

    # 4. Instalar Ubuntu
    Write-Status "Instalando $UBUNTU_DISTRO... (isso pode demorar alguns minutos)" -Type Info
    Write-Host ""
    Write-Host "IMPORTANTE: Quando a janela do Ubuntu abrir:" -ForegroundColor Yellow
    Write-Host "  1. Crie um nome de usuario (ex: seu-nome)" -ForegroundColor White
    Write-Host "  2. Crie uma senha (pode ser simples, mas MEMORIZE)" -ForegroundColor White
    Write-Host "  3. Confirme a senha" -ForegroundColor White
    Write-Host "  4. Apos a mensagem de sucesso, digite 'exit' para sair" -ForegroundColor White
    Write-Host ""

    try {
        # Usar wsl --install para instalar a distro
        wsl --install -d $UBUNTU_DISTRO

        if ($LASTEXITCODE -eq 0) {
            Write-Status "$UBUNTU_DISTRO instalado com sucesso!" -Type Success
        }
        else {
            Write-Status "Pode ter havido um problema na instalacao (codigo: $LASTEXITCODE)" -Type Warning
            Write-Status "Tente verificar com: wsl --list --verbose" -Type Warning
        }
    }
    catch {
        Write-Status "Excecao durante instalacao: $($_.Exception.Message)" -Type Error
        return $false
    }

    # 5. Garantir que esta usando WSL2
    Write-Status "Garantindo que $UBUNTU_DISTRO use WSL2..." -Type Info
    Start-Sleep -Seconds 3
    wsl --set-version $UBUNTU_DISTRO 2 2>&1 | Out-Null

    Write-Host ""
    Write-Status "Instalacao concluida!" -Type Success
    Write-Host ""
    Write-Host "Proximo passo:" -ForegroundColor Yellow
    Write-Host "  .\install-wsl2-portable.ps1 -Phase Validate" -ForegroundColor White
    Write-Host ""

    return $true
}

# ============================================
# FASE: VALIDATE - Verificar Instalacao
# ============================================

function Invoke-ValidatePhase {
    Write-Status "FASE: VALIDATE - Verificando Instalacao" -Type Header

    $allPassed = $true

    # 1. Verificar WSL
    Write-Status "Verificando WSL..." -Type Info
    try {
        wsl --status 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Status "WSL operacional" -Type Success
        }
        else {
            Write-Status "WSL com problemas" -Type Error
            $allPassed = $false
        }
    }
    catch {
        Write-Status "Erro ao verificar WSL" -Type Error
        $allPassed = $false
    }

    # 2. Verificar Ubuntu
    Write-Status "Verificando $UBUNTU_DISTRO..." -Type Info
    $distros = wsl --list --verbose 2>&1
    if ($distros -match $UBUNTU_DISTRO) {
        Write-Status "$UBUNTU_DISTRO encontrado" -Type Success

        # Verificar versao WSL
        if ($distros -match "$UBUNTU_DISTRO.*2") {
            Write-Status "$UBUNTU_DISTRO usando WSL2" -Type Success
        }
        else {
            Write-Status "$UBUNTU_DISTRO pode estar usando WSL1!" -Type Warning
            Write-Status "Execute: wsl --set-version $UBUNTU_DISTRO 2" -Type Warning
        }
    }
    else {
        Write-Status "$UBUNTU_DISTRO NAO encontrado" -Type Error
        $allPassed = $false
    }

    # 3. Testar execucao de comandos
    Write-Status "Testando execucao de comandos no Ubuntu..." -Type Info
    try {
        $testResult = wsl -d $UBUNTU_DISTRO -- whoami 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Comandos funcionando - Usuario: $testResult" -Type Success
        }
        else {
            Write-Status "Erro ao executar comandos" -Type Error
            $allPassed = $false
        }
    }
    catch {
        Write-Status "Excecao ao testar comandos" -Type Error
        $allPassed = $false
    }

    # 4. Verificar Python
    Write-Status "Verificando Python no Ubuntu..." -Type Info
    try {
        $pythonVer = wsl -d $UBUNTU_DISTRO -- python3 --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Python: $pythonVer" -Type Success
        }
        else {
            Write-Status "Python nao encontrado - sera instalado depois" -Type Warning
        }
    }
    catch {
        Write-Status "Erro ao verificar Python" -Type Warning
    }

    # 5. Verificar Git
    Write-Status "Verificando Git no Ubuntu..." -Type Info
    try {
        $gitVer = wsl -d $UBUNTU_DISTRO -- git --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Git: $gitVer" -Type Success
        }
        else {
            Write-Status "Git nao encontrado - sera instalado depois" -Type Warning
        }
    }
    catch {
        Write-Status "Erro ao verificar Git" -Type Warning
    }

    # Resultado
    Write-Host ""
    if ($allPassed) {
        Write-Host "========================================" -ForegroundColor Green
        Write-Host " WSL2 INSTALADO COM SUCESSO!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Proximos passos:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  1. Abrir o Ubuntu:" -ForegroundColor Cyan
        Write-Host "     wsl -d $UBUNTU_DISTRO" -ForegroundColor White
        Write-Host ""
        Write-Host "  2. Atualizar o sistema:" -ForegroundColor Cyan
        Write-Host "     sudo apt update && sudo apt upgrade -y" -ForegroundColor White
        Write-Host ""
        Write-Host "  3. Instalar ferramentas base:" -ForegroundColor Cyan
        Write-Host "     sudo apt install -y build-essential curl wget git" -ForegroundColor White
        Write-Host ""
        Write-Host "  4. Clonar o repositorio:" -ForegroundColor Cyan
        Write-Host "     mkdir -p ~/projetos && cd ~/projetos" -ForegroundColor White
        Write-Host "     git clone https://github.com/PedroGiudice/Claude-Code-Projetos.git" -ForegroundColor White
        Write-Host ""
    }
    else {
        Write-Host "========================================" -ForegroundColor Red
        Write-Host " ALGUNS PROBLEMAS DETECTADOS" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        Write-Host ""
        Write-Host "Verifique os erros acima e tente:" -ForegroundColor Yellow
        Write-Host "  1. Reiniciar o computador" -ForegroundColor White
        Write-Host "  2. Executar novamente: .\install-wsl2-portable.ps1 -Phase Install" -ForegroundColor White
        Write-Host ""
    }

    return $allPassed
}

# ============================================
# FASE: FULL - Execucao Completa
# ============================================

function Invoke-FullPhase {
    Write-Status "FASE: FULL - Instalacao Completa" -Type Header
    Write-Host ""
    Write-Host "Este modo executara todas as fases em sequencia." -ForegroundColor Yellow
    Write-Host "Se houver necessidade de restart, o script avisara." -ForegroundColor Yellow
    Write-Host ""

    # Check
    $checkOk = Invoke-CheckPhase
    if (-not $checkOk) {
        Write-Status "Fase CHECK falhou - corrija os erros e execute novamente" -Type Error
        return $false
    }

    Write-Host ""
    $response = Read-Host "Pre-requisitos OK. Continuar com Enable? (S/N)"
    if ($response -ne "S" -and $response -ne "s") {
        Write-Status "Instalacao cancelada" -Type Warning
        return $false
    }

    # Enable
    $enableOk = Invoke-EnablePhase
    if (-not $enableOk) {
        return $false
    }

    # Se chegou aqui sem restart, continua
    Write-Host ""
    $response = Read-Host "Continuar com Install? (S/N)"
    if ($response -ne "S" -and $response -ne "s") {
        Write-Status "Instalacao pausada" -Type Warning
        return $false
    }

    # Install
    $installOk = Invoke-InstallPhase
    if (-not $installOk) {
        return $false
    }

    # Validate
    Start-Sleep -Seconds 5
    Invoke-ValidatePhase

    return $true
}

# ============================================
# EXECUCAO PRINCIPAL
# ============================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " WSL2 Portable Installer v2.0" -ForegroundColor Cyan
Write-Host " Compativel com qualquer PC Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Fase selecionada: $Phase" -ForegroundColor White
Write-Host ""

switch ($Phase) {
    "Check"    { Invoke-CheckPhase }
    "Enable"   { Invoke-EnablePhase }
    "Install"  { Invoke-InstallPhase }
    "Validate" { Invoke-ValidatePhase }
    "Full"     { Invoke-FullPhase }
}
