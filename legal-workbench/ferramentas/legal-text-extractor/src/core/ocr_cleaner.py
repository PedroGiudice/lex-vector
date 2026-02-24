"""
Pipeline heurístico de limpeza para markdown extraído por Marker OCR.

Remove artefatos de OCR de autos judiciais escaneados: repetições em loop,
tabelas esparsas, fragmentos isolados, separadores de página, espaços excessivos
e assinaturas digitais.

Uso:
    from src.core.ocr_cleaner import clean_ocr_markdown, CleanerConfig

    clean_ocr_markdown("/tmp/marker_output/pdf-sujo-teste.md", "/tmp/output")

    # Com config customizada:
    config = CleanerConfig(sparse_table_threshold=0.8)
    clean_ocr_markdown("/tmp/input.md", "/tmp/output", config)
"""

import re
from dataclasses import dataclass
from pathlib import Path

from .detector import JudicialSystemDetector
from .patterns import SystemPatterns


@dataclass
class CleanerConfig:
    """Configuração de thresholds para o pipeline de limpeza OCR."""

    # Fase 1: Estrutural
    min_separator_len: int = 10
    max_consecutive_blank_lines: int = 2

    # Fase 2: Repetição
    min_repeats: int = 3
    min_repeat_unit_len: int = 5
    long_line_threshold: int = 100
    repeat_coverage_threshold: float = 0.5

    # Fase 3: Tabelas
    sparse_table_threshold: float = 0.75
    table_min_rows: int = 2
    table_substantive_cell_len: int = 50

    # Fase 4: Fragmentos
    fragment_max_len: int = 5
    substantive_line_min_len: int = 20

    # Fase 5: Assinaturas jurídicas
    system: str = "auto"

    # Fase 6: Espaços excessivos
    space_ratio_threshold: float = 0.7


# Regex pré-compilados
_RE_PAGE_MARKER = re.compile(r"^\{\d+\}-{3,}$")
_RE_SEPARATOR = re.compile(r"^[=\-_*]{%MIN%,}$")
_RE_MARKER_IMAGE = re.compile(r"^!\[.*\]\(_page_\d+.*\)$")
_RE_TABLE_SEPARATOR = re.compile(r"^\|[\s\-:|]+\|$")
_RE_HTML_TAGS = re.compile(r"<[^>]+>")
_RE_LIST_MARKER = re.compile(r"^[a-zA-Z0-9]+[.)]\s*$")
_RE_COMPOUND_ALINCA = re.compile(r"^[a-z]\.\d+\)")
_RE_SCATTERED_CHARS = re.compile(r"^(\S\s){4,}\S?$")

_JURIDICAL_WHITELIST = frozenset({"fl.", "fls.", "v.", "ss.", "art."})


