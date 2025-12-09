# Template de Formatação CMR para Peças Jurídicas

Gera arquivos .docx formatados no padrão do escritório C. M. Rodrigues Advogados.

**IMPORTANTE: Leia este documento INTEIRO antes de começar. As regras de formatação são específicas e devem ser seguidas EXATAMENTE.**

## Configuração Base

```javascript
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, LevelFormat, HeadingLevel, BorderStyle,
        WidthType, ShadingType, VerticalAlign, PageNumber, PageBreak,
        TabStopType, TabStopPosition } = require('docx');
const fs = require('fs');

// ===== CONFIGURAÇÃO DE PÁGINA (A4 - PADRÃO CMR) =====
const PAGE_CONFIG = {
  size: { width: 11906, height: 16838 }, // A4 em twips
  margin: {
    top: 1417,      // 0.98" / 2.5cm
    bottom: 1417,   // 0.98" / 2.5cm
    left: 1701,     // 1.18" / 3cm
    right: 1133,    // 0.79" / 2cm
    header: 708,    // 0.49"
    footer: 708,    // 0.49"
    gutter: 0
  }
};

// ===== FONTES E TAMANHOS (PADRÃO CMR) =====
const FONTS = {
  body: "Verdana",           // Corpo de texto normal
  chapter: "Century Gothic", // Títulos de capítulos/seções
  fallback: "Arial"          // Fallback universal
};

const SIZES = {
  normal: 20,      // 10pt (half-points)
  title: 24,       // 12pt para títulos internos
  heading1: 24,    // 12pt
  footnote: 18,    // 9pt
  small: 12        // 6pt
};

// ===== ESPAÇAMENTOS (EM TWIPS) =====
const SPACING = {
  line1_0: 240,    // Espaçamento simples (1.0 linha)
  line1_5: 360,    // Espaçamento 1.5 linhas
  line2_0: 480,    // Espaçamento duplo
  paragraphAfter: 0,
  paragraphBefore: 0
};

// ===== RECUOS (EM TWIPS) =====
const INDENT = {
  firstLine: 2268,  // Recuo de primeira linha padrão (~4cm)
  citation: 2268,   // Recuo esquerdo para citações
  listItem: 720,    // Recuo para itens de lista
  hanging: 360      // Recuo deslocado
};
```

## Definição de Estilos

```javascript
const CMR_STYLES = {
  default: {
    document: {
      run: { font: FONTS.body, size: SIZES.normal }
    }
  },
  paragraphStyles: [
    // === ENDEREÇAMENTO (topo do documento) ===
    {
      id: "Enderecamento",
      name: "Endereçamento",
      basedOn: "Normal",
      run: { font: FONTS.body, size: SIZES.normal },
      paragraph: {
        alignment: AlignmentType.BOTH,
        spacing: { line: SPACING.line1_5, after: 0 }
      }
    },

    // === TÍTULO DO DOCUMENTO (ex: "CONTESTAÇÃO") ===
    {
      id: "TituloPeca",
      name: "Título da Peça",
      basedOn: "Normal",
      run: { font: FONTS.body, size: SIZES.title, bold: true },
      paragraph: {
        alignment: AlignmentType.CENTER,
        spacing: { line: SPACING.line1_5, before: 240, after: 240 }
      }
    },

    // === CAPÍTULOS (ex: "I. TEMPESTIVIDADE") ===
    {
      id: "Capitulo",
      name: "Capítulo",
      basedOn: "Normal",
      run: { font: FONTS.chapter, size: SIZES.heading1, bold: true },
      paragraph: {
        alignment: AlignmentType.BOTH,
        spacing: { line: SPACING.line1_5, before: 360, after: 120 }
      }
    },

    // === SUBCAPÍTULOS (ex: "A. DA ILEGITIMIDADE PASSIVA") ===
    {
      id: "Subcapitulo",
      name: "Subcapítulo",
      basedOn: "Normal",
      run: { font: FONTS.chapter, size: SIZES.normal, bold: true },
      paragraph: {
        alignment: AlignmentType.BOTH,
        spacing: { line: SPACING.line1_5, before: 240, after: 120 }
      }
    },

    // === PARÁGRAFOS NUMERADOS (corpo principal) ===
    {
      id: "ParagrafoNumerado",
      name: "Parágrafo Numerado",
      basedOn: "Normal",
      run: { font: FONTS.body, size: SIZES.normal },
      paragraph: {
        alignment: AlignmentType.BOTH,
        spacing: { line: SPACING.line1_5, after: 0 },
        indent: { firstLine: INDENT.firstLine }
      }
    },

    // === CITAÇÃO DE JURISPRUDÊNCIA ===
    // CRÍTICO: Usa itálico, recuo à esquerda, espaçamento simples
    {
      id: "Citacao",
      name: "Citação",
      basedOn: "Normal",
      run: { font: FONTS.body, size: SIZES.normal, italics: true },
      paragraph: {
        alignment: AlignmentType.LEFT,
        spacing: { line: SPACING.line1_0, before: 120, after: 120 },
        indent: { left: INDENT.citation }
      }
    },

    // === REFERÊNCIA DA CITAÇÃO (ex: "(STJ, REsp 1.234.567/SP...)") ===
    {
      id: "ReferenciaCitacao",
      name: "Referência da Citação",
      basedOn: "Citacao",
      run: { font: FONTS.body, size: SIZES.normal, italics: true },
      paragraph: {
        alignment: AlignmentType.LEFT,
        spacing: { line: SPACING.line1_0, after: 240 },
        indent: { left: INDENT.citation }
      }
    },

    // === ITENS DE LISTA (alíneas a, b, c...) ===
    {
      id: "ItemLista",
      name: "Item de Lista",
      basedOn: "Normal",
      run: { font: FONTS.body, size: SIZES.normal },
      paragraph: {
        alignment: AlignmentType.BOTH,
        spacing: { line: SPACING.line1_5, after: 60 },
        indent: { left: INDENT.citation, hanging: INDENT.hanging }
      }
    },

    // === ASSINATURA ===
    {
      id: "Assinatura",
      name: "Assinatura",
      basedOn: "Normal",
      run: { font: FONTS.body, size: SIZES.normal, bold: true },
      paragraph: {
        alignment: AlignmentType.LEFT,
        spacing: { line: SPACING.line1_0, before: 480, after: 0 }
      }
    }
  ]
};
```

## Configuração de Numeração

```javascript
const NUMBERING_CONFIG = {
  config: [
    // Lista de parágrafos numerados (1. 2. 3...)
    {
      reference: "paragrafos-numerados",
      levels: [{
        level: 0,
        format: LevelFormat.DECIMAL,
        text: "%1.",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 0, hanging: 0 } } }
      }]
    },
    // Lista de alíneas (a) b) c)...)
    {
      reference: "alineas",
      levels: [{
        level: 0,
        format: LevelFormat.LOWER_LETTER,
        text: "%1)",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: INDENT.citation, hanging: INDENT.hanging } } }
      }]
    },
    // Lista romana (i. ii. iii...)
    {
      reference: "romanos",
      levels: [{
        level: 0,
        format: LevelFormat.LOWER_ROMAN,
        text: "(%1)",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: INDENT.citation + 360, hanging: INDENT.hanging } } }
      }]
    }
  ]
};
```

## Cabeçalho e Rodapé

```javascript
// === CABEÇALHO PADRÃO CMR ===
function createHeader() {
  return new Header({
    children: [
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        spacing: { after: 0 },
        children: [
          new TextRun({ text: "C. M. RODRIGUES", font: FONTS.body, size: SIZES.normal })
        ]
      }),
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [
          new TextRun({ text: "Advogados", font: FONTS.body, size: SIZES.normal })
        ]
      })
    ]
  });
}

// === RODAPÉ PADRÃO CMR ===
function createFooter() {
  return new Footer({
    children: [
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        spacing: { after: 0 },
        children: [
          new TextRun({ text: "Alameda Santos nº. 211, 16º andar, cj. 1607", font: FONTS.body, size: SIZES.small })
        ]
      }),
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        spacing: { after: 0 },
        children: [
          new TextRun({ text: "São Paulo – SP 01419-000", font: FONTS.body, size: SIZES.small })
        ]
      }),
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [
          new TextRun({ text: "Tel.: (11) 3044 4160", font: FONTS.body, size: SIZES.small })
        ]
      })
    ]
  });
}
```

