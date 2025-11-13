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
# 1. DETECTAR AMBIENTE
# ============================================================================
Write-Host "[1/4] Detectando ambiente..." -ForegroundColor Yellow

$projectDir = Get-Location
$settingsPath = Join-Path $projectDir ".claude\settings.json"
$settingsLocalPath = Join-Path $projectDir ".claude\settings.local.json"
$settingsHybridPath = Join-Path $projectDir ".claude\settings.hybrid.json"

Write-Host "   Diretório: $projectDir" -ForegroundColor Gray

if (Test-Path $settingsPath) {
    Write-Host "   ✅ settings.json encontrado" -ForegroundColor Green
} else {
    Write-Host "   ❌ settings.json NÃO encontrado!" -ForegroundColor Red
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
