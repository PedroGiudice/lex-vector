# Legal Extraction

**Suite de ferramentas para extração e limpeza de documentos jurídicos brasileiros**

---

## 📦 Projetos Consolidados

Este diretório centraliza 2 ferramentas complementares de extração de texto:

### 1. [verbose-correct-doodle](./verbose-correct-doodle/)
**Pré-Processador Jurídico v4.1 Professional Edition**

- **Tipo**: Aplicação HTML/JavaScript (100% offline)
- **Interface**: Web UI com design OLED-friendly
- **OCR**: ✅ Tesseract.js integrado
- **Sistemas**: 7 (PJE, ESAJ, EPROC, PROJUDI, STF, STJ, AUTO)
- **Features**: Processamento em lote, análise de 13 tipos de peças jurídicas
- **Export**: TXT, MD, DOCX, HTML
- **Uso**: Abrir `preprocessador-juridico-v4.1.html` no navegador

**Quando usar:**
- Precisa processar PDFs escaneados (OCR)
- Quer interface gráfica amigável
- Não tem ambiente Python configurado
- Processamento offline completo

---

### 2. [pdf-extractor-cli](./pdf-extractor-cli/)
**CLI Python profissional para limpeza de documentos jurídicos**

- **Tipo**: Command-line tool (Python 3.10+)
- **Interface**: CLI moderna com Rich terminal
- **OCR**: ❌ Não disponível (Fase 1) - Vem na Fase 2
- **Sistemas**: 7 (mesmos do verbose-correct-doodle)
- **Features**: 75+ padrões de limpeza, auto-detecção, blacklist customizável
- **Export**: TXT (futuro: MD, DOCX, HTML)
- **Uso**: `pdf-extractor process documento.pdf`

**Quando usar:**
- PDFs com camada de texto (não escaneados)
- Automação via scripts (PowerShell, Bash)
- Processamento em lote via linha de comando
- Integração com pipelines de dados

---

## 🔄 Relação Entre os Projetos

`pdf-extractor-cli` foi **portado e expandido** a partir de `verbose-correct-doodle`:

| Característica | verbose-correct-doodle | pdf-extractor-cli |
|----------------|------------------------|-------------------|
| **Plataforma** | Browser (offline) | Terminal (Python) |
| **OCR** | ✅ Tesseract.js | ❌ Fase 2 (futuro) |
| **Interface** | Web UI | CLI |
| **Batch** | ✅ UI de lote | Script externo |
| **Automação** | ❌ Manual | ✅ Scriptable |
| **Portabilidade Core** | ❌ Acoplado ao HTML | ✅ Core independente |

**São complementares!** Use verbose-correct-doodle para PDFs escaneados e interface gráfica. Use pdf-extractor-cli para automação e integração com outros sistemas.

---

## 🚀 Quick Start

### Opção 1: Interface Web (verbose-correct-doodle)

```bash
cd verbose-correct-doodle

# Abrir no navegador
xdg-open preprocessador-juridico-v4.1.html  # Linux
open preprocessador-juridico-v4.1.html      # macOS
start preprocessador-juridico-v4.1.html     # Windows
```

**Ou hospedar servidor local:**
```bash
python server.py
# Acesse http://localhost:8000
```

### Opção 2: CLI (pdf-extractor-cli)

```bash
cd pdf-extractor-cli

# Instalar
uv pip install -e .
# ou
pip install -e .

# Usar
pdf-extractor process documento.pdf
pdf-extractor detect sentenca.pdf
pdf-extractor systems
```

---

## 📊 Casos de Uso

### Cenário 1: Petição escaneada (sem camada de texto)

**Ferramenta**: verbose-correct-doodle
**Motivo**: Possui OCR integrado

```
1. Abrir preprocessador-juridico-v4.1.html
2. Selecionar PDF escaneado
3. Sistema: AUTO (detecção automática)
4. Processar (OCR será aplicado automaticamente)
5. Exportar em TXT, MD, DOCX ou HTML
```

### Cenário 2: Lote de 50 sentenças (com camada de texto)

**Ferramenta**: pdf-extractor-cli
**Motivo**: Automação via script

```powershell
# processar_lote.ps1
Get-ChildItem C:\Sentencas\*.pdf | ForEach-Object {
    pdf-extractor process $_.FullName --output "processadas\$($_.BaseName).txt"
}
```

### Cenário 3: Análise exploratória (identificar sistemas)

**Ferramenta**: pdf-extractor-cli
**Motivo**: Comando `detect` específico

```bash
# Analisar corpus
for pdf in *.pdf; do
    pdf-extractor detect "$pdf" >> analise_corpus.txt
done
```

### Cenário 4: Organizar autos processuais

**Ferramenta**: verbose-correct-doodle
**Motivo**: Feature de organização cronológica de peças

```
1. Abrir preprocessador-juridico-v4.1.html
2. Selecionar múltiplos PDFs
3. PROCESSAR LOTE
4. Clicar em "ORGANIZAR COMO AUTOS"
5. Exportar ZIP com cronologia automática
```

