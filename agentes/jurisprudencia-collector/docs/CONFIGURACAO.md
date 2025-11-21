# Guia de Configuração - Jurisprudência Collector

Opções de customização do comportamento do sistema.

## Configuração via Variáveis de Ambiente

Crie um arquivo `.env` na raiz do agente:

```bash
cat > /home/cmr-auto/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector/.env << 'EOF'
# ============================================================================
# CAMINHOS DE DADOS
# ============================================================================

# Raiz de dados (LAYER 3 - conforme CLAUDE.md)
CLAUDE_DATA_ROOT=/home/cmr-auto/claude-work/data

# Banco de dados
DB_PATH=${CLAUDE_DATA_ROOT}/agentes/jurisprudencia-collector/jurisprudencia.db

# Diretório de cache
DJEN_CACHE_DIR=${CLAUDE_DATA_ROOT}/agentes/jurisprudencia-collector/cache

# Diretório de logs
LOG_DIR=${CLAUDE_DATA_ROOT}/agentes/jurisprudencia-collector/logs

# ============================================================================
# CONFIGURAÇÕES DE API
# ============================================================================

# Timeout para requisições HTTP (segundos)
DJEN_API_TIMEOUT=30

# Número de tentativas em caso de erro
DJEN_RETRY_COUNT=3

# Delay entre tentativas (segundos)
DJEN_RETRY_DELAY=5

# User-Agent para requisições
DJEN_USER_AGENT=JurisprudenciaCollector/1.0

# ============================================================================
# PROCESSAMENTO
# ============================================================================

# Tamanho máximo de ementa (caracteres)
MAX_EMENTA_LENGTH=2000

# Tamanho máximo de relator (caracteres)
MAX_RELATOR_LENGTH=200

# Tamanho máximo de texto limpo (caracteres)
MAX_TEXTO_LIMPO_LENGTH=50000

# ============================================================================
# LOGGING
# ============================================================================

# Nível de log: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Arquivo de log principal
LOG_FILE=${LOG_DIR}/app.log

# Arquivo de log de erros
LOG_ERROR_FILE=${LOG_DIR}/errors.log

# Máximo tamanho do arquivo de log (bytes)
LOG_MAX_SIZE=10485760  # 10 MB

# Número de backups de log
LOG_BACKUP_COUNT=5

# ============================================================================
# SCHEDULER (para futuro - downloads automáticos)
# ============================================================================

# Hora de execução do scheduler (HH:MM)
SCHEDULER_TIME=08:00

# Tribunais prioritários (separados por vírgula)
SCHEDULER_TRIBUNAIS=STJ,STF,TST,TJSP,TJRJ,TJMG,TRF3,TRF4

# ============================================================================
# BANCO DE DADOS
# ============================================================================

# Modo journal (WAL - Write-Ahead Logging ou DELETE)
DB_JOURNAL_MODE=WAL

# Tamanho de cache (bytes, negativo = KB)
DB_CACHE_SIZE=-64000  # 64 MB

# Modo sincronização (OFF, NORMAL, FULL)
DB_SYNCHRONOUS=NORMAL

# ============================================================================
# EMBEDDINGS (para futuro - RAG)
# ============================================================================

# Modelo de embedding
EMBEDDING_MODEL=neuralmind/bert-base-portuguese-cased

# Dimensão do embedding
EMBEDDING_DIM=768

# Tamanho de chunk para textos longos
CHUNK_SIZE=512

# Overlap entre chunks
CHUNK_OVERLAP=50

EOF
```

## Carregar Variáveis no Python

### Option 1: Usar biblioteca `python-dotenv`

```bash
# Instalar
pip install python-dotenv
```

```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar .env
load_dotenv('.env')

# Acessar variáveis
db_path = Path(os.getenv('DB_PATH'))
log_dir = Path(os.getenv('LOG_DIR', 'logs'))
timeout = int(os.getenv('DJEN_API_TIMEOUT', 30))

print(f"Banco: {db_path}")
print(f"Logs: {log_dir}")
print(f"Timeout: {timeout}s")
```

### Option 2: Ler manualmente (sem dependência extra)

```python
import os
from pathlib import Path

def carregar_env():
    """Carrega variáveis do .env."""
    env_path = Path('.env')

    if not env_path.exists():
        print("⚠️ Arquivo .env não encontrado. Usando defaults.")
        return {}

    env_vars = {}
    with open(env_path, 'r') as f:
        for linha in f:
            linha = linha.strip()
            # Ignorar comentários e linhas vazias
            if not linha or linha.startswith('#'):
                continue

            # Parsear KEY=VALUE
            if '=' in linha:
                key, value = linha.split('=', 1)
                env_vars[key.strip()] = value.strip()

    return env_vars

# Usar
env = carregar_env()
db_path = env.get('DB_PATH', 'jurisprudencia.db')
```

## Configuração de Logging

### Exemplo: Configurar Logging Avançado

