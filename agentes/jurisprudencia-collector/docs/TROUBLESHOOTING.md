# Guia de Troubleshooting - Jurisprudência Collector

Solução de problemas comuns durante instalação e uso.

## 1. Problemas de Instalação

### Erro: "Python 3.12+ não encontrado"

**Sintoma:**
```
python3: command not found
# ou
Python 2.7.18 (versão incorreta)
```

**Solução:**

```bash
# Verificar Python instalado
python3 --version
which python3

# Se Python 3.12+ não estiver instalado
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev

# Verificar novamente
python3.12 --version

# Se desejar usar como padrão
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
```

### Erro: "ModuleNotFoundError: No module named 'bs4'"

**Sintoma:**
```
ModuleNotFoundError: No module named 'bs4'
(ou lxml, requests)
```

**Causa:** Dependências não instaladas ou venv não ativado

**Solução:**

```bash
# 1. Verificar se venv está ativado
which python
# Esperado: /path/to/.venv/bin/python (contém .venv)

# 2. Se não estiver, ativar
cd agentes/jurisprudencia-collector
source .venv/bin/activate

# 3. Reinstalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# 4. Verificar instalação
pip list | grep -E "beautifulsoup4|lxml|requests"
```

### Erro: "Permission denied" ao criar venv

**Sintoma:**
```
PermissionError: [Errno 13] Permission denied: '.venv'
```

**Causa:** Permissões de arquivo insuficientes

**Solução:**

```bash
# Verificar permissões
ls -la | grep venv

# Se necessário, ajustar permissões
chmod -R 755 .venv

# Ou remover e recriar
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
```

### Erro: "pip install: externally-managed-environment"

**Sintoma:**
```
error: externally-managed-environment

× This environment is externally managed
```

**Causa:** Tentando instalar pacotes globalmente em Python gerenciado pelo sistema

**Solução:** (Use SEMPRE virtual environment)

```bash
# Estar dentro de venv ativado
source .venv/bin/activate

# Verificar
which pip
# Esperado: /path/to/.venv/bin/pip

# Instalar dentro de venv
pip install -r requirements.txt
```

## 2. Problemas de Processamento

### Erro: "ConnectionError: Failed to connect to API DJEN"

**Sintoma:**
```
requests.exceptions.ConnectionError: HTTPConnectionPool(host='comunicaapi.pje.jus.br', port=443)
```

**Causa:** Problema de conexão com a internet ou servidor DJEN indisponível

**Solução:**

```bash
# 1. Testar conexão de internet
ping google.com

# 2. Testar acesso à API DJEN
curl -s "https://comunicaapi.pje.jus.br/api/v1/ping" | jq

# 3. Se API estiver fora do ar, aguardar ou tentar mais tarde
# 4. Se problema persistir, aumentar timeout
```

**Código com retry automático:**

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def criar_sessao():
    retry = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount('https://', adapter)
    return session

session = criar_sessao()
response = session.get(
    'https://comunicaapi.pje.jus.br/api/v1/comunicacao',
    params={...},
    timeout=30
)
```

### Erro: "TimeoutError" ao baixar publicações

**Sintoma:**
```
requests.exceptions.Timeout: HTTPSConnectionPool read timed out
```

**Causa:** API respondendo lentamente ou timeout configurado é muito curto

**Solução:**

```bash
# 1. Aumentar timeout em variável de ambiente
export DJEN_API_TIMEOUT=60

# 2. Ou especificar no código
response = requests.get(url, params=params, timeout=60)

# 3. Se problema persistir, executar em horário de menor carga
# Recomendado: madrugada (0h-6h) ou tarde (18h-22h)
```

### Erro: "Taxa de sucesso de ementa abaixo de 85%"

**Sintoma:**
```
⚠️ Taxa de extração de ementa ABAIXO DO ESPERADO
(esperado: >= 85%, obtido: 60%)
```

**Causa:** Padrões regex desatualizados para novo formato DJEN

**Verificação:**

```bash
# Executar teste com verbosidade
python test_processador_stj.py 2>&1 | tail -50

# Analisar ementas que falharam
python -c "
import requests
from src.processador_texto import extrair_ementa

# Baixar amostra
response = requests.get(
    'https://comunicaapi.pje.jus.br/api/v1/comunicacao',
    params={
        'dataInicio': '2025-11-20',
        'dataFim': '2025-11-20',
        'siglaTribunal': 'STJ',
        'limit': 10
    }
)

items = response.json().get('items', [])
for item in items[:3]:
    texto = item.get('texto', '')
    ementa = extrair_ementa(texto)
    print(f'Processo: {item.get(\"numeroprocessocommascara\")}')
    print(f'Encontrada: {\"Sim\" if ementa else \"Não\"}')
    print(f'Preview: {texto[:200]}...')
    print('-' * 80)
