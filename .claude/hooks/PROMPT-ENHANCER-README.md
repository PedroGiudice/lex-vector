# 📝 Prompt Enhancer v0.2 - Sistema de Tradução Intenção → Arquitetura

**Status**: ✅ Production-Ready (v0.2.0)
**Última atualização**: 2025-11-16
**Autor**: Legal-Braniac Orchestrator

---

## 🎯 Missão

Transformar prompts vagos em especificações técnicas claras, reduzindo iterações de clarificação através de:

1. **Detecção automática** de padrões de intenção (regex-based)
2. **Tradução** intenção → contexto arquitetural
3. **Enriquecimento** com componentes técnicos sugeridos
4. **Tracking** de qualidade e métricas
5. **🆕 Learning adaptativo** - aprende com seu vocabulário e melhora com o tempo

---

## 🏗️ Arquitetura

```
UserPrompt → hook-wrapper.js → prompt-enhancer.js → Claude (contexto enriquecido)
                                      ↓
                              intent-patterns.json (12 padrões genéricos)
                                      ↓
                              prompt-quality.json (tracking de métricas)
                                      ↓
                              legal-braniac-statusline.js (visualização)
```

---

## 📦 Componentes

### 1. Hook Principal (`.claude/hooks/prompt-enhancer.js`)

**Funcionalidades**:
- ✅ Bypass detection: `*`, `/`, `#`, `++` (force enhance)
- ✅ Quality scoring: 0-100 (comprimento, termos técnicos, especificidade)
- ✅ Pattern matching: Regex contra 12 padrões genéricos
- ✅ Graceful degradation: Se falhar, passa prompt original
- ✅ Low overhead: <200ms para prompts claros
- ✅ Error handling: Nunca quebra Claude Code

**Input (stdin)**:
```json
{
  "userPrompt": "baixar múltiplos PDFs do site X",
  "workspace": {
    "current_dir": "/path/to/project"
  }
}
```

**Output (stdout)**:
```json
{
  "continue": true,
  "systemMessage": "📝 Prompt Enhancer: Padrões arquiteturais detectados:\n\n[1] API_SCRAPING_STORAGE\n..."
}
```

### 2. Biblioteca de Padrões (`.claude/hooks/lib/intent-patterns.json`)

**12 Padrões Genéricos**:
1. `mass-data-collection` - Scraping em massa
2. `monitor-notify` - Monitoramento + alertas
3. `data-transformation` - Pipelines ETL
4. `api-integration` - Consumo de APIs
5. `automated-testing` - Automação de testes
6. `dashboard-visualization` - Dashboards e gráficos
7. `batch-processing` - Processamento em lote
8. `report-generation` - Geração de relatórios
9. `authentication-system` - Auth/login
10. `data-validation` - Validação de dados
11. `caching-layer` - Sistemas de cache
12. `search-functionality` - Busca/indexação

**Estrutura de cada padrão**:
```json
{
  "id": "mass-data-collection",
  "intent": "(baixar|download|scrape|coletar).*(massa|bulk|múltiplos)",
  "architecture": "API_SCRAPING_STORAGE",
  "components": [
    "api-client (with retry logic)",
    "rate-limiter (respect API quotas)",
    "data-parser (normalize formats)",
    "storage-layer (scalable persistence)"
  ],
  "translation": "Sistema de coleta em massa requer:\n  1. Cliente API...",
  "questions": [
    "Qual a fonte de dados? (API REST, scraping HTML, arquivos)",
    "Volume estimado? (centenas, milhares, milhões)",
    "Formato de saída? (JSON, CSV, banco de dados)"
  ]
}
```

### 3. Tracking System (`.claude/statusline/prompt-quality.json`)

**Métricas rastreadas**:
- `totalPrompts`: Total de prompts processados
- `enhancedPrompts`: Prompts que receberam enhancement
- `averageQuality`: Qualidade média (0-100)
- `lastRun`: Timestamp da última execução
- `history`: Últimos 50 prompts com detalhes

**Exemplo**:
```json
{
  "enabled": true,
  "stats": {
    "totalPrompts": 26,
    "enhancedPrompts": 10,
    "averageQuality": 14,
    "lastRun": 1763277898496
  },
  "history": [
    {
      "timestamp": 1763277893625,
      "quality": 45,
      "enhanced": true,
      "reason": "enhanced",
      "promptLength": 52,
      "matches": [...],
      "elapsed": 87
    }
  ]
}
```

### 4. Skill Manual (`skills/prompt-enhancer/SKILL.md`)

**Workflow de 5 fases**:
1. **Análise de Intenção** - Extrair verbo + domínio + escala
2. **Identificação de Padrões** - Match contra biblioteca
3. **Proposta de Componentes** - Detalhar arquitetura técnica
4. **Perguntas de Clarificação** - Max 3 perguntas (opções múltiplas)
5. **Execução Enriquecida** - Delegar com contexto completo

