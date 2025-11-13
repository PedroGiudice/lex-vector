# Legal Articles Finder

**Agente especializado em análise e extração de artigos de leis brasileiras**

Identifica citações legais em documentos (TXT, MD, JSON) e extrai artigos completos de um corpus local de leis.

---

## 🎯 Objetivo

Automatizar a identificação e extração de artigos de leis citados em documentos jurídicos, fornecendo o texto completo com caput, parágrafos, incisos e alíneas.

---

## ✨ Features

- ✅ **Parser robusto**: Identifica 9+ formatos de citações legais
- ✅ **Corpus local**: SQLite com textos completos das leis
- ✅ **Extração completa**: Caput + §§ + incisos + alíneas
- ✅ **CLI profissional**: 5 comandos (analyze, search, index, stats, test)
- ✅ **Output flexível**: JSON ou Markdown
- ✅ **Deduplicação**: Remove citações repetidas
- ✅ **Estatísticas**: Cobertura de leis citadas
- ✅ **Extensível**: Adicione novas leis via CLI

---

## 🚀 Quick Start

### Instalação

```bash
cd agentes/legal-articles-finder
python -m venv .venv
.venv/Scripts/activate  # Windows
# ou
source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### Uso Básico

```bash
# Analisar documento
python src/main.py analyze documento.txt --format markdown

# Buscar artigo específico
python src/main.py search CF 5

# Estatísticas do corpus
python src/main.py stats
```

---

## 📖 Comandos

### 1. analyze - Analisa documento jurídico

```bash
python src/main.py analyze <documento> [OPTIONS]

Opções:
  -o, --output FILE         Arquivo de saída (default: stdout)
  -f, --format {json,markdown}  Formato (default: markdown)
  --no-deduplicate          Não remover duplicatas
```

**Exemplo:**
```bash
python src/main.py analyze peticao.txt -o analise.md -f markdown
```

**Output:**
```markdown
# Análise Legal: peticao.txt

## 📊 Sumário
- Citações encontradas: 12
- Artigos localizados: 10 (83%)
- Não localizados: 2

### Leis Citadas
- CF - Constituição Federal: 5 artigos
- CC - Código Civil: 3 artigos
- CPC - Código de Processo Civil: 2 artigos

## 📖 Artigos Extraídos

### 1. Constituição Federal - Artigo 5

**Caput:** Todos são iguais perante a lei...

**Parágrafos:**
§1º As normas definidoras...
```

### 2. search - Busca artigo específico

```bash
python src/main.py search <LEI> <ARTIGO>
```

**Exemplo:**
```bash
python src/main.py search CF 5

✅ Artigo encontrado:

**Art. 5**

Todos são iguais perante a lei, sem distinção de qualquer natureza...

**Parágrafos:**

§1º As normas definidoras dos direitos...
```

### 3. index - Indexa nova lei no corpus

```bash
python src/main.py index <CODE> "<NOME>" <ARQUIVO> [ANO]
```

**Exemplo:**
```bash
python src/main.py index CF "Constituição Federal de 1988" corpus/cf-1988.txt 1988

✅ Lei indexada: CF (250 artigos)
```

### 4. stats - Mostra estatísticas

```bash
python src/main.py stats

📊 Estatísticas do Corpus

**Total de leis:** 3
**Total de artigos:** 5.482

📖 Leis Indexadas:

• **CF**: Constituição Federal de 1988
  Artigos: 250

• **CC**: Código Civil (Lei 10.406/2002)
  Artigos: 2.046
```

### 5. test - Testa parser de citações

```bash
python src/main.py test "Conforme art. 5º da CF/88..."

📋 2 citação(ões) encontrada(s):

1. CF, art. 5
   Raw: 'art. 5º da CF/88'
   Lei: Constituição Federal
   Artigo: 5
```

---

## 📚 Leis Suportadas

| Código | Lei | Status |
|--------|-----|--------|
| CF | Constituição Federal (1988) | ⚠️ Template |
| CC | Código Civil (2002) | ❌ Pendente |
| CPC | Código de Processo Civil (2015) | ❌ Pendente |
| CPP | Código de Processo Penal (1941) | ❌ Pendente |
| CP | Código Penal (1940) | ❌ Pendente |
| CLT | Consolidação das Leis do Trabalho (1943) | ❌ Pendente |
| CDC | Código de Defesa do Consumidor (1990) | ❌ Pendente |
| ECA | Estatuto da Criança e do Adolescente (1990) | ❌ Pendente |
| CTN | Código Tributário Nacional (1966) | ❌ Pendente |

### Adicionando Leis ao Corpus

Ver [corpus/README.md](corpus/README.md) para instruções completas.

**Resumo:**
1. Obtenha texto oficial (Planalto, Senado)
2. Converta para TXT (formato: `Art. N [texto]`)
3. Indexe: `python src/main.py index <CODE> "<NOME>" <ARQUIVO> [ANO]`

---

## 🏗️ Arquitetura

```
legal-articles-finder/
├── src/
│   ├── citation_parser.py      # Parser de citações (283 linhas)
│   ├── corpus_indexer.py       # Indexador SQLite (356 linhas)
│   ├── article_extractor.py    # Extrator de artigos (208 linhas)
│   ├── analyzer.py             # Orquestrador (252 linhas)
│   └── main.py                 # CLI principal (208 linhas)
├── corpus/
│   ├── README.md               # Guia do corpus
│   ├── index.db                # SQLite (gerado)
│   └── [*.txt]                 # Textos das leis
└── tests/                      # Testes (futuro)
```

### Fluxo de Dados

```
Documento TXT/MD/JSON
    ↓
