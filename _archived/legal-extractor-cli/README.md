# Legal Extractor CLI

> ⚠️ **DEPRECADO**: Este projeto foi descontinuado. Use `legal-workbench/ferramentas/legal-text-extractor/` como a implementação ativa.

CLI simplificada para extração de texto de documentos jurídicos em PDF.

## Características

- **Interface Rich**: Output colorido e formatado
- **Extração Inteligente**: Detecta automaticamente o melhor método por página
- **Engines Múltiplos**: pdfplumber, Tesseract, Marker (escalonamento automático)
- **Modo Interativo**: Pode pedir caminho do arquivo se não fornecido
- **Processamento em Lote**: Processa múltiplos PDFs de uma vez

## Instalação

```bash
cd legal-extractor-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Uso

### Extrair um PDF

```bash
# Via argumento
legal-extract extract documento.pdf

# Interativo (pede o caminho)
legal-extract extract

# Com opções
legal-extract extract documento.pdf --output ./saida/ --system PJE
```

### Ver informações do sistema

```bash
legal-extract info
```

### Processar em lote

```bash
legal-extract batch ./pasta-com-pdfs/
```

## Arquitetura

Esta CLI **NÃO reimplementa** a lógica de extração. Ela é um wrapper que chama:

```
ferramentas/legal-text-extractor/
├── main.py                 # LegalTextExtractor
├── src/
│   ├── steps/
│   │   ├── step_01_layout.py   # Análise de layout
│   │   ├── step_02_vision.py   # Processamento de imagem
│   │   └── step_03_extract.py  # Extração de texto
│   └── engines/
│       ├── selector.py         # Seleção de engine
│       ├── tesseract_engine.py
│       └── marker_engine.py
```

## Engines

| Engine | RAM | Velocidade | Uso |
|--------|-----|------------|-----|
| pdfplumber | ~100MB | Rápido | Texto nativo |
| Tesseract | ~500MB | Médio | Scans limpos |
| Marker | ~4GB | Lento | Scans degradados |

O sistema escolhe automaticamente baseado na complexidade de cada página.

## Requisitos

- Python 3.10+
- Tesseract OCR (para páginas escaneadas)
- Marker (opcional, para scans degradados)

```bash
# Instalar Tesseract
sudo apt install tesseract-ocr tesseract-ocr-por
```

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota
