#!/usr/bin/env python3
"""
CMR Style Extractor - "O Inspetor"
Extrai o DNA de formatação de arquivos .docx para JSON.

Uso:
    python style_extractor.py <template.docx> [saida.json]
    python style_extractor.py --consensus <pasta> [saida.json]
"""

import zipfile
from lxml import etree
import json
import os
import sys
from collections import Counter
from typing import Dict, Any, Optional

# Namespace XML do Word
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


def get_xml_tree(docx_path: str, xml_file: str) -> Optional[etree._Element]:
    """Abre o DOCX como ZIP e lê um arquivo XML específico."""
    try:
        with zipfile.ZipFile(docx_path) as z:
            return etree.fromstring(z.read(xml_file))
    except Exception:
        return None


def get_attr(element: Optional[etree._Element], attr: str) -> Optional[str]:
    """Obtém atributo com namespace de forma segura."""
    if element is None:
        return None
    return element.get(f"{{{NS['w']}}}{attr}")


def extract_page_setup(docx_path: str) -> Dict[str, Any]:
    """Extrai configurações de página (margens, tamanho)."""
    page_setup = {}

    root_doc = get_xml_tree(docx_path, 'word/document.xml')
    if root_doc is None:
        return page_setup

    sectPr = root_doc.find('.//w:sectPr', NS)
    if sectPr is None:
        return page_setup

    # Tamanho da página
    pgSz = sectPr.find('w:pgSz', NS)
    if pgSz is not None:
        page_setup["size"] = {
            "width_twips": int(get_attr(pgSz, 'w') or 11906),
            "height_twips": int(get_attr(pgSz, 'h') or 16838),
            "format": "A4"
        }

    # Margens
    pgMar = sectPr.find('w:pgMar', NS)
    if pgMar is not None:
        page_setup["margins_twips"] = {
            "top": int(get_attr(pgMar, 'top') or 1417),
            "bottom": int(get_attr(pgMar, 'bottom') or 1417),
            "left": int(get_attr(pgMar, 'left') or 1701),
            "right": int(get_attr(pgMar, 'right') or 1133),
            "header": int(get_attr(pgMar, 'header') or 708),
            "footer": int(get_attr(pgMar, 'footer') or 708)
        }

    return page_setup


def extract_run_properties(rPr: Optional[etree._Element]) -> Dict[str, Any]:
    """Extrai propriedades de formatação de texto (run)."""
    props = {}
    if rPr is None:
        return props

    # Fonte
    fonts = rPr.find('w:rFonts', NS)
    if fonts is not None:
        font_name = get_attr(fonts, 'ascii') or get_attr(fonts, 'hAnsi')
        if font_name:
            props["font_name"] = font_name

    # Tamanho (sz é em half-points, dividir por 2 para pt)
    sz = rPr.find('w:sz', NS)
    if sz is not None:
        val = get_attr(sz, 'val')
        if val:
            props["font_size_pt"] = int(val) / 2

    # Negrito
    if rPr.find('w:b', NS) is not None:
        props["bold"] = True

    # Itálico
    if rPr.find('w:i', NS) is not None:
        props["italics"] = True

    # Cor
    color = rPr.find('w:color', NS)
    if color is not None:
        val = get_attr(color, 'val')
        if val and val != 'auto':
            props["color"] = val

    return props


def extract_paragraph_properties(pPr: Optional[etree._Element]) -> Dict[str, Any]:
    """Extrai propriedades de parágrafo."""
    props = {}
    if pPr is None:
        return props

    # Alinhamento
    jc = pPr.find('w:jc', NS)
    if jc is not None:
        val = get_attr(jc, 'val')
        if val:
            props["alignment"] = val.upper()

    # Recuos
    ind = pPr.find('w:ind', NS)
    if ind is not None:
        first_line = get_attr(ind, 'firstLine')
        left = get_attr(ind, 'left')
        hanging = get_attr(ind, 'hanging')

        if first_line:
            props["indent_first_line_twips"] = int(first_line)
        if left:
            props["indent_left_twips"] = int(left)
        if hanging:
            props["indent_hanging_twips"] = int(hanging)

    # Espaçamento
    spacing = pPr.find('w:spacing', NS)
    if spacing is not None:
        before = get_attr(spacing, 'before')
        after = get_attr(spacing, 'after')
        line = get_attr(spacing, 'line')
        lineRule = get_attr(spacing, 'lineRule')

        if before:
            props["spacing_before_twips"] = int(before)
        if after:
            props["spacing_after_twips"] = int(after)

        # Espaçamento entre linhas
        if lineRule == 'auto' and line:
            line_val = int(line)
            if line_val == 240:
                props["line_spacing_rule"] = "SINGLE"
            elif line_val == 360:
                props["line_spacing_rule"] = "1.5"
            elif line_val == 480:
                props["line_spacing_rule"] = "DOUBLE"

    return props


def extract_styles(docx_path: str) -> Dict[str, Dict[str, Any]]:
    """Extrai todos os estilos definidos no documento."""
    styles_map = {}

    root_styles = get_xml_tree(docx_path, 'word/styles.xml')
    if root_styles is None:
        return styles_map

    # Estilos a ignorar (internos do Word)
    ignore_styles = {'NormalTable', 'NoList', 'DefaultParagraphFont',
                     'TableNormal', 'NoSpacing', 'ListParagraph'}

    for style in root_styles.findall('.//w:style', NS):
        style_id = get_attr(style, 'styleId')
        if not style_id or style_id in ignore_styles:
            continue

        style_def = {}

        # Nome legível do estilo
        name_node = style.find('w:name', NS)
        if name_node is not None:
            style_name = get_attr(name_node, 'val')
            if style_name and style_name != style_id:
                style_def["display_name"] = style_name

        # Estilo base (herança)
        based_on = style.find('w:basedOn', NS)
        if based_on is not None:
            parent = get_attr(based_on, 'val')
            if parent:
                style_def["based_on"] = parent

        # Propriedades de run (fonte, tamanho, etc.)
        rPr = style.find('w:rPr', NS)
        style_def.update(extract_run_properties(rPr))

        # Propriedades de parágrafo
        pPr = style.find('w:pPr', NS)
        style_def.update(extract_paragraph_properties(pPr))

        # Só salva se tiver propriedades relevantes
        if style_def:
            styles_map[style_id] = style_def

    return styles_map


def extract_header_footer(docx_path: str) -> Dict[str, Any]:
    """Extrai informações de header e footer."""
    hf_info = {}

    # Tentar ler header
    header = get_xml_tree(docx_path, 'word/header1.xml')
    if header is not None:
        paragraphs = []
        for p in header.findall('.//w:p', NS):
            texts = [t.text for t in p.findall('.//w:t', NS) if t.text]
            if texts:
                paragraphs.append(''.join(texts))
        if paragraphs:
            hf_info["header_content"] = paragraphs

    # Tentar ler footer
    footer = get_xml_tree(docx_path, 'word/footer1.xml')
    if footer is not None:
        paragraphs = []
        for p in footer.findall('.//w:p', NS):
            texts = [t.text for t in p.findall('.//w:t', NS) if t.text]
            if texts:
                paragraphs.append(''.join(texts))
        if paragraphs:
            hf_info["footer_content"] = paragraphs

    return hf_info


