<#
.SYNOPSIS
    Configura ambiente de desenvolvimento dentro do WSL2 (apos instalacao)

.DESCRIPTION
    Script para executar APOS o WSL2 estar funcionando.
    Instala Node.js, nvm, Python, e Claude Code.

.PARAMETER SkipNodeJS
    Pular instalacao do Node.js/nvm

.PARAMETER SkipPython
    Pular verificacao do Python

.PARAMETER SkipClaudeCode
    Pular instalacao do Claude Code

.NOTES
    Versao: 1.0.0
    Requisito: WSL2 com Ubuntu ja instalado

.EXAMPLE
    .\setup-dev-environment.ps1
    Executa setup completo
#>

param(
    [switch]$SkipNodeJS,
    [switch]$SkipPython,
    [switch]$SkipClaudeCode
)

$ErrorActionPreference = "Continue"
$UBUNTU_DISTRO = "Ubuntu-24.04"

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

# ============================================
# VERIFICACAO INICIAL
# ============================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Setup Ambiente de Desenvolvimento" -ForegroundColor Cyan
Write-Host " Para WSL2 / Ubuntu" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Status "Verificando se WSL2 esta funcionando..." -Type Info

# Verificar se Ubuntu esta disponivel
try {
    $distros = wsl --list --quiet 2>&1
    if ($distros -notmatch $UBUNTU_DISTRO) {
        Write-Status "$UBUNTU_DISTRO nao encontrado!" -Type Error
        Write-Status "Execute primeiro: .\install-wsl2-portable.ps1 -Phase Full" -Type Warning
        exit 1
    }
    Write-Status "$UBUNTU_DISTRO encontrado" -Type Success
}
catch {
    Write-Status "Erro ao verificar WSL" -Type Error
    exit 1
}

# ============================================
# ATUALIZACAO DO SISTEMA
# ============================================

Write-Status "Atualizando sistema Ubuntu..." -Type Header

$updateScript = @"
#!/bin/bash
set -e
echo '[1/3] Atualizando lista de pacotes...'
sudo apt update -qq

echo '[2/3] Atualizando pacotes instalados...'
sudo apt upgrade -y -qq

echo '[3/3] Instalando ferramentas essenciais...'
sudo apt install -y build-essential curl wget git vim htop tree ripgrep jq zip unzip

echo ''
echo '=== Sistema atualizado com sucesso! ==='
"@

wsl -d $UBUNTU_DISTRO -- bash -c $updateScript

# ============================================
# NODEJS / NVM
# ============================================

if (-not $SkipNodeJS) {
    Write-Status "Instalando Node.js via nvm..." -Type Header

    $nvmScript = @"
#!/bin/bash
set -e

# Verificar se nvm ja existe
if [ -d "\$HOME/.nvm" ]; then
    echo 'nvm ja instalado, verificando...'
    export NVM_DIR="\$HOME/.nvm"
    [ -s "\$NVM_DIR/nvm.sh" ] && . "\$NVM_DIR/nvm.sh"
else
    echo '[1/4] Baixando nvm...'
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash

    export NVM_DIR="\$HOME/.nvm"
    [ -s "\$NVM_DIR/nvm.sh" ] && . "\$NVM_DIR/nvm.sh"
fi

echo '[2/4] Instalando Node.js 22 LTS...'
nvm install 22
nvm alias default 22
nvm use 22

echo '[3/4] Configurando npm global...'
mkdir -p ~/.npm-global
npm config set prefix ~/.npm-global

# Adicionar ao .bashrc se nao existir
if ! grep -q 'npm-global' ~/.bashrc; then
    echo 'export PATH="\$HOME/.npm-global/bin:\$PATH"' >> ~/.bashrc
fi

echo '[4/4] Verificando instalacao...'
echo "Node.js: \$(node --version)"
echo "npm: \$(npm --version)"

echo ''
echo '=== Node.js instalado com sucesso! ==='
"@

    wsl -d $UBUNTU_DISTRO -- bash -c $nvmScript
}
else {
    Write-Status "Pulando instalacao do Node.js (SkipNodeJS)" -Type Warning
}

# ============================================
# PYTHON
# ============================================

