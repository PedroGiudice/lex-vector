# ============================================================================
# fix-windows-hooks.ps1 - Corrige configuração de hooks no Windows
# ============================================================================
#
# PROBLEMA: memory-integration.js e skill-activation ainda estão executando
# CAUSA: settings.json no Windows pode ter versão antiga ou local overrides
# SOLUÇÃO: Aplica configuração correta (apenas 3 hooks ASYNC)
#
# USO:
#   .\fix-windows-hooks.ps1                    # Diagnóstico + correção
#   .\fix-windows-hooks.ps1 -DiagnosisOnly     # Apenas diagnóstico
#
# ============================================================================

param(
    [switch]$DiagnosisOnly
)

$ErrorActionPreference = "Stop"

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "DIAGNÓSTICO E CORREÇÃO - Windows Hooks" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# 1. DETECTAR AMBIENTE E VALIDAR LOCALIZAÇÃO
# ============================================================================
Write-Host "[1/4] Detectando ambiente..." -ForegroundColor Yellow

# CRITICAL: Detect if script is running from wrong location
$currentDir = Get-Location
Write-Host "   Diretório atual: $currentDir" -ForegroundColor Gray

# Try to find project root (contains .git and .claude directories)
$projectDir = $null

# Check current directory first
if ((Test-Path (Join-Path $currentDir ".git")) -and (Test-Path (Join-Path $currentDir ".claude"))) {
    $projectDir = $currentDir
    Write-Host "   ✅ Projeto detectado no diretório atual" -ForegroundColor Green
}
# Check if we're in a subdirectory - walk up to find project root
elseif ($currentDir -match "Claude-Code-Projetos") {
    $searchDir = $currentDir
    while ($searchDir) {
        if ((Test-Path (Join-Path $searchDir ".git")) -and (Test-Path (Join-Path $searchDir ".claude"))) {
            $projectDir = $searchDir
            Write-Host "   ✅ Projeto encontrado em: $projectDir" -ForegroundColor Green
            break
        }
        $parentDir = Split-Path $searchDir -Parent
        if ($parentDir -eq $searchDir) { break }  # Reached root
        $searchDir = $parentDir
    }
}

# If still not found, check common locations
if (-not $projectDir) {
    $commonPaths = @(
        "C:\claude-work\repos\Claude-Code-Projetos",
        "C:\Users\$env:USERNAME\Claude-Code-Projetos",
        "D:\repos\Claude-Code-Projetos"
    )

    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            if ((Test-Path (Join-Path $path ".git")) -and (Test-Path (Join-Path $path ".claude"))) {
                $projectDir = $path
                Write-Host "   ✅ Projeto encontrado em: $projectDir" -ForegroundColor Yellow
                Write-Host "   ⚠️  Navegando para diretório do projeto..." -ForegroundColor Yellow
                Set-Location $projectDir
                break
            }
        }
    }
}