def extract_styles_to_json(docx_path: str, output_json: str) -> None:
    """
    Função principal: Extrai DNA completo de um template DOCX.
    """
    if not os.path.exists(docx_path):
        print(f"Erro: O arquivo '{docx_path}' não foi encontrado.")
        return

    print(f"🔍 Analisando template: {docx_path}...")

    dna = {
        "metadata": {
            "source_template": os.path.basename(docx_path),
            "generated_by": "CMR Style Extractor v2.0"
        },
        "page_setup": extract_page_setup(docx_path),
        "styles_map": extract_styles(docx_path)
    }

    # Adicionar info de header/footer se encontrado
    hf_info = extract_header_footer(docx_path)
    if hf_info:
        dna["header_footer"] = hf_info

    # Salvar JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(dna, f, indent=2, ensure_ascii=False)

    print(f"✅ DNA extraído: {output_json}")
    print(f"   - Page setup: {bool(dna['page_setup'])}")
    print(f"   - Estilos encontrados: {len(dna['styles_map'])}")


def build_consensus(folder_path: str, output_json: str) -> None:
    """
    Analisa múltiplos DOCX e gera DNA baseado na moda estatística.
    """
    all_margins = []
    style_votes: Dict[str, Dict[str, list]] = {}

    docx_files = [f for f in os.listdir(folder_path)
                  if f.endswith('.docx') and not f.startswith('~')]

    if not docx_files:
        print("Nenhum arquivo .docx encontrado na pasta.")
        return

    print(f"📊 Analisando {len(docx_files)} documentos para Consenso...")

    for filename in docx_files:
        filepath = os.path.join(folder_path, filename)
        print(f"   -> {filename}")

        # Coletar margens
        page_setup = extract_page_setup(filepath)
        if page_setup.get('margins_twips'):
            all_margins.append(json.dumps(page_setup['margins_twips'], sort_keys=True))

        # Coletar estilos
        styles = extract_styles(filepath)
        for style_id, style_def in styles.items():
            if style_id not in style_votes:
                style_votes[style_id] = {}

            for prop, val in style_def.items():
                if prop not in style_votes[style_id]:
                    style_votes[style_id][prop] = []
                style_votes[style_id][prop].append(val)

    # Construir DNA de consenso
    final_dna = {
        "metadata": {
            "profile_name": "Padrão CMR (Consenso)",
            "source_files_count": len(docx_files),
            "generated_by": "CMR Consensus Extractor v2.0"
        },
        "page_setup": {
            "size": {"width_twips": 11906, "height_twips": 16838, "format": "A4"}
        },
        "styles_map": {}
    }

    # Margens (moda)
    if all_margins:
        most_common = Counter(all_margins).most_common(1)[0][0]
        final_dna["page_setup"]["margins_twips"] = json.loads(most_common)

    # Estilos (moda por propriedade)
    for style_id, props in style_votes.items():
        consensus_style = {}
        for prop_name, values in props.items():
            most_common_val = Counter(map(str, values)).most_common(1)[0][0]
            # Converter de volta para tipo original se possível
            try:
                if most_common_val.replace('.', '').isdigit():
                    consensus_style[prop_name] = float(most_common_val) if '.' in most_common_val else int(most_common_val)
                elif most_common_val.lower() in ('true', 'false'):
                    consensus_style[prop_name] = most_common_val.lower() == 'true'
                else:
                    consensus_style[prop_name] = most_common_val
            except:
                consensus_style[prop_name] = most_common_val

        final_dna["styles_map"][style_id] = consensus_style

    # Salvar
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(final_dna, f, indent=2, ensure_ascii=False)

    print(f"\n✅ DNA de Consenso gerado: {output_json}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python style_extractor.py <template.docx> [saida.json]")
        print("  python style_extractor.py --consensus <pasta> [saida.json]")
        sys.exit(1)

    if sys.argv[1] == '--consensus':
        folder = sys.argv[2] if len(sys.argv) > 2 else '.'
        output = sys.argv[3] if len(sys.argv) > 3 else 'cmr_styles_consensus.json'
        build_consensus(folder, output)
    else:
        docx_file = sys.argv[1]
        output = sys.argv[2] if len(sys.argv) > 2 else docx_file.replace('.docx', '_styles.json')
        extract_styles_to_json(docx_file, output)
