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

## Step 04: Bibliotecário com Gemini - IMPLEMENTADO ✅

**Data:** 2025-12-10
**ADR:** [ADR-002](docs/adr/ADR-002-step04-gemini.md)

### BREAKING CHANGE: Regex → Gemini 2.5 Flash

O Step 04 foi **reimplementado** usando Gemini 2.5 Flash para classificação semântica, substituindo a implementação baseada em regex.

```
final.md → [Gemini: Classificação] → [Gemini: Limpeza] → Outputs
                    ↓                        ↓
           semantic_structure.json    final_cleaned.md
                                      final_tagged.md
```

### Comparação: Antes vs Depois

| Aspecto | Antes (regex) | Depois (Gemini) |
|---------|---------------|-----------------|
| Método | Pattern matching | Compreensão semântica |
| Tempo | Instantâneo (<100ms) | ~5-15s por documento |
| Custo | Gratuito | ~$0.001-0.01 por doc |
| Precisão | ~80% | ~95%+ |
| Manutenção | Código novo por padrão | Ajuste de prompt |
| Edge cases | Falha silenciosa | Lida com ambiguidade |

### Nova Arquitetura

```
src/gemini/                    # NOVO - Módulo Gemini
├── __init__.py
├── client.py                  # GeminiClient wrapper
├── schemas.py                 # Pydantic models
└── prompts/
    ├── classifier.py          # Prompt de classificação (7.5k chars)
    └── cleaner.py             # Prompt de limpeza (3.6k chars)

src/steps/
├── step_04_classify.py        # Nova implementação (Gemini)
└── step_04_legacy.py          # Backup (regex)
```

### Taxonomia de 12 Categorias

1. `PETICAO_INICIAL` - Documento que inicia o processo
2. `CONTESTACAO` - Resposta do réu
3. `REPLICA` - Resposta à contestação
4. `DECISAO_JUDICIAL` - Sentenças, acórdãos
5. `DESPACHO` - Determinações procedimentais
6. `RECURSO` - Apelações, agravos, embargos
7. `PARECER_MP` - Pareceres do MP
8. `ATA_TERMO` - Atas de audiência, termos
9. `CERTIDAO` - Certidões, intimações
10. `ANEXOS` - Documentos probatórios
11. `CAPA_DADOS` - Capa e dados de autuação
12. `INDETERMINADO` - Fallback

### Uso

```python
from src.steps.step_04_classify import GeminiBibliotecario

bibliotecario = GeminiBibliotecario()
result = bibliotecario.process(Path("outputs/doc/final.md"))

print(f"Seções: {result['classification'].total_sections}")
print(f"Redução: {result['cleaning'].reduction_percent}%")
```

### CLI

```bash
# Classificação + Limpeza
python -m src.steps.step_04_classify -i outputs/doc/final.md

# Só classificação
python -m src.steps.step_04_classify -i outputs/doc/final.md --skip-cleaning

# Com modelo Pro (mais preciso, mais caro)
python -m src.steps.step_04_classify -i outputs/doc/final.md -m gemini-2.5-pro
```

### Outputs Gerados

1. **`semantic_structure.json`** - Classificação estruturada (sempre)
2. **`final_tagged.md`** - Original com tags semânticas (sempre)
3. **`final_cleaned.md`** - Texto limpo sem ruído (opcional)

### Features

- ✅ Classificação semântica via Gemini 2.5 Flash
- ✅ Limpeza contextual (remove ruído, preserva conteúdo)
- ✅ Validação Pydantic rigorosa
- ✅ CLI compatível com versão anterior
- ✅ 21 testes unitários passando
- ✅ ADR-002 documentando decisão
- ✅ Fallback disponível (step_04_legacy.py)

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

| Decisão | Motivo | ADR |
|---------|--------|-----|
| Marker-only para extração | Simplicidade, qualidade, output leve | [ADR-001](docs/adr/ADR-001-marker-only-architecture.md) |
| **Gemini para classificação** | Precisão semântica superior a regex | [ADR-002](docs/adr/ADR-002-step04-gemini.md) |
| Gemini Flash (não Pro) | 16x mais barato, suficiente para classificação | ADR-002 |
| Output em JSON | Facilita integração com sistemas downstream | - |
| SQLite para Context Store | Zero-config, file-based, ACID compliant | - |
| Pydantic para validação | LLMs podem retornar outputs inesperados | ADR-002 |
| Engine quality ranking | Marker (melhor) > PDFPlumber > Tesseract (pior) | ADR-001 |
| Auto-deprecation | Padrões não confiáveis (3+ falhas) são removidos | - |

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
| Step 04 (Classify) - regex | ~100ms |
| Step 04 (Classify) - **Gemini** | ~5-15s |
| **Total (com Gemini)** | **~6-16s/página** |

### Custo Estimado (Gemini)

| Tamanho Doc | Tokens (aprox) | Custo Flash |
|-------------|----------------|-------------|
| 10 páginas | ~50k tokens | ~$0.004 |
| 50 páginas | ~250k tokens | ~$0.02 |
| 100 páginas | ~500k tokens | ~$0.04 |

---

*Última atualização: 2025-12-10*