"
```

**Solução:** Atualizar padrões regex em `src/processador_texto.py`

## 3. Problemas de Banco de Dados

### Erro: "sqlite3.DatabaseError: database disk image is malformed"

**Sintoma:**
```
sqlite3.DatabaseError: database disk image is malformed
```

**Causa:** Banco corrompido (falha ao gravar, disco cheio, etc)

**Solução:**

```bash
# 1. Tentar recuperar integridade
sqlite3 jurisprudencia.db "PRAGMA integrity_check;"
# Resultado: ok ou lista de problemas

# 2. Se danificado, restaurar do backup
ls -la backups/
cp backups/jurisprudencia_backup_20251120_100000.db jurisprudencia.db

# 3. Se não houver backup, recriar do zero
rm jurisprudencia.db
sqlite3 jurisprudencia.db < schema.sql

# 4. Verificar espaço em disco
df -h
# Esperado: > 1 GB livre
```

### Erro: "sqlite3.OperationalError: database is locked"

**Sintoma:**
```
sqlite3.OperationalError: database is locked
```

**Causa:** Múltiplos processos acessando banco simultaneamente

**Solução:**

```bash
# 1. Verificar processos usando banco
lsof | grep jurisprudencia.db

# 2. Encerrar processos conflitantes se necessário
kill -9 <PID>

# 3. Usar WAL mode (mais tolerante a concorrência)
sqlite3 jurisprudencia.db "PRAGMA journal_mode = WAL;"

# 4. Adicionar timeout nas conexões
sqlite3 jurisprudencia.db "PRAGMA busy_timeout = 10000;"  # 10 segundos
```

**Código Python com timeout:**

```python
import sqlite3

conn = sqlite3.connect('jurisprudencia.db', timeout=10.0)
cursor = conn.cursor()
# ... usar normalmente
```

### Erro: "sqlite3.IntegrityError: UNIQUE constraint failed"

**Sintoma:**
```
sqlite3.IntegrityError: UNIQUE constraint failed: publicacoes.hash_conteudo
```

**Causa:** Tentando inserir publicação duplicada (por hash)

**Solução:** Este é o comportamento esperado de deduplicação!

```python
# Usar INSERT OR IGNORE para evitar erro
cursor.execute("""
INSERT OR IGNORE INTO publicacoes (...)
VALUES (...)
""")

# Ou verificar antes de inserir
cursor.execute("SELECT 1 FROM publicacoes WHERE hash_conteudo = ?", (hash,))
if cursor.fetchone():
    print("Publicação já existe")
else:
    cursor.execute("INSERT INTO publicacoes (...) VALUES (...)")
```

### Erro: "No such table: publicacoes"

**Sintoma:**
```
sqlite3.OperationalError: no such table: publicacoes
```

**Causa:** Schema não foi criado

**Solução:**

```bash
# Criar schema
sqlite3 jurisprudencia.db < schema.sql

# Verificar criação
sqlite3 jurisprudencia.db ".tables"
# Esperado: chunks  chunks_embeddings  downloads_historico  embeddings  publicacoes  ...
```

## 4. Problemas de Configuração

### Variável de ambiente não reconhecida

**Sintoma:**
```python
db_path = os.getenv('DB_PATH')
# Resultado: None
```

**Causa:** Variável não definida ou arquivo .env não carregado

**Solução:**

```bash
# 1. Verificar se .env existe
ls -la .env

# 2. Definir manualmente
export DB_PATH=/path/to/database

# 3. Ou usar biblioteca python-dotenv
pip install python-dotenv
```

**Código com fallback:**

```python
import os
from pathlib import Path

db_path = Path(os.getenv('DB_PATH', 'jurisprudencia.db'))

# Criar diretório se não existir
db_path.parent.mkdir(parents=True, exist_ok=True)

print(f"Usando banco em: {db_path}")
```

## 5. Problemas de Memória e Performance

### Erro: "MemoryError: Unable to allocate N bytes"

**Sintoma:**
```
MemoryError: Unable to allocate N bytes
```

**Causa:** Processando arquivo muito grande ou leak de memória

**Solução:**

```bash
# 1. Verificar memória disponível
free -h

# 2. Processar em chunks menores
# Modificar USO_BASICO.md - seção 2.2

# 3. Aumentar limite de memória virtual
ulimit -v unlimited
```

**Código com processamento eficiente:**

```python
def processar_lote_com_limite_memoria(items, batch_size=100):
    """Processa em lotes para economizar memória."""

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]

        processadas = []
        for item in batch:
            pub = processar_publicacao(item)
            processadas.append(pub)

        # Inserir batch
        inserir_lote(db_path, processadas)

        # Limpar memória
        del processadas

        print(f"Processado lote {i//batch_size + 1}")
