/**
 * Conversor de Markdown para DOCX - Padrão CMR Advogados
 *
 * Converte arquivos markdown de peças jurídicas para o formato
 * Word seguindo o template de formatação do escritório CMR.
 */

const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, LevelFormat, BorderStyle,
        WidthType, ShadingType, TabStopType } = require('docx');
const fs = require('fs');
const path = require('path');

// ===== CONFIGURAÇÃO DE PÁGINA (A4 - PADRÃO CMR) =====
const PAGE_CONFIG = {
  size: { width: 11906, height: 16838 }, // A4 em twips
  margin: {
    top: 1417,      // 0.98" / 2.5cm
    bottom: 1417,   // 0.98" / 2.5cm
    left: 1701,     // 1.18" / 3cm
    right: 1133,    // 0.79" / 2cm
    header: 708,
    footer: 708,
    gutter: 0
  }
};

// ===== FONTES =====
// CRÍTICO: Century Gothic é a fonte do CORPO, Verdana só no header
const FONTS = {
  header: "Verdana",       // APENAS para cabeçalho
  body: "Century Gothic"   // Corpo, capítulos, citações, TUDO
};

// ===== TAMANHOS (em half-points) =====
const SIZES = {
  normal: 24,      // 12pt - PADRÃO DO CORPO
  header: 52,      // 26pt - Cabeçalho "C. M. RODRIGUES"
  citation: 20,    // 10pt - Citações de jurisprudência
  small: 12        // 6pt - Rodapé
};

// ===== ESPAÇAMENTOS (em twips) =====
const SPACING = {
  line1_0: 240,    // 1.0 linha
  line1_5: 360     // 1.5 linhas
};

// ===== RECUOS (em twips) =====
const INDENT = {
  firstLine: 2268,  // ~4cm
  citation: 2268,
  hanging: 360
};

// ===== ESTILOS =====
const CMR_STYLES = {
  default: {
    document: {
      run: { font: FONTS.body, size: SIZES.normal }
    }
  },
  paragraphStyles: [
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
    {
      id: "TituloPeca",
      name: "Título da Peça",
      basedOn: "Normal",
      run: { font: FONTS.body, size: SIZES.normal, bold: true },  // Century Gothic 12pt bold
      paragraph: {
        alignment: AlignmentType.CENTER,
        spacing: { line: SPACING.line1_5, before: 240, after: 240 }
      }
    },
    {
      id: "Capitulo",
      name: "Capítulo",
      basedOn: "Normal",
      run: { font: FONTS.body, size: SIZES.normal, bold: true },  // Century Gothic 12pt bold
      paragraph: {
        alignment: AlignmentType.BOTH,
        spacing: { line: SPACING.line1_5, before: 360, after: 120 }
      }
    },
    {
      id: "Subcapitulo",
      name: "Subcapítulo",
      basedOn: "Normal",
      run: { font: FONTS.body, size: SIZES.normal, bold: true },  // Century Gothic 12pt bold
      paragraph: {
        alignment: AlignmentType.BOTH,
        spacing: { line: SPACING.line1_5, before: 240, after: 120 }
      }
    },
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
    {
      id: "Citacao",
      name: "Citação",
      basedOn: "Normal",
      run: { font: FONTS.body, size: SIZES.citation, italics: true },  // Century Gothic 10pt italic
      paragraph: {
        alignment: AlignmentType.LEFT,
        spacing: { line: SPACING.line1_0, before: 120, after: 120 },
        indent: { left: INDENT.citation }
      }
    },
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

// ===== CABEÇALHO =====
// CRÍTICO: Cabeçalho usa VERDANA (não Century Gothic!)
function createHeader() {
  return new Header({
    children: [
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        spacing: { after: 0 },
        children: [
          new TextRun({ text: "C. M. RODRIGUES", font: FONTS.header, size: SIZES.header })  // Verdana 26pt
        ]
      }),
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [
          new TextRun({ text: "Advogados", font: FONTS.header, size: SIZES.normal })  // Verdana 12pt
        ]
      })
    ]
  });
}

// ===== RODAPÉ =====
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

// ===== PARSER DE MARKDOWN =====

