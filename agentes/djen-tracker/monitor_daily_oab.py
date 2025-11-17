#!/usr/bin/env python3
"""
Monitor diário de OAB no DJEN - Versão otimizada para execução diária

Características:
- Busca apenas o dia atual (ou último dia útil)
- Prioriza tribunais relevantes (SP, federais)
- Mantém checkpoint do que já foi processado
- Download incremental (stop on first match opcional)
- Notificação imediata quando encontra
- Salva histórico de publicações encontradas
"""

import requests
import zipfile
import io
import json
import html
import re
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import time
import hashlib

# Diretório de dados
DATA_DIR = Path(__file__).parent / 'data'
DATA_DIR.mkdir(exist_ok=True)

CHECKPOINT_FILE = DATA_DIR / 'monitor_checkpoint.json'
HISTORICO_FILE = DATA_DIR / 'oab_historico.json'

# Tribunais prioritários (onde advogado de SP mais atua)
TRIBUNAIS_PRIORITARIOS = [
    # São Paulo
    'TJSP',

    # Justiça Federal (SP = TRF3)
    'TRF3', 'TRF1', 'TRF2', 'TRF4', 'TRF5', 'TRF6',

    # Superiores
    'STJ', 'STF', 'TST',

    # Outros TJs (caso necessário)
    'TJRJ', 'TJMG', 'TJPR', 'TJRS', 'TJSC',
]

# Meios prioritários (D tem 100x mais publicações que E)
MEIOS_PRIORITARIOS = ['D', 'E']