```python
import logging
import logging.handlers
from pathlib import Path

def configurar_logging(log_level='INFO', log_file='app.log'):
    """Configura logging com rotação de arquivos."""

    # Criar diretório de logs
    log_path = Path(log_file).parent
    log_path.mkdir(parents=True, exist_ok=True)

    # Criar logger
    logger = logging.getLogger('jurisprudencia')
    logger.setLevel(getattr(logging, log_level))

    # Handler para arquivo com rotação
    handler_file = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10485760,  # 10 MB
        backupCount=5
    )

    # Handler para console
    handler_console = logging.StreamHandler()

    # Formato
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    handler_file.setFormatter(formatter)
    handler_console.setFormatter(formatter)

    logger.addHandler(handler_file)
    logger.addHandler(handler_console)

    return logger

# Usar
logger = configurar_logging(log_level='INFO', log_file='logs/app.log')
logger.info("Sistema iniciado")
logger.warning("Aviso teste")
logger.error("Erro teste")
```

**Saída esperada:**

```
2025-11-20 10:30:45 | INFO     | jurisprudencia | Sistema iniciado
2025-11-20 10:30:46 | WARNING  | jurisprudencia | Aviso teste
2025-11-20 10:30:47 | ERROR    | jurisprudencia | Erro teste
```

## Configuração de API DJEN

### Customizar Timeout e Retries

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def criar_sessao_com_retries(
    timeout=30,
    retry_count=3,
    retry_delay=5
):
    """Cria sessão HTTP com retry automático."""

    # Estratégia de retry
    estrategia_retry = Retry(
        total=retry_count,
        backoff_factor=retry_delay,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=['GET']
    )

    # Adapter
    adapter = HTTPAdapter(max_retries=estrategia_retry)

    # Sessão
    session = requests.Session()
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session

# Usar
sessao = criar_sessao_com_retries(timeout=30, retry_count=3, retry_delay=2)

url = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
params = {
    'dataInicio': '2025-11-20',
    'dataFim': '2025-11-20',
    'siglaTribunal': 'STJ',
    'limit': 100
}

try:
    response = sessao.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    print(f"✅ Sucesso: {len(data.get('items', []))} publicações")
except requests.exceptions.RequestException as e:
    print(f"❌ Erro após retries: {e}")
```

## Configuração do Banco de Dados

### Otimizar Performance

```python
import sqlite3

