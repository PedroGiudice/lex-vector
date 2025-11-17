#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Helper script para instalar PowerShell profile customizado

.DESCRIPTION
    Este script:
    1. Localiza automaticamente o arquivo de profile do PowerShell ($PROFILE)
    2. Faz backup do profile existente (se houver)
    3. Abre o profile no editor padrão para você colar o conteúdo customizado
    4. Mostra instruções claras do que fazer

.NOTES
    Uso: .\install-powershell-profile.ps1
    Requisitos: PowerShell 5.1+ ou PowerShell Core 7+
#>

# Colors para output
$Green = @{ ForegroundColor = "Green" }
$Yellow = @{ ForegroundColor = "Yellow" }
$Cyan = @{ ForegroundColor = "Cyan" }
$Red = @{ ForegroundColor = "Red" }

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" @Cyan
Write-Host "  PowerShell Profile Installer - Claude Code Projetos" @Cyan
Write-Host "═══════════════════════════════════════════════════════════" @Cyan
Write-Host ""

# Passo 1: Detectar localização do profile
Write-Host "[1/4] Detectando localização do PowerShell profile..." @Yellow
Write-Host "      Caminho: " -NoNewline
Write-Host $PROFILE @Cyan
Write-Host ""

# Passo 2: Criar diretório se não existir
$profileDir = Split-Path $PROFILE -Parent
if (-not (Test-Path $profileDir)) {
    Write-Host "[2/4] Criando diretório do profile..." @Yellow
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    Write-Host "      ✓ Diretório criado" @Green
} else {
    Write-Host "[2/4] Diretório do profile já existe" @Green
}
Write-Host ""

# Passo 3: Fazer backup se profile existir
if (Test-Path $PROFILE) {
    Write-Host "[3/4] Profile existente encontrado - fazendo backup..." @Yellow
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupPath = "$PROFILE.backup.$timestamp"
    Copy-Item $PROFILE $backupPath
    Write-Host "      ✓ Backup salvo em:" @Green
    Write-Host "        $backupPath" @Cyan
} else {
    Write-Host "[3/4] Nenhum profile anterior encontrado" @Green
}
Write-Host ""

# Passo 4: Copiar conteúdo do custom profile
Write-Host "[4/4] Instalando profile customizado..." @Yellow

$customProfilePath = Join-Path $PSScriptRoot "powershell-profile.ps1"

if (-not (Test-Path $customProfilePath)) {
    Write-Host "      ✗ ERRO: Arquivo powershell-profile.ps1 não encontrado!" @Red
    Write-Host "        Esperado em: $customProfilePath" @Red
    Write-Host ""
    Write-Host "      Execute este script a partir do diretório do projeto:" @Yellow
    Write-Host "      cd C:\caminho\para\Claude-Code-Projetos" @Cyan
    Write-Host "      .\install-powershell-profile.ps1" @Cyan
    exit 1
}

# Copiar o conteúdo
Copy-Item $customProfilePath $PROFILE -Force
Write-Host "      ✓ Profile copiado com sucesso!" @Green
Write-Host ""

# Passo 5: IMPORTANTE - Ajustar username WSL
Write-Host "═══════════════════════════════════════════════════════════" @Yellow
Write-Host "  ATENÇÃO: CONFIGURAÇÃO NECESSÁRIA" @Yellow
Write-Host "═══════════════════════════════════════════════════════════" @Yellow
Write-Host ""
Write-Host "O profile foi instalado, mas você precisa configurar seu username WSL:" @Yellow
Write-Host ""
Write-Host "1. O profile será aberto agora no Bloco de Notas" @Cyan
Write-Host "2. Procure pela linha (por volta da linha 39):" @Cyan
Write-Host '   $wslUser = "cmr-auto"  # ← TROCAR ESTE VALOR!' @Red
Write-Host ""
Write-Host "3. No WSL Ubuntu, descubra seu username:" @Cyan
Write-Host "   wsl" @Cyan
Write-Host "   whoami" @Cyan
Write-Host ""
Write-Host "4. Troque no profile:" @Cyan
Write-Host '   $wslUser = "seu-username-aqui"' @Green
Write-Host ""
Write-Host "5. Salve (Ctrl+S) e feche o Bloco de Notas" @Cyan
Write-Host ""

# Perguntar se quer abrir agora
Write-Host "Deseja abrir o profile agora para configurar? (S/N): " -NoNewline @Yellow
$response = Read-Host

if ($response -eq "S" -or $response -eq "s" -or $response -eq "Y" -or $response -eq "y" -or $response -eq "") {
    Write-Host ""
    Write-Host "Abrindo profile no editor..." @Cyan

    # Tentar diferentes editores
    if (Get-Command code -ErrorAction SilentlyContinue) {
        # VS Code disponível
        code $PROFILE
        Write-Host "✓ Aberto no VS Code" @Green
    } elseif (Get-Command notepad++ -ErrorAction SilentlyContinue) {
        # Notepad++ disponível
        notepad++ $PROFILE
        Write-Host "✓ Aberto no Notepad++" @Green
    } else {
        # Fallback para Bloco de Notas padrão
        notepad $PROFILE
        Write-Host "✓ Aberto no Bloco de Notas" @Green
    }
} else {
    Write-Host ""
    Write-Host "OK! Você pode editar o profile manualmente depois:" @Cyan
    Write-Host "notepad `$PROFILE" @Cyan
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" @Green
Write-Host "  Próximos Passos" @Green
Write-Host "═══════════════════════════════════════════════════════════" @Green
Write-Host ""
Write-Host "1. Configure o username WSL no profile (veja instruções acima)" @Yellow
Write-Host "2. Configure ExecutionPolicy (se ainda não fez):" @Yellow
Write-Host "   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" @Cyan
Write-Host ""
Write-Host "3. Recarregue o profile:" @Yellow
Write-Host "   . `$PROFILE" @Cyan
Write-Host ""
Write-Host "4. Teste os comandos:" @Yellow
Write-Host "   cstatus    # Ver status do ambiente" @Cyan
Write-Host "   scc        # Iniciar Claude Code no projeto" @Cyan
Write-Host "   gcp        # Abrir bash WSL no projeto" @Cyan
Write-Host "   gsync      # Git pull + status" @Cyan
Write-Host ""
Write-Host "✓ Instalação completa!" @Green
Write-Host ""