def _find_repeating_unit(
    line: str,
    min_repeats: int,
    min_unit_len: int,
    coverage_threshold: float,
) -> tuple[str, int] | None:
    """
    Encontra substring que se repete min_repeats+ vezes na linha.

    Testa candidatos a partir de múltiplas posições iniciais para detectar
    repetição com prefixo não-repetitivo (ex: "Texto legal Control of the Control of the...").

    Retorna (unidade, count) ou None.
    """
    s = line.strip()
    length = len(s)
    if length < min_unit_len * min_repeats:
        return None

    max_unit_len = length // min_repeats

    # Testar candidatos a partir de múltiplas posições iniciais
    # Posições: 0, 10%, 20%, 30% do comprimento (cobrir prefixos variados)
    start_positions = sorted(set([0, length // 10, length // 5, length * 3 // 10]))

    for start in start_positions:
        if start + min_unit_len > length:
            break
        local_max = min(max_unit_len, length - start)
        for unit_len in range(min_unit_len, local_max + 1):
            candidate = s[start : start + unit_len]
            count = s.count(candidate)
            if count >= min_repeats:
                coverage = (count * unit_len) / length
                if coverage >= coverage_threshold:
                    return (candidate, count)

    return None


def _phase_structural(lines: list[str], config: CleanerConfig) -> tuple[list[str], list[str]]:
    """Fase 1: remove marcadores de página, separadores, imagens Marker, blank lines excessivas."""
    result: list[str] = []
    log: list[str] = []
    sep_re = re.compile(rf"^[=\-_*]{{{config.min_separator_len},}}$")

    removed_markers = 0
    removed_separators = 0
    removed_images = 0
    removed_blanks = 0
    consecutive_blanks = 0

    for line in lines:
        stripped = line.strip()

        if _RE_PAGE_MARKER.match(stripped):
            removed_markers += 1
            consecutive_blanks = 0
            continue

        if stripped and sep_re.match(stripped):
            removed_separators += 1
            consecutive_blanks = 0
            continue

        if _RE_MARKER_IMAGE.match(stripped):
            removed_images += 1
            consecutive_blanks = 0
            continue

        if not stripped:
            consecutive_blanks += 1
            if consecutive_blanks > config.max_consecutive_blank_lines:
                removed_blanks += 1
                continue
        else:
            consecutive_blanks = 0

        result.append(line)

    if removed_markers:
        log.append(f"  {removed_markers} marcadores de página")
    if removed_separators:
        log.append(f"  {removed_separators} separadores")
    if removed_images:
        log.append(f"  {removed_images} referências de imagem Marker")
    if removed_blanks:
        log.append(f"  {removed_blanks} linhas em branco excessivas")

    return result, log


def _phase_repetition(lines: list[str], config: CleanerConfig) -> tuple[list[str], list[str]]:
    """Fase 2: detecta e colapsa repetição adjacente e intra-linha."""
    result: list[str] = []
    log: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Tabelas: aplicar detecção de repetição intra-célula
        if stripped.startswith("|"):
            if len(stripped) > config.long_line_threshold:
                cells = stripped.split("|")
                new_cells: list[str] = []
                changed = False
                for cell in cells:
                    cell_stripped = cell.strip()
                    if len(cell_stripped) > config.long_line_threshold:
                        match = _find_repeating_unit(
                            cell_stripped,
                            config.min_repeats,
                            config.min_repeat_unit_len,
                            config.repeat_coverage_threshold,
                        )
                        if match:
                            unit, count = match
                            new_cells.append(f" {unit.strip()} ")
                            changed = True
                            log.append(
                                f"  L{i + 1}: célula tabela '{unit.strip()[:40]}' "
                                f"repetido {count}x → colapsado"
                            )
                            continue
                    new_cells.append(cell)
                if changed:
                    result.append("|".join(new_cells))
                else:
                    result.append(line)
            else:
                result.append(line)
            i += 1
            continue

        # Repetição adjacente (pula linhas em branco intercaladas)
        if stripped:
            run_start = i
            repeat_count = 1
            j = i + 1
            while j < n:
                next_stripped = lines[j].strip()
                if not next_stripped:
                    j += 1
                    continue
                if next_stripped == stripped:
                    repeat_count += 1
                    j += 1
                else:
                    break
            if repeat_count >= config.min_repeats:
                result.append(line)
                log.append(
                    f"  L{run_start + 1}: '{stripped[:50]}' repetido {repeat_count}x → colapsado"
                )
                i = j
                continue

        # Repetição intra-linha
        if len(stripped) > config.long_line_threshold:
            match = _find_repeating_unit(
                stripped,
                config.min_repeats,
                config.min_repeat_unit_len,
                config.repeat_coverage_threshold,
            )
            if match:
                unit, count = match
                collapsed = unit.strip()
                log.append(f"  L{i + 1}: '{collapsed[:50]}' repetido {count}x → colapsado")
                # Fragmentos colapsados de repeticao sao lixo OCR -- threshold mais alto
                if len(collapsed) <= max(config.fragment_max_len * 4, 20):
                    log.append(f"  L{i + 1}: fragmento colapsado '{collapsed}' descartado (curto)")
                else:
                    result.append(collapsed)
                i += 1
                continue

        result.append(line)
        i += 1

    return result, log


def _phase_sparse_tables(lines: list[str], config: CleanerConfig) -> tuple[list[str], list[str]]:
    """Fase 3: remove tabelas markdown com maioria de células vazias."""
    result: list[str] = []
    log: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        # Detectar início de tabela
        if not lines[i].strip().startswith("|"):
            result.append(lines[i])
            i += 1
            continue

        # Coletar bloco de tabela
        table_start = i
        table_block: list[str] = []
        while i < n and lines[i].strip().startswith("|"):
            table_block.append(lines[i])
            i += 1

        # Avaliar tabela
        data_rows: list[str] = []
        for row in table_block:
            if not _RE_TABLE_SEPARATOR.match(row.strip()):
                data_rows.append(row)

        if len(data_rows) < config.table_min_rows:
            result.extend(table_block)
            continue

        # Parsear e avaliar células
        total_cells = 0
        empty_cells = 0
        has_substantive = False

        for row in data_rows:
            cells = row.split("|")
            # Primeiro e último split são vazios por causa dos pipes externos
            cells = [c for c in cells if c or c == ""]
            for cell in cells:
                clean_cell = _RE_HTML_TAGS.sub("", cell).strip()
                total_cells += 1

                if len(clean_cell) > config.table_substantive_cell_len:
                    has_substantive = True

                if len(clean_cell) < 3 or all(c in " \t.,;:-_|/\\'" for c in clean_cell):
                    empty_cells += 1

        if total_cells == 0:
            result.extend(table_block)
            continue

        empty_ratio = empty_cells / total_cells

        if empty_ratio > config.sparse_table_threshold and not has_substantive:
            log.append(
                f"  L{table_start + 1}-{table_start + len(table_block)}: "
                f"tabela {total_cells} células, {empty_cells} vazias "
                f"({empty_ratio:.0%}) → removida"
            )
        else:
            result.extend(table_block)

    return result, log


def _phase_fragments(lines: list[str], config: CleanerConfig) -> tuple[list[str], list[str]]:
    """Fase 4: remove fragmentos isolados (<= N chars sem vizinhos substantivos)."""
    result: list[str] = []
    log: list[str] = []
    n = len(lines)

    for i, line in enumerate(lines):
        stripped = line.strip()

        if not stripped:
            result.append(line)
            continue

        if len(stripped) > config.fragment_max_len:
            result.append(line)
            continue

        # Whitelist: marcadores de lista
        if _RE_LIST_MARKER.match(stripped):
            result.append(line)
            continue

        # Whitelist: alíneas compostas
        if _RE_COMPOUND_ALINCA.match(stripped):
            result.append(line)
            continue

        # Whitelist: abreviações jurídicas
        if stripped.lower().rstrip(".") + "." in _JURIDICAL_WHITELIST or stripped in (
            "§",
            "§§",
        ):
            result.append(line)
            continue

        # Verificar vizinhos substantivos
        prev_substantive = i > 0 and len(lines[i - 1].strip()) >= config.substantive_line_min_len
        next_substantive = (
            i < n - 1 and len(lines[i + 1].strip()) >= config.substantive_line_min_len
        )

        if prev_substantive or next_substantive:
            result.append(line)
            continue

        log.append(f"  L{i + 1}: '{stripped}' (fragmento isolado)")

    return result, log


def _phase_juridical(lines: list[str], config: CleanerConfig) -> tuple[list[str], list[str]]:
    """Fase 5: aplica SystemPatterns por blocos de 20 linhas."""
    log: list[str] = []

    # Detectar sistema
    if config.system == "auto":
        sample = "\n".join(lines[:500])
        detector = JudicialSystemDetector()
        detection = detector.detect_system(sample)
        system_code = detection.system
        log.append(f"  Sistema detectado: {detection.name} (confiança: {detection.confidence})")
    else:
        system_code = config.system.upper()

    patterns = SystemPatterns.get_patterns(system_code)

    block_size = 20
    overlap = 5
    result_lines = list(lines)
    patterns_applied: set[str] = set()

    i = 0
    while i < len(result_lines):
        end = min(i + block_size, len(result_lines))
        block_text = "\n".join(result_lines[i:end])

        for pattern in patterns:
            new_text = pattern.regex.sub(pattern.replacement, block_text)
            if new_text != block_text:
                patterns_applied.add(pattern.description)
                block_text = new_text

        new_lines = block_text.split("\n")
        result_lines[i:end] = new_lines

        # Avançar com overlap
        step = block_size - overlap
        if step <= 0:
            step = 1
        i += step

    # Remover linhas completamente vazias criadas pela remoção de patterns
    # (mas preservar blank lines originais -- só remover runs de 3+)
    for desc in sorted(patterns_applied):
        log.append(f"  Pattern aplicado: '{desc}'")

    return result_lines, log


def _phase_excessive_spaces(lines: list[str], config: CleanerConfig) -> tuple[list[str], list[str]]:
    """Fase 6: remove linhas com proporção anormal de espaços."""
    result: list[str] = []
    log: list[str] = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            result.append(line)
            continue

        length = len(stripped)

        # Ratio de espaços
        space_count = stripped.count(" ")
        ratio = space_count / length if length > 0 else 0

        if ratio > config.space_ratio_threshold:
            log.append(f"  L{i + 1}: ratio {ratio:.2f} → removida")
            continue

        # Caracteres espalhados por OCR (linha inteira)
        if _RE_SCATTERED_CHARS.match(stripped):
            log.append(f"  L{i + 1}: chars espalhados → removida")
            continue

        result.append(line)

    return result, log


def run_ocr_cleaner(
    lines: list[str],
    config: CleanerConfig | None = None,
) -> tuple[list[str], list[str]]:
    """
    Lógica pura: recebe linhas, devolve (linhas_limpas, log_entries).
    Testável sem filesystem.
    """
    config = config or CleanerConfig()
    log_entries: list[str] = []

    phases = [
        ("Estrutural", _phase_structural),
        ("Repetição", _phase_repetition),
        ("Tabelas esparsas", _phase_sparse_tables),
        ("Fragmentos isolados", _phase_fragments),
        ("Assinaturas jurídicas", _phase_juridical),
        ("Espaços excessivos", _phase_excessive_spaces),
    ]

    for name, fn in phases:
        before = len(lines)
        lines, phase_log = fn(lines, config)
        after = len(lines)
        log_entries.append(f"== Fase: {name} ==")
        log_entries.append(f"Removidas: {before - after} linhas")
        log_entries.extend(phase_log)
        log_entries.append("")

    # Passo final: colapsar blank lines criadas por remoções nas fases 2-6
    before_final = len(lines)
    final_lines: list[str] = []
    consecutive_blanks = 0
    for line in lines:
        if not line.strip():
            consecutive_blanks += 1
            if consecutive_blanks <= config.max_consecutive_blank_lines:
                final_lines.append(line)
        else:
            consecutive_blanks = 0
            final_lines.append(line)
    removed_final = before_final - len(final_lines)
    if removed_final:
        log_entries.append("== Passo final: colapso de blank lines ==")
        log_entries.append(f"Removidas: {removed_final} linhas em branco excessivas")
        log_entries.append("")

    return final_lines, log_entries


def clean_ocr_markdown(
    input_path: str | Path,
    output_dir: str | Path,
    config: CleanerConfig | None = None,
) -> None:
    """
    Wrapper de I/O: lê arquivo, chama run_ocr_cleaner, escreve saída.

    Gera dois arquivos em output_dir:
      - {stem}_cleaned.md    -- texto limpo
      - {stem}_cleaning.log  -- log detalhado do que cada fase removeu
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    stem = input_path.stem

    text = input_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    log_header = [f"Input: {input_path}", f"Linhas originais: {len(lines)}", ""]
    cleaned_lines, log_entries = run_ocr_cleaner(lines, config)
    log_footer = ["", f"Linhas finais: {len(cleaned_lines)}"]

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{stem}_cleaned.md").write_text("\n".join(cleaned_lines), encoding="utf-8")
    (output_dir / f"{stem}_cleaning.log").write_text(
        "\n".join(log_header + log_entries + log_footer), encoding="utf-8"
    )
