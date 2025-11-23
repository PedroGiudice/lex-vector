"""
Processador para dados do STJ Dados Abertos.
Reaproveita código do sistema DJEN para evitar retrabalho.
"""
import json
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging
from rich.console import Console

import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "jurisprudencia-collector" / "src"))

# Reaproveitar funções do sistema DJEN
from processador_texto import (
    extrair_ementa,
    extrair_relator
)

console = Console()
logger = logging.getLogger(__name__)


def processar_publicacao_stj(json_data: Dict) -> Dict:
    """
    Processa publicação JSON do STJ Dados Abertos.

    DIFERENÇA CRÍTICA vs DJEN:
    - Input é JSON estruturado (não HTML!)
    - Campos já vêm separados (ementa, relatório, voto)
    - Texto integral já está limpo

    Args:
        json_data: Dict do JSON STJ com estrutura esperada:
            - processo: número do processo
            - dataPublicacao: data ISO
            - dataJulgamento: data ISO
            - orgaoJulgador: turma/seção
            - relator: nome do ministro
            - ementa: texto da ementa
            - inteiro_teor: texto completo do acórdão
            - assuntos: lista de assuntos

    Returns:
        Dict pronto para inserção no DuckDB
    """
    # Extrair campos principais
    numero_processo = json_data.get('processo', '')
    texto_integral = json_data.get('inteiro_teor', '')

    # Se não tem inteiro teor, tentar concatenar partes
    if not texto_integral:
        partes = []
        if json_data.get('ementa'):
            partes.append(f"EMENTA:\n{json_data['ementa']}")
        if json_data.get('relatorio'):
            partes.append(f"RELATÓRIO:\n{json_data['relatorio']}")
        if json_data.get('voto'):
            partes.append(f"VOTO:\n{json_data['voto']}")
        if json_data.get('decisao'):
            partes.append(f"DECISÃO:\n{json_data['decisao']}")

        texto_integral = "\n\n".join(partes)

    # Gerar hash para deduplicação (método do DJEN)
    hash_conteudo = hashlib.sha256(texto_integral.encode('utf-8')).hexdigest()

    # Extrair ementa
    # STJ às vezes tem campo 'ementa' direto, outras vezes está no texto
    ementa = json_data.get('ementa')
    if not ementa and texto_integral:
        # Usar função do DJEN se não vier estruturada
        ementa = extrair_ementa(texto_integral)

    # Extrair relator
    # STJ geralmente tem campo 'relator' ou 'ministro'
    relator = json_data.get('relator') or json_data.get('ministro')
    if not relator and texto_integral:
        # Usar função do DJEN como fallback
        relator = extrair_relator(texto_integral)

    # Converter datas
    data_publicacao = json_data.get('dataPublicacao')
    data_julgamento = json_data.get('dataJulgamento')

    # Se as datas vierem em timestamp (milliseconds)
    if isinstance(data_publicacao, (int, float)):
        data_publicacao = datetime.fromtimestamp(data_publicacao / 1000).isoformat()
    if isinstance(data_julgamento, (int, float)):
        data_julgamento = datetime.fromtimestamp(data_julgamento / 1000).isoformat()

    # Classificar tipo (STJ é sempre acórdão ou decisão monocrática)
    tipo_decisao = 'Acórdão'
    if 'monocratica' in texto_integral.lower()[:500]:
        tipo_decisao = 'Decisão Monocrática'

    # Montar registro processado
    return {
        'id': str(uuid.uuid4()),
        'numero_processo': numero_processo,
        'hash_conteudo': hash_conteudo,
        'tribunal': 'STJ',
        'orgao_julgador': json_data.get('orgaoJulgador', ''),
        'tipo_decisao': tipo_decisao,
        'classe_processual': json_data.get('classe', ''),
        'ementa': ementa,
        'texto_integral': texto_integral,
        'relator': relator,
        'data_publicacao': data_publicacao,
        'data_julgamento': data_julgamento,
        'assuntos': json.dumps(json_data.get('assuntos', [])),
        'fonte': 'STJ-Dados-Abertos',
        'fonte_url': json_data.get('url', ''),
        'metadata': json.dumps({
            'original_id': json_data.get('id'),
            'versao': json_data.get('versao', '1.0'),
            'processado_em': datetime.now().isoformat()
        })
    }