if (-not $projectDir) {
    Write-Host ""
    Write-Host "   ❌ ERRO: Projeto Claude-Code-Projetos NÃO encontrado!" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Este script deve ser executado de dentro do projeto ou você deve especificar o caminho:" -ForegroundColor Yellow
    Write-Host "   cd C:\claude-work\repos\Claude-Code-Projetos" -ForegroundColor Gray
    Write-Host "   .\.claude\fix-windows-hooks.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   OU execute especificando o caminho manualmente:" -ForegroundColor Yellow
    Write-Host "   C:\claude-work\repos\Claude-Code-Projetos\.claude\fix-windows-hooks.ps1" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

$settingsPath = Join-Path $projectDir ".claude\settings.json"
$settingsLocalPath = Join-Path $projectDir ".claude\settings.local.json"
$settingsHybridPath = Join-Path $projectDir ".claude\settings.hybrid.json"

Write-Host "   Diretório do projeto: $projectDir" -ForegroundColor Cyan

if (Test-Path $settingsPath) {
    Write-Host "   ✅ settings.json encontrado" -ForegroundColor Green
} else {
    Write-Host "   ❌ settings.json NÃO encontrado em: $settingsPath" -ForegroundColor Red
    exit 1
}

# ============================================================================
# 2. ANALISAR CONFIGURAÇÃO ATUAL
# ============================================================================
Write-Host "`n[2/4] Analisando configuração atual..." -ForegroundColor Yellow

$settings = Get-Content $settingsPath -Raw | ConvertFrom-Json

$hooksConfigured = @()
if ($settings.hooks.UserPromptSubmit) {
    foreach ($hookEntry in $settings.hooks.UserPromptSubmit) {
        if ($hookEntry.hooks) {
            foreach ($hook in $hookEntry.hooks) {
                $hooksConfigured += $hook.command
            }
        }
    }
}

Write-Host "   Hooks configurados: $($hooksConfigured.Count)" -ForegroundColor Gray

$problemsFound = @()

foreach ($hookCmd in $hooksConfigured) {
    $hookName = Split-Path $hookCmd -Leaf

    if ($hookCmd -like "*memory-integration*") {
        Write-Host "   ❌ PROBLEMA: memory-integration.js (execSync bloqueante)" -ForegroundColor Red
        $problemsFound += "memory-integration.js"
    }
    elseif ($hookCmd -like "*skill-activation*") {
        Write-Host "   ❌ PROBLEMA: skill-activation-prompt (readFileSync bloqueante)" -ForegroundColor Red
        $problemsFound += "skill-activation-prompt"
    }
    else {
        Write-Host "   ✅ $hookName" -ForegroundColor Green
    }
}

# ============================================================================
# 3. VERIFICAR GIT STATUS
# ============================================================================
Write-Host "`n[3/4] Verificando Git status..." -ForegroundColor Yellow

try {
    $gitStatus = git status --porcelain 2>&1

    if ($gitStatus -match "settings.json") {
        Write-Host "   ⚠️  settings.json tem mudanças locais" -ForegroundColor Yellow
    } else {
        Write-Host "   ✅ settings.json está limpo" -ForegroundColor Green
    }

    # Verificar se está na branch correta
    $currentBranch = git branch --show-current 2>&1
    Write-Host "   Branch atual: $currentBranch" -ForegroundColor Gray

} catch {
    Write-Host "   ⚠️  Não foi possível verificar Git status" -ForegroundColor Yellow
}

# ============================================================================
# 4. SUMÁRIO
# ============================================================================
Write-Host "`n[4/4] Sumário" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Cyan

if ($problemsFound.Count -eq 0) {
    Write-Host "✅ TUDO OK! Nenhum hook bloqueante configurado." -ForegroundColor Green
    Write-Host ""
    Write-Host "Hooks corretos detectados:" -ForegroundColor Gray
    foreach ($hookCmd in $hooksConfigured) {
        $hookName = Split-Path $hookCmd -Leaf
        Write-Host "   - $hookName" -ForegroundColor Gray
    }
    exit 0
}

Write-Host "❌ PROBLEMAS ENCONTRADOS: $($problemsFound.Count)" -ForegroundColor Red
Write-Host ""
Write-Host "Hooks bloqueantes detectados:" -ForegroundColor Yellow
foreach ($problem in $problemsFound) {
    Write-Host "   - $problem" -ForegroundColor Red
}

if ($DiagnosisOnly) {
    Write-Host "`n⚠️  Modo diagnóstico apenas. Use sem -DiagnosisOnly para aplicar correção." -ForegroundColor Yellow
    exit 1
}

# ============================================================================
# APLICAR CORREÇÃO
# ============================================================================
Write-Host "`n" -NoNewline
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 69) -ForegroundColor Green
Write-Host "APLICANDO CORREÇÃO AUTOMÁTICA" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 69) -ForegroundColor Green
Write-Host ""

