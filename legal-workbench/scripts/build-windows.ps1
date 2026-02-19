# Build Legal Workbench para Windows
# Executar no PC Windows (cmr-002) em PowerShell como Admin
#
# Pre-requisitos:
#   1. Rust: https://rustup.rs/ (rustup-init.exe)
#   2. Node.js v22+: https://nodejs.org/
#   3. Visual Studio Build Tools 2022:
#      - Workload: "Desktop development with C++"
#      - Componentes: MSVC v143, Windows SDK
#   4. WebView2 Runtime (geralmente ja vem no Windows 11)
#   5. Git for Windows
#
# Uso:
#   cd C:\Users\pedro\lex-vector\legal-workbench\frontend
#   .\scripts\build-windows.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Legal Workbench - Windows Build ===" -ForegroundColor Cyan

# Verificar pre-requisitos
Write-Host "`nVerificando pre-requisitos..." -ForegroundColor Yellow

$checks = @(
    @{ cmd = "rustc"; args = "--version"; name = "Rust" },
    @{ cmd = "cargo"; args = "--version"; name = "Cargo" },
    @{ cmd = "node"; args = "--version"; name = "Node.js" },
    @{ cmd = "npm"; args = "--version"; name = "npm" }
)

$missing = @()
foreach ($check in $checks) {
    try {
        $result = & $check.cmd $check.args 2>&1
        Write-Host "  [OK] $($check.name): $result" -ForegroundColor Green
    } catch {
        Write-Host "  [FALTA] $($check.name)" -ForegroundColor Red
        $missing += $check.name
    }
}

if ($missing.Count -gt 0) {
    Write-Host "`nFaltam dependencias: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "Instale e tente novamente." -ForegroundColor Red
    exit 1
}

# Ir para diretorio do frontend
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Split-Path -Parent $scriptDir
Set-Location $frontendDir

Write-Host "`nDiretorio: $(Get-Location)" -ForegroundColor Yellow

# Instalar dependencias npm
Write-Host "`nInstalando dependencias npm..." -ForegroundColor Yellow
npm install

# Build Tauri com MCP Bridge
Write-Host "`nBuildando Tauri (release + mcp-bridge)..." -ForegroundColor Yellow
npx tauri build --features mcp-bridge

Write-Host "`n=== Build completo ===" -ForegroundColor Green
Write-Host "Artefatos em: src-tauri\target\release\bundle\" -ForegroundColor Cyan

# Listar artefatos
$bundleDir = "src-tauri\target\release\bundle"
if (Test-Path "$bundleDir\msi") {
    Get-ChildItem "$bundleDir\msi\*.msi" | ForEach-Object {
        Write-Host "  MSI: $($_.FullName) ($([math]::Round($_.Length / 1MB, 1)) MB)" -ForegroundColor Green
    }
}
if (Test-Path "$bundleDir\nsis") {
    Get-ChildItem "$bundleDir\nsis\*.exe" | ForEach-Object {
        Write-Host "  EXE: $($_.FullName) ($([math]::Round($_.Length / 1MB, 1)) MB)" -ForegroundColor Green
    }
}