/**
 * Processa formatação inline (negrito, itálico, etc.)
 */
function parseInlineFormatting(text) {
  const runs = [];
  let remaining = text;

  // Regex para diferentes formatações
  const patterns = [
    { regex: /\*\*\*(.+?)\*\*\*/g, bold: true, italics: true },   // ***bold italic***
    { regex: /\*\*(.+?)\*\*/g, bold: true, italics: false },      // **bold**
    { regex: /\*(.+?)\*/g, bold: false, italics: true },          // *italic*
    { regex: /_(.+?)_/g, bold: false, italics: true },            // _italic_
  ];

  // Simplificado: processa texto sequencialmente
  let lastIndex = 0;
  const allMatches = [];

  // Encontra todas as ocorrências de formatação
  for (const pattern of patterns) {
    let match;
    const regex = new RegExp(pattern.regex.source, 'g');
    while ((match = regex.exec(text)) !== null) {
      allMatches.push({
        start: match.index,
        end: match.index + match[0].length,
        text: match[1],
        bold: pattern.bold,
        italics: pattern.italics
      });
    }
  }

  // Ordena por posição
  allMatches.sort((a, b) => a.start - b.start);

  // Remove sobreposições
  const filteredMatches = [];
  let lastEnd = 0;
  for (const match of allMatches) {
    if (match.start >= lastEnd) {
      filteredMatches.push(match);
      lastEnd = match.end;
    }
  }

  // Gera TextRuns
  lastIndex = 0;
  for (const match of filteredMatches) {
    // Texto antes da formatação
    if (match.start > lastIndex) {
      const plainText = text.substring(lastIndex, match.start);
      if (plainText) {
        runs.push(new TextRun({ text: plainText, font: FONTS.body, size: SIZES.normal }));
      }
    }

    // Texto formatado
    runs.push(new TextRun({
      text: match.text,
      bold: match.bold,
      italics: match.italics,
      font: FONTS.body,
      size: SIZES.normal
    }));

    lastIndex = match.end;
  }

  // Texto restante
  if (lastIndex < text.length) {
    const plainText = text.substring(lastIndex);
    if (plainText) {
      runs.push(new TextRun({ text: plainText, font: FONTS.body, size: SIZES.normal }));
    }
  }

  // Se não encontrou nenhuma formatação
  if (runs.length === 0) {
    runs.push(new TextRun({ text: text, font: FONTS.body, size: SIZES.normal }));
  }

  return runs;
}

/**
 * Converte uma tabela markdown para Table do docx
 */
function parseTable(lines) {
  const rows = [];
  const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: "000000" };
  const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    // Pula linha de separação (|---|---|)
    if (line.match(/^\|[\s\-:]+\|$/)) continue;

    // Parse das células
    const cells = line.split('|').filter(c => c.trim() !== '');

    const isHeader = i === 0;

    const tableRow = new TableRow({
      tableHeader: isHeader,
      children: cells.map(cellText => {
        const runs = parseInlineFormatting(cellText.trim());
        if (isHeader) {
          // Força negrito no cabeçalho
          runs.forEach(r => r.bold = true);
        }

        return new TableCell({
          borders: cellBorders,
          shading: isHeader ? { fill: "D9D9D9", type: ShadingType.CLEAR } : undefined,
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: runs
          })]
        });
      })
    });

    rows.push(tableRow);
  }

  // Calcula largura das colunas
  const numCols = rows[0]?.children?.length || 2;
  const totalWidth = 8200; // Largura útil aproximada
  const colWidth = Math.floor(totalWidth / numCols);
  const columnWidths = new Array(numCols).fill(colWidth);

  return new Table({
    columnWidths: columnWidths,
    rows: rows
  });
}

/**
 * Converte markdown para array de elementos docx
 */
function markdownToDocx(markdown) {
  const lines = markdown.split('\n');
  const elements = [];
  let i = 0;
  let inBlockquote = false;
  let blockquoteLines = [];

  while (i < lines.length) {
    const line = lines[i];
    const trimmedLine = line.trim();

    // === LINHA VAZIA ===
    if (trimmedLine === '') {
      // Finaliza blockquote se estava em um
      if (inBlockquote && blockquoteLines.length > 0) {
        const quoteText = blockquoteLines.join(' ').replace(/^>\s*/gm, '').trim();
        elements.push(new Paragraph({
          style: "Citacao",
          children: [new TextRun({ text: quoteText, italics: true, font: FONTS.body, size: SIZES.citation })]
        }));
        blockquoteLines = [];
        inBlockquote = false;
      }
      i++;
      continue;
    }

    // === LINHA HORIZONTAL (---) ===
    if (trimmedLine.match(/^-{3,}$/)) {
      i++;
      continue;
    }

    // === TABELA ===
    if (trimmedLine.startsWith('|') && trimmedLine.endsWith('|')) {
      const tableLines = [];
      while (i < lines.length && lines[i].trim().startsWith('|')) {
        tableLines.push(lines[i]);
        i++;
      }
      elements.push(parseTable(tableLines));
      continue;
    }

    // === BLOCKQUOTE (Citação) ===
    if (trimmedLine.startsWith('>')) {
      inBlockquote = true;
      blockquoteLines.push(trimmedLine.replace(/^>\s*/, ''));
      i++;
      continue;
    }

    // Finaliza blockquote pendente
    if (inBlockquote && blockquoteLines.length > 0) {
      const quoteText = blockquoteLines.join(' ').trim();
      elements.push(new Paragraph({
        style: "Citacao",
        children: [new TextRun({ text: quoteText, italics: true, font: FONTS.body, size: SIZES.normal })]
      }));
      blockquoteLines = [];
      inBlockquote = false;
    }

    // === HEADING 1 (# Endereçamento) ===
    if (trimmedLine.startsWith('# ')) {
      const text = trimmedLine.substring(2).trim();
      elements.push(new Paragraph({
        style: "Enderecamento",
        children: [new TextRun({ text: text, font: FONTS.body, size: SIZES.normal })]
      }));
      i++;
      continue;
    }

    // === HEADING 2 (## Título do capítulo) ===
    if (trimmedLine.startsWith('## ')) {
      const text = trimmedLine.substring(3).trim();

      // Se é título da peça (CONTESTAÇÃO, APELAÇÃO, etc.)
      if (text === 'CONTESTAÇÃO' || text === 'APELAÇÃO' || text === 'RECURSO' ||
          text === 'PETIÇÃO INICIAL' || text.match(/^[A-ZÇÃÕÁÉÍÓÚÂÊÔ\s]+$/)) {
        elements.push(new Paragraph({
          style: "TituloPeca",
          children: [new TextRun({ text: text, bold: true, font: FONTS.body, size: SIZES.normal })]
        }));
      } else {
        // Capítulo normal (I. TEMPESTIVIDADE, II. SÍNTESE...)
        elements.push(new Paragraph({
          style: "Capitulo",
          children: [new TextRun({ text: text, bold: true, font: FONTS.body, size: SIZES.normal })]
        }));
      }
      i++;
      continue;
    }

    // === HEADING 3 (### Subcapítulo) ===
    if (trimmedLine.startsWith('### ')) {
      const text = trimmedLine.substring(4).trim();
      elements.push(new Paragraph({
        style: "Subcapitulo",
        children: [new TextRun({ text: text, bold: true, font: FONTS.body, size: SIZES.normal })]
      }));
      i++;
      continue;
    }

    // === LISTA COM LETRAS (a), b), c)...) ou números ===
    const listMatch = trimmedLine.match(/^(\*\*)?([a-z]\)|[0-9]+\.|[-•])(\*\*)?\s+(.+)$/);
    if (listMatch) {
      const marker = listMatch[2];
      const content = listMatch[4];
      const runs = parseInlineFormatting(content);

      // Adiciona o marcador
      runs.unshift(new TextRun({
        text: marker + " ",
        bold: marker.match(/^[a-z]\)$/) ? true : false,
        font: FONTS.body,
        size: SIZES.normal
      }));

      elements.push(new Paragraph({
        style: "ItemLista",
        children: runs
      }));
      i++;
      continue;
    }

    // === LISTA COM HÍFEN E ROMANO ===
    const romanListMatch = trimmedLine.match(/^\s*-\s+\(([ivx]+)\)\s+(.+)$/i);
    if (romanListMatch) {
      const roman = romanListMatch[1];
      const content = romanListMatch[2];
      const runs = parseInlineFormatting(content);

      runs.unshift(new TextRun({
        text: "(" + roman + ") ",
        font: FONTS.body,
        size: SIZES.normal
      }));

      elements.push(new Paragraph({
        alignment: AlignmentType.BOTH,
        spacing: { line: SPACING.line1_5 },
        indent: { left: INDENT.citation + 360, hanging: INDENT.hanging },
        children: runs
      }));
      i++;
      continue;
    }

    // === PARÁGRAFO NUMERADO (começa com número.) ===
    const numberedMatch = trimmedLine.match(/^(\d+)\.\s+(.+)$/);
    if (numberedMatch) {
      const num = numberedMatch[1];
      const content = numberedMatch[2];
      const runs = parseInlineFormatting(content);

      runs.unshift(new TextRun({
        text: num + ". ",
        font: FONTS.body,
        size: SIZES.normal
      }));

      elements.push(new Paragraph({
        style: "ParagrafoNumerado",
        children: runs
      }));
      i++;
      continue;
    }

    // === ASSINATURA ===
    if (trimmedLine.startsWith('**') && trimmedLine.endsWith('**') &&
        (trimmedLine.includes('OAB') || lines[i+1]?.includes('OAB'))) {
      const name = trimmedLine.replace(/\*\*/g, '').trim();
      elements.push(new Paragraph({
        style: "Assinatura",
        children: [new TextRun({ text: name, bold: true, font: FONTS.body, size: SIZES.normal })]
      }));
      i++;
      continue;
    }

    // === OAB ===
    if (trimmedLine.startsWith('OAB/')) {
      elements.push(new Paragraph({
        alignment: AlignmentType.LEFT,
        spacing: { line: SPACING.line1_0, after: 240 },
        children: [new TextRun({ text: trimmedLine, font: FONTS.body, size: SIZES.normal })]
      }));
      i++;
      continue;
    }

    // === PARÁGRAFO NORMAL ===
    const runs = parseInlineFormatting(trimmedLine);

    // Verifica se parece continuação de qualificação ou texto especial
    const isQualification = trimmedLine.includes('CNPJ') || trimmedLine.includes('pessoa jurídica') ||
                           trimmedLine.includes('devidamente qualificad');

    elements.push(new Paragraph({
      alignment: AlignmentType.BOTH,
      spacing: { line: SPACING.line1_5, after: 0 },
      indent: isQualification ? { firstLine: INDENT.firstLine } : undefined,
      children: runs
    }));

    i++;
  }

  // Finaliza blockquote pendente no final
  if (inBlockquote && blockquoteLines.length > 0) {
    const quoteText = blockquoteLines.join(' ').trim();
    elements.push(new Paragraph({
      style: "Citacao",
      children: [new TextRun({ text: quoteText, italics: true, font: FONTS.body, size: SIZES.normal })]
    }));
  }

  return elements;
}

/**
 * Função principal de conversão
 */
async function convertMdToDocx(inputPath, outputPath) {
  console.log(`Lendo arquivo: ${inputPath}`);
  const markdown = fs.readFileSync(inputPath, 'utf-8');

  console.log('Convertendo markdown para elementos docx...');
  const content = markdownToDocx(markdown);

  console.log(`Total de elementos: ${content.length}`);

  const doc = new Document({
    styles: CMR_STYLES,
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
      children: content
    }]
  });

  console.log('Gerando arquivo docx...');
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);

  console.log(`Arquivo salvo: ${outputPath}`);
  return outputPath;
}

// ===== EXECUÇÃO =====
const inputFile = process.argv[2] || 'CONTESTACAO_REDEBRASIL_x_SALESFORCE.md';
const outputFile = process.argv[3] || inputFile.replace('.md', '.docx');

const inputPath = path.resolve(__dirname, inputFile);
const outputPath = path.resolve(__dirname, outputFile);

convertMdToDocx(inputPath, outputPath)
  .then(() => console.log('Conversão concluída com sucesso!'))
  .catch(err => console.error('Erro na conversão:', err));