## Estrutura do Documento Completo

```javascript
const doc = new Document({
  styles: CMR_STYLES,
  numbering: NUMBERING_CONFIG,
  sections: [{
    properties: {
      page: PAGE_CONFIG
    },
    headers: {
      default: createHeader()
    },
    footers: {
      default: createFooter()
    },
    children: [
      // ... conteúdo do documento
    ]
  }]
});

// Salvar
Packer.toBuffer(doc).then(buffer => fs.writeFileSync("documento.docx", buffer));
```

## Padrões de Formatação Específicos

### 1. Endereçamento (Início do Documento)

```javascript
// EXCELENTÍSSIMO SENHOR DOUTOR JUIZ...
new Paragraph({
  style: "Enderecamento",
  children: [
    new TextRun({ text: "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA ", bold: false }),
    new TextRun({ text: "11ª VARA CÍVEL DO FORO REGIONAL DE SANTO AMARO", bold: false }),
    new TextRun({ text: " DA COMARCA DE SÃO PAULO – SP", bold: false })
  ]
})
```

### 2. Qualificação das Partes

```javascript
// Empresa ré com qualificação
new Paragraph({
  alignment: AlignmentType.BOTH,
  spacing: { line: SPACING.line1_5 },
  indent: { firstLine: INDENT.firstLine },
  children: [
    new TextRun({ text: "SALESFORCE TECNOLOGIA LTDA.", bold: true }),
    new TextRun({ text: ", pessoa jurídica de direito privado, inscrita no CNPJ nº 01.080.512/0001-78..." })
  ]
})
```

### 3. Título da Peça (ex: CONTESTAÇÃO)

```javascript
new Paragraph({
  style: "TituloPeca",
  children: [new TextRun({ text: "CONTESTAÇÃO", bold: true })]
})
```

### 4. Capítulos com Numeração Romana

```javascript
// I. TEMPESTIVIDADE, II. SÍNTESE DOS FATOS, etc.
new Paragraph({
  style: "Capitulo",
  children: [new TextRun({ text: "I. TEMPESTIVIDADE" })]
})
```

### 5. Subcapítulos com Letras

```javascript
// A. DA ILEGITIMIDADE PASSIVA
new Paragraph({
  style: "Subcapitulo",
  children: [new TextRun({ text: "A. DA ILEGITIMIDADE PASSIVA DA SALESFORCE" })]
})
```

### 6. Parágrafos Numerados (PADRÃO PRINCIPAL)

```javascript
// CRÍTICO: Cada parágrafo começa com número + ponto
// O número é PARTE DO TEXTO, não da numeração automática
new Paragraph({
  style: "ParagrafoNumerado",
  children: [
    new TextRun({ text: "14. " }),
    new TextRun({ text: "A legitimidade passiva " }),
    new TextRun({ text: "ad causam", italics: true }),
    new TextRun({ text: " exige que a conduta do réu seja apta..." })
  ]
})
```

### 7. Citações de Jurisprudência (FORMATO CRÍTICO)

```javascript
// IMPORTANTE: Citações são em itálico, recuadas, espaçamento simples
// Começam com aspas e terminam com aspas
new Paragraph({
  style: "Citacao",
  children: [
    new TextRun({
      text: "\"De acordo com a teoria da asserção, acolhida pela jurisprudência do Superior Tribunal de Justiça para a verificação das condições da ação, o reconhecimento da legitimidade passiva ad causam exige que os argumentos deduzidos na inicial possibilitem a inferência, ainda que abstratamente, de que o réu possa ser o sujeito responsável pela violação do direito subjetivo invocado pelo autor.\"",
      italics: true
    })
  ]
}),

// Referência da citação (tribunal, processo, relator, data)
new Paragraph({
  style: "ReferenciaCitacao",
  children: [
    new TextRun({
      text: "(STJ, REsp 1.964.337/RJ, Rel. Min. Marco Aurélio Bellizze, j. 08/03/2022)",
      italics: true
    })
  ]
})
```

### 8. Tabelas Comparativas

