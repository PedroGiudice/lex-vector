# Guia de Instalação - Jurisprudência Collector

Guia passo-a-passo para instalar e configurar o sistema de coleta e processamento de jurisprudência do DJEN.

## Requisitos Mínimos

- **Python:** 3.12+ (testado com 3.12.3)
- **Sistema Operacional:** WSL2/Linux (Ubuntu 24.04 LTS recomendado)
- **Espaço em disco:** 2 GB (desenvolvimento), 100+ GB (produção - 1 ano de dados)
- **Conexão de internet:** Para downloads de publicações

## Verificar Versão do Python

```bash
python3 --version
# Expected output: Python 3.12.3 (or higher)
```

Se não tiver Python 3.12+, atualize:

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
```

## Passo 1: Clonar o Repositório

```bash
# Navegar para diretório de trabalho
cd ~/claude-work/repos

# Clonar repositório (se ainda não existir)
git clone https://github.com/PedroGiudice/Claude-Code-Projetos.git
cd Claude-Code-Projetos
```

## Passo 2: Criar Virtual Environment

```bash
# Ir para diretório do agente
cd agentes/jurisprudencia-collector

# Criar venv
python3 -m venv .venv

# Ativar venv (Linux/WSL)
source .venv/bin/activate

# Verificar ativação
which python
# Esperado: /home/[user]/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector/.venv/bin/python
```

Se não usar WSL/Linux, use:

```powershell
# Windows PowerShell
.venv\Scripts\activate
```

## Passo 3: Atualizar pip e Ferramentas

```bash
# Com venv ativado
pip install --upgrade pip setuptools wheel

# Verificar
pip --version
# Esperado: pip 24.0+ (ou superior)
```

## Passo 4: Instalar Dependências

```bash
# Instalar do requirements.txt
pip install -r requirements.txt

# Verificar instalação
pip list
```

**Pacotes instalados:**
- `beautifulsoup4==4.12.2` - Parse de HTML
- `lxml==4.9.3` - Processamento de XML/HTML
- `requests==2.31.0` - Requisições HTTP

Exemplo de saída esperada:

```
beautifulsoup4          4.12.2
lxml                    4.9.3
pip                     24.0
requests                2.31.0
setuptools              68.0.0
wheel                   0.41.0
```

## Passo 5: Validar Instalação

Execute o teste de validação:

```bash
# Com venv ativado
python test_processador_stj.py
```

**Saída esperada (exemplo):**

```
================================================================================
VALIDAÇÃO DO PROCESSADOR DE TEXTO - STJ
================================================================================

Baixando publicações do STJ (2025-11-13 a 2025-11-20)...
Total obtido: 100 publicações

================================================================================
TESTE 1: EXTRAÇÃO DE EMENTA
================================================================================

Total analisado: 17
Sucessos: 17
Falhas: 0
Taxa de sucesso: 100.0%

Exemplos de ementas extraídas (primeiras 3):

1. Processo: 0445824-83.2025.3.00.0000
   Tamanho: 245 caracteres
   Preview: APELAÇÃO CRIMINAL - Crime de ameaça - Lei nº 1.518/97 - [...]

...

================================================================================
RESUMO FINAL
================================================================================

Total de publicações analisadas: 100
Acórdãos identificados: 17 (17.0%)
Taxa de extração de ementa: 100.0% (esperado: ~90%)
Taxa de extração de relator: 0.0%

✅ Taxa de extração de ementa APROVADA (>= 85%)
```

**Possíveis erros e soluções:**

| Erro | Causa | Solução |
|------|-------|---------|
| `ModuleNotFoundError: No module named 'bs4'` | beautifulsoup4 não instalado | Execute `pip install -r requirements.txt` |
| `ModuleNotFoundError: No module named 'requests'` | requests não instalado | Execute `pip install requests` |
| `ConnectionError: Failed to resolve` | Sem acesso à API DJEN | Verificar conexão de internet |
| `TimeoutError` | API lenta/sobrecarregada | Aguardar e tentar novamente |

## Passo 6: Configurar Variáveis de Ambiente (Opcional)

Se quiser customizar caminhos de dados:

```bash
# Criar arquivo .env na raiz do agente
cat > .env << 'EOF'
# Caminhos de dados
CLAUDE_DATA_ROOT=/home/user/claude-work/data
DJEN_CACHE_DIR=/home/user/claude-work/data/agentes/jurisprudencia-collector/cache
DB_PATH=/home/user/claude-work/data/agentes/jurisprudencia-collector/jurisprudencia.db

# Configurações de API
DJEN_API_TIMEOUT=30
DJEN_RETRY_COUNT=3
DJEN_RETRY_DELAY=5

# Logging
LOG_LEVEL=INFO
LOG_FILE=/home/user/claude-work/data/agentes/jurisprudencia-collector/logs/app.log
EOF
```

Depois, no código Python:

```python
import os
from pathlib import Path

