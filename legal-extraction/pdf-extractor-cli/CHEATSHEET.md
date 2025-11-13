# PDF Extractor CLI - Cheatsheet

Guia de referência rápida para uso diário no escritório.

## 🚀 Comandos Essenciais

### Processar um PDF

```powershell
# Uso básico (auto-detecção de sistema)
pdf-extractor process documento.pdf

# Com saída personalizada
pdf-extractor process petição.pdf --output limpo.txt

# Com cabeçalho de metadados
pdf-extractor process doc.pdf --with-header

# Especificar sistema manualmente
pdf-extractor process doc.pdf --system PJE

# Adicionar termos customizados para remover
pdf-extractor process doc.pdf -b CONFIDENCIAL -b "USO INTERNO"
```

### Detectar Sistema Judicial

```powershell
# Identificar qual sistema gerou o PDF
pdf-extractor detect documento.pdf
```

### Listar Sistemas Suportados

```powershell
# Ver todos os sistemas que a CLI reconhece
pdf-extractor systems
```

### Ajuda

```powershell
# Ajuda geral
pdf-extractor --help

# Ajuda de comando específico
pdf-extractor process --help
```

## 📁 Trabalhando com Caminhos de Rede

### Servidor Local (UNC Paths)

```powershell
# Processar de servidor Windows
pdf-extractor process "\\servidor\processos\2025\petição.pdf"

# Salvar em servidor
pdf-extractor process doc.pdf --output "\\servidor\limpos\doc_limpo.txt"
```

### Drives Mapeados

```powershell
# Drive Z: mapeado para \\servidor\processos
pdf-extractor process "Z:\2025\Janeiro\petição.pdf"

# Salvar em drive mapeado
pdf-extractor process doc.pdf --output "Z:\limpos\doc_limpo.txt"
```

### Caminhos com Espaços

```powershell
# SEMPRE use aspas duplas
pdf-extractor process "C:\Meus Documentos\Processos\doc.pdf"
pdf-extractor process "\\servidor\Processos 2025\petição.pdf"
```

## 🔄 Batch Processing (Processar Múltiplos PDFs)

### Processar Todos os PDFs de uma Pasta

```powershell
# Processar todos os PDFs da pasta atual
Get-ChildItem *.pdf | ForEach-Object {
    pdf-extractor process $_.FullName
}

# Processar PDFs de pasta específica
Get-ChildItem "Z:\Processos\2025\*.pdf" | ForEach-Object {
    pdf-extractor process $_.FullName
}
```

### Processar e Salvar em Outra Pasta

```powershell
# Criar pasta de saída se não existir
New-Item -ItemType Directory -Force -Path "Z:\Limpos\2025"

# Processar todos os PDFs e salvar em outra pasta
Get-ChildItem "Z:\Processos\2025\*.pdf" | ForEach-Object {
    $outputFile = "Z:\Limpos\2025\$($_.BaseName)_limpo.txt"
    Write-Host "Processando: $($_.Name)"
    pdf-extractor process $_.FullName --output $outputFile
}
```

### Processar com Blacklist Customizado

```powershell
# Remover termos específicos de todos os PDFs
Get-ChildItem "Z:\Processos\*.pdf" | ForEach-Object {
    pdf-extractor process $_.FullName -b CONFIDENCIAL -b "ADVOGADO OAB"
}
```

### Processar com Cabeçalho de Metadados

```powershell
# Adicionar cabeçalho com estatísticas em todos
Get-ChildItem *.pdf | ForEach-Object {
    pdf-extractor process $_.FullName --with-header
}
```

## 📊 Script de Batch Avançado

Salve como `processar_lote.ps1`:

```powershell
# ============================================
# Script de Processamento em Lote
# ============================================

param(
    [string]$InputFolder = "Z:\Processos\2025",
    [string]$OutputFolder = "Z:\Limpos\2025",
    [switch]$WithHeader = $false,
    [string[]]$Blacklist = @()
)

# Criar pasta de saída
New-Item -ItemType Directory -Force -Path $OutputFolder | Out-Null

# Obter todos os PDFs
$pdfs = Get-ChildItem $InputFolder -Filter *.pdf

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PDF Extractor - Processamento em Lote" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Pasta de entrada: $InputFolder"
Write-Host "Pasta de saída: $OutputFolder"
Write-Host "Total de PDFs: $($pdfs.Count)"
Write-Host ""

$contador = 0
$sucesso = 0
$erros = 0

foreach ($pdf in $pdfs) {
    $contador++
    $percentual = [math]::Round(($contador / $pdfs.Count) * 100, 1)

    Write-Host "[$contador/$($pdfs.Count) - $percentual%] Processando: " -NoNewline
    Write-Host $pdf.Name -ForegroundColor Yellow

    $outputFile = Join-Path $OutputFolder "$($pdf.BaseName)_limpo.txt"

    try {
        # Montar comando
        $args = @("process", $pdf.FullName, "--output", $outputFile)

        if ($WithHeader) {
            $args += "--with-header"
        }

        foreach ($termo in $Blacklist) {
            $args += "-b"
            $args += $termo
        }

        # Executar
        & pdf-extractor $args

        if ($LASTEXITCODE -eq 0) {
            $sucesso++
            Write-Host "  ✓ Sucesso" -ForegroundColor Green
        } else {
            $erros++
            Write-Host "  ✗ Erro no processamento" -ForegroundColor Red
        }

    } catch {
        $erros++
        Write-Host "  ✗ Erro: $($_.Exception.Message)" -ForegroundColor Red
    }

    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Processamento Concluído!" -ForegroundColor Green
Write-Host "Total processados: $contador"
Write-Host "Sucessos: $sucesso" -ForegroundColor Green
Write-Host "Erros: $erros" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Cyan
```

