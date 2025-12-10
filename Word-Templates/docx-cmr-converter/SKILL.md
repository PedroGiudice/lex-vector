---
name: docx-cmr-converter
description: Converte documentos Markdown para Word (DOCX) seguindo o padrão de formatação CMR Advogados - fontes, espaçamentos e estilos jurídicos
version: 1.0.0
---

# Conversor de Markdown para DOCX - Padrão CMR Advogados

Esta skill permite converter documentos Markdown de peças jurídicas para arquivos Word (.docx) seguindo exatamente o padrão de formatação do escritório C. M. Rodrigues Advogados.

## Especificações de Formatação

### Fontes (CRÍTICO)

| Elemento | Fonte | Tamanho |
|----------|-------|---------|
| **Cabeçalho** | Verdana | 26pt |
| **Subtítulo cabeçalho** | Verdana | 12pt |
| **Corpo do texto** | Century Gothic | 12pt |
| **Capítulos** | Century Gothic | 12pt bold |
| **Citações** | Century Gothic | 10pt italic |
| **Rodapé** | Century Gothic | 6pt |

**REGRA FUNDAMENTAL:** Verdana é usada APENAS no cabeçalho ("C. M. RODRIGUES / Advogados"). Todo o restante do documento usa Century Gothic.

### Configuração de Página (A4)

```
Tamanho: A4 (210mm x 297mm)
Margens:
  - Superior: 2.5cm (1417 twips)
  - Inferior: 2.5cm (1417 twips)
  - Esquerda: 3cm (1701 twips)
  - Direita: 2cm (1133 twips)
```

### Espaçamentos

| Tipo | Espaçamento |
|------|-------------|
| Corpo do texto | 1.5 linhas |
| Citações | 1.0 linha |
| Rodapé | 1.0 linha |

### Recuos

- **Primeira linha (parágrafos):** 4cm (2268 twips)
- **Citações (esquerda):** 4cm (2268 twips)

## Estrutura do Documento

### 1. Cabeçalho (Header)
```
                                    C. M. RODRIGUES    [Verdana 26pt]
                                         Advogados    [Verdana 12pt]
```
Alinhamento: direita

### 2. Endereçamento
```
EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA XX VARA CÍVEL...
```
Century Gothic 12pt, justificado, espaçamento 1.5

### 3. Qualificação das Partes
```
        EMPRESA LTDA., pessoa jurídica de direito privado...
```
Century Gothic 12pt, justificado, espaçamento 1.5, recuo de primeira linha

### 4. Título da Peça
```
                              CONTESTAÇÃO
```
Century Gothic 12pt bold, centralizado

### 5. Capítulos (Numeração Romana)
```
I. TEMPESTIVIDADE
II. SÍNTESE DOS FATOS
III. DO MÉRITO
```
Century Gothic 12pt bold, justificado

### 6. Subcapítulos (Letras)
```
A. DA ILEGITIMIDADE PASSIVA
B. DA AUSÊNCIA DE NEXO CAUSAL
```
Century Gothic 12pt bold, justificado

### 7. Parágrafos Numerados
```
        14. A legitimidade passiva ad causam exige que a conduta...
```
Century Gothic 12pt, justificado, recuo de primeira linha, espaçamento 1.5

### 8. Citações de Jurisprudência
```
        "De acordo com a teoria da asserção, acolhida pela
        jurisprudência do Superior Tribunal de Justiça..."
        (STJ, REsp 1.234.567/SP, Rel. Min. Fulano, j. 01/01/2024)
```
Century Gothic 10pt italic, alinhado à esquerda, recuo de 4cm, espaçamento simples

### 9. Alíneas (Pedidos)
```
        a) O acolhimento da preliminar de ilegitimidade passiva;
        b) A extinção do processo sem resolução do mérito;
```
Century Gothic 12pt, justificado, recuo de 4cm

### 10. Assinatura
```
Carlos Magno N. Rodrigues
OAB/SP nº 129.021

Ana Beatriz Vianna Paoli
OAB/SP nº 493.706
```
Century Gothic 12pt (nome em bold), alinhado à esquerda

### 11. Rodapé (Footer)
```
                    Alameda Santos nº. 211, 16º andar, cj. 1607
                                  São Paulo – SP 01419-000
                                      Tel.: (11) 3044 4160
```
Century Gothic 6pt, alinhado à direita

## Script de Conversão

O script `convert-md-to-docx.js` na pasta `scripts/` realiza a conversão automática.

### Uso

```bash
node scripts/convert-md-to-docx.js documento.md [saida.docx]
```

### Dependências

```bash
npm install docx
```

## Mapeamento Markdown para DOCX

| Markdown | Estilo DOCX |
|----------|-------------|
| `# Texto` | Endereçamento |
| `## CONTESTAÇÃO` | TituloPeca (se maiúsculo) |
| `## I. Título` | Capitulo |
| `### A. Subtítulo` | Subcapitulo |
| `1. Parágrafo` | ParagrafoNumerado |
| `> Citação` | Citacao (10pt italic) |
| `a) Item` | ItemLista |
| `**Nome**` + OAB | Assinatura |
| `| tabela |` | Table com bordas |

## Conversão de Unidades

```javascript
// Twips para diferentes medidas
1 cm = 567 twips
1 inch = 1440 twips
1 pt = 2 half-points (size no docx)

// Valores comuns
4cm = 2268 twips (recuo padrão)
3cm = 1701 twips (margem esquerda)
2.5cm = 1417 twips (margens sup/inf)
2cm = 1133 twips (margem direita)
```

## Erros Comuns a Evitar

1. **Usar Verdana no corpo** - Verdana é APENAS para cabeçalho
2. **Fonte 10pt no corpo** - O corpo é 12pt, apenas citações são 10pt
3. **Esquecer recuo de primeira linha** - Parágrafos normais têm recuo de 4cm
4. **Espaçamento errado em citações** - Citações usam espaçamento simples (1.0)
5. **Usar `\n` para quebras** - Sempre criar novo Paragraph
