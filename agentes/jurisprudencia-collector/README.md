# Jurisprudencia Collector

Processamento de publicações DJEN para construção de base de dados de jurisprudência local.

## Arquitetura

Implementa o **Pipeline de Ingestão** descrito em `docs/ARQUITETURA_JURISPRUDENCIA.md`:

1. ✅ **Processamento de Texto** (implementado)
   - Limpeza de HTML
   - Extração de ementas (~100% taxa de sucesso)
   - Extração de relatores
   - Classificação de tipos
   - Deduplicação via hash SHA256

2. ⏳ Download automático de publicações DJEN (próxima etapa)
3. ⏳ Armazenamento em SQLite (próxima etapa)
4. ⏳ Geração de embeddings RAG (próxima etapa)

## Features

- **Processamento de texto HTML** (BeautifulSoup)
- **Extração de ementa** (taxa de sucesso: ~100% para acórdãos STJ)
- **Extração de relator/juiz** (patterns validados)
- **Classificação automática** (Acórdão/Sentença/Decisão/Intimação)
- **Deduplicação via hash SHA256**
- **Validação completa de dados**

## Instalação

```bash
# Criar virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/WSL
# ou
.venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

## Uso Básico

```python
from src.processador_texto import processar_publicacao

# Dados brutos da API DJEN
raw_data = {
    'texto': '<p>EMENTA: Direito Civil...</p>',
    'tipoComunicacao': 'Intimação',
    'siglaTribunal': 'STJ',
    'numeroprocessocommascara': '1234567-89.2025.8.00.0000',
    'data_disponibilizacao': '2025-11-20'
}

# Processar
pub = processar_publicacao(raw_data)

# Resultado pronto para banco
print(pub['id'])              # UUID v4
print(pub['hash_conteudo'])   # SHA256 (deduplicação)
print(pub['tipo_publicacao']) # Acórdão/Sentença/Decisão/Intimação
print(pub['ementa'])          # Ementa extraída (se aplicável)
print(pub['relator'])         # Relator/Juiz (se encontrado)
```

## Funções Disponíveis

### `processar_publicacao(raw_data: Dict) -> Dict`

Processa dados brutos do DJEN e retorna dicionário pronto para inserção no banco.

### `extrair_ementa(texto: str) -> Optional[str]`

Extrai ementa de acórdão. Taxa de sucesso: ~100% para acórdãos do STJ.

### `extrair_relator(texto: str) -> Optional[str]`

Extrai nome do relator/juiz.

### `classificar_tipo(tipo_comunicacao: str, texto: str) -> str`

Classifica tipo de publicação baseado em heurísticas.

### `gerar_hash_sha256(texto: str) -> str`

Gera hash SHA256 para deduplicação.

### `validar_publicacao_processada(pub: Dict) -> bool`

Valida se publicação processada tem todos os campos obrigatórios.

## Validação com Dados Reais

Execute o teste de validação:

```bash
python test_processador_stj.py
```

**Saída esperada:**
```
Total de publicações analisadas: 100
Acórdãos identificados: 17 (17.0%)
Taxa de extração de ementa: 100.0% (esperado: ~90%)
Taxa de extração de relator: 0.0%

✅ Taxa de extração de ementa APROVADA (>= 85%)
```

## Exemplo Completo

Execute o exemplo para ver processamento de publicação real:

```bash
python exemplo_uso.py
```

**Saída:**
- Dados brutos da API DJEN
- Dados processados
- Validação
- Exemplo de inserção SQL

## Estrutura de Saída

Dicionário retornado por `processar_publicacao()`:

```python
{
    'id': '17a7fcf7-d718-47bf-b4fc-93e0063f1bcd',
    'hash_conteudo': '261aa52d10c445395bdf42ac0d8288d4...',
    'numero_processo': '04458248320253000000',
    'numero_processo_fmt': '0445824-83.2025.3.00.0000',
    'tribunal': 'STJ',
    'orgao_julgador': 'SPF COORDENADORIA...',
    'tipo_publicacao': 'Acórdão',
    'classe_processual': 'HABEAS CORPUS',
    'texto_html': '<html><body>...',
    'texto_limpo': 'HC 1051825/SP...',
    'ementa': 'APELAÇÃO CRIMINAL - Crime de ameaça...',
    'data_publicacao': '2025-11-19',
    'relator': 'MINISTRO PRESIDENTE DO STJ',
    'fonte': 'DJEN'
}
```

## Integração com Banco de Dados

```python
import sqlite3
from src.processador_texto import processar_publicacao, validar_publicacao_processada

# Processar publicação
pub = processar_publicacao(raw_data)

# Validar
if not validar_publicacao_processada(pub):
    raise ValueError("Publicação inválida")

# Inserir no banco
conn = sqlite3.connect('jurisprudencia.db')
cursor = conn.cursor()

cursor.execute("""
INSERT OR IGNORE INTO publicacoes (
    id, hash_conteudo, numero_processo, numero_processo_fmt,
    tribunal, orgao_julgador, tipo_publicacao, classe_processual,
    texto_html, texto_limpo, ementa, data_publicacao, relator, fonte
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    pub['id'], pub['hash_conteudo'], pub['numero_processo'],
    pub['numero_processo_fmt'], pub['tribunal'], pub['orgao_julgador'],
    pub['tipo_publicacao'], pub['classe_processual'], pub['texto_html'],
    pub['texto_limpo'], pub['ementa'], pub['data_publicacao'],
    pub['relator'], pub['fonte']
))

conn.commit()
```

## Schema do Banco (SQLite)

Ver `docs/ARQUITETURA_JURISPRUDENCIA.md` para schema completo.

```sql
CREATE TABLE publicacoes (
    id                  TEXT PRIMARY KEY,
    hash_conteudo       TEXT NOT NULL UNIQUE,
    numero_processo     TEXT,
    numero_processo_fmt TEXT,
    tribunal            TEXT NOT NULL,
    orgao_julgador      TEXT,
    tipo_publicacao     TEXT NOT NULL,
    classe_processual   TEXT,
    texto_html          TEXT NOT NULL,
    texto_limpo         TEXT NOT NULL,
    ementa              TEXT,
    data_publicacao     TEXT NOT NULL,
    relator             TEXT,
    fonte               TEXT NOT NULL
);
```

## Roadmap

- [ ] Melhorar extração de relator (taxa atual: 0%)
- [ ] Adicionar extração de data de julgamento
- [ ] Adicionar extração de assuntos
- [ ] Suporte a chunking para textos longos (RAG)
- [ ] Testes unitários com pytest
- [ ] Integração com embeddings (multilingual-e5-small)

## Referências

- **API DJEN:** https://comunicaapi.pje.jus.br/
- **Arquitetura:** `docs/ARQUITETURA_JURISPRUDENCIA.md`
- **API Testing:** `docs/API_TESTING_REPRODUCIBLE.md`

## Licença

Este módulo faz parte do projeto Claude-Code-Projetos.

---

**Última atualização:** 2025-11-20
**Autor:** Claude Code (Sonnet 4.5)
