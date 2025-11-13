# PDF Extractor CLI

🇧🇷 **Ferramenta profissional para extração e limpeza de documentos jurídicos brasileiros**

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

Extrai texto de PDFs processuais e remove automaticamente assinaturas digitais, certificações ICP-Brasil, códigos de validação e outros elementos não-textuais específicos de cada sistema judicial.

## ✨ Características

- ✅ **7 Sistemas Judiciais**: Detecção automática de PJE, ESAJ, EPROC, PROJUDI, STF, STJ, e genérico
- ✅ **75+ Padrões de Limpeza**: Regex otimizados para cada sistema + universais ICP-Brasil
- ✅ **Auto-Detecção Inteligente**: Identifica o sistema com scoring de confiança
- ✅ **Blacklist Customizável**: Remova termos específicos adicionais
- ✅ **Interface Profissional**: CLI moderna com Rich terminal output
- ✅ **Sem OCR (Fase 1)**: Focado em PDFs com camada de texto (OCR vem na Fase 2)

## 🎯 Casos de Uso

- Extração de petições e sentenças para análise
- Limpeza de documentos para arquivamento
- Preparação de textos para processamento posterior
- Remoção em massa de elementos de certificação
- Análise de corpus jurídico

## 📦 Instalação

### Opção 1: Via `uv` (Recomendado)

```bash
# Instalar uv (se ainda não tiver)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar o PDF Extractor CLI
cd pdf-extractor-cli
uv pip install -e .
```

### Opção 2: Via `pip`

```bash
cd pdf-extractor-cli
pip install -e .
```

### Dependências

O projeto usa:
- `click` - CLI framework
- `pdfplumber` - Extração de texto de PDFs
- `rich` - Terminal output colorido
- Python 3.10+

## 🚀 Uso Rápido

### Processar um PDF

```bash
# Uso básico (auto-detecção de sistema)
pdf-extractor process documento.pdf

# Com saída personalizada
pdf-extractor process petição.pdf --output clean.txt

# Com cabeçalho de metadados
pdf-extractor process doc.pdf --with-header

# Especificar sistema manualmente
pdf-extractor process doc.pdf --system PJE

# Adicionar termos customizados para remover
pdf-extractor process doc.pdf -b CONFIDENCIAL -b "USO INTERNO"
```

### Detectar Sistema

```bash
# Apenas identificar o sistema sem limpar
pdf-extractor detect documento.pdf
```

Saída exemplo:
```
🔍 Analyzing: sentença.pdf

────────────────────────────────────────────────────────────
System: PJE (Processo Judicial Eletrônico)
Code: PJE
Confidence: 92%
Status: 🟢

Matches: 5/8 patterns

Other possibilities:
  • ESAJ: 23%
  • GENERIC_JUDICIAL: 15%
────────────────────────────────────────────────────────────
```

### Listar Sistemas Suportados

```bash
pdf-extractor systems
```

### Debug Mode

```bash
pdf-extractor --debug process documento.pdf
```

## 📖 Documentação Completa

### Comando `process`

Extrai e limpa texto de um PDF.

```bash
pdf-extractor process [OPTIONS] PDF_FILE
```

**Opções:**

| Opção | Descrição | Padrão |
|-------|-----------|--------|
| `-o, --output PATH` | Caminho do arquivo de saída | `{input}.txt` |
| `-s, --system TEXT` | Sistema judicial (auto\|PJE\|ESAJ\|EPROC\|PROJUDI\|STF\|STJ) | `auto` |
| `-b, --blacklist TEXT` | Termo customizado para remover (use múltiplas vezes) | - |
| `--with-header` | Incluir cabeçalho com metadados no output | `False` |

**Exemplo de saída com `--with-header`:**

```
DOCUMENTO PROCESSADO
Sistema Detectado: PJE (Processo Judicial Eletrônico) (PJE)
Confiança da Detecção: 92%
Tamanho Original: 45,231 caracteres
Tamanho Final: 38,104 caracteres
Redução: 15.76%
Padrões Removidos: 23
================================================================================

[Texto limpo aqui...]
```

### Comando `detect`

Analisa o PDF e identifica qual sistema judicial o gerou.

```bash
pdf-extractor detect PDF_FILE
```

Útil para:
- Verificar qualidade da detecção antes de processar
- Debugging de problemas de limpeza
- Análise de corpus (identificar sistemas presentes)

### Comando `systems`

Lista todos os sistemas judiciais suportados com descrições.

