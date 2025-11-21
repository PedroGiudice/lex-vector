# Quick Start - Jurisprudência Collector

Começar em 5 minutos.

## 1. Instalação (2 minutos)

```bash
# Ir para agente
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector

# Criar e ativar venv
python3 -m venv .venv
source .venv/bin/activate  # Linux/WSL
# .venv\Scripts\activate   # Windows

# Instalar dependências
pip install -r requirements.txt

# Criar banco
sqlite3 jurisprudencia.db < schema.sql
```

**Verificação:**
```bash
python -c "from src.processador_texto import processar_publicacao; print('✅ OK')"
```

## 2. Primeiro Processamento (2 minutos)

```python
# salvar como teste.py
from src.processador_texto import processar_publicacao

raw_data = {
    'texto': '<p><strong>EMENTA:</strong> Direito Civil...</p>',
    'tipoComunicacao': 'Intimação',
    'siglaTribunal': 'STJ',
    'numeroprocessocommascara': '0001234-56.2024.8.21.0000',
    'data_disponibilizacao': '2025-11-20'
}

pub = processar_publicacao(raw_data)
print(f"✅ Processada: {pub['tipo_publicacao']}")
```

```bash
python teste.py
# ✅ Processada: Acórdão
```

## 3. Processar Dados Reais (1 minuto)

```python
# salvar como processar_djen.py
import requests
from src.processador_texto import processar_publicacao

# Baixar do DJEN
response = requests.get(
    'https://comunicaapi.pje.jus.br/api/v1/comunicacao',
    params={
        'dataInicio': '2025-11-20',
        'dataFim': '2025-11-20',
        'siglaTribunal': 'STJ',
        'limit': 10
    },
    timeout=30
)

items = response.json().get('items', [])
for item in items[:3]:
    pub = processar_publicacao(item)
    print(f"✅ {pub['tribunal']} | {pub['tipo_publicacao']}")
```

```bash
python processar_djen.py
# ✅ STJ | Acórdão
# ✅ STJ | Sentença
# ✅ STJ | Acórdão
```

## 4. Inserir no Banco (Opcional)

```python
import sqlite3
from src.processador_texto import processar_publicacao

# Conectar
conn = sqlite3.connect('jurisprudencia.db')
cursor = conn.cursor()

# Processar e inserir
pub = processar_publicacao(raw_data)

cursor.execute("""
INSERT OR IGNORE INTO publicacoes (
    id, hash_conteudo, numero_processo, numero_processo_fmt,
    tribunal, orgao_julgador, tipo_publicacao, classe_processual,
    texto_html, texto_limpo, ementa, data_publicacao, relator, fonte
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    pub['id'], pub['hash_conteudo'], pub.get('numero_processo'),
    pub.get('numero_processo_fmt'), pub['tribunal'], pub.get('orgao_julgador'),
    pub['tipo_publicacao'], pub.get('classe_processual'),
    pub['texto_html'], pub['texto_limpo'], pub.get('ementa'),
    pub.get('data_publicacao'), pub.get('relator'), pub['fonte']
))

conn.commit()
conn.close()
print("✅ Inserida no banco")
```

## 5. Consultar Banco

```bash
# Estatísticas
sqlite3 jurisprudencia.db "SELECT * FROM v_stats;"

# Últimas publicações
sqlite3 jurisprudencia.db "SELECT numero_processo_fmt, tribunal, tipo_publicacao FROM publicacoes LIMIT 5;"

# Por tribunal
sqlite3 jurisprudencia.db "SELECT * FROM v_publicacoes_por_tribunal;"
```

## Documentação Completa

- **Instalação:** `INSTALACAO.md`
- **Uso Básico:** `USO_BASICO.md`
- **Configuração:** `CONFIGURACAO.md`
- **Troubleshooting:** `TROUBLESHOOTING.md`

## Estrutura

```
├── src/
│   └── processador_texto.py  # Processador principal
├── schema.sql                # Banco de dados
├── requirements.txt          # Dependências
├── test_processador_stj.py   # Testes com API real
└── docs/
    ├── QUICK_START.md        # Este arquivo
    ├── INSTALACAO.md
    ├── USO_BASICO.md
    ├── CONFIGURACAO.md
    └── TROUBLESHOOTING.md
```

## Referências

- Arquitetura: `../../docs/ARQUITETURA_JURISPRUDENCIA.md`
- API Testing: `../../docs/API_TESTING_REPRODUCIBLE.md`

---

**Data:** 2025-11-20