# Carregar variáveis
data_root = Path(os.getenv('CLAUDE_DATA_ROOT', '/home/user/claude-work/data'))
db_path = Path(os.getenv('DB_PATH', data_root / 'agentes/jurisprudencia-collector/jurisprudencia.db'))
```

## Passo 7: Criar Banco de Dados Inicial

```bash
# Com venv ativado, na raiz do agente
sqlite3 jurisprudencia.db < schema.sql

# Verificar criação
sqlite3 jurisprudencia.db "SELECT COUNT(*) as tables_created FROM sqlite_master WHERE type='table';"
# Esperado: 8 (publicacoes, embeddings, chunks, downloads_historico, temas, etc)
```

## Passo 8: Testar Processamento de Publicação

```bash
# Ainda na raiz do agente, criar script de teste
cat > teste_basico.py << 'EOF'
from src.processador_texto import processar_publicacao

# Dados brutos de exemplo (simulando resposta da API DJEN)
raw_data = {
    'texto': '''
        <p><strong>EMENTA:</strong> Direito Civil. Responsabilidade Civil.
        Danos morais. Configuração. Precedentes da Corte.</p>
        <p><strong>ACÓRDÃO</strong></p>
        <p>Vistos, relatados e discutidos os autos...</p>
        <p><strong>RELATOR:</strong> Ministro JOÃO SILVA</p>
    ''',
    'tipoComunicacao': 'Intimação',
    'numero_processo': '00012345620248210000',
    'numeroprocessocommascara': '0001234-56.2024.8.21.0000',
    'siglaTribunal': 'STJ',
    'nomeOrgao': '1ª Turma',
    'nomeClasse': 'Apelação',
    'data_disponibilizacao': '2025-11-20'
}

# Processar
pub = processar_publicacao(raw_data)

# Exibir resultado
print("✅ Publicação processada com sucesso!")
print(f"ID: {pub['id']}")
print(f"Tipo: {pub['tipo_publicacao']}")
print(f"Tribunal: {pub['tribunal']}")
print(f"Hash: {pub['hash_conteudo'][:16]}...")
print(f"Ementa encontrada: {'Sim' if pub['ementa'] else 'Não'}")
print(f"Relator: {pub['relator'] or 'Não encontrado'}")
EOF

# Executar
python teste_basico.py
```

**Saída esperada:**

```
✅ Publicação processada com sucesso!
ID: 17a7fcf7-d718-47bf-b4fc-93e0063f1bcd
Tipo: Acórdão
Tribunal: STJ
Hash: 261aa52d10c44539...
Ementa encontrada: Sim
Relator: JOÃO SILVA
```

## Passo 9: Verificar Estrutura de Diretórios

Após instalação, a estrutura deve ser:

```
jurisprudencia-collector/
├── .venv/                    # Virtual environment (ignorado no Git)
├── src/
│   ├── __init__.py
│   ├── processador_texto.py  # Processador principal
│   └── downloader.py         # Downloader (futuro)
├── docs/
│   ├── INSTALACAO.md        # Este arquivo
│   ├── USO_BASICO.md
│   ├── CONFIGURACAO.md
│   └── TROUBLESHOOTING.md
├── schema.sql                # Schema do banco de dados
├── requirements.txt          # Dependências
├── main.py                   # Script principal (futuro)
├── test_processador_stj.py   # Testes com dados reais
└── README.md                 # Overview do projeto
```

## Verificação Final

Execute este checklist para confirmar a instalação:

```bash
# 1. Verificar Python e venv
source .venv/bin/activate
python --version  # 3.12+
which python      # Deve apontar para .venv/bin/python

# 2. Verificar pacotes
pip list | grep -E "beautifulsoup4|lxml|requests"

# 3. Testar import
python -c "from src.processador_texto import processar_publicacao; print('✅ Imports OK')"

# 4. Verificar banco
sqlite3 jurisprudencia.db ".tables"
# Esperado: chunks  chunks_embeddings  downloads_historico  embeddings  publicacoes  publicacoes_fts  publicacoes_temas  temas

# 5. Verificar conexão com API DJEN
python -c "import requests; resp = requests.get('https://comunicaapi.pje.jus.br/api/v1/ping', timeout=5); print(f'✅ API OK: {resp.status_code}')"
```

**Saída esperada de sucesso:**

```
✅ Imports OK
✅ API OK: 200
```

## Troubleshooting de Instalação

Veja `TROUBLESHOOTING.md` para problemas comuns:
- Virtual environment não ativa
- Erros de import
- Banco de dados não criado
- Conexão com API DJEN

## Próximos Passos

Após instalação bem-sucedida:

1. **Uso Básico:** Veja `USO_BASICO.md` para exemplos de uso
2. **Configuração:** Veja `CONFIGURACAO.md` para customizar comportamento
3. **Referências:** Veja `../../docs/ARQUITETURA_JURISPRUDENCIA.md` para arquitetura completa

---

**Data de última atualização:** 2025-11-20
**Testado em:** WSL2 Ubuntu 24.04 LTS com Python 3.12.3