# Configuração correta (apenas 3 hooks ASYNC)
$correctConfig = @{
    "_comment" = "Configuração HÍBRIDA de hooks - Solução para Windows CLI subprocess polling issue"
    "_docs" = "https://github.com/DennisLiuCk/cc-toolkit/commit/09ab8674200a7bf9e31b0090f39ed12cbc3f6f5d"
    "_strategy" = "Use SessionStart para Web/Linux, UserPromptSubmit para Windows CLI. Hooks híbridos previnem execução repetida via run-once guard."

    "hooks" = @{
        "UserPromptSubmit" = @(
            @{
                "hooks" = @(
                    @{
                        "type" = "command"
                        "command" = "node .claude/hooks/session-context-hybrid.js"
                    },
                    @{
                        "type" = "command"
                        "command" = "node .claude/hooks/invoke-legal-braniac-hybrid.js"
                    },
                    @{
                        "type" = "command"
                        "command" = "node .claude/hooks/venv-check.js"
                    }
                )
            }
        )
    }
}

# Backup do arquivo original
$backupPath = "$settingsPath.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item $settingsPath $backupPath -Force
Write-Host "✅ Backup criado: $backupPath" -ForegroundColor Green

# Salvar configuração correta (BEST PRACTICE: -Depth 100)
$correctConfig | ConvertTo-Json -Depth 100 | Set-Content $settingsPath -Encoding UTF8 -NoNewline
Write-Host "✅ settings.json atualizado com configuração correta" -ForegroundColor Green

# Validar JSON (BEST PRACTICE: -Raw)
try {
    $null = Get-Content $settingsPath -Raw | ConvertFrom-Json
    Write-Host "✅ JSON válido (validado programaticamente)" -ForegroundColor Green
} catch {
    Write-Host "❌ JSON INVÁLIDO após correção! Restaurando backup..." -ForegroundColor Red
    Copy-Item $backupPath $settingsPath -Force
    throw "Erro ao validar JSON. Backup restaurado."
}

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 69) -ForegroundColor Green
Write-Host "✅ CORREÇÃO APLICADA COM SUCESSO!" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 69) -ForegroundColor Green
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Cyan
Write-Host "   1. Execute: claude doctor" -ForegroundColor Gray
Write-Host "   2. Execute: claude" -ForegroundColor Gray
Write-Host "   3. NÃO deve mais precisar de tab+enter 3x" -ForegroundColor Gray
Write-Host ""
Write-Host "Hooks configurados agora (3 ASYNC):" -ForegroundColor Cyan
Write-Host "   ✅ session-context-hybrid.js      (contexto do projeto)" -ForegroundColor Green
Write-Host "   ✅ invoke-legal-braniac-hybrid.js (orquestrador)" -ForegroundColor Green
Write-Host "   ✅ venv-check.js                  (verifica venv)" -ForegroundColor Green
Write-Host ""

# ============================================================================
# LIMPEZA: Remover settings.json criado em local errado
# ============================================================================
$userClaudeDir = Join-Path $env:USERPROFILE ".claude"
$userSettingsPath = Join-Path $userClaudeDir "settings.json"

if (Test-Path $userSettingsPath) {
    Write-Host "⚠️  ATENÇÃO: Detectado settings.json no diretório do usuário" -ForegroundColor Yellow
    Write-Host "   Caminho: $userSettingsPath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   Este arquivo foi criado por engano quando o script foi executado" -ForegroundColor Yellow
    Write-Host "   de fora do diretório do projeto." -ForegroundColor Yellow
    Write-Host ""

    $remove = Read-Host "   Deseja remover este arquivo agora? (S/N)"

    if ($remove -eq 'S' -or $remove -eq 's') {
        try {
            Remove-Item $userSettingsPath -Force
            Write-Host "   ✅ Arquivo removido com sucesso!" -ForegroundColor Green

            # Check if .claude directory is now empty
            $dirItems = Get-ChildItem $userClaudeDir -Force
            if ($dirItems.Count -eq 0) {
                Remove-Item $userClaudeDir -Force
                Write-Host "   ✅ Diretório .claude vazio removido" -ForegroundColor Green
            }
        } catch {
            Write-Host "   ❌ Erro ao remover arquivo: $_" -ForegroundColor Red
            Write-Host "   Remova manualmente: Remove-Item '$userSettingsPath' -Force" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ⚠️  Arquivo não removido. Para remover manualmente:" -ForegroundColor Yellow
        Write-Host "   Remove-Item '$userSettingsPath' -Force" -ForegroundColor Gray
    }
    Write-Host ""
}

