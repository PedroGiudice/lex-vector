# MD2PDF Converter - Setup Script
# Configura o ambiente e baixa dependências

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MD2PDF CONVERTER - SETUP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verifica se está executando como Administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[AVISO] Recomenda-se executar como Administrador" -ForegroundColor Yellow
    Write-Host ""
}

# Cria estrutura de diretórios
Write-Host "[1/4] Criando estrutura de diretórios..." -ForegroundColor Green
$dirs = @("assets", "lib", "docs")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "  - Criado: $dir" -ForegroundColor Gray
    } else {
        Write-Host "  - Existente: $dir" -ForegroundColor Gray
    }
}

# Baixa dependências CDN (para cache local opcional)
Write-Host ""
Write-Host "[2/4] Verificando dependências..." -ForegroundColor Green

$dependencies = @{
    "marked.min.js" = "https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js"
    "docx.min.js" = "https://cdnjs.cloudflare.com/ajax/libs/docx/7.8.2/docx.min.js"
    "FileSaver.min.js" = "https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.5/FileSaver.min.js"
}

foreach ($file in $dependencies.Keys) {
    $url = $dependencies[$file]
    $output = "lib/$file"

    if (-not (Test-Path $output)) {
        Write-Host "  - Baixando: $file" -ForegroundColor Gray
        try {
            Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
            Write-Host "    OK" -ForegroundColor Green
        } catch {
            Write-Host "    ERRO: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "  - Existente: $file" -ForegroundColor Gray
    }
}

# Cria arquivo index.html se não existir
Write-Host ""
Write-Host "[3/4] Verificando arquivo principal..." -ForegroundColor Green
if (-not (Test-Path "index.html")) {
    Write-Host "  [AVISO] index.html não encontrado!" -ForegroundColor Yellow
    Write-Host "  O arquivo index.html deve estar presente no diretório" -ForegroundColor Yellow
} else {
    Write-Host "  - index.html encontrado" -ForegroundColor Gray
    $fileSize = (Get-Item "index.html").Length / 1KB
    Write-Host "    Tamanho: $([math]::Round($fileSize, 2)) KB" -ForegroundColor Gray
}

# Verifica Python para servidor HTTP
Write-Host ""
Write-Host "[4/4] Verificando servidor HTTP..." -ForegroundColor Green

$pythonInstalled = Get-Command python -ErrorAction SilentlyContinue

if ($pythonInstalled) {
    Write-Host "  - Python detectado: $(python --version)" -ForegroundColor Gray
    Write-Host "  - Servidor disponível via: python -m http.server 8000" -ForegroundColor Gray
} else {
    Write-Host "  [INFO] Python não detectado" -ForegroundColor Yellow
    Write-Host "  Use o servidor PowerShell integrado (server.ps1)" -ForegroundColor Yellow
}

# Sumário
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CONFIGURAÇÃO CONCLUÍDA" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para iniciar o servidor:" -ForegroundColor White
Write-Host "  1. PowerShell: .\server.ps1" -ForegroundColor Yellow
Write-Host "  2. Python:     python -m http.server 8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Acesse: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Funcionalidades disponíveis:" -ForegroundColor White
Write-Host "  - 14 opções de fontes profissionais" -ForegroundColor Gray
Write-Host "  - Controles avançados de formatação" -ForegroundColor Gray
Write-Host "  - Exportação para PDF" -ForegroundColor Gray
Write-Host "  - Exportação para DOCX" -ForegroundColor Gray
Write-Host ""