### Usar o Script:

```powershell
# Uso básico
.\processar_lote.ps1

# Com parâmetros customizados
.\processar_lote.ps1 -InputFolder "Z:\Processos\Urgentes" -OutputFolder "Z:\Limpos\Urgentes"

# Com cabeçalho
.\processar_lote.ps1 -WithHeader

# Com blacklist
.\processar_lote.ps1 -Blacklist @("CONFIDENCIAL", "USO INTERNO")

# Tudo junto
.\processar_lote.ps1 -InputFolder "Z:\Processos\2025" `
                     -OutputFolder "Z:\Limpos\2025" `
                     -WithHeader `
                     -Blacklist @("CONFIDENCIAL", "OAB")
```

## 🔍 Troubleshooting

### Comando não encontrado

```powershell
# Ativar ambiente virtual primeiro
cd C:\claude-work\repos\pdf-extractor-cli
.\.venv\Scripts\Activate.ps1

# Agora deve funcionar
pdf-extractor --version
```

### Erro: "PDF contains insufficient text"

```powershell
# PDF é escaneado (sem camada de texto)
# Solução: Aguardar implementação do OCR (Fase 2)
# Por enquanto, use ferramentas de OCR externas ou PDFs digitais
```

### Performance lenta

```powershell
# Para PDFs grandes (100+ páginas), seja paciente
# Fase 1 não tem otimizações de performance
# Fase 2+ terá processamento paralelo
```

### Encoding de caracteres

```powershell
# Output sempre em UTF-8
# Se precisar outro encoding, use PowerShell:
Get-Content output.txt | Out-File output_latin1.txt -Encoding Latin1
```

## 🎯 Workflows Comuns

### 1. Processar Petições Recebidas

```powershell
# Pasta de entrada: Z:\Petições\Novas
# Pasta de saída: Z:\Petições\Processadas

Get-ChildItem "Z:\Petições\Novas\*.pdf" | ForEach-Object {
    $output = "Z:\Petições\Processadas\$($_.BaseName).txt"
    pdf-extractor process $_.FullName --output $output --with-header
}
```

### 2. Analisar Sistema de PDFs Desconhecidos

```powershell
# Identificar sistemas de vários PDFs
Get-ChildItem "Z:\Documentos\*.pdf" | ForEach-Object {
    Write-Host "`n===== $($_.Name) =====" -ForegroundColor Cyan
    pdf-extractor detect $_.FullName
}
```

### 3. Limpeza com Blacklist Específica do Escritório

```powershell
# Termos recorrentes do seu escritório
$blacklist = @(
    "CONFIDENCIAL",
    "USO INTERNO",
    "ADVOGADO OAB/SP 123.456",
    "ESCRITÓRIO EXEMPLO & ASSOCIADOS"
)

Get-ChildItem *.pdf | ForEach-Object {
    $args = @("process", $_.FullName)
    foreach ($termo in $blacklist) {
        $args += "-b"
        $args += $termo
    }
    & pdf-extractor $args
}
```

## ⚙️ PowerShell: Criar Alias Permanente

```powershell
# Editar perfil do PowerShell
notepad $PROFILE

# Adicionar ao arquivo:
function Invoke-PdfExtractor { pdf-extractor $args }
Set-Alias -Name pre -Value Invoke-PdfExtractor

# Salvar e recarregar
. $PROFILE

# Agora pode usar:
pre process documento.pdf
pre detect documento.pdf
pre systems
```

## 📋 Sistemas Suportados (Códigos)

| Código | Sistema |
|--------|---------|
| `STF` | Supremo Tribunal Federal |
| `STJ` | Superior Tribunal de Justiça |
| `PJE` | Processo Judicial Eletrônico |
| `ESAJ` | Sistema de Automação da Justiça |
| `EPROC` | Sistema de Processo Eletrônico |
| `PROJUDI` | Processo Judicial Digital |
| `GENERIC_JUDICIAL` | Genérico (fallback) |

## 🔮 Próximas Features (Fase 2+)

- **OCR**: Processar PDFs escaneados (contratos, e-mails, prints)
- **Batch paralelo**: Processar múltiplos PDFs simultaneamente
- **Export MD/DOCX/HTML**: Mais formatos de saída
- **Headers/footers**: Remoção aprimorada de cabeçalhos e rodapés

---

**Dúvidas?** Consulte o [README.md](README.md) completo ou use `pdf-extractor --help`
