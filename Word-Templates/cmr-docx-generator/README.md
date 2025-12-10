# CMR DOCX Generator

Gerador de documentos Word (.docx) a partir de Markdown, com formatação padrão CMR Advogados.

## Arquitetura

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Markdown      │ ──▶  │  doc_builder.py │ ──▶  │   OUTPUT.docx   │
│   (peça)        │      │                 │      │                 │
└─────────────────┘      └────────┬────────┘      └─────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ cmr_styles.json │
                         │   (DNA/Config)  │
                         └─────────────────┘
```

## Instalação

```bash
cd cmr-docx-generator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

### Converter Markdown para DOCX

```bash
python doc_builder.py documento.md [saida.docx]
```

### Extrair DNA de um template existente

```bash
python style_extractor.py template.docx [estilos.json]
```

### Gerar DNA de consenso de múltiplos documentos

```bash
python style_extractor.py --consensus ./pasta-com-docx/ [consenso.json]
```

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `doc_builder.py` | Conversor MD → DOCX |
| `style_extractor.py` | Extrator de DNA de templates |
| `cmr_styles.json` | Configuração de estilos CMR |
| `requirements.txt` | Dependências Python |

## Mapeamento Markdown → Estilo

| Markdown | Estilo DOCX |
|----------|-------------|
| `# Texto` | Endereçamento |
| `## CONTESTAÇÃO` | Title_Peca (centralizado) |
| `## I. Título` | Chapter_Heading |
| `### A. Subtítulo` | Subcapitulo |
| `1. Parágrafo` | Paragraph_Numbered |
| `> Citação` | Citation (10pt, itálico) |
| `a) Item` | Item_Lista |
| `**Nome** + OAB` | Assinatura |
| `---` | Page break |

## Configuração (cmr_styles.json)

O arquivo `cmr_styles.json` define:

- **page_setup**: Tamanho A4, margens
- **header**: "C. M. RODRIGUES / Advogados" (Verdana)
- **footer**: Endereço do escritório (Century Gothic 6pt)
- **styles_map**: Definições de cada estilo

### Exemplo de estilo:

```json
{
  "Paragraph_Numbered": {
    "font_name": "Century Gothic",
    "font_size_pt": 12,
    "alignment": "BOTH",
    "indent_first_line_twips": 2268,
    "line_spacing_rule": "1.5"
  }
}
```

## Unidades

- **twips**: 1 cm = 567 twips
- **pt**: Pontos tipográficos
- **half-points**: Usado internamente pelo Word (pt × 2)

| Medida | Twips |
|--------|-------|
| 4 cm | 2268 |
| 3 cm | 1701 |
| 2.5 cm | 1417 |
| 2 cm | 1133 |