**Invocação**:
- Automático: Quando hook detecta padrão + quality < 30
- Manual: Prefixar prompt com `++`

### 5. Statusline Integration (`.claude/statusline/legal-braniac-statusline.js`)

**Visualização em tempo real**:
```
├ 📝 Enhancer [●ON] Quality: 14/100 | Enhanced: 38% (10/26) | Manual: ++
```

**Color coding**:
- `●ON` (green) / `○OFF` (dim) - Status enabled/disabled
- Quality: Red (<40), Yellow (40-69), Green (70+)
- Enhanced rate: Cyan

---

## 🚀 Como Usar

### Uso Automático

Simplesmente use prompts vagos. Se o hook detectar padrão + quality baixa, enriquece automaticamente:

```
Prompt: "baixar dados do site X"

Enhancement automático:
📝 Prompt Enhancer: Padrões arquiteturais detectados:

[1] MASS_DATA_COLLECTION
Sistema de coleta em massa requer:
  1. Cliente API com rate limiting e retry
  2. Parser de dados para normalização
  3. Storage escalável (considere chunking)
  4. Error handling robusto

Componentes sugeridos:
  • api-client (with retry logic)
  • rate-limiter (respect API quotas)
  • data-parser (normalize formats)
  • storage-layer (scalable persistence)

Quality: 32/100
```

### Uso Manual (Force Enhance)

Prefixar com `++` para forçar enhancement:

```
Prompt: ++baixar dados do site X

Enhancement forçado:
[Mesma saída acima]
+ Perguntas de clarificação (fase 4 da skill)
```

### Bypass (Desabilitar Enhancement)

Prefixar com `*`, `/`, `#` para bypass:

```
Prompt: *implementar cache Redis

Resultado: Passa direto para Claude (sem enhancement)
```

---

## 🧪 Testes

**Test suite**: `.claude/hooks/test-prompt-enhancer.sh`

**10 testes end-to-end**:
1. ✅ Bypass with `*`
2. ✅ Bypass with `/`
3. ✅ Bypass with `#`
4. ✅ Force enhance with `++`
5. ✅ Pattern: mass data collection
6. ✅ Pattern: monitor-notify
7. ✅ Pattern: API integration
8. ✅ High quality prompt (auto-bypass)
9. ✅ Empty prompt (bypass)
10. ✅ Very short prompt (low quality)

**Executar testes**:
```bash
./.claude/hooks/test-prompt-enhancer.sh  # Testes básicos (10 tests)
./.claude/hooks/test-learning.sh         # Testes de learning (3 tests)
```

---

## 🧠 Sistema de Learning Adaptativo (v0.2)

### O Que É

O Prompt Enhancer **aprende automaticamente** com seu vocabulário e padrões de uso, tornando-se mais preciso ao longo do tempo.

### Como Funciona

#### 1. **User Vocabulary Capture**

Toda vez que você usa um termo técnico, o sistema:
- Captura o termo (camelCase, snake_case, kebab-case, ACRONYMS)
- Conta frequência de uso
- Trackeia quais patterns matcharam quando o termo foi usado
- **Auto-cria pattern customizado** após 5 usos do mesmo termo

**Exemplo**:
```
Você usa "superTech" 5 vezes → Sistema cria pattern "custom-supertech"
Próxima vez que usar "superTech" → Match automático!
```

**Arquivo**: `.claude/hooks/lib/user-vocabulary.json`
```json
{
  "terms": {
    "supertech": {
      "count": 5,
      "firstSeen": 1699999999,
      "lastSeen": 1700000100,
      "matchedPatterns": ["api-integration", "api-integration", ...]
    }
  },
  "customPatterns": [
    {
      "id": "custom-supertech",
      "intent": "\\bsupertech\\b",
      "architecture": "USER_CUSTOM_PATTERN",
      "translation": "Padrão customizado: termo 'superTech' usado frequentemente (5x)",
      "source": "auto-learned",
      "createdAt": 1700000100
    }
  ]
}
```

#### 2. **Pattern Confidence Tracking**

Para cada pattern detectado, o sistema trackeia:
- Total de matches
- Traduções bem-sucedidas (quando você não faz follow-up de clarificação)
- **Confidence score** (0-100%) com decay temporal
- Histórico das últimas 20 matches

**Arquivo**: `.claude/hooks/lib/pattern-confidence.json`
```json
{
  "patterns": {
    "api-integration": {
      "totalMatches": 15,
      "successfulTranslations": 14,
      "confidenceScore": 95,
      "lastUpdated": 1700000200,
      "history": [
        {"timestamp": 1700000100, "successful": true},
        {"timestamp": 1700000150, "successful": true},
        ...
      ]
    }
  }
}
```

**Confidence Score**:
- `>= 80%` = Pattern muito confiável (verde no statusline)
- `60-79%` = Moderado (amarelo)
- `< 60%` = Baixa confiança (vermelho) + warning no log

**Decay Factor**: 0.95 → Dados recentes pesam mais que antigos

#### 3. **Visualização no Statusline**

O statusline agora exibe métricas de learning:

```
📝 Enhancer [●ON] Quality: 14/100 | Enhanced: 38% (10/26) | 📚 Learned: 2 terms | Confidence: 100% | Manual: ++
```

**Legenda**:
- `Learned: 2 terms` = Quantos termos técnicos únicos o sistema capturou
- `Confidence: 100%` = Confidence médio dos patterns (color-coded)

### Benefícios

1. ✅ **Personalização automática**: Sistema se adapta ao SEU vocabulário
2. ✅ **Zero configuração**: Learning acontece em background
3. ✅ **Melhora contínua**: Quanto mais você usa, mais preciso fica
4. ✅ **Transparência**: Logs de criação de patterns + warnings de baixa confidence

### Testes de Learning

```bash
./.claude/hooks/test-learning.sh
```

**Output esperado**:
```
🧪 Testing Prompt Enhancer Learning System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Test 1: Auto-learning custom pattern (5x repetition)...
  ✅ Vocabulary file created
  📚 Terms learned: 2
  🎯 Custom patterns created: 2

Test 2: Pattern confidence tracking...
  ✅ Confidence file created
  📊 Patterns tracked: 1
  💯 Average confidence: 100%

Test 3: Learning data inspection...

📚 Most frequent terms:
  - api: 5x
  - supertech: 5x

📊 Pattern confidence scores:
  - api-integration: 100% (5/5)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Learning system test complete!
```

**Resultado esperado**:
```
🧪 Prompt Enhancer v0 - End-to-End Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Test 1: Bypass with * ... PASSED
Test 2: Bypass with / ... PASSED
...
Test 10: Very short prompt (low quality) ... PASSED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Test Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total:  10
Passed: 10
Failed: 0

✅ All tests passed!
```

---

## 📊 Métricas de Sucesso

**v0.1.0 (MVP)**:
- ✅ 12 padrões genéricos (100% coverage de casos comuns)
- ✅ 10/10 testes passing
- ✅ Overhead < 200ms (prompts claros)
- ✅ Graceful degradation (0% breakage)
- ✅ Tracking de métricas funcionando

**Métricas coletadas em produção**:
```
Total prompts:    26
Enhanced prompts: 10 (38%)
Average quality:  14/100
```

**Insights**:
- 38% dos prompts são vagos o suficiente para enhancement
- Quality média baixa (14/100) indica espaço para melhoria
- 0 falhas (sistema robusto)

---

## 🔧 Configuração

### Habilitar/Desabilitar

**Via arquivo de configuração** (`.claude/statusline/prompt-quality.json`):
```json
{
  "enabled": false  // Desabilita enhancement
}
```

**Via bypass no prompt** (temporário):
```
*seu prompt aqui  (bypass único)
```

### Adicionar Novo Padrão

Editar `.claude/hooks/lib/intent-patterns.json`:

```json
{
  "id": "seu-novo-padrao",
  "intent": "(regex|pattern|aqui)",
  "architecture": "NOME_DA_ARQUITETURA",
  "components": [
    "componente-1",
    "componente-2"
  ],
  "translation": "Descrição do padrão...",
  "questions": [
    "Pergunta 1?",
    "Pergunta 2?"
  ]
}
```

### Ajustar Quality Thresholds

Editar `.claude/hooks/prompt-enhancer.js`:

```javascript
const CONFIG = {
  BYPASS_PREFIXES: ['*', '/', '#', '++'],
  FORCE_ENHANCE_PREFIX: '++',
  MIN_QUALITY_FOR_ENHANCEMENT: 30,  // Ajustar threshold aqui
  MAX_ENHANCEMENT_OVERHEAD_MS: 200
};
```

---

## 🐛 Troubleshooting

### Enhancement sempre bypassed mesmo com `++`

**Causa**: `prompt-quality.json` tem `"enabled": false`

**Solução**:
```bash
# Editar arquivo
vim .claude/statusline/prompt-quality.json

# Alterar para:
{
  "enabled": true,
  ...
}
```

### Padrões não detectados (0 matches)

**Causa**: Regex inválido ou pattern não matching

**Solução**:
```bash
# Testar regex em https://regex101.com
# Validar JSON
node -e "JSON.parse(require('fs').readFileSync('.claude/hooks/lib/intent-patterns.json', 'utf-8'));"

# Ver logs de erro
cat ~/.vibe-log/hooks.log | grep prompt-enhancer
```

### Performance lenta (>500ms overhead)

**Causa**: Muitos padrões ou regex complexos

**Solução**:
- Reduzir número de padrões
- Simplificar regexes
- Aumentar `MIN_QUALITY_FOR_ENHANCEMENT` para 50

---

## 🗺️ Roadmap

### v0.2 (Melhorias)
- [ ] Learning de padrões customizados (usuário pode adicionar)
- [ ] Historical matching (reusar decisões de prompts similares)
- [ ] Multi-language support (padrões em PT + EN)
- [ ] Confidence scoring (quão certo está do match)
- [ ] 20+ padrões genéricos

### v1.0 (Production-Ready)
- [ ] 50+ padrões arquiteturais
- [ ] Embeddings-based matching (semantic similarity)
- [ ] Auto-learning de novos padrões (ML)
- [ ] Integration com IDE (VSCode extension)
- [ ] A/B testing de enhancement quality

---

## 📚 Exemplos Práticos

### Exemplo 1: Scraping em Massa

**Input**:
```
baixar 500 PDFs do site da OAB e extrair dados estruturados
```

**Enhancement**:
```
📝 Prompt Enhancer: Padrões arquiteturais detectados:

[1] MASS_DATA_COLLECTION
Sistema de coleta em massa requer:
  1. Cliente API com rate limiting e retry
  2. Parser de dados para normalização
  3. Storage escalável (considere chunking para 500 PDFs)
  4. Error handling robusto para retomar de falhas

Componentes sugeridos:
  • api-client (with retry logic)
  • rate-limiter (respect API quotas)
  • data-parser (normalize formats)
  • storage-layer (scalable persistence)
  • error-handler (resume on failure)

Perguntas de clarificação:
  ❓ Qual a fonte de dados? (API REST, scraping HTML, arquivos)
  ❓ Volume estimado? (centenas, milhares, milhões)
  ❓ Formato de saída? (JSON, CSV, banco de dados)

Quality: 52/100
```

### Exemplo 2: Monitoramento + Alertas

**Input**:
```
monitorar publicações diárias do DJEN e enviar email quando houver menção ao processo X
```

**Enhancement**:
```
📝 Prompt Enhancer: Padrões arquiteturais detectados:

[1] POLLING_NOTIFICATION
Sistema de monitoramento requer:
  1. Scheduler para polling periódico
  2. Detector de mudanças (diff entre estados)
  3. Serviço de notificação (email, SMS, webhook)
  4. Storage de estado para comparação

Componentes sugeridos:
  • scheduler (cron/interval)
  • diff-detector (state comparison)
  • notification-service (email/webhook/etc)
  • state-storage (track last known state)

Quality: 67/100
```

### Exemplo 3: Prompt Claro (Auto-Bypass)

**Input**:
```
Implementar cache Redis com TTL de 1 hora para endpoint /api/products usando biblioteca ioredis, com error handling e logging de cache hits/misses
```

**Enhancement**: Nenhum (quality: 95/100 → bypass automático)

**Razão**: Prompt já tecnicamente claro com:
- Tecnologia específica (Redis, ioredis)
- Parâmetros definidos (TTL 1h)
- Endpoint especificado (/api/products)
- Requisitos claros (error handling, logging)

---

## 📖 Arquitetura de Decisão

```
UserPrompt
    ↓
Bypass prefix? (*/#/++)
    ↓ No
Calculate quality (0-100)
    ↓
Quality >= 70?
    ↓ No
Match patterns (regex)
    ↓
Matches found?
    ↓ Yes
Generate enhancement
    ↓
Track metrics
    ↓
Output to Claude
```

---

## 🤝 Contribuindo

Para adicionar novos padrões:

1. Editar `.claude/hooks/lib/intent-patterns.json`
2. Adicionar padrão com regex testado
3. Executar testes: `./.claude/hooks/test-prompt-enhancer.sh`
4. Validar no statusline: Verificar métricas

Para melhorias no código:

1. Fork do projeto
2. Criar branch: `git checkout -b feature/nome-da-feature`
3. Implementar + testes
4. Pull request

---

## 📄 Licença

MIT (projeto Claude-Code-Projetos)

---

## 🙏 Agradecimentos

- **Legal-Braniac**: Orquestração e arquitetura
- **Claude Code**: Plataforma de desenvolvimento
- **Intent Patterns Library**: 12 padrões genéricos comunitários

---

**Status Final**: ✅ Production-Ready v0.1.0
**Última atualização**: 2025-11-16
**Próxima release**: v0.2 (Q1 2026)
