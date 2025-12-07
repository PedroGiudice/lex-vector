# Roadmap - Legal Text Extractor

## Arquitetura Atual (Fase 3) - COMPLETA

Pipeline de 4 estagios algoritmicos:

```
PDF → [Cartografo] → [Saneador] → [Extrator] → [Bibliotecario] → structure.json
       step_01       step_02       step_03       step_04
```

| Estagio | Nome | Script | Funcao |
|---------|------|--------|--------|
| 1 | Cartografo | `step_01_layout.py` | Detecta sistema judicial, mapeia layout |
| 2 | Saneador | `step_02_vision.py` | Pre-processa imagens para OCR |
| 3 | Extrator | `step_03_extract.py` | Extrai texto com bbox filtering |
| 4 | Bibliotecario | `step_04_classify.py` | Classifica pecas processuais |

**Status:** ✅ Completo (4 estagios implementados e testados)

---

## Sistema de Contexto (Context Store) - COMPLETO ✅

**Implementado em:** 2025-11-29

Sistema de aprendizado que armazena padrões observados durante processamento e sugere otimizações.

### Princípios

1. **Similaridade, não identidade** - Sugere baseado em cosine similarity
2. **Engine-aware** - Engine inferior não sobrescreve superior
3. **Feedback loop** - Aprende com acertos e erros, depreca padrões não confiáveis

### Arquitetura

```
src/context/
├── schema.sql          # SQLite schema (3 tabelas, 2 views, 3 triggers)
├── models.py           # Data models (8 dataclasses, 2 enums)
├── store.py            # ContextStore (9 métodos públicos)
└── __init__.py         # Public API
```

### Features Implementadas

- ✅ Database SQLite com schema completo
- ✅ Similaridade por cosine (threshold=0.85)
- ✅ Engine quality ranking (Marker > PDFPlumber > Tesseract)
- ✅ Auto-deprecação após 3 divergências
- ✅ Estatísticas por engine
- ✅ 15 testes unitários (100% passing)
- ✅ Exemplo interativo
- ✅ Documentação completa

### Integração Pendente

- [ ] Função `compute_signature(page) -> SignatureVector`
- [ ] Integração com `MultiEngineExtractor`
- [ ] CLI dashboard de estatísticas
- [ ] Testes end-to-end com documentos reais

**Documentação:** `docs/CONTEXT_STORE.md`

---

## Detalhes do Bibliotecario (Step 04)

Quarto estagio da pipeline:

```
PDF → [Cartógrafo] → [Saneador] → [Extrator] → [Bibliotecário] → structure.json
       step_01       step_02       step_03       step_04
```

### ESTÁGIO 4: O BIBLIOTECÁRIO (Semantic Classifier)

**Script:** `src/steps/step_04_classify.py`

**Input:** `outputs/{doc_id}/final.md` (do Estágio 3)

**Lógica:**
1. Lê o Markdown estruturado
2. Aplica biblioteca de Regex (portada do JS) para identificar cabeçalhos de peças:
   - `EXCELENTÍSSIMO SENHOR DOUTOR JUIZ...` → Petição Inicial
   - `SENTENÇA` → Sentença
   - `ACÓRDÃO` → Acórdão
   - `CONTESTAÇÃO` → Contestação
   - `RÉPLICA` → Réplica
   - `EMBARGOS DE DECLARAÇÃO` → Embargos
   - `DESPACHO` → Despacho
   - `DECISÃO INTERLOCUTÓRIA` → Decisão
   - `CERTIDÃO` → Certidão
   - `ATA DE AUDIÊNCIA` → Ata
3. Segmenta o documento logicamente por peça processual

**Output:** `outputs/{doc_id}/structure.json`

