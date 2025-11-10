# Legal Lens - Script de execução
# Ativa ambiente virtual e executa o agente

$ErrorActionPreference = "Stop"

Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "    LEGAL LENS - Análise RAG de Documentos Jurídicos        " -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se está no diretório correto
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "[1/4] Verificando ambiente virtual..." -ForegroundColor Yellow

# Verificar se .venv existe
if (-not (Test-Path ".venv")) {
    Write-Host "✗ Ambiente virtual não encontrado!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Execute os seguintes comandos para criar:" -ForegroundColor White
    Write-Host "  python -m venv .venv" -ForegroundColor Green
    Write-Host "  .venv\Scripts\activate" -ForegroundColor Green
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Green
    exit 1
}

Write-Host "✓ Ambiente virtual encontrado" -ForegroundColor Green
Write-Host ""

Write-Host "[2/4] Ativando ambiente virtual..." -ForegroundColor Yellow

# Ativar ambiente virtual
& ".venv\Scripts\Activate.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Erro ao ativar ambiente virtual!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Ambiente virtual ativado" -ForegroundColor Green
Write-Host ""

Write-Host "[3/4] Verificando dependências..." -ForegroundColor Yellow

# Verificar se requirements.txt existe
if (-not (Test-Path "requirements.txt")) {
    Write-Host "✗ Arquivo requirements.txt não encontrado!" -ForegroundColor Red
    exit 1
}

# Verificar se pacotes estão instalados (verificar alguns críticos)
$packages = @("chromadb", "sentence-transformers", "pdfplumber")
$missing = @()

foreach ($package in $packages) {
    $installed = pip show $package 2>$null
    if (-not $installed) {
        $missing += $package
    }
}

if ($missing.Count -gt 0) {
    Write-Host "⚠  Pacotes ausentes: $($missing -join ', ')" -ForegroundColor Yellow
    Write-Host ""
    $install = Read-Host "Instalar pacotes agora? (s/N)"

    if ($install -eq 's' -or $install -eq 'S') {
        Write-Host "Instalando dependências..." -ForegroundColor Yellow
        pip install -r requirements.txt

        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Erro na instalação!" -ForegroundColor Red
            exit 1
        }

        Write-Host "✓ Dependências instaladas" -ForegroundColor Green
    } else {
        Write-Host "✗ Execute: pip install -r requirements.txt" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ Dependências OK" -ForegroundColor Green
}

Write-Host ""
Write-Host "[4/4] Iniciando Legal Lens..." -ForegroundColor Yellow
Write-Host ""

# Executar agente
python main.py

# Capturar código de saída
$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "==============================================================" -ForegroundColor Cyan

if ($exitCode -eq 0) {
    Write-Host "Legal Lens encerrado com sucesso" -ForegroundColor Green
} else {
    Write-Host "Legal Lens encerrado com erros (código: $exitCode)" -ForegroundColor Red
}

Write-Host "==============================================================" -ForegroundColor Cyan

exit $exitCode