---

## 🧠 Integração Legal-Braniac

Ambos os projetos são automaticamente descobertos pelo **Legal-Braniac Orchestrator**.

### Configuração

Legal-Braniac detecta ferramentas em `legal-extraction/` e disponibiliza via agentes:

```
Legal-Braniac
├── Agentes
│   ├── oab-watcher
│   ├── djen-tracker
│   └── ...
└── Legal Extraction (este diretório)
    ├── verbose-correct-doodle → Web UI para OCR
    └── pdf-extractor-cli      → CLI para automação
```

### Uso via Legal-Braniac

**Exemplo de orquestração:**
```python
# Legal-Braniac decide qual ferramenta usar baseado na task:

# Task 1: "Extrair texto de PDF escaneado"
# → Recomenda: verbose-correct-doodle (tem OCR)

# Task 2: "Processar 100 PDFs do DJEN em lote"
# → Recomenda: pdf-extractor-cli (scriptable)

# Task 3: "Identificar sistema judicial de um PDF"
# → Recomenda: pdf-extractor-cli (comando `detect`)
```

---

## 📁 Estrutura do Diretório

```
legal-extraction/
├── README.md                       ← Este arquivo
├── verbose-correct-doodle/         ← Projeto 1: Web UI com OCR
│   ├── preprocessador-juridico-v4.1.html
│   ├── modules/
│   │   ├── pdf-structural-parser.js
│   │   ├── ocr-engine.js
│   │   ├── batch-processor.js
│   │   └── ...
│   ├── CHANGELOG_v4.1.3.md
│   ├── CLAUDE_README.md            ← Documentação técnica completa
│   └── README.md                   ← Documentação específica
│
└── pdf-extractor-cli/              ← Projeto 2: CLI Python
    ├── src/pdf_extractor/
    │   ├── cli/                    ← Interface Click
    │   ├── core/                   ← Lógica portável
    │   │   ├── patterns.py         ← 75+ regex patterns
    │   │   ├── detector.py         ← Auto-detecção
    │   │   └── cleaner.py
    │   └── exporters/
    ├── tests/
    ├── pyproject.toml
    ├── CHEATSHEET.md
    └── README.md                   ← Documentação específica
```

---

## 🎯 Roadmap Unificado

### ✅ Implementado

**verbose-correct-doodle v4.1.3:**
- [x] OCR Tesseract.js
- [x] Processamento em lote
- [x] 13 tipos de peças jurídicas
- [x] Export multi-formato (TXT, MD, DOCX, HTML)
- [x] Interface OLED-friendly

**pdf-extractor-cli v1.0.0:**
- [x] 75+ padrões de limpeza
- [x] Auto-detecção de sistemas
- [x] CLI profissional (Click + Rich)
- [x] Export TXT

### 🚧 Em Desenvolvimento

**pdf-extractor-cli Fase 2:**
- [ ] Integração OCR (PaddleOCR)
- [ ] Processamento paralelo
- [ ] Barra de progresso

**Integração Legal-Braniac:**
- [ ] Auto-seleção de ferramenta baseada em contexto
- [ ] Pipeline unificado: Web UI → CLI → Backend

### 📅 Futuro

**pdf-extractor-cli Fase 3:**
- [ ] Batch processing nativo
- [ ] Export MD, DOCX, HTML
- [ ] Análise de documentos (13 tipos)

**pdf-extractor-cli Fase 4:**
- [ ] Backend FastAPI
- [ ] API REST
- [ ] Deploy Docker

**Convergência:**
- [ ] Core unificado (Python) usado por ambos
- [ ] Web UI consome API do CLI backend
- [ ] Legal-Braniac orquestra todo o pipeline

---

## 📚 Documentação Adicional

- **verbose-correct-doodle**: Ver `verbose-correct-doodle/CLAUDE_README.md` (870 linhas de documentação técnica)
- **pdf-extractor-cli**: Ver `pdf-extractor-cli/CHEATSHEET.md` (guia rápido) e `README.md`
- **Legal-Braniac**: Ver `.claude/agents/legal-braniac.md` (orquestrador principal)

---

## 🤝 Contribuindo

Ambos os projetos aceitam contribuições!

**Diretrizes:**
- verbose-correct-doodle: JavaScript/HTML puro (offline-first)
- pdf-extractor-cli: Python 3.10+, seguir ruff style

---

## 📄 Licença

Ambos os projetos: **MIT License**

---

## 🙏 Créditos

**Desenvolvido com ❤️ para a comunidade jurídica brasileira**

- Inspirado em Projeto Victor (STF)
- Baseado em ISO 32000-2:2020 (PDF Specification)
- Conformidade com Lei 11.419/2006 (Processo Eletrônico)

---

**Última Atualização**: 2025-11-13
**Mantido por**: Legal-Braniac Orchestrator
**Status**: ✅ Production-ready