class OABMonitor:
    def __init__(self, oab_alvo, uf='SP', max_workers=10):
        self.oab_alvo = str(oab_alvo)
        self.uf = uf
        self.max_workers = max_workers
        self.checkpoint = self._load_checkpoint()
        self.historico = self._load_historico()

    def _load_checkpoint(self):
        """Carrega checkpoint (cadernos já processados)"""
        if CHECKPOINT_FILE.exists():
            with open(CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        return {}

    def _save_checkpoint(self):
        """Salva checkpoint"""
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump(self.checkpoint, f, indent=2)

    def _load_historico(self):
        """Carrega histórico de publicações encontradas"""
        if HISTORICO_FILE.exists():
            with open(HISTORICO_FILE, 'r') as f:
                return json.load(f)
        return []

    def _save_historico(self):
        """Salva histórico"""
        with open(HISTORICO_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.historico, f, indent=2, ensure_ascii=False)

    def _get_data_busca(self):
        """Retorna data a ser buscada (hoje ou último dia útil)"""
        hoje = datetime.now()

        # Se for sábado/domingo, buscar sexta
        if hoje.weekday() == 5:  # Sábado
            return (hoje - timedelta(days=1)).strftime('%Y-%m-%d')
        elif hoje.weekday() == 6:  # Domingo
            return (hoje - timedelta(days=2)).strftime('%Y-%m-%d')

        return hoje.strftime('%Y-%m-%d')

    def _gerar_hash_caderno(self, tribunal, data, meio):
        """Gera hash único para identificar caderno"""
        return hashlib.md5(f"{tribunal}_{data}_{meio}".encode()).hexdigest()

    def _foi_processado(self, tribunal, data, meio):
        """Verifica se caderno já foi processado"""
        hash_caderno = self._gerar_hash_caderno(tribunal, data, meio)
        return hash_caderno in self.checkpoint

    def _marcar_processado(self, tribunal, data, meio, matches_count=0):
        """Marca caderno como processado"""
        hash_caderno = self._gerar_hash_caderno(tribunal, data, meio)
        self.checkpoint[hash_caderno] = {
            'tribunal': tribunal,
            'data': data,
            'meio': meio,
            'processado_em': datetime.now().isoformat(),
            'matches': matches_count
        }
        self._save_checkpoint()

    def _search_oab_in_json(self, data_json):
        """Busca OAB em um JSON"""
        resultados = []

        if not isinstance(data_json, dict) or 'items' not in data_json:
            return resultados

        oab_plain = self.oab_alvo
        oab_dot = f"{oab_plain[:3]}.{oab_plain[3:]}" if len(oab_plain) == 6 else oab_plain

        variações = [
            oab_plain, oab_dot,
            f"{oab_plain}/{self.uf}", f"{oab_dot}/{self.uf}",
            f"OAB {oab_plain}", f"OAB/{self.uf} {oab_plain}",
            f"OAB/{self.uf} {oab_dot}",
            f"OAB nº {oab_plain}", f"OAB/{self.uf} nº {oab_dot}",
        ]

        for item in data_json['items']:
            texto = item.get('texto', '') or ''

            for var in variações:
                if var in texto:
                    # Extrair texto limpo
                    texto_limpo = html.unescape(re.sub('<[^<]+?>', '', texto))

                    # Contexto
                    idx = texto_limpo.find(var)
                    if idx > 0:
                        inicio = max(0, idx - 200)
                        fim = min(len(texto_limpo), idx + 300)
                        contexto = texto_limpo[inicio:fim].strip()
                    else:
                        contexto = texto_limpo[:500]

                    # Detectar falsos positivos simples
                    falso_positivo = self._is_false_positive(var, texto_limpo)

                    resultados.append({
                        'id': item.get('id'),
                        'data': item.get('data_disponibilizacao'),
                        'tribunal': item.get('siglaTribunal'),
                        'orgao': item.get('nomeOrgao', 'N/A'),
                        'tipo': item.get('tipoComunicacao', 'N/A'),
                        'variacao': var,
                        'contexto': contexto,
                        'falso_positivo': falso_positivo,
                        'texto_completo': texto_limpo if not falso_positivo else None
                    })
                    break

        return resultados

    def _is_false_positive(self, variacao, texto):
        """Detecta falsos positivos comuns"""
        # Padrões de falsos positivos

        # 1. Parte de número de processo (ex: 2025/0129021-3)
        if re.search(r'\d{4}/0?' + re.escape(variacao) + r'-\d', texto):
            return True

        # 2. Parte de protocolo (ex: 20251113151129021729)
        if re.search(r'\d{14,}' + re.escape(variacao) + r'\d+', texto):
            return True

        # 3. Data concatenada (ex: 20251129021)
        if re.search(r'202[0-9]' + re.escape(variacao), texto):
            return True

        return False

    def _buscar_caderno(self, tribunal, data, meio):
        """Busca OAB em um caderno específico"""

        # Verificar se já foi processado
        if self._foi_processado(tribunal, data, meio):
            return None

        url_api = f"https://comunicaapi.pje.jus.br/api/v1/caderno/{tribunal}/{data}/{meio}"

        try:
            # Obter metadados
            resp = requests.get(url_api, timeout=30)

            if resp.status_code == 404:
                self._marcar_processado(tribunal, data, meio, 0)
                return None

            if resp.status_code != 200:
                return None

            api_data = resp.json()

            if api_data.get('status') != 'Processado':
                return None

            # Baixar ZIP
            s3_url = api_data.get('url')
            if not s3_url:
                return None

            s3_resp = requests.get(s3_url, timeout=120)
            s3_resp.raise_for_status()

            # Processar JSONs
            resultados = []
            zip_bytes = io.BytesIO(s3_resp.content)

            with zipfile.ZipFile(zip_bytes, 'r') as zf:
                json_files = [f for f in zf.namelist() if f.endswith('.json')]

                for json_file in json_files:
                    json_content = zf.read(json_file)
                    data_json = json.loads(json_content)

                    resultados.extend(self._search_oab_in_json(data_json))

            # Marcar como processado
            self._marcar_processado(tribunal, data, meio, len(resultados))

            if resultados:
                return {
                    'tribunal': tribunal,
                    'data': data,
                    'meio': meio,
                    'matches': resultados
                }

            return None

        except Exception as e:
            print(f"Erro ao processar {tribunal} {data} {meio}: {e}")
            return None

    def monitorar_hoje(self):
        """Monitora publicações do dia atual"""
        print("=" * 80)
        print(f"🔍 MONITOR DIÁRIO - OAB {self.oab_alvo}/{self.uf}")
        print("=" * 80)

        data_busca = self._get_data_busca()
        print(f"\n📅 Data de busca: {data_busca}")
        print(f"🏛️  Tribunais: {len(TRIBUNAIS_PRIORITARIOS)} prioritários")
        print(f"📋 Meios: {', '.join(MEIOS_PRIORITARIOS)}")

        # Gerar tarefas
        tarefas = []
        for tribunal in TRIBUNAIS_PRIORITARIOS:
            for meio in MEIOS_PRIORITARIOS:
                if not self._foi_processado(tribunal, data_busca, meio):
                    tarefas.append((tribunal, data_busca, meio))

        print(f"\n📊 Cadernos a processar: {len(tarefas)}")
        print(f"⏭️  Cadernos já processados: {len(self.checkpoint)}")

        if len(tarefas) == 0:
            print(f"\n✅ Todos os cadernos de {data_busca} já foram processados!")
            return

        print(f"\n🚀 Iniciando monitoramento...\n")

        # Processar em paralelo
        resultados_totais = []
        inicio = time.time()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._buscar_caderno, t, d, m): (t, d, m)
                      for t, d, m in tarefas}

            for future in as_completed(futures):
                tribunal, data, meio = futures[future]

                try:
                    resultado = future.result()

                    if resultado and resultado['matches']:
                        # Encontrou match!
                        matches_reais = [m for m in resultado['matches'] if not m.get('falso_positivo')]

                        if matches_reais:
                            print(f"🎯 {tribunal} {meio}: {len(matches_reais)} MATCHES REAIS!")

                            # Adicionar ao histórico
                            for match in matches_reais:
                                self.historico.append({
                                    'encontrado_em': datetime.now().isoformat(),
                                    'tribunal': tribunal,
                                    'data_publicacao': data,
                                    'meio': meio,
                                    'publicacao': match
                                })

                            self._save_historico()
                            resultados_totais.append(resultado)

                except Exception as e:
                    print(f"Erro: {e}")

        tempo_total = time.time() - inicio

        # Resumo
        print("\n" + "=" * 80)
        print("📊 RESUMO DO MONITORAMENTO")
        print("=" * 80)
        print(f"\n⏱️  Tempo: {tempo_total:.1f}s")
        print(f"📋 Cadernos processados: {len(tarefas)}")

        total_matches = sum(len([m for m in r['matches'] if not m.get('falso_positivo')])
                          for r in resultados_totais)

        print(f"🎯 Matches encontrados: {total_matches}")

        if total_matches > 0:
            print(f"\n✅ OAB {self.oab_alvo} ENCONTRADA! 🎉\n")

            for resultado in resultados_totais:
                matches_reais = [m for m in resultado['matches'] if not m.get('falso_positivo')]

                if matches_reais:
                    print(f"{'─' * 80}")
                    print(f"Tribunal: {resultado['tribunal']} - Meio: {resultado['meio']}")
                    print(f"Matches: {len(matches_reais)}\n")

                    for i, match in enumerate(matches_reais, 1):
                        print(f"  {i}. ID: {match['id']}")
                        print(f"     Tipo: {match['tipo']}")
                        print(f"     Órgão: {match['orgao']}")
                        print(f"     Contexto: {match['contexto'][:150]}...")
                        print()
        else:
            print(f"\n❌ Nenhuma publicação encontrada para OAB {self.oab_alvo} hoje")

        print("=" * 80)


def main():
    """Execução principal"""
    # Configuração
    OAB_ALVO = '129021'
    UF = 'SP'

    # Criar monitor
    monitor = OABMonitor(OAB_ALVO, UF, max_workers=15)

    # Executar monitoramento
    monitor.monitorar_hoje()


if __name__ == '__main__':
    main()
