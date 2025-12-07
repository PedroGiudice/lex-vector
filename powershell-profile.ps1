#==============================================================================
# PowerShell Profile - Claude Code + WSL Integration
#
# INSTALLATION:
# 1. Copy this file to: $PROFILE
# 2. Or run: Copy-Item .\powershell-profile.ps1 $PROFILE -Force
# 3. Reload: . $PROFILE
#
# BEHAVIOR:
# - Opens WSL automatically when PowerShell starts
# - Auto-detects WSL username and project location
# - Quick commands available (claude, scc, gcp, etc.)
#
# Last updated: 2025-12-07
#==============================================================================

#==============================================================================
# WSL ENVIRONMENT CONFIGURATION
#==============================================================================

# Configure Claude Code to run in WSL
$env:CLAUDE_SHELL = "wsl"

# Environment variables passed from Windows to WSL
$env:WSLENV = "CLAUDE_SHELL"

#==============================================================================
# AUTO-DETECT WSL CONFIGURATION
#==============================================================================

# Auto-detect WSL username
$WSL_USERNAME = (wsl -- whoami 2>$null).Trim()
if (-not $WSL_USERNAME) {
    Write-Host "[ERRO] WSL nao encontrado ou nao configurado!" -ForegroundColor Red
    return
}

# Auto-detect Claude Code path
$CLAUDE_PATH = (wsl -- which claude 2>$null).Trim()
if (-not $CLAUDE_PATH) {
    $CLAUDE_PATH = "/home/$WSL_USERNAME/.npm-global/bin/claude"
}

# Auto-detect project directory (procura Claude-Code-Projetos)
$PROJECT_DIR = (wsl -- bash -c "find ~ -maxdepth 4 -type d -name 'Claude-Code-Projetos' 2>/dev/null | head -1").Trim()
if (-not $PROJECT_DIR) {
    # Fallback para locais comuns
    $PROJECT_DIR = "~/projetos/Claude-Code-Projetos"
}

#==============================================================================
# FUNCTION: claude command interceptor
#==============================================================================

function claude {
    $argString = $args -join ' '
    wsl -- $CLAUDE_PATH $argString
}

#==============================================================================
# QUICK COMMANDS
#==============================================================================

function Start-Claude {
    Write-Host "[*] Starting Claude Code in project..." -ForegroundColor Cyan
    # Change to safe directory first (prevents Claude from indexing problematic Windows paths)
    Push-Location $env:USERPROFILE
    wsl -- bash -c "cd $PROJECT_DIR && exec $CLAUDE_PATH"
    Pop-Location
}
Set-Alias -Name scc -Value Start-Claude

function Go-ClaudeProject {
    Write-Host "[*] Opening project in WSL..." -ForegroundColor Cyan
    wsl -- bash -c "cd $PROJECT_DIR && exec bash"
}
Set-Alias -Name gcp -Value Go-ClaudeProject

# Open WSL in project directory
Set-Alias -Name owsl -Value wsl

function Sync-Repo {
    Write-Host "[*] Syncing repository..." -ForegroundColor Cyan
    wsl -- bash -c "cd $PROJECT_DIR && git pull && echo '' && git status"
}
Set-Alias -Name gsync -Value Sync-Repo

function Get-ClaudeStatus {
    Write-Host "[*] Checking Claude Code in WSL..." -ForegroundColor Cyan
    wsl -- bash -c "which claude && claude --version"
}
Set-Alias -Name cstatus -Value Get-ClaudeStatus

function Get-ClaudeEnv {
    Write-Host ""
    Write-Host "==============================================================================" -ForegroundColor Yellow
    Write-Host " Claude Code Environment Info" -ForegroundColor Yellow
    Write-Host "==============================================================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Windows Environment:" -ForegroundColor Cyan
    Write-Host "  CLAUDE_SHELL: $env:CLAUDE_SHELL" -ForegroundColor Green
    Write-Host "  WSLENV: $env:WSLENV" -ForegroundColor Green
    Write-Host ""
    Write-Host "WSL Environment:" -ForegroundColor Cyan
    wsl -- bash -c "cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2"
    Write-Host "  Node.js: " -NoNewline -ForegroundColor White
    wsl -- node --version
    Write-Host "  npm: " -NoNewline -ForegroundColor White
    wsl -- npm --version
    Write-Host "  Claude: " -NoNewline -ForegroundColor White
    wsl -- claude --version 2>$null
    Write-Host ""
    Write-Host "Project Directory:" -ForegroundColor Cyan
    Write-Host "  $PROJECT_DIR" -ForegroundColor Green
    Write-Host ""
}
Set-Alias -Name cenv -Value Get-ClaudeEnv

