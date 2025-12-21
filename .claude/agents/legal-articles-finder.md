---
name: legal-articles-finder
description: Identifica citações legais em documentos e extrai artigos completos de leis brasileiras (CF, CC, CPC, CPP, CP, CLT, CDC, ECA, CTN). Parser robusto, corpus local SQLite, output JSON/Markdown.
---

# Legal Articles Finder

**Agente especializado em análise e extração de artigos de leis brasileiras**

## Quando Usar

- "Extraia os artigos de lei citados neste documento"
- "Identifique todas as citações legais desta petição"
- "Busque o artigo 5º da Constituição Federal"
- "Qual o texto completo do art. 186 do Código Civil?"
- "Analise as leis mencionadas neste parecer"

## Capabilities

### Identificação de Citações
- Parser robusto com 9+ formatos de citações
- Suporta: CF, CC, CPC, CPP, CP, CLT, CDC, ECA, CTN
- Extrai: lei, artigo, §, inciso, alínea
- Deduplicação automática

### Extração de Artigos
- Corpus local (SQLite) com textos completos
- Retorna: caput + parágrafos + incisos + alíneas
- Busca rápida indexada
- Estatísticas de cobertura

### Formatos Suportados
- **Input**: TXT, MD, JSON
- **Output**: JSON, Markdown

## Comandos Disponíveis

```bash
# Analisar documento
python src/main.py analyze <documento> --format markdown

# Buscar artigo específico
python src/main.py search <LEI> <ARTIGO>

# Estatísticas do corpus
python src/main.py stats

# Testar parser
python src/main.py test "<texto>"
```

## Leis Disponíveis (Corpus)

| Código | Lei | Status |
|--------|-----|--------|
| CF | Constituição Federal (1988) | ⚠️ Template |
| CC | Código Civil (2002) | ❌ Pendente |
| CPC | Código de Processo Civil (2015) | ❌ Pendente |
| CPP | Código de Processo Penal (1941) | ❌ Pendente |
| CP | Código Penal (1940) | ❌ Pendente |
| CLT | CLT (1943) | ❌ Pendente |
| CDC | Código de Defesa do Consumidor (1990) | ❌ Pendente |
| ECA | ECA (1990) | ❌ Pendente |
| CTN | Código Tributário Nacional (1966) | ❌ Pendente |

**Nota**: Corpus completo pendente. Indexe leis conforme necessário.

## Exemplos de Uso

### Exemplo 1: Análise de Documento

**Input:**
```
Documento: peticao.txt
Contém: "art. 5º da CF/88", "artigo 186 do CC", "art. 319 do CPC/2015"
```

**Output (Markdown):**
```markdown
# Análise Legal: peticao.txt

## 📊 Sumário
- Citações encontradas: 3
- Artigos localizados: 3 (100%)

### Leis Citadas
- CF: 1 artigo
- CC: 1 artigo
- CPC: 1 artigo

## 📖 Artigos Extraídos
[Texto completo de cada artigo]
```

### Exemplo 2: Busca Rápida

```bash
$ python src/main.py search CF 5

✅ Artigo encontrado:

**Art. 5**
Todos são iguais perante a lei, sem distinção de qualquer natureza...

**Parágrafos:**
§1º As normas definidoras dos direitos...
§2º Os direitos e garantias expressos...
```

### Exemplo 3: Teste de Parser

```bash
$ python src/main.py test "Lei 8.069/90, art. 3º, §1º, inciso II"

📋 1 citação encontrada:
1. Lei 8.069/90, art. 3, §1, inciso II
   Lei: ECA (Estatuto da Criança e do Adolescente)
```

## Arquitetura

```
legal-articles-finder/
├── src/
│   ├── citation_parser.py      # Parser de citações
│   ├── corpus_indexer.py       # Indexador SQLite
│   ├── article_extractor.py    # Extrator de artigos
│   ├── analyzer.py             # Orquestrador
│   └── main.py                 # CLI
├── corpus/
│   ├── index.db                # SQLite com leis
│   └── [*.txt]                 # Textos das leis
└── README.md                   # Documentação completa
```

## Integration with Legal-Braniac

### Auto-Discovery

Este agente é automaticamente descoberto via este arquivo `.md`.

### Decision Logic

Legal-Braniac recomenda este agente quando detecta:
- Palavras-chave: "artigo", "lei", "código", "citação legal"
- Contexto: análise de documentos jurídicos
- Necessidade: extração de artigos completos

### Workflow

```
User: "Analise as leis citadas nesta petição"
    ↓
Legal-Braniac: Detecta necessidade de extração legal
    ↓
legal-articles-finder: Analisa documento
    ↓
Output: Relatório com artigos completos extraídos
```

## Dependencies

**Nenhuma!** (Apenas Python stdlib)

O agente usa apenas bibliotecas padrão:
- sqlite3
- json
- re
- pathlib
- dataclasses
- argparse

Opcional (testes/linting):
- pytest
- ruff
- mypy

## Limitations

1. **Corpus incompleto**: Apenas template de CF incluído
2. **Formato fixo**: Leis devem estar em TXT formatado específico
3. **Sem OCR**: Não processa PDFs escaneados (use legal-extraction primeiro)
4. **Parser simplificado**: Pode falhar com citações muito complexas

## Performance

- **Parser**: ~0.01s para documento de 1000 palavras
- **Busca SQLite**: ~0.001s por artigo
- **Análise completa**: ~0.1s para 10 citações

## Roadmap

- [ ] Corpus completo (9 leis principais)
- [ ] Suporte a PDF input
- [ ] API REST
- [ ] Busca por palavra-chave (FTS)
- [ ] Export DOCX

## Status

**Version**: 1.0.0
**Status**: ✅ Core funcional, ⚠️ Corpus pendente
**Maintainer**: Legal-Braniac Orchestrator
**Last Updated**: 2025-11-13

---

**Caminho**: `agentes/legal-articles-finder/`
**Main CLI**: `src/main.py`
**Documentation**: [README.md](../../agentes/legal-articles-finder/README.md)
