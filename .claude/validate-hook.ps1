# ============================================================================
# validate-hook.ps1 - Valida hooks antes de adicionar a settings.json
# ============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$HookName
)

$ErrorActionPreference = "Stop"

$hookPath = Join-Path $PSScriptRoot "hooks\$HookName"

if (-not (Test-Path $hookPath)) {
    Write-Host "❌ Hook não encontrado: $hookPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Uso: .\validate-hook.ps1 <hook-name>.js" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Exemplos:" -ForegroundColor Cyan
    Write-Host "  .\validate-hook.ps1 git-status-watcher.js" -ForegroundColor Gray
    Write-Host "  .\validate-hook.ps1 data-layer-validator.js" -ForegroundColor Gray
    exit 1
}

Write-Host "🧪 Validando hook: $HookName" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# TESTE 1: Sintaxe JavaScript
# ============================================================================
Write-Host "[1/5] Verificando sintaxe JavaScript..." -ForegroundColor Yellow

try {
    $syntaxCheck = node --check $hookPath 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Sintaxe válida" -ForegroundColor Green
    } else {
        Write-Host "   ❌ FALHOU: Erro de sintaxe" -ForegroundColor Red
        Write-Host $syntaxCheck
        exit 1
    }
} catch {
    Write-Host "   ❌ FALHOU: Erro ao verificar sintaxe" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

# ============================================================================
# TESTE 2: Timeout (1s máximo)
# ============================================================================
Write-Host ""
Write-Host "[2/5] Testando execução com timeout (1s máximo)..." -ForegroundColor Yellow

$outputPath = Join-Path $env:TEMP "hook-output.json"

try {
    $job = Start-Job -ScriptBlock {
        param($hook)
        node $hook
    } -ArgumentList $hookPath

    $completed = Wait-Job $job -Timeout 1

    if ($null -eq $completed) {
        # Timeout
        Stop-Job $job
        Remove-Job $job
        Write-Host "   ❌ FALHOU: Hook travou (timeout 1s)" -ForegroundColor Red
        Write-Host "   ⚠️  Hooks DEVEM terminar em <500ms" -ForegroundColor Yellow
        exit 1
    }

    $output = Receive-Job $job
    Remove-Job $job

    # Salvar output
    $output | Out-File -FilePath $outputPath -Encoding UTF8 -NoNewline

    Write-Host "   ✅ Executou em <1s" -ForegroundColor Green
} catch {
    Write-Host "   ❌ FALHOU: Erro durante execução" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

# ============================================================================
# TESTE 3: Output é JSON válido
# ============================================================================
Write-Host ""
Write-Host "[3/5] Validando output JSON..." -ForegroundColor Yellow

try {
    $jsonOutput = Get-Content $outputPath -Raw | ConvertFrom-Json
    Write-Host "   ✅ JSON válido" -ForegroundColor Green
} catch {
    Write-Host "   ❌ FALHOU: Output não é JSON válido" -ForegroundColor Red
    Write-Host "   Output recebido:"
    Get-Content $outputPath
    exit 1
}

# ============================================================================
# TESTE 4: Estrutura do output
# ============================================================================
Write-Host ""
Write-Host "[4/5] Verificando estrutura do output..." -ForegroundColor Yellow

if ($jsonOutput.continue -ne $true) {
    Write-Host "   ❌ FALHOU: Output deve ter { continue: true }" -ForegroundColor Red
    $jsonOutput | ConvertTo-Json -Depth 10
    exit 1
} else {
    Write-Host "   ✅ Estrutura correta (continue: true)" -ForegroundColor Green
}

# ============================================================================
# TESTE 5: Run-once guard (segunda execução deve ser instantânea)
# ============================================================================
Write-Host ""
Write-Host "[5/5] Testando run-once guard (segunda execução)..." -ForegroundColor Yellow

# Resetar env vars primeiro
$env:CLAUDE_GIT_STATUS_CHECKED = $null
$env:CLAUDE_DATA_LAYER_VALIDATED = $null
$env:CLAUDE_DEPS_CHECKED = $null
$env:CLAUDE_ERRORS_CHECKED = $null
$env:CLAUDE_LEGAL_CONTEXT_INJECTED = $null

# Primeira execução
node $hookPath | Out-Null

# Segunda execução (deve ser instantânea se run-once guard funciona)
$startTime = Get-Date
node $hookPath | Out-Null
$endTime = Get-Date

$elapsedMs = ($endTime - $startTime).TotalMilliseconds

if ($elapsedMs -lt 100) {
    Write-Host "   ✅ Segunda execução em ${elapsedMs}ms (run-once guard funcionando)" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Segunda execução em ${elapsedMs}ms (pode não ter run-once guard)" -ForegroundColor Yellow
    Write-Host "   💡 Isso é OK se hook é stateless" -ForegroundColor Gray
}

# ============================================================================
# RESUMO
# ============================================================================
Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Green
Write-Host "✅ HOOK VALIDADO COM SUCESSO!" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Green
Write-Host ""

Write-Host "📋 Output do hook:" -ForegroundColor Cyan
$jsonOutput | ConvertTo-Json -Depth 10

if ($jsonOutput.systemMessage) {
    Write-Host ""
    Write-Host "💬 Mensagem que será injetada:" -ForegroundColor Cyan
    Write-Host "---"
    Write-Host $jsonOutput.systemMessage
    Write-Host "---"
}

Write-Host ""
Write-Host "🚀 Próximos passos:" -ForegroundColor Cyan
Write-Host "   1. Adicione a settings.local.json para teste integrado:" -ForegroundColor Gray
Write-Host "      {" -ForegroundColor Gray
Write-Host "        `"hooks`": {" -ForegroundColor Gray
Write-Host "          `"UserPromptSubmit`": [{" -ForegroundColor Gray
Write-Host "            `"hooks`": [{" -ForegroundColor Gray
Write-Host "              `"type`": `"command`"," -ForegroundColor Gray
Write-Host "              `"command`": `"node .claude/hooks/$HookName`"" -ForegroundColor Gray
Write-Host "            }]" -ForegroundColor Gray
Write-Host "          }]" -ForegroundColor Gray
Write-Host "        }" -ForegroundColor Gray
Write-Host "      }" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Teste com: claude" -ForegroundColor Gray
Write-Host ""
Write-Host "   3. Se funcionar, adicione a settings.json e commit" -ForegroundColor Gray
Write-Host ""
