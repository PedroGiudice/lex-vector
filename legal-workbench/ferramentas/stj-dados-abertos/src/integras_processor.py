"""
Processador de integras do STJ.

Normaliza metadados (campos variantes entre consolidados e diarios),
converte HTML para texto limpo, e prepara registros para insercao no DuckDB.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class _HTMLStripper(HTMLParser):
    """Remove tags HTML preservando texto e quebras de linha."""

    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_starttag(self, tag, attrs):
        if tag in ("br", "p", "div", "li", "tr"):
            self.text.write("\n")

    def handle_endtag(self, tag):
        if tag in ("p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"):
            self.text.write("\n")

    def handle_data(self, data):
        self.text.write(data)

    def get_text(self) -> str:
        return self.text.getvalue()


def html_para_texto(html: Optional[str]) -> str:
    """
    Converte HTML do texto completo para texto limpo.
    Preserva estrutura de paragrafos.
    Usa html.parser da stdlib (sem dependencia externa).
    """
    if not html:
        return ""

    stripper = _HTMLStripper()
    try:
        stripper.feed(html)
    except Exception:
        # Se falhar o parse, retornar texto bruto sem tags
        return re.sub(r'<[^>]+>', ' ', html).strip()

    texto = stripper.get_text()
    # Limpar multiplas quebras de linha consecutivas
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    # Limpar espacos antes/depois de quebras
    texto = re.sub(r' *\n *', '\n', texto)
    return texto.strip()


def extrair_numero_processo(processo: Optional[str]) -> str:
    """Extrai numero do campo processo (ex: 'AREsp 2591846' -> '2591846')."""
    if not processo:
        return ""
    match = re.search(r'\d+', processo.strip())
    return match.group(0) if match else ""


def extrair_classe_processual(processo: Optional[str]) -> str:
    """Extrai classe do campo processo (ex: 'AREsp 2591846' -> 'AREsp')."""
    if not processo:
        return ""
    match = re.match(r'([A-Za-z]+)', processo.strip())
    return match.group(1) if match else ""


def _epoch_ms_para_iso(epoch_ms: int) -> str:
    """Converte epoch em milissegundos para data ISO (YYYY-MM-DD)."""
    dt = datetime.fromtimestamp(epoch_ms / 1000)
    return dt.strftime("%Y-%m-%d")


def _normalizar_assuntos(assuntos_raw) -> list[str]:
    """Normaliza campo assuntos (pode ser string com ; ou , ou None)."""
    if not assuntos_raw:
        return []
    if isinstance(assuntos_raw, list):
        return [str(a).strip() for a in assuntos_raw if str(a).strip()]
    assuntos_str = str(assuntos_raw)
    # Detectar separador: ponto-e-virgula ou virgula
    if ";" in assuntos_str:
        parts = assuntos_str.split(";")
    else:
        parts = assuntos_str.split(",")
    return [p.strip() for p in parts if p.strip()]


def normalizar_metadados(raw: dict) -> dict:
    """
    Normaliza um registro de metadados, tratando variacoes entre
    consolidados mensais e diarios.

    Normaliza:
    - SeqDocumento/seqDocumento -> seq_documento
    - ministro/NM_MINISTRO -> ministro
    - Datas epoch ms -> ISO string
    - processo -> numero_processo + classe_processual
    - assuntos (separador ; ou ,) -> lista de codigos CNJ
    """
    # SeqDocumento: maiusculo (diarios) ou minusculo (consolidados)
    seq_documento = raw.get("SeqDocumento") or raw.get("seqDocumento")

    # Ministro: NM_MINISTRO (diarios) ou ministro (consolidados)
    ministro = raw.get("NM_MINISTRO") or raw.get("ministro") or ""

    # Data publicacao: ISO string (diarios) ou epoch ms (consolidados)
    data_pub_raw = raw.get("dataPublicacao")
    if isinstance(data_pub_raw, (int, float)):
        data_publicacao = _epoch_ms_para_iso(int(data_pub_raw))
    else:
        data_publicacao = str(data_pub_raw) if data_pub_raw else None

    # Data recebimento (consolidados apenas)
    data_rec_raw = raw.get("dataRecebimento")
    data_recebimento = None
    if isinstance(data_rec_raw, (int, float)):
        data_recebimento = _epoch_ms_para_iso(int(data_rec_raw))
    elif data_rec_raw:
        data_recebimento = str(data_rec_raw)

    # Data distribuicao (consolidados apenas)
    data_dist_raw = raw.get("dataDistribuicao")
    data_distribuicao = None
    if isinstance(data_dist_raw, (int, float)):
        data_distribuicao = _epoch_ms_para_iso(int(data_dist_raw))
    elif data_dist_raw:
        data_distribuicao = str(data_dist_raw)

    # Processo
    processo = raw.get("processo", "")
    numero_processo = extrair_numero_processo(processo)
    classe_processual = extrair_classe_processual(processo)

    # Assuntos
    assuntos = _normalizar_assuntos(raw.get("assuntos"))

    return {
        "seq_documento": seq_documento,
        "numero_processo": numero_processo,
        "classe_processual": classe_processual,
        "numero_registro": raw.get("numeroRegistro", ""),
        "tipo_documento": raw.get("tipoDocumento", ""),
        "ministro": ministro,
        "teor": raw.get("teor", ""),
        "descricao_monocratica": raw.get("descricaoMonocratica"),
        "recurso": raw.get("recurso"),
        "data_publicacao": data_publicacao,
        "data_recebimento": data_recebimento,
        "data_distribuicao": data_distribuicao,
        "assuntos": assuntos,
    }


def preparar_registro_integra(metadados: dict, texto_html: str) -> dict:
    """
    Combina metadados normalizados + texto extraido em registro
    pronto para insercao na tabela integras do DuckDB.
    """
    texto_limpo = html_para_texto(texto_html)
    meta = normalizar_metadados(metadados)
    return {
        "seq_documento": meta["seq_documento"],
        "numero_processo": meta["numero_processo"],
        "classe_processual": meta["classe_processual"],
        "numero_registro": meta["numero_registro"],
        "hash_conteudo": hashlib.sha256(texto_limpo.encode()).hexdigest(),
        "tipo_documento": meta["tipo_documento"],
        "ministro": meta["ministro"],
        "teor": meta["teor"],
        "descricao_monocratica": meta.get("descricao_monocratica"),
        "texto_completo": texto_limpo,
        "data_publicacao": meta["data_publicacao"],
        "data_recebimento": meta.get("data_recebimento"),
        "data_distribuicao": meta.get("data_distribuicao"),
        "recurso": meta.get("recurso"),
        "assuntos": json.dumps(meta["assuntos"]),
        "data_insercao": datetime.now().isoformat(),
    }


class IntegrasProcessor:
    """Processa lotes de integras (metadados + textos)."""

    def __init__(self):
        self.processados = 0
        self.erros = 0
        self.sem_texto = 0

    def processar_batch(
        self, metadados: list[dict], textos_dir: Path
    ) -> list[dict]:
        """
        Para cada metadado, encontra o .txt correspondente,
        converte HTML->texto, e prepara registro.

        O txt pode estar diretamente em textos_dir ou em subdiretorios.
        Nome do arquivo: {SeqDocumento}.txt
        """
        registros = []

        for meta in metadados:
            seq = meta.get("SeqDocumento") or meta.get("seqDocumento")
            if not seq:
                self.erros += 1
                continue

            # Buscar arquivo de texto (pode estar em subdiretorio)
            txt_path = None
            # Primeiro: busca direta
            direct = textos_dir / f"{seq}.txt"
            if direct.exists():
                txt_path = direct
            else:
                # Busca em subdiretorios (um nivel)
                for subdir in textos_dir.iterdir():
                    if subdir.is_dir():
                        candidate = subdir / f"{seq}.txt"
                        if candidate.exists():
                            txt_path = candidate
                            break

            if not txt_path:
                self.sem_texto += 1
                logger.debug(f"Texto nao encontrado para SeqDocumento {seq}")
                continue

            try:
                texto_html = txt_path.read_text(encoding="utf-8", errors="replace")
                registro = preparar_registro_integra(meta, texto_html)
                registros.append(registro)
                self.processados += 1
            except Exception as e:
                logger.error(f"Erro ao processar SeqDocumento {seq}: {e}")
                self.erros += 1

        return registros