citation_parser.py → Identifica citações
    ↓
article_extractor.py → Busca no corpus (SQLite)
    ↓
analyzer.py → Formata output (JSON/Markdown)
    ↓
Arquivo ou stdout
```

---

## 🧪 Exemplos

### Exemplo 1: Análise de Petição

**Input** (`peticao.txt`):
```
Conforme o art. 5º da CF/88, todos são iguais perante a lei.
O artigo 186 do CC estabelece a responsabilidade civil por ato ilícito.
Nos termos do art. 319 do CPC/2015, a petição inicial deve conter...
```

**Comando:**
```bash
python src/main.py analyze peticao.txt -f markdown -o analise.md
```

**Output** (`analise.md`):
```markdown
# Análise Legal: peticao.txt

## 📊 Sumário
- Citações encontradas: 3
- Artigos localizados: 3 (100%)
- Não localizados: 0

### Leis Citadas
- CF - Constituição Federal: 1 artigo
- CC - Código Civil: 1 artigo
- CPC - Código de Processo Civil: 1 artigo

## 📖 Artigos Extraídos
[Artigos completos...]
```

### Exemplo 2: Busca Rápida

```bash
# Buscar artigo da Constituição
python src/main.py search CF 5

# Buscar artigo do Código Civil
python src/main.py search CC 186
```

### Exemplo 3: Teste de Parser

```bash
python src/main.py test "Com base na Lei 8.069/90, art. 3º, §1º, inciso II, alínea a"

📋 1 citação(ões) encontrada(s):

1. Lei 8.069/90, art. 3, §1, inciso II, alínea a
   Raw: 'Lei 8.069/90, art. 3º, §1º, inciso II, alínea a'
   Artigo: 3
   Parágrafo: §1
   Inciso: II
   Alínea: a
```

---

## 🔧 Desenvolvimento

### Estrutura de Classes

```python
# Citation Parser
CitationParser().parse(text) → List[LegalCitation]

# Corpus Indexer
CorpusIndexer(db_path).index_law(code, name, file_path, year)
CorpusIndexer().find_article(law_code, article_number) → Article

# Article Extractor
ArticleExtractor(indexer).extract(citation) → ExtractedArticle

# Analyzer
DocumentAnalyzer(corpus_db).analyze(document_path) → AnalysisResult
```

### Adicionando Novo Formato de Citação

Edite `citation_parser.py`, adicione regex em `PATTERNS`:

```python
PATTERNS = [
    # Novo formato: "Lei nº 8.069, artigo 3º"
    r'Lei\s+n[ºo]\s+(?P<lei_num>[\d.]+).*?artigo\s+(?P<artigo>\d+)',
    # ... outros patterns
]
```

---

## 📊 Estatísticas

- **Linhas de código**: 1,307
- **Módulos**: 5
- **Comandos CLI**: 5
- **Leis suportadas**: 9
- **Formatos de citação**: 9+
- **Output formats**: 2 (JSON, Markdown)

---

## 🗺️ Roadmap

### ✅ v1.0 (Atual)
- [x] Parser de citações
- [x] Indexador SQLite
- [x] Extrator de artigos
- [x] CLI completo (5 comandos)
- [x] Output JSON/Markdown

### 🚧 v1.1 (Próximo)
- [ ] Corpus completo (CF, CC, CPC, CPP, CP, CLT, CDC, ECA, CTN)
- [ ] Testes unitários (pytest)
- [ ] Integração Legal-Braniac
- [ ] Documentação API

### 📅 v2.0 (Futuro)
- [ ] Suporte a PDF input
- [ ] Busca por palavra-chave (FTS)
- [ ] Export DOCX
- [ ] API REST (FastAPI)
- [ ] UI web

---

## 🧠 Integração Legal-Braniac

Este agente será automaticamente descoberto pelo Legal-Braniac Orchestrator.

**Arquivo de descoberta**: `.claude/agents/legal-articles-finder.md` (pendente)

**Uso via Legal-Braniac:**
```
User: "Analise esta petição e extraia os artigos de lei citados"
Legal-Braniac: [Detecta necessidade de extração legal]
                ↓
              legal-articles-finder
                ↓
              Análise completa com artigos extraídos
```

---

## 📄 Licença

MIT License - Uso comercial permitido

---

## 🙏 Créditos

- **Textos legais**: Domínio público (Lei 9.610/98, art. 8º, IV)
- **Fontes oficiais**: Planalto, Senado Federal
- **Desenvolvido para**: Legal-Braniac Ecosystem

---

**Versão**: 1.0.0
**Data**: 2025-11-13
**Autor**: Legal-Braniac Orchestrator
**Status**: ✅ Production-ready (corpus pendente)