def otimizar_banco(db_path='jurisprudencia.db'):
    """Aplica otimizações ao banco."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Habilitar foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # 2. Usar WAL (Write-Ahead Logging)
    cursor.execute("PRAGMA journal_mode = WAL")

    # 3. Cache de 64 MB
    cursor.execute("PRAGMA cache_size = -64000")

    # 4. Sincronização balanceada
    cursor.execute("PRAGMA synchronous = NORMAL")

    # 5. Operações temp em memória
    cursor.execute("PRAGMA temp_store = MEMORY")

    # 6. Análise para otimizar queries
    cursor.execute("ANALYZE")

    conn.commit()
    conn.close()

    print("✅ Banco otimizado")

# Usar
otimizar_banco('jurisprudencia.db')
```

## Extrair Componentes com Padrões Customizados

### Adicionar Novos Padrões de Ementa

```python
from src.processador_texto import extrair_ementa

# Estender função existente
def extrair_ementa_customizado(texto, patterns_adicionais=None):
    """Extrai ementa com padrões customizados."""

    # Padrões padrão
    patterns = [
        r'EMENTA\s*:\s*(.+?)(?=\n\s*(?:ACÓRDÃO|VOTO)|$)',
        r'EMENTA\s*[-–]\s*(.+?)(?=\n\s*(?:ACÓRDÃO|VOTO)|$)',
    ]

    # Adicionar padrões customizados
    if patterns_adicionais:
        patterns.extend(patterns_adicionais)

    import re
    for pattern in patterns:
        match = re.search(pattern, texto, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()[:2000]

    return None

# Usar com padrões customizados
texto = "SUMÁRIO: Direito Civil..."
padroes_custom = [r'SUMÁRIO\s*:\s*(.+?)(?=\n|$)']
ementa = extrair_ementa_customizado(texto, padroes_custom)
print(f"Ementa encontrada: {ementa}")
```

## Configuração de Filtros de Busca

### Adicionar Filtros Customizados

```python
import sqlite3

def buscar_com_filtros(
    db_path,
    termo,
    tribunal=None,
    tipo_publicacao=None,
    data_inicio=None,
    data_fim=None
):
    """Busca com múltiplos filtros."""

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Construir query dinamicamente
    query = """
    SELECT p.* FROM publicacoes_fts
    JOIN publicacoes p ON publicacoes_fts.rowid = p.rowid
    WHERE publicacoes_fts MATCH ?
    """
    params = [termo]

    # Filtros opcionais
    if tribunal:
        query += " AND p.tribunal = ?"
        params.append(tribunal)

    if tipo_publicacao:
        query += " AND p.tipo_publicacao = ?"
        params.append(tipo_publicacao)

    if data_inicio:
        query += " AND p.data_publicacao >= ?"
        params.append(data_inicio)

    if data_fim:
        query += " AND p.data_publicacao <= ?"
        params.append(data_fim)

    query += " ORDER BY rank LIMIT 20"

    cursor.execute(query, params)
    return cursor.fetchall()

# Usar
resultados = buscar_com_filtros(
    'jurisprudencia.db',
    'responsabilidade civil',
    tribunal='STJ',
    tipo_publicacao='Acórdão',
    data_inicio='2025-11-01',
    data_fim='2025-11-20'
)

print(f"Encontrados: {len(resultados)}")
for row in resultados[:3]:
    print(f"  - {row['numero_processo_fmt']}: {row['tipo_publicacao']}")
```

## Monitoramento e Relatórios

### Gerar Relatório de Downloads

```python
import sqlite3
from datetime import datetime, timedelta

def gerar_relatorio(db_path, dias=7):
    """Gera relatório de downloads dos últimos N dias."""

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Usar VIEW v_downloads_resumo
    cursor.execute("""
    SELECT * FROM v_downloads_resumo
    WHERE date(data) >= date('now', ?)
    """, (f'-{dias} days',))

    print(f"\n📊 RELATÓRIO DE DOWNLOADS (últimos {dias} dias)")
    print("="*100)
    print(f"{'Data':<12} {'Tribunal':<8} {'Tipo':<12} {'Total':<8} {'Novas':<8} {'Duplicatas':<12} {'Sucesso':<8}")
    print("-"*100)

    for row in cursor.fetchall():
        print(
            f"{row['data']:<12} {row['tribunal']:<8} {row['tipo_download']:<12} "
            f"{row['total_publicacoes']:<8} {row['total_novas']:<8} "
            f"{row['total_duplicadas']:<12} {row['sucessos']:<8}"
        )

    conn.close()

# Usar
gerar_relatorio('jurisprudencia.db', dias=7)
```

## Backup e Manutenção

### Script de Backup

```python
import sqlite3
from pathlib import Path
from datetime import datetime

def fazer_backup(db_path='jurisprudencia.db', backup_dir='backups'):
    """Cria backup do banco de dados."""

    # Criar diretório
    Path(backup_dir).mkdir(exist_ok=True)

    # Nome do backup com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{backup_dir}/jurisprudencia_backup_{timestamp}.db"

    # Conectar ao banco original
    conn = sqlite3.connect(db_path)

    # Criar backup
    with sqlite3.connect(backup_path) as backup_conn:
        conn.backup(backup_conn)

    conn.close()

    print(f"✅ Backup criado: {backup_path}")
    return backup_path

# Usar
fazer_backup()
```

### Limpeza de Banco (VACUUM)

```python
import sqlite3

def limpar_banco(db_path='jurisprudencia.db'):
    """Otimiza banco após muitas inserções/deleções."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Limpando banco...")
    cursor.execute("VACUUM")
    cursor.execute("ANALYZE")

    conn.commit()
    conn.close()

    print("✅ Banco limpo e analisado")

# Usar
limpar_banco()
```

## Integração com Variáveis de Ambiente do Sistema

Se quiser usar variáveis do sistema operacional (não recomendado para senhas):

```bash
# Exportar no shell
export DB_PATH=/dados/jurisprudencia.db
export LOG_LEVEL=DEBUG

# Em Python
import os
db_path = os.environ.get('DB_PATH', 'jurisprudencia.db')
log_level = os.environ.get('LOG_LEVEL', 'INFO')
```

## Boas Práticas de Configuração

1. **Nunca commitar .env ao Git**
   ```bash
   # Adicionar ao .gitignore
   echo ".env" >> .gitignore
   echo ".env.local" >> .gitignore
   ```

2. **Criar .env.example para referência**
   ```bash
   # Copiar .env sem valores sensíveis
   cat > .env.example << 'EOF'
   DB_PATH=/path/to/database
   DJEN_API_TIMEOUT=30
   LOG_LEVEL=INFO
   EOF
   ```

3. **Validar variáveis ao inicializar**
   ```python
   from pathlib import Path

   def validar_configuracao():
       db_path = Path(os.getenv('DB_PATH'))
       if not db_path.parent.exists():
           raise ValueError(f"Diretório de dados não existe: {db_path.parent}")
       return True
   ```

4. **Usar valores padrão sensatos**
   ```python
   timeout = int(os.getenv('DJEN_API_TIMEOUT', 30))
   retry_count = int(os.getenv('DJEN_RETRY_COUNT', 3))
   ```

---

**Próximo:** Veja `TROUBLESHOOTING.md` para resolução de problemas.

**Data de última atualização:** 2025-11-20
