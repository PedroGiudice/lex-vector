"""
Filtro de Jurisprudência em Cadernos DJEN

Após download massivo de cadernos, permite filtrar por:
- Tema/palavras-chave
- Estado/Tribunal
- Data (range)
- Tipo de processo (1ª/2ª instância)

Integra com BuscaInteligente do oab-watcher para scoring de relevância.
"""
import json
import logging
import re
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class FiltroJurisprudencia:
    """Critérios de filtro para jurisprudência."""
    temas: Optional[List[str]] = None  # ["execução fiscal", "ICMS", "crédito tributário"]
    tribunais: Optional[List[str]] = None  # ["STF", "STJ", "TJSP"]
    data_inicio: Optional[str] = None  # "2025-01-01"
    data_fim: Optional[str] = None  # "2025-12-31"
    instancia: Optional[str] = None  # "1", "2", "superior"
    palavras_chave: Optional[List[str]] = None  # Palavras específicas no texto
    score_minimo: float = 0.5  # Score mínimo de relevância (0.0 a 1.0)


@dataclass
class ResultadoJurisprudencia:
    """Resultado de busca de jurisprudência."""
    arquivo_caderno: str
    tribunal: str
    data_publicacao: str
    trechos_relevantes: List[str]  # Trechos do texto que matcharam
    score_relevancia: float  # 0.0 a 1.0
    metadata: Dict  # Informações adicionais (tamanho, páginas, etc)