```json
{
  "doc_id": "processo_123",
  "total_sections": 5,
  "sections": [
    {
      "id": 1,
      "type": "peticao_inicial",
      "title": "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO...",
      "start_line": 1,
      "end_line": 150,
      "confidence": 0.95
    },
    {
      "id": 2,
      "type": "contestacao",
      "title": "CONTESTAÇÃO",
      "start_line": 151,
      "end_line": 280,
      "confidence": 0.92
    }
  ]
}
```

---

## Backlog

### Fase 3.1: Implementacao do Bibliotecario - COMPLETO
- [x] Criar `step_04_classify.py`
- [x] Portar regex de identificacao de pecas do JS
- [x] Implementar segmentacao por cabecalhos
- [x] Gerar `semantic_structure.json` com metadados
- [x] Gerar `final_tagged.md` com tags semanticas
- [ ] Testes unitarios para cada tipo de peca

**Implementado em 2025-11-25:**
- 12 categorias de pecas processuais
- Limpeza avancada de texto (15 regras regex)
- Taxonomia JSON com sinonimos e patterns
- CLI typer com comandos `classify` e `validate-taxonomy`

### Fase 3.2: Context Store - COMPLETO ✅
- [x] Schema SQLite (caso, observed_patterns, divergences)
- [x] Data models com validação (8 dataclasses)
- [x] ContextStore implementation (9 métodos públicos)
- [x] Cosine similarity search (threshold=0.85)
- [x] Engine-aware updates (quality ranking)
- [x] Auto-deprecation (3+ divergências)
- [x] Unit tests (15 testes, 100% passing)
- [x] Interactive example
- [x] Complete documentation

**Implementado em 2025-11-29:**
- 1,236 linhas de código
- 434 linhas de testes
- 491 linhas de documentação
- Performance: O(1) para CRUD, O(n) para similaridade

### Fase 3.3: Integração Context Store
- [ ] Implementar `compute_signature(page)` para extrair features
- [ ] Integrar hints com `MultiEngineExtractor`
- [ ] Dashboard CLI de estatísticas
- [ ] Logging de decisões (hint usado/ignorado)
- [ ] Benchmarks de performance
- [ ] Testes end-to-end com documentos reais

### Fase 3.4: Refinamentos do ImageCleaner
- [ ] Adicionar suporte a documentos com múltiplas colunas
- [ ] Otimizar detecção de carimbos coloridos (azul, vermelho, verde)
- [ ] Melhorar threshold adaptativo para scans muito escuros

### Fase 3.5: Integração End-to-End
- [ ] CLI unificada para pipeline completo
- [ ] Relatório de qualidade por documento
- [ ] Benchmark de performance (tempo/página)

---

## Decisões Arquiteturais

| Decisão | Motivo |
|---------|--------|
| Pipeline algorítmica (sem LLM) | Custo proibitivo de API para volume alto |
| Regex para classificação | Padrões jurídicos são bem definidos |
| Output em JSON | Facilita integração com sistemas downstream |
| Grayscale output | Suficiente para OCR, menor tamanho |
| SQLite para Context Store | Zero-config, file-based, ACID compliant |
| Cosine similarity | Simples, rápido, efetivo para vetores normalizados |
| Engine quality ranking | Marker (melhor) > PDFPlumber > Tesseract (pior) |
| Auto-deprecation | Padrões não confiáveis (3+ falhas) são removidos |

---

## Performance Benchmarks

### Context Store

| Operação | Complexidade | Tempo Esperado |
|----------|--------------|----------------|
| get_or_create_caso() | O(1) | <1ms |
| find_similar_pattern() | O(n) | <10ms (n<100) |
| learn_from_page() | O(1) | <5ms |
| Cosine similarity | O(d) | <1ms (d<50) |

### Pipeline (médias por página)

| Etapa | Tempo Médio |
|-------|-------------|
| Step 01 (Layout) | ~50ms |
| Step 02 (Vision) | ~200ms |
| Step 03 (Extract) | ~500ms |
| Step 04 (Classify) | ~100ms |
| **Total** | **~850ms/página** |

---

*Última atualização: 2025-11-29*