if (-not $SkipPython) {
    Write-Status "Verificando Python..." -Type Header

    $pythonScript = @"
#!/bin/bash
set -e

echo 'Verificando Python 3...'

if command -v python3 &> /dev/null; then
    echo "Python3: \$(python3 --version)"
else
    echo 'Instalando Python3...'
    sudo apt install -y python3 python3-pip python3-venv python3-dev
fi

# Verificar pip
if command -v pip3 &> /dev/null; then
    echo "pip3: \$(pip3 --version)"
else
    echo 'Instalando pip3...'
    sudo apt install -y python3-pip
fi

echo ''
echo '=== Python verificado! ==='
"@

    wsl -d $UBUNTU_DISTRO -- bash -c $pythonScript
}
else {
    Write-Status "Pulando verificacao do Python (SkipPython)" -Type Warning
}

# ============================================
# CLAUDE CODE
# ============================================

if (-not $SkipClaudeCode) {
    Write-Status "Instalando Claude Code CLI..." -Type Header

    $claudeScript = @"
#!/bin/bash
set -e

# Garantir que nvm esta carregado
export NVM_DIR="\$HOME/.nvm"
[ -s "\$NVM_DIR/nvm.sh" ] && . "\$NVM_DIR/nvm.sh"

# Garantir PATH do npm global
export PATH="\$HOME/.npm-global/bin:\$PATH"

echo '[1/2] Instalando Claude Code via npm...'
npm install -g @anthropic-ai/claude-code

echo '[2/2] Verificando instalacao...'
if command -v claude &> /dev/null; then
    echo "Claude Code: \$(claude --version)"
    echo ''
    echo '=== Claude Code instalado com sucesso! ==='
else
    echo 'AVISO: Claude nao encontrado no PATH'
    echo 'Tente fechar e reabrir o terminal'
fi
"@

    wsl -d $UBUNTU_DISTRO -- bash -c $claudeScript
}
else {
    Write-Status "Pulando instalacao do Claude Code (SkipClaudeCode)" -Type Warning
}

# ============================================
# CONFIGURACAO GIT
# ============================================

Write-Status "Configurando Git..." -Type Header

Write-Host ""
Write-Host "Configure seu Git com seu nome e email:" -ForegroundColor Yellow
Write-Host ""

$gitName = Read-Host "Seu nome completo para Git (ou Enter para pular)"
$gitEmail = Read-Host "Seu email para Git (ou Enter para pular)"

if ($gitName -and $gitEmail) {
    $gitScript = @"
#!/bin/bash
git config --global user.name "$gitName"
git config --global user.email "$gitEmail"
git config --global init.defaultBranch main
echo 'Git configurado:'
git config --global --list | grep user
"@

    wsl -d $UBUNTU_DISTRO -- bash -c $gitScript
    Write-Status "Git configurado" -Type Success
}
else {
    Write-Status "Configuracao Git pulada" -Type Warning
}

# ============================================
# RESUMO FINAL
# ============================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " AMBIENTE CONFIGURADO COM SUCESSO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Resumo da instalacao:" -ForegroundColor Yellow

$summaryScript = @"
#!/bin/bash
export NVM_DIR="\$HOME/.nvm"
[ -s "\$NVM_DIR/nvm.sh" ] && . "\$NVM_DIR/nvm.sh"
export PATH="\$HOME/.npm-global/bin:\$PATH"

echo "  - Node.js: \$(node --version 2>/dev/null || echo 'nao instalado')"
echo "  - npm: \$(npm --version 2>/dev/null || echo 'nao instalado')"
echo "  - Python: \$(python3 --version 2>/dev/null || echo 'nao instalado')"
echo "  - Git: \$(git --version 2>/dev/null || echo 'nao instalado')"
echo "  - Claude: \$(claude --version 2>/dev/null || echo 'nao instalado')"
"@

wsl -d $UBUNTU_DISTRO -- bash -c $summaryScript

Write-Host ""
Write-Host "Proximos passos:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Entrar no Ubuntu:" -ForegroundColor Cyan
Write-Host "     wsl" -ForegroundColor White
Write-Host ""
Write-Host "  2. Clonar o repositorio:" -ForegroundColor Cyan
Write-Host "     mkdir -p ~/projetos && cd ~/projetos" -ForegroundColor White
Write-Host "     git clone https://github.com/PedroGiudice/Claude-Code-Projetos.git" -ForegroundColor White
Write-Host ""
Write-Host "  3. Iniciar Claude Code:" -ForegroundColor Cyan
Write-Host "     cd ~/projetos/Claude-Code-Projetos" -ForegroundColor White
Write-Host "     claude" -ForegroundColor White
Write-Host ""