```bash
pdf-extractor systems
```

## 🔧 Configuração Avançada

### Arquivo `.env`

Crie um arquivo `.env` na raiz do projeto (veja `.env.example`):

```bash
# Exemplo
PDF_EXTRACTOR_DEFAULT_SYSTEM=auto
PDF_EXTRACTOR_LOG_LEVEL=INFO
```

## 📊 Sistemas Suportados

| Sistema | Código | Prioridade | Características |
|---------|--------|------------|-----------------|
| **STF** | `STF` | Alta | PKCS#7, marca d'água com CPF, Projeto Victor |
| **STJ** | `STJ` | Alta | Múltiplos elementos de validação, timestamps |
| **PJE** | `PJE` | Média | Resolução CNJ 281/2019, códigos alfanuméricos |
| **ESAJ** | `ESAJ` | Média | Selo lateral vertical, QR codes, TJSP |
| **EPROC** | `EPROC` | Média | Assinatura destacada (.p7s), CAdES |
| **PROJUDI** | `PROJUDI` | Baixa | Variações regionais, versões diversas |

## 🎨 Exemplos

### PowerShell Integration

```powershell
# Criar alias permanente
Set-Alias -Name pre -Value pdf-extractor

# Agora pode usar:
pre process documento.pdf

# Processar pasta inteira
Get-ChildItem *.pdf | ForEach-Object {
    pre process $_.FullName
}

# Processar e buscar termo
pre process doc.pdf | Select-String "termo importante"
```

### Batch Processing Script

```powershell
# processar_lote.ps1
$pdfs = Get-ChildItem C:\Processos\2025 -Filter *.pdf

foreach ($pdf in $pdfs) {
    Write-Host "Processing $($pdf.Name)..."
    pdf-extractor process $pdf.FullName `
        --output "processados\$($pdf.BaseName).txt" `
        -b "CONFIDENCIAL"
}

Write-Host "✓ Processed $($pdfs.Count) files"
```

## 🏗️ Arquitetura

```
src/pdf_extractor/
├── cli/              # Interface Click
├── core/             # Lógica principal (portável!)
│   ├── patterns.py   # 75+ regex patterns
│   ├── detector.py   # Sistema de detecção
│   ├── cleaner.py    # Orquestrador
│   └── normalizer.py # Pós-processamento
├── exporters/        # Formatos de saída
└── utils/            # Utilitários
```

**Princípio chave:** Core modules são **independentes do CLI**, permitindo reuso futuro em backend web.

## 🔮 Roadmap

### ✅ Fase 1: MVP (Atual)
- [x] Core de limpeza com 75+ padrões
- [x] Auto-detecção de sistemas
- [x] CLI funcional
- [x] Export TXT

### 🚧 Fase 2: OCR (Próxima)
- [ ] Integração PaddleOCR
- [ ] Detecção automática de PDFs escaneados
- [ ] Processamento paralelo de páginas
- [ ] Barra de progresso

### 📅 Fase 3: Features Avançadas
- [ ] Batch processing paralelo
- [ ] Export MD, DOCX, HTML
- [ ] Configuração via YAML
- [ ] Análise de documentos (13 tipos)

### 🌐 Fase 4: Integração Web (Futuro)
- [ ] Backend FastAPI
- [ ] API REST
- [ ] Integração com web UI atual
- [ ] Deploy Docker

## 🧪 Desenvolvimento

### Instalar em modo de desenvolvimento

```bash
# Com uv
uv pip install -e ".[dev]"

# Ou com pip
pip install -e ".[dev]"
```

### Rodar testes

```bash
pytest tests/
```

### Code quality

```bash
# Linting
ruff check src/

# Type checking
mypy src/
```

## 📝 Changelog

### v1.0.0 (2025-11-12)

**MVP - Fase 1 Completa**

- ✨ Core de limpeza com 75+ padrões regex
- ✨ Detector automático de 7 sistemas judiciais
- ✨ CLI profissional com Click
- ✨ Export para TXT
- ✨ Blacklist customizável
- 📚 Documentação completa

## 👥 Contribuindo

Contribuições são bem-vindas! Este é um projeto em desenvolvimento ativo.

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

## 🙏 Créditos

Portado e expandido a partir do projeto [verbose-correct-doodle](https://github.com/PedroGiudice/verbose-correct-doodle).

Baseado em pesquisa sobre sistemas de processo judicial eletrônico no Brasil.

---

**Desenvolvido com ❤️ para a comunidade jurídica brasileira**