```javascript
const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: "000000" };
const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };

new Table({
  columnWidths: [1800, 3200, 3200], // Distribuição das colunas
  rows: [
    // Cabeçalho da tabela
    new TableRow({
      tableHeader: true,
      children: [
        new TableCell({
          borders: cellBorders,
          shading: { fill: "D9D9D9", type: ShadingType.CLEAR },
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: "Elemento", bold: true, font: FONTS.body, size: SIZES.normal })]
          })]
        }),
        // ... mais células
      ]
    }),
    // Linhas de dados
    new TableRow({
      children: [
        new TableCell({
          borders: cellBorders,
          children: [new Paragraph({
            children: [new TextRun({ text: "Partes", font: FONTS.body, size: SIZES.normal })]
          })]
        }),
        // ... mais células
      ]
    })
  ]
})
```

### 9. Pedidos com Alíneas

```javascript
// Pedido principal em negrito
new Paragraph({
  style: "ParagrafoNumerado",
  children: [
    new TextRun({ text: "73. ", bold: false }),
    new TextRun({ text: "Diante de todo o exposto, ..." })
  ]
}),

// Alíneas dos pedidos
new Paragraph({
  style: "ItemLista",
  children: [
    new TextRun({ text: "a) ", bold: true }),
    new TextRun({ text: "O acolhimento da preliminar de " }),
    new TextRun({ text: "ilegitimidade passiva", bold: true }),
    new TextRun({ text: ", com a consequente " }),
    new TextRun({ text: "extinção do processo sem resolução do mérito", bold: true }),
    new TextRun({ text: " em relação à Salesforce;" })
  ]
})
```

### 10. Assinatura Final

```javascript
new Paragraph({
  style: "Assinatura",
  children: [new TextRun({ text: "Carlos Magno N. Rodrigues", bold: true })]
}),
new Paragraph({
  alignment: AlignmentType.LEFT,
  children: [new TextRun({ text: "OAB/SP nº 129.021" })]
}),
// Linha em branco
new Paragraph({ children: [] }),
new Paragraph({
  style: "Assinatura",
  children: [new TextRun({ text: "Ana Beatriz Vianna Paoli", bold: true })]
}),
new Paragraph({
  alignment: AlignmentType.LEFT,
  children: [new TextRun({ text: "OAB/SP nº 493.706" })]
})
```

## Regras Críticas de Formatação

| Elemento | Fonte | Tamanho | Espaçamento | Alinhamento | Recuo |
|----------|-------|---------|-------------|-------------|-------|
| Corpo normal | Verdana | 10pt | 1.5 linhas | Justificado | 1ª linha: 2268 twips |
| Capítulos | Century Gothic | 12pt | 1.5 linhas | Justificado | Nenhum |
| Citações | Verdana | 10pt | 1.0 linha | Esquerda | Esquerda: 2268 twips |
| Tabelas | Verdana | 10pt | 1.0 linha | Conforme | Nenhum |
| Rodapé | Verdana | 6pt | 1.0 linha | Direita | Nenhum |

## Erros Comuns a Evitar

1. **NUNCA** use `\n` para quebras de linha - sempre crie novo `Paragraph`
2. **NUNCA** omita o parâmetro `type` em `ShadingType` - sempre use `ShadingType.CLEAR`
3. **SEMPRE** defina `columnWidths` em tabelas E `width` em cada célula
4. **NUNCA** use bullets Unicode (`•`) - sempre use `LevelFormat.BULLET`
5. **SEMPRE** coloque `PageBreak` dentro de `Paragraph`
6. **NUNCA** misture estilos `heading` com estilos customizados no mesmo parágrafo
7. **SEMPRE** use valores em half-points para `size` (10pt = 20 half-points)
8. **SEMPRE** use valores em twips para margens e recuos (1 inch = 1440 twips)

## Conversão de Unidades

```javascript
// Conversões úteis
const cmToTwips = (cm) => Math.round(cm * 567);  // 1cm ≈ 567 twips
const inchToTwips = (inch) => inch * 1440;       // 1inch = 1440 twips
const ptToHalfPoints = (pt) => pt * 2;           // 10pt = 20 half-points

// Valores comuns
// 2268 twips ≈ 4cm (recuo padrão)
// 1701 twips ≈ 3cm (margem esquerda)
// 1417 twips ≈ 2.5cm (margens superior/inferior)
// 1133 twips ≈ 2cm (margem direita)
```