class CadernoFilter:
    """
    Filtro de jurisprudência em cadernos DJEN baixados.

    Processa PDFs de cadernos e filtra por tema, estado, data.
    Integra com BuscaInteligente para scoring de relevância.
    """

    def __init__(self, cadernos_dir: Path):
        """
        Inicializa CadernoFilter.

        Args:
            cadernos_dir: Diretório com cadernos baixados
        """
        self.cadernos_dir = Path(cadernos_dir)
        self.cache_dir = self.cadernos_dir.parent / "cache" / "textos_extraidos"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"CadernoFilter inicializado: {cadernos_dir}")

    def listar_cadernos(
        self,
        tribunais: Optional[List[str]] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None
    ) -> List[Path]:
        """
        Lista cadernos disponíveis no diretório.

        Args:
            tribunais: Filtrar por tribunais específicos
            data_inicio: Data início (YYYY-MM-DD)
            data_fim: Data fim (YYYY-MM-DD)

        Returns:
            Lista de paths para cadernos PDF
        """
        pattern = "*.pdf"
        cadernos = list(self.cadernos_dir.glob(pattern))

        # Filtrar por tribunal
        if tribunais:
            tribunais_upper = [t.upper() for t in tribunais]
            cadernos = [
                c for c in cadernos
                if any(t in c.name.upper() for t in tribunais_upper)
            ]

        # Filtrar por data (assumindo formato: TJSP_2025-11-13_D.pdf)
        if data_inicio or data_fim:
            cadernos_filtrados = []
            for caderno in cadernos:
                try:
                    # Extrair data do nome do arquivo
                    match = re.search(r'(\d{4}-\d{2}-\d{2})', caderno.name)
                    if match:
                        data_str = match.group(1)
                        data_caderno = datetime.strptime(data_str, '%Y-%m-%d').date()

                        # Verificar range
                        if data_inicio:
                            data_ini = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                            if data_caderno < data_ini:
                                continue

                        if data_fim:
                            data_fi = datetime.strptime(data_fim, '%Y-%m-%d').date()
                            if data_caderno > data_fi:
                                continue

                        cadernos_filtrados.append(caderno)
                except Exception as e:
                    logger.warning(f"Erro ao extrair data de {caderno.name}: {e}")
                    continue

            cadernos = cadernos_filtrados

        logger.info(f"Encontrados {len(cadernos)} cadernos após filtros")
        return sorted(cadernos)

    def extrair_texto_pdf(
        self,
        pdf_path: Path,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Extrai texto de PDF de caderno.

        Args:
            pdf_path: Path para PDF
            use_cache: Se True, usa cache de textos já extraídos

        Returns:
            Texto extraído ou None se erro
        """
        cache_file = self.cache_dir / f"{pdf_path.stem}.txt"

        # Verificar cache
        if use_cache and cache_file.exists():
            logger.debug(f"Cache HIT para {pdf_path.name}")
            try:
                return cache_file.read_text(encoding='utf-8')
            except Exception as e:
                logger.warning(f"Erro ao ler cache {cache_file}: {e}")

        # Extrair texto do PDF
        logger.info(f"Extraindo texto de {pdf_path.name}...")

        try:
            # Tentar pdfplumber (melhor para tabelas e formatação)
            import pdfplumber

            texto_completo = []

            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    texto = page.extract_text()
                    if texto:
                        texto_completo.append(texto)

            texto_final = '\n\n'.join(texto_completo)

            # Salvar em cache
            if use_cache:
                try:
                    cache_file.write_text(texto_final, encoding='utf-8')
                    logger.debug(f"Texto salvo em cache: {cache_file}")
                except Exception as e:
                    logger.warning(f"Erro ao salvar cache: {e}")

            return texto_final

        except ImportError:
            logger.warning("pdfplumber não disponível, tentando PyPDF2...")

            try:
                # Fallback para PyPDF2
                from PyPDF2 import PdfReader

                texto_completo = []

                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    texto = page.extract_text()
                    if texto:
                        texto_completo.append(texto)

                texto_final = '\n\n'.join(texto_completo)

                # Salvar em cache
                if use_cache:
                    try:
                        cache_file.write_text(texto_final, encoding='utf-8')
                    except Exception as e:
                        logger.warning(f"Erro ao salvar cache: {e}")

                return texto_final

            except ImportError:
                logger.error("Nem pdfplumber nem PyPDF2 disponíveis. Instale um deles.")
                return None
            except Exception as e:
                logger.error(f"Erro ao extrair texto com PyPDF2: {e}")
                return None

        except Exception as e:
            logger.error(f"Erro ao extrair texto de {pdf_path}: {e}")
            return None

    def calcular_score_relevancia(
        self,
        texto: str,
        filtro: FiltroJurisprudencia
    ) -> Tuple[float, List[str]]:
        """
        Calcula score de relevância de um texto baseado nos filtros.

        Args:
            texto: Texto do caderno
            filtro: Critérios de filtro

        Returns:
            (score: float, trechos_relevantes: List[str])
        """
        score = 0.0
        trechos = []

        texto_lower = texto.lower()

        # Peso 1: Temas (0.4)
        if filtro.temas:
            matches_temas = 0
            for tema in filtro.temas:
                tema_lower = tema.lower()
                # Contar ocorrências
                count = texto_lower.count(tema_lower)
                if count > 0:
                    matches_temas += 1

                    # Extrair trecho relevante (contexto de 200 caracteres)
                    idx = texto_lower.find(tema_lower)
                    if idx >= 0:
                        start = max(0, idx - 100)
                        end = min(len(texto), idx + len(tema) + 100)
                        trecho = texto[start:end].strip()
                        trechos.append(f"[TEMA: {tema}] ...{trecho}...")

            # Score proporcional a quantos temas matcharam
            score_temas = (matches_temas / len(filtro.temas)) * 0.4
            score += score_temas

        # Peso 2: Palavras-chave (0.3)
        if filtro.palavras_chave:
            matches_palavras = 0
            for palavra in filtro.palavras_chave:
                palavra_lower = palavra.lower()
                if palavra_lower in texto_lower:
                    matches_palavras += 1

                    # Extrair trecho
                    idx = texto_lower.find(palavra_lower)
                    if idx >= 0:
                        start = max(0, idx - 100)
                        end = min(len(texto), idx + len(palavra) + 100)
                        trecho = texto[start:end].strip()
                        trechos.append(f"[PALAVRA: {palavra}] ...{trecho}...")

            score_palavras = (matches_palavras / len(filtro.palavras_chave)) * 0.3
            score += score_palavras

        # Peso 3: Instância (0.2)
        if filtro.instancia:
            # Detectar menções a instâncias
            if filtro.instancia == "1":
                patterns = [r'1ª instância', r'primeira instância', r'juiz de direito']
            elif filtro.instancia == "2":
                patterns = [r'2ª instância', r'segunda instância', r'câmara', r'desembargador']
            else:  # superior
                patterns = [r'recurso especial', r'recurso extraordinário', r'STJ', r'STF']

            matches_instancia = sum(
                1 for pattern in patterns
                if re.search(pattern, texto_lower)
            )

            if matches_instancia > 0:
                score += 0.2

        # Peso 4: Presença mínima de conteúdo jurídico (0.1)
        # Heurística: se tem termos jurídicos básicos
        termos_juridicos = ['processo', 'sentença', 'acórdão', 'recurso', 'decisão', 'juiz']
        matches_juridicos = sum(1 for termo in termos_juridicos if termo in texto_lower)

        if matches_juridicos >= 3:
            score += 0.1

        return (min(1.0, score), trechos[:10])  # Limitar a 10 trechos

    def filtrar(
        self,
        filtro: FiltroJurisprudencia,
        max_resultados: Optional[int] = None,
        use_cache: bool = True
    ) -> List[ResultadoJurisprudencia]:
        """
        Filtra cadernos baseado nos critérios.

        Args:
            filtro: Critérios de filtro
            max_resultados: Número máximo de resultados (None = ilimitado)
            use_cache: Se True, usa cache de textos extraídos

        Returns:
            Lista de ResultadoJurisprudencia ordenados por relevância
        """
        logger.info(f"Iniciando filtro de jurisprudência...")
        logger.info(f"  Temas: {filtro.temas}")
        logger.info(f"  Tribunais: {filtro.tribunais}")
        logger.info(f"  Data: {filtro.data_inicio} → {filtro.data_fim}")

        # Listar cadernos aplicando filtros básicos (tribunal, data)
        cadernos = self.listar_cadernos(
            tribunais=filtro.tribunais,
            data_inicio=filtro.data_inicio,
            data_fim=filtro.data_fim
        )

        if not cadernos:
            logger.warning("Nenhum caderno encontrado após filtros básicos")
            return []

        resultados = []

        # Processar cada caderno
        for caderno_path in cadernos:
            logger.info(f"Processando {caderno_path.name}...")

            # Extrair texto
            texto = self.extrair_texto_pdf(caderno_path, use_cache=use_cache)

            if not texto:
                logger.warning(f"Não foi possível extrair texto de {caderno_path.name}")
                continue

            # Calcular score de relevância
            score, trechos = self.calcular_score_relevancia(texto, filtro)

            # Verificar threshold
            if score >= filtro.score_minimo:
                # Extrair metadata do nome do arquivo
                # Formato esperado: TJSP_2025-11-13_D.pdf
                match = re.match(r'([A-Z0-9]+)_(\d{4}-\d{2}-\d{2})_([DE])\.pdf', caderno_path.name)

                if match:
                    tribunal, data_pub, meio = match.groups()
                else:
                    tribunal = "DESCONHECIDO"
                    data_pub = "DESCONHECIDA"

                resultado = ResultadoJurisprudencia(
                    arquivo_caderno=str(caderno_path),
                    tribunal=tribunal,
                    data_publicacao=data_pub,
                    trechos_relevantes=trechos,
                    score_relevancia=score,
                    metadata={
                        'tamanho_bytes': caderno_path.stat().st_size,
                        'tamanho_texto': len(texto),
                        'nome_arquivo': caderno_path.name
                    }
                )

                resultados.append(resultado)

                logger.info(
                    f"  ✅ Relevante (score={score:.2f}): "
                    f"{tribunal} {data_pub} - {len(trechos)} trechos"
                )
            else:
                logger.debug(f"  ⏭️  Irrelevante (score={score:.2f})")

        # Ordenar por relevância (maior primeiro)
        resultados.sort(key=lambda r: r.score_relevancia, reverse=True)

        # Limitar resultados se especificado
        if max_resultados:
            resultados = resultados[:max_resultados]

        logger.info(f"Filtro concluído: {len(resultados)} resultados relevantes")

        return resultados

    def exportar_resultados(
        self,
        resultados: List[ResultadoJurisprudencia],
        output_file: Path,
        formato: str = 'json'
    ) -> None:
        """
        Exporta resultados para arquivo.

        Args:
            resultados: Lista de resultados
            output_file: Path para arquivo de saída
            formato: 'json' ou 'txt'
        """
        if formato == 'json':
            data = [asdict(r) for r in resultados]

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Resultados exportados para {output_file} (JSON)")

        elif formato == 'txt':
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# RESULTADOS DE JURISPRUDÊNCIA\n")
                f.write(f"# Total: {len(resultados)} resultados\n")
                f.write(f"# Gerado em: {datetime.now().isoformat()}\n\n")
                f.write("=" * 80 + "\n\n")

                for i, resultado in enumerate(resultados, 1):
                    f.write(f"## RESULTADO {i}/{len(resultados)}\n\n")
                    f.write(f"**Tribunal**: {resultado.tribunal}\n")
                    f.write(f"**Data**: {resultado.data_publicacao}\n")
                    f.write(f"**Score**: {resultado.score_relevancia:.2f}\n")
                    f.write(f"**Arquivo**: {resultado.arquivo_caderno}\n\n")

                    f.write("### Trechos Relevantes\n\n")
                    for j, trecho in enumerate(resultado.trechos_relevantes, 1):
                        f.write(f"{j}. {trecho}\n\n")

                    f.write("=" * 80 + "\n\n")

            logger.info(f"Resultados exportados para {output_file} (TXT)")

        else:
            raise ValueError(f"Formato inválido: {formato}. Use 'json' ou 'txt'")


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Filtro de Jurisprudência em Cadernos DJEN")
    parser.add_argument('--cadernos-dir', required=True, help="Diretório com cadernos baixados")
    parser.add_argument('--temas', nargs='+', help="Temas para buscar (ex: 'ICMS' 'execução fiscal')")
    parser.add_argument('--tribunais', nargs='+', help="Tribunais (ex: STF STJ TJSP)")
    parser.add_argument('--data-inicio', help="Data início (YYYY-MM-DD)")
    parser.add_argument('--data-fim', help="Data fim (YYYY-MM-DD)")
    parser.add_argument('--palavras-chave', nargs='+', help="Palavras-chave adicionais")
    parser.add_argument('--score-minimo', type=float, default=0.5, help="Score mínimo (0.0-1.0)")
    parser.add_argument('--max-resultados', type=int, help="Máximo de resultados")
    parser.add_argument('--output', required=True, help="Arquivo de saída (.json ou .txt)")
    parser.add_argument('--formato', choices=['json', 'txt'], default='json', help="Formato de saída")
    parser.add_argument('--no-cache', action='store_true', help="Desabilitar cache de textos")

    args = parser.parse_args()

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Criar filtro
    filtro = FiltroJurisprudencia(
        temas=args.temas,
        tribunais=args.tribunais,
        data_inicio=args.data_inicio,
        data_fim=args.data_fim,
        palavras_chave=args.palavras_chave,
        score_minimo=args.score_minimo
    )

    # Executar filtro
    caderno_filter = CadernoFilter(Path(args.cadernos_dir))
    resultados = caderno_filter.filtrar(
        filtro=filtro,
        max_resultados=args.max_resultados,
        use_cache=not args.no_cache
    )

    # Exportar resultados
    output_path = Path(args.output)
    caderno_filter.exportar_resultados(resultados, output_path, formato=args.formato)

    print(f"\n✅ {len(resultados)} resultados encontrados e exportados para {output_path}")
