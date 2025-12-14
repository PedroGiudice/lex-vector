# Exemplos de Uso - Legal Text Extractor

Scripts demonstrativos para cada estágio do pipeline.

---

## Step 02: Vision Pipeline (O Saneador)

### Shell Script (Automação)

```bash
./examples/run_step_02.sh [doc_id] [layout_json] [pdf_path]
```

**Exemplo:**
```bash
# Uso padrão
./examples/run_step_02.sh exemplo_scan

# Customizado
./examples/run_step_02.sh meu_doc outputs/meu_doc/layout.json inputs/meu_doc.pdf
```

**O que faz:**
1. Verifica dependências (pdf2image, opencv, poppler)
2. Valida inputs (layout.json e PDF existem)
3. Conta páginas RASTER_NEEDED
4. Executa processamento
5. Verifica output e lista imagens geradas

---

### Python Script (Exemplos Programáticos)

```bash
python examples/step_02_example.py [numero]
```

**Exemplos disponíveis:**

**1. Uso Básico**
```bash
python examples/step_02_example.py 1
```
Demonstra uso padrão com configuração default.

**2. Configuração Customizada (Scans Antigos)**
```bash
python examples/step_02_example.py 2
```
DPI alto + denoise agressivo para documentos de baixa qualidade.

**3. Performance Otimizada (Batch)**
```bash
python examples/step_02_example.py 3
```
DPI baixo + sem denoise + JPEG para processar múltiplos documentos rapidamente.

**4. Análise de Layout**
```bash
python examples/step_02_example.py 4
```
Inspeciona `layout.json` e mostra estatísticas antes de processar.

**5. Tratamento de Erros**
```bash
python examples/step_02_example.py 5
```
Demonstra tratamento de erros robusto (arquivos missing, etc).

**Executar todos:**
```bash
python examples/step_02_example.py all
```

---

## Estrutura

```
examples/
├── README.md                 # Este arquivo
├── run_step_02.sh            # Script bash automatizado
└── step_02_example.py        # Exemplos Python programáticos
```

---

## Pré-requisitos

### 1. Virtual Environment
```bash
cd ferramentas/legal-text-extractor
python -m venv .venv
source .venv/bin/activate
```

### 2. Dependências Python
```bash
pip install -r requirements.txt
```

### 3. Poppler (Sistema)
```bash
# Ubuntu/WSL
sudo apt install poppler-utils

# macOS
brew install poppler
```

### 4. Dados de Teste
```bash
# Execute step_01 primeiro para gerar layout.json
python src/steps/step_01_layout.py \
    test-documents/exemplo_scan.pdf \
    --doc-id exemplo_scan
```

---

## Troubleshooting

### Erro: "No module named 'pdf2image'"
```bash
pip install -r requirements.txt
```

### Erro: "Unable to load PDF file"
```bash
# Instalar poppler
sudo apt install poppler-utils

# Verificar
pdftoppm -h
```

### Erro: "Layout não encontrado"
```bash
# Execute step_01 primeiro
python src/steps/step_01_layout.py test-documents/exemplo.pdf --doc-id exemplo
```

---

## Próximos Passos

Após executar os exemplos do Step 02:

1. **Inspecionar imagens geradas**:
   ```bash
   ls -lh outputs/exemplo_scan/images/
   ```

2. **Executar Step 03 (OCR)**:
   ```bash
   python src/steps/step_03_extract.py \
       outputs/exemplo_scan/layout.json \
       outputs/exemplo_scan/images/ \
       --doc-id exemplo_scan
   ```

3. **Pipeline completo**:
   ```bash
   # Step 01: Layout
   python src/steps/step_01_layout.py inputs/doc.pdf --doc-id doc123

   # Step 02: Vision
   ./examples/run_step_02.sh doc123

   # Step 03: Extract
   python src/steps/step_03_extract.py \
       outputs/doc123/layout.json \
       outputs/doc123/images/ \
       --doc-id doc123
   ```

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota
