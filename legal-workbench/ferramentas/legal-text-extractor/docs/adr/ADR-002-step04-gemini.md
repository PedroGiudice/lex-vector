# ADR-002: Step 04 com Gemini para Classificação Semântica

**Status:** Aceito
**Data:** 2025-12-10
**Decisores:** PGR (Product Design Director), Claude (Technical Director)

## Contexto

O Step 04 (Bibliotecário) originalmente usava regex e heurísticas para classificar peças processuais (implementação em `step_04_legacy.py`). Embora funcional para padrões explícitos, tinha limitações significativas:

### Problemas da Implementação Regex

1. **Rigidez:** Não identificava peças sem triggers textuais exatos
2. **Falsos Positivos:** "SENTENÇA" em citação era classificado como sentença
3. **Contexto Ignorado:** Não considerava o contexto semântico do documento
4. **Manutenção Difícil:** Cada novo padrão exigia código novo
5. **Edge Cases:** Documentos mal formatados não eram classificados

### Requisitos do Product Design Director

> "Não será aceito nada além de perfeição para esse módulo."

- Classificação precisa de 12 categorias de peças processuais
- Limpeza contextual SEM condensar/resumir
- Implementação completa, sem "melhorias futuras"

## Decisão

Substituir implementação regex por **Gemini 2.5 Flash** para classificação semântica.

### Nova Arquitetura

```
final.md → [GeminiClient] → Classificação → [GeminiClient] → Limpeza → Outputs
                                ↓                                 ↓
                    semantic_structure.json              final_cleaned.md
                                                         final_tagged.md
```

### Componentes Criados

| Componente | Arquivo | Responsabilidade |
|------------|---------|------------------|
| GeminiClient | `src/gemini/client.py` | Wrapper para Gemini CLI |
| Schemas | `src/gemini/schemas.py` | Validação Pydantic de outputs |
| Prompts | `src/gemini/prompts/` | Instruções para classificação/limpeza |
| Bibliotecário | `src/steps/step_04_classify.py` | Orquestrador principal |

### Por que Gemini Flash (não Pro)

| Aspecto | Flash | Pro |
|---------|-------|-----|
| Custo | ~$0.075/1M tokens | ~$1.25/1M tokens |
| Latência | ~1-3s | ~5-10s |
| Qualidade | Suficiente para classificação | Overkill para esta task |
| Context Window | 1M tokens | 2M tokens |

**Conclusão:** Flash é **16x mais barato** e suficiente para classificação com taxonomia bem definida.

## Alternativas Consideradas

### 1. Manter Regex + Expandir Patterns

**Rejeitada porque:**
- Complexidade crescente (75+ patterns existentes)
- Não resolve problema de contexto semântico
- Custo de manutenção alto

### 2. Usar Claude (Anthropic API)

**Rejeitada porque:**
- Custo mais alto que Gemini Flash
- Já usamos Claude para outras tarefas (context competition)
- Gemini tem context window maior (1M vs 200k)

### 3. Fine-tuning de Modelo Local

**Rejeitada porque:**
- Requer dataset de treinamento
- Complexidade de deployment
- Trade-off qualidade/custo desfavorável vs API

## Consequências

### Positivas

- **Precisão:** Entende contexto semântico, não apenas patterns
- **Manutenibilidade:** Ajustar prompt é mais fácil que regex
- **Limpeza Inteligente:** Remove ruído contextualmente
- **Extensibilidade:** Adicionar categorias é trivial
- **Robustez:** Funciona com documentos mal formatados

### Negativas

- **Custo:** ~$0.001-0.01 por documento (vs zero com regex)
- **Latência:** ~5-15s por documento (vs <1s com regex)
- **Dependência Externa:** Requer API Gemini disponível
- **Não-Determinismo:** LLM pode variar marginalmente

### Mitigações

| Risco | Mitigação |
|-------|-----------|
| Custo | Cache de resultados, rate limiting |
| Latência | Processamento batch, async |
| Dependência | Fallback para regex (step_04_legacy.py) |
| Não-Determinismo | Validação Pydantic rigorosa |

## Implementação

### Arquivos Criados

```
src/gemini/
├── __init__.py         # Exports
├── client.py           # GeminiClient wrapper
├── schemas.py          # Pydantic models
└── prompts/
    ├── __init__.py
    ├── classifier.py   # Prompt de classificação (7.5k chars)
    └── cleaner.py      # Prompt de limpeza (3.6k chars)

src/steps/
├── step_04_classify.py # Nova implementação
└── step_04_legacy.py   # Backup (regex)
```

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

# Com modelo Pro
python -m src.steps.step_04_classify -i outputs/doc/final.md -m gemini-2.5-pro
```

## Métricas de Sucesso

| Métrica | Target | Como Medir |
|---------|--------|------------|
| Precisão de classificação | >= 95% | Conjunto de teste anotado |
| Tempo de processamento | < 30s | Benchmark com docs de 100 páginas |
| Redução de ruído | >= 20% | Comparar chars antes/depois |
| Preservação de conteúdo | 100% | Revisão manual de outputs |

## Taxonomia de Peças (12 categorias)

Definida na ADR-001 e implementada em `PecaType`:

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

## Referências

- [ADR-001: Marker-Only Architecture](ADR-001-marker-only-architecture.md)
- [Plano de Implementação](../plans/2025-12-10-step04-gemini-bibliotecario.md)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

*Última atualização: 2025-12-10*