function Get-ProjectStatus {
    Write-Host ""
    Write-Host "==============================================================================" -ForegroundColor Magenta
    Write-Host " Project Status - Claude-Code-Projetos" -ForegroundColor Magenta
    Write-Host "==============================================================================" -ForegroundColor Magenta
    Write-Host ""
    wsl -- bash -c "cd $PROJECT_DIR && git status --short --branch"
    Write-Host ""
    Write-Host "Structure:" -ForegroundColor Yellow
    Write-Host "  Agents: " -NoNewline -ForegroundColor White
    wsl -- bash -c "cd $PROJECT_DIR && ls -1 .claude/agents/*.md 2>/dev/null | wc -l"
    Write-Host "  Skills: " -NoNewline -ForegroundColor White
    wsl -- bash -c "cd $PROJECT_DIR && ls -1d skills/*/ 2>/dev/null | wc -l"
    Write-Host "  Hooks: " -NoNewline -ForegroundColor White
    wsl -- bash -c "cd $PROJECT_DIR && ls -1 .claude/hooks/*.js 2>/dev/null | wc -l"
    Write-Host ""
}
Set-Alias -Name pstatus -Value Get-ProjectStatus

#==============================================================================
# GIT WORKFLOW SHORTCUTS
#==============================================================================

function Quick-Commit {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message
    )
    Write-Host "[*] Creating commit..." -ForegroundColor Cyan
    wsl -- bash -c "cd $PROJECT_DIR && git add . && git commit -m '$Message' && git status"
}
Set-Alias -Name qcommit -Value Quick-Commit

function Quick-Push {
    Write-Host "[*] Pushing to remote..." -ForegroundColor Cyan
    wsl -- bash -c "cd $PROJECT_DIR && git push"
}
Set-Alias -Name qpush -Value Quick-Push

function Quick-Sync {
    param(
        [string]$Message = "quick update"
    )
    Write-Host "[*] Full sync: pull -> commit -> push" -ForegroundColor Yellow
    wsl -- bash -c "cd $PROJECT_DIR && git pull && git add . && git commit -m '$Message' && git push && git status"
}
Set-Alias -Name qsync -Value Quick-Sync

#==============================================================================
# WELCOME MESSAGE
#==============================================================================

function Show-ClaudeWelcome {
    Write-Host ""
    Write-Host "==============================================================================" -ForegroundColor Cyan
    Write-Host " Claude Code + WSL Environment Ready" -ForegroundColor Cyan
    Write-Host "==============================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Detectado:" -ForegroundColor Yellow
    Write-Host "  Usuario WSL: $WSL_USERNAME" -ForegroundColor Green
    Write-Host "  Projeto:     $PROJECT_DIR" -ForegroundColor Green
    Write-Host "  Claude:      $CLAUDE_PATH" -ForegroundColor Green
    Write-Host ""
    Write-Host "Comandos:" -ForegroundColor Yellow
    Write-Host "  scc     - Iniciar Claude Code no projeto" -ForegroundColor White
    Write-Host "  gcp     - Abrir bash no projeto" -ForegroundColor White
    Write-Host "  gsync   - Git pull + status" -ForegroundColor White
    Write-Host "  cenv    - Info do ambiente" -ForegroundColor White
    Write-Host ""
    Write-Host "Entrando no WSL..." -ForegroundColor Gray
    Write-Host ""
}

# Show welcome message
Show-ClaudeWelcome

#==============================================================================
# AUTO-START WSL
#==============================================================================

# AUTO-START: Opens WSL automatically when PowerShell starts in project directory
# To DISABLE auto-start, comment the line below:
wsl -- bash -c "cd $PROJECT_DIR && exec bash"

# ALTERNATIVES:
# - To start Claude Code automatically instead: scc
# - To open WSL in home directory: wsl

#==============================================================================
# TROUBLESHOOTING
#==============================================================================

# PROBLEM: "claude: command not found"
# SOLUTION: Check if Claude Code is installed in WSL
#   wsl -- which claude
#   If not found, install: wsl -- npm install -g @anthropic-ai/claude-code
#
# PROBLEM: "wsl: command not found"
# SOLUTION: WSL is not installed or not in PATH
#   Install WSL: wsl --install
#   Or add to PATH: C:\Windows\System32\wsl.exe
#
# PROBLEM: "Permission denied"
# SOLUTION: Check execution policy
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#
# PROBLEM: Environment variables not passing to WSL
# SOLUTION: Make sure WSLENV is configured correctly
#   $env:WSLENV = "VARIABLE1:VARIABLE2:CLAUDE_SHELL"
#
# PROBLEM: Auto-start is slow
# SOLUTION: Disable auto-start by commenting the Open-WSL line
#   Use manual commands (scc, gcp, owsl) when needed

#==============================================================================
# END OF PROFILE
#==============================================================================