```

### Banco muito lento para buscas

**Sintoma:**
```
Busca FTS levando > 5 segundos
```

**Causa:** Falta de índices ou muita carga

**Solução:**

```bash
# 1. Executar ANALYZE para atualizar estatísticas
sqlite3 jurisprudencia.db "ANALYZE;"

# 2. Verificar índices existentes
sqlite3 jurisprudencia.db ".indexes"

# 3. Se desejar adicionar índice customizado
sqlite3 jurisprudencia.db "
CREATE INDEX idx_texto_limpo ON publicacoes(texto_limpo)
WHERE texto_limpo IS NOT NULL;
"

# 4. Executar VACUUM se houver muitas deleções
sqlite3 jurisprudencia.db "VACUUM;"
```

## 6. FAQ e Casos Especiais

### P: Como ignorar publicações duplicadas sem erro?

**R:**
```python
# Use INSERT OR IGNORE
cursor.execute("""
INSERT OR IGNORE INTO publicacoes (
    id, hash_conteudo, ...
) VALUES (?, ?, ...)
""")

# Verificar se foi inserida
novas = cursor.rowcount > 0
```

### P: Como restaurar banco de um backup?

**R:**
```bash
# Listar backups
ls -la backups/

# Restaurar (substitui banco atual)
cp backups/jurisprudencia_backup_20251120_100000.db jurisprudencia.db

# Verificar integridade
sqlite3 jurisprudencia.db "PRAGMA integrity_check;"
```

### P: Qual é o tamanho máximo do banco?

**R:**
```bash
# Verificar tamanho atual
du -sh jurisprudencia.db
du -sh jurisprudencia.db-wal  # arquivo WAL (se existir)

# SQLite suporta arquivos até 140 TB teoricamente
# Praticamente limitado a espaço em disco disponível
```

### P: Como deletar publicações antigas?

**R:**
```python
import sqlite3

conn = sqlite3.connect('jurisprudencia.db')
cursor = conn.cursor()

# Deletar publicações anteriores a data X
cursor.execute("""
DELETE FROM publicacoes
WHERE data_publicacao < '2025-01-01'
""")

conn.commit()

# Otimizar banco após deleção
cursor.execute("VACUUM")
cursor.execute("ANALYZE")

conn.close()
```

### P: Posso usar o banco em múltiplas máquinas?

**R:** Não diretamente. SQLite é single-process. Para múltiplas máquinas:
- Use arquivo remoto NFS (lento, não recomendado)
- Sincronize com rsync/git periodicamente
- Considere migrar para PostgreSQL para uso distribuído

### P: Como fazer backup incremental?

**R:**
```bash
#!/bin/bash
# backup_incremental.sh

DATA=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups"

mkdir -p $BACKUP_DIR

# Backup completo (ou usar rsync para incremental)
sqlite3 jurisprudencia.db ".backup $BACKUP_DIR/backup_$DATA.db"

# Manter apenas últimos 7 dias
find $BACKUP_DIR -name "backup_*.db" -mtime +7 -delete

echo "✅ Backup criado: $BACKUP_DIR/backup_$DATA.db"
```

## Relatório de Erro Passo-a-Passo

Se o problema não está listado acima, execute:

```bash
# 1. Coletar informações do sistema
echo "=== SISTEMA ===" > diagnóstico.txt
uname -a >> diagnóstico.txt
python3 --version >> diagnóstico.txt
pip --version >> diagnóstico.txt

# 2. Status do banco
echo "=== BANCO ===" >> diagnóstico.txt
sqlite3 jurisprudencia.db "PRAGMA integrity_check;" >> diagnóstico.txt
du -sh jurisprudencia.db >> diagnóstico.txt

# 3. Logs
echo "=== LOGS ===" >> diagnóstico.txt
tail -100 logs/app.log >> diagnóstico.txt

# 4. Teste de API
echo "=== API DJEN ===" >> diagnóstico.txt
curl -s "https://comunicaapi.pje.jus.br/api/v1/ping" | jq >> diagnóstico.txt

# 5. Verificar pacotes
echo "=== PACOTES ===" >> diagnóstico.txt
pip list >> diagnóstico.txt

# Exibir diagnóstico
cat diagnóstico.txt
```

## Contato e Suporte

Para problemas não resolvidos:

1. Consulte `../../docs/ARQUITETURA_JURISPRUDENCIA.md` para contexto arquitetural
2. Consulte `../../docs/API_TESTING_REPRODUCIBLE.md` para testes de API
3. Abra issue no repositório com arquivo `diagnóstico.txt`

---

**Data de última atualização:** 2025-11-20
**Versão:** 1.0
