# DJEN Tracker v1.0 - Script de Execução
# Ativa ambiente virtual e executa o agente

# Strict mode
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "          DJEN TRACKER v1.0 - Download Contínuo" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se está no diretório correto
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "Erro: Execute este script do diretório agentes/djen-tracker" -ForegroundColor Red
    Write-Host "Comando: cd agentes\djen-tracker; .\run_agent.ps1" -ForegroundColor Yellow
    exit 1
}

# Detectar se uv está instalado
$UV_AVAILABLE = Get-Command "uv" -ErrorAction SilentlyContinue

if ($UV_AVAILABLE) {
    Write-Host "[uv] Detectado! Usando uv para gerenciamento de dependências" -ForegroundColor Green
    Write-Host ""

    # Criar venv com uv
    if (-not (Test-Path ".venv")) {
        Write-Host "[uv] Criando ambiente virtual..." -ForegroundColor Yellow
        uv venv
    }

    # Ativar venv
    Write-Host "[uv] Ativando ambiente virtual..." -ForegroundColor Yellow
    & .venv\Scripts\Activate.ps1

    # Verificar ativação
    $pythonPath = (Get-Command python).Source
    if ($pythonPath -notlike "*\.venv\*") {
        Write-Host "[uv] Erro ao ativar ambiente virtual!" -ForegroundColor Red
        exit 1
    }
    Write-Host "[uv] Ambiente ativo: $pythonPath" -ForegroundColor Green

    # Instalar dependências com uv
    Write-Host "[uv] Instalando/atualizando dependências..." -ForegroundColor Yellow
    uv pip install -e ".[dev]"

} else {
    Write-Host "[pip] uv não encontrado, usando pip tradicional" -ForegroundColor Yellow
    Write-Host "[pip] Dica: Instale uv para instalações ultra-rápidas!" -ForegroundColor Cyan
    Write-Host "[pip]   Windows: irm https://astral.sh/uv/install.ps1 | iex" -ForegroundColor Cyan
    Write-Host ""

    # Criar venv com Python padrão
    if (-not (Test-Path ".venv")) {
        Write-Host "[pip] Criando ambiente virtual..." -ForegroundColor Yellow
        python -m venv .venv
    }

    # Ativar venv
    Write-Host "[pip] Ativando ambiente virtual..." -ForegroundColor Yellow
    & .venv\Scripts\Activate.ps1

    # Verificar ativação
    $pythonPath = (Get-Command python).Source
    if ($pythonPath -notlike "*\.venv\*") {
        Write-Host "[pip] Erro ao ativar ambiente virtual!" -ForegroundColor Red
        exit 1
    }
    Write-Host "[pip] Ambiente ativo: $pythonPath" -ForegroundColor Green

    # Instalar dependências
    Write-Host "[pip] Instalando/atualizando dependências..." -ForegroundColor Yellow
    pip install --upgrade pip

    if (Test-Path "requirements.txt") {
        pip install -r requirements.txt
    } else {
        pip install -e ".[dev]"
    }
}

# Verificar se E:\claude-code-data existe (Windows específico)
$dataPath = "E:\claude-code-data\agentes\djen-tracker"
if (-not (Test-Path $dataPath)) {
    Write-Host ""
    Write-Host "Aviso: Diretório de dados não encontrado: $dataPath" -ForegroundColor Yellow
    Write-Host "Criando estrutura de dados..." -ForegroundColor Yellow

    New-Item -ItemType Directory -Force -Path "$dataPath\cadernos\STF" | Out-Null
    New-Item -ItemType Directory -Force -Path "$dataPath\cadernos\STJ" | Out-Null
    New-Item -ItemType Directory -Force -Path "$dataPath\cadernos\TJSP" | Out-Null
    New-Item -ItemType Directory -Force -Path "$dataPath\cache" | Out-Null
    New-Item -ItemType Directory -Force -Path "$dataPath\logs" | Out-Null

    Write-Host "Estrutura de dados criada!" -ForegroundColor Green
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "  Ambiente pronto! Iniciando DJEN Tracker v1.0..." -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""

# Executar aplicação
python main.py

# Capturar código de saída
$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
if ($exitCode -eq 0) {
    Write-Host "  Sessão encerrada com sucesso" -ForegroundColor Green
} else {
    Write-Host "  Sessão encerrada com erros (código: $exitCode)" -ForegroundColor Red
}
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Dica: Para executar novamente, use:" -ForegroundColor Yellow
Write-Host "  .\run_agent.ps1" -ForegroundColor White
Write-Host ""

exit $exitCode