class STJProcessor:
    """
    Processador batch para múltiplos arquivos JSON do STJ.
    """

    def __init__(self):
        self.stats = {
            'processados': 0,
            'com_ementa': 0,
            'com_relator': 0,
            'erros': 0
        }

    def processar_arquivo_json(self, json_path: Path) -> List[Dict]:
        """
        Processa um arquivo JSON do STJ.

        Args:
            json_path: Caminho do arquivo JSON

        Returns:
            Lista de dicts processados
        """
        try:
            logger.info(f"Processando: {json_path.name}")

            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # O JSON pode ser lista ou objeto único
            if not isinstance(data, list):
                data = [data]

            resultados = []
            for item in data:
                try:
                    processado = processar_publicacao_stj(item)
                    resultados.append(processado)

                    # Atualizar stats
                    self.stats['processados'] += 1
                    if processado.get('ementa'):
                        self.stats['com_ementa'] += 1
                    if processado.get('relator'):
                        self.stats['com_relator'] += 1

                except Exception as e:
                    logger.error(f"Erro processando item: {e}")
                    self.stats['erros'] += 1
                    continue

            logger.info(f"Processados {len(resultados)} itens de {json_path.name}")
            return resultados

        except Exception as e:
            logger.error(f"Erro ao processar arquivo {json_path}: {e}")
            self.stats['erros'] += 1
            return []

    def processar_batch(self, json_files: List[Path]) -> List[Dict]:
        """
        Processa múltiplos arquivos JSON.

        Args:
            json_files: Lista de caminhos de arquivos

        Returns:
            Lista consolidada de todos os registros processados
        """
        todos_resultados = []

        for json_path in json_files:
            resultados = self.processar_arquivo_json(json_path)
            todos_resultados.extend(resultados)

        return todos_resultados

    def print_stats(self):
        """Imprime estatísticas do processamento."""
        console.print("\n[bold cyan]Estatísticas de Processamento:[/bold cyan]")
        console.print(f"📄 Total processados: {self.stats['processados']}")
        console.print(f"📝 Com ementa: {self.stats['com_ementa']} ({self.stats['com_ementa']*100//max(self.stats['processados'],1)}%)")
        console.print(f"👨‍⚖️ Com relator: {self.stats['com_relator']} ({self.stats['com_relator']*100//max(self.stats['processados'],1)}%)")
        console.print(f"❌ Erros: {self.stats['erros']}")


def test_processor():
    """Teste do processador com dados mockados."""
    # Dados de teste simulando estrutura STJ
    test_data = {
        "processo": "REsp 1234567/SP",
        "dataPublicacao": "2024-11-20T00:00:00",
        "dataJulgamento": "2024-11-15T00:00:00",
        "orgaoJulgador": "Terceira Turma",
        "relator": "Ministro Paulo de Tarso Sanseverino",
        "ementa": "RECURSO ESPECIAL. DIREITO CIVIL. RESPONSABILIDADE CIVIL. DANO MORAL. QUANTUM INDENIZATÓRIO.",
        "inteiro_teor": """
        EMENTA: RECURSO ESPECIAL. DIREITO CIVIL. RESPONSABILIDADE CIVIL.
        RELATÓRIO: O SENHOR MINISTRO PAULO DE TARSO SANSEVERINO (Relator):
        Trata-se de recurso especial interposto...
        VOTO: Como relatado, trata-se de recurso especial...
        """,
        "classe": "REsp",
        "assuntos": ["Direito Civil", "Responsabilidade Civil", "Dano Moral"]
    }

    # Processar
    resultado = processar_publicacao_stj(test_data)

    # Validar
    console.print("[bold green]Teste de Processamento:[/bold green]")
    console.print(f"✅ ID gerado: {resultado['id'][:8]}...")
    console.print(f"✅ Hash: {resultado['hash_conteudo'][:16]}...")
    console.print(f"✅ Ementa extraída: {resultado['ementa'][:50]}...")
    console.print(f"✅ Relator: {resultado['relator']}")
    console.print(f"✅ Órgão: {resultado['orgao_julgador']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_processor()