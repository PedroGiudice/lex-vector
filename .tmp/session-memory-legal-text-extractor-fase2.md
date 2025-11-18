# Memória de Sessão - Legal Text Extractor Fase 2 (Sistema Auto-Melhorável)

**Data:** 2025-11-18
**Sessão:** Planejamento Fase 2 completa (SDK + Learning + Self-Improvement)
**Status:** Plano criado, aguardando implementação

---

## CONTEXTO DA DISCUSSÃO

### Pergunta Inicial do Usuário

Usuário pediu explicação sobre "Implementar separação de seções (Claude SDK)" da Fase 2. Tinha dúvida sobre:
1. Uso do SDK vs Claude diretamente na conversa
2. Sistema de "aprendizado" contínuo
3. Quantidade de PDFs para testes (30 é muito?)
4. Se sistema pode "aprender" como ML/AI

### Esclarecimentos Realizados

#### 1. SDK vs Claude Direto

**ESCLARECIDO:**
- **Agente = Claude "sandboxed" via API** (usuário entendeu corretamente!)
- **SDK é necessário** para o agente funcionar AUTONOMAMENTE (sem usuário presente)
- **Eu (Claude na conversa)** posso fazer separação em tempo real, mas agente precisa de SDK para funcionar sozinho

**Analogia usada:**
- Sem SDK = Você é chef, eu sou sous-chef (você precisa pedir cada vez)
- Com SDK = Você é chef, agente é robô com IA (funciona sozinho, te liga quando precisa)

**Abordagem híbrida recomendada:**
- **Fase 2A:** Eu (Claude) ajudo a validar e refinar (aprendizado assistido)
- **Fase 2B:** Agente usa SDK autonomamente (produção)

#### 2. Sistema de Aprendizado Contínuo

**SIM, É POSSÍVEL!** Agente PODE ter aprendizado contínuo via:

**Técnica 1: Few-Shot Learning**
```python
# Agente adiciona exemplos de sucesso ao prompt
prompt = f"""
EXEMPLOS DE SUCESSO:
{format_examples(successful_cases)}

Agora analise ESTE documento:
{novo_texto}
"""
```

**Técnica 2: Memória de Padrões Persistente**
```python
# Agente salva padrões aprendidos em JSON
learned_patterns.json → atualizado após cada teste
# Próxima execução carrega padrões anteriores
```

**Técnica 3: Auto-Atualização de Prompts**
```python
# Agente MELHORA SEU PRÓPRIO PROMPT
def _update_prompt_template(self):
    improved_prompt = self.prompt + f"""
    PADRÕES APRENDIDOS (atualizado automaticamente):
    {self.learned_patterns}
    """
    save_file("prompts/current.txt", improved_prompt)
```

**Resultado:** Agente melhora SOZINHO após cada teste! 🎯

#### 3. 30 PDFs para Testes

**RESPOSTA:** É ÓTIMO! Quantidade ideal.

**Estratégia sugerida:**
- **Batch 1:** 10 PDFs (validação básica)
- **Batch 2:** 10 PDFs (refinamento)
- **Batch 3:** 10 PDFs (casos edge)

**NÃO processar tudo de uma vez** - fazer em 3 fases permite:
- Aprendizado incremental
- Ajustes entre batches
- Sistema melhora a cada batch

#### 4. Documentos Anexos (Contratos, Boletos, Prints)

**DESAFIO REAL:** Autos contêm:
- Peças jurídicas estruturadas ✅
- Contratos escaneados ⚠️
- Boletos bancários ⚠️
- Prints de WhatsApp ⚠️
- Planilhas → PDF ⚠️

**SOLUÇÃO:** Sistema de classificação + OCR seletivo
```python
if doc_type == DocumentType.JUDICIAL_PIECE:
    # Processamento completo
elif doc_type == DocumentType.CONTRACT:
    # OCR + extração de cláusulas
elif doc_type == DocumentType.INVOICE:
    # OCR + dados estruturados
elif doc_type == DocumentType.SCREENSHOT:
    # OCR básico, baixa prioridade
elif doc_type == DocumentType.IRRELEVANT:
    # Pular, apenas registrar
```

---

## DECISÃO FINAL DO USUÁRIO

**"Implementar sistema COMPLETO agora (SDK + Learning + Auto-improvement)"**

**Justificativa:**
- Testar sistema REAL desde o início
- Few-shot learning começa imediatamente
- Economia de tempo (uma rodada de testes)
- Ajustes conforme necessário durante desenvolvimento

---

## PLANO COMPLETO CRIADO

### Arquitetura (3 Camadas)

```
LAYER 1: Section Separation (Claude SDK)
  ├─ Identifica seções via prompt engineering
  ├─ Retorna JSON estruturado
  └─ Confidence scoring

LAYER 2: Learning System
  ├─ Extrai padrões de casos de sucesso
  ├─ Gerencia exemplos few-shot
  └─ Calcula métricas (precision/recall/F1)

LAYER 3: Self-Improvement
  ├─ Atualiza prompts automaticamente
  ├─ Versiona mudanças
  └─ A/B testing de prompts
```

### Nova Estrutura de Diretórios

```
agentes/legal-text-extractor/
├── src/
│   ├── learning/              # NOVO
│   │   ├── pattern_learner.py
│   │   ├── few_shot_manager.py
│   │   ├── metrics_tracker.py
│   │   └── self_improver.py
│   ├── memory/                # NOVO
│   │   ├── storage.py
│   │   └── schemas.py
│   ├── prompts/               # NOVO
│   │   ├── base_prompts.py
│   │   ├── prompt_versioning.py
│   │   └── prompt_registry.py
│   └── analyzers/
│       └── section_analyzer.py  # ATUALIZAR (adicionar SDK)
│
├── data/                      # NOVO (não versionado)
│   ├── learning/
│   │   ├── learned_patterns.json
│   │   ├── few_shot_examples.json
│   │   ├── metrics_history.json
│   │   └── ground_truth/
│   ├── prompts/
│   │   ├── prompt_v1.yaml
│   │   └── changelog.md
│   └── checkpoints/
│
├── scripts/                   # NOVO
│   ├── batch_test.py
│   ├── validate_results.py
│   └── export_report.py
│
└── test-documents/
    ├── batch_001/  (10 PDFs)
    ├── batch_002/  (10 PDFs)
    └── batch_003/  (10 PDFs)
```

### 4 Milestones

#### **Milestone 1: SDK Integration (6-8h)**
**Tarefas:**
1. Setup API client com rate limiting (30min)
2. Criar prompt base para separação (1h)
3. Parser JSON response (45min)
4. Extração de seções baseada em marcadores (1h)
5. Tratamento de edge cases (30min)

**Entrega:** Separação de seções funcionando com Claude API

#### **Milestone 2: Learning System (8-10h)**
**Tarefas:**
1. Criar schemas Pydantic (45min)
2. Implementar storage JSON (1h)
3. Pattern extraction logic (2h)
4. Few-shot manager (1.5h)
5. Metrics tracker (precision/recall/F1) (1.5h)

**Entrega:** Sistema que aprende com cada teste

#### **Milestone 3: Self-Improvement (6-8h)**
**Tarefas:**
1. Sistema de versionamento de prompts (1h)
2. Self-improver logic (2h)
3. A/B testing de prompts (1.5h)

**Entrega:** Agente que atualiza próprios prompts automaticamente

#### **Milestone 4: End-to-End Testing (10-12h)**
**Tarefas:**
1. Interface de validação (2h)
2. Batch testing script (1.5h)
3. Report generation (1h)
4. Processar e validar 30 PDFs (6-7h)

**Entrega:** Sistema validado em 30 PDFs reais

### Cronograma Total

**30-38 horas** distribuídas em 1-2 semanas:
- Dia 1-2: Milestone 1 (SDK)
- Dia 3-4: Milestone 2 (Learning)
- Dia 5: Milestone 3 (Self-Improvement)
- Dia 6-10: Milestone 4 (Testing com 30 PDFs)

---

## FLUXO DE APRENDIZADO DURANTE TESTES

```
PDF 1:
  ↓ Processa → Você valida → Sistema aprende
  ↓ Extrai padrão: "SENTENÇA começa com 'Vistos, relatados...'"
  ↓ Adiciona exemplo ao few-shot
  ↓ Salva em learned_patterns.json

PDF 2:
  ↓ Carrega conhecimento de PDF 1
  ↓ Processa com prompt MELHORADO
  ↓ Você valida → Aprende mais
  ↓ Atualiza padrões

PDF 10:
  ↓ Processa com conhecimento de 9 PDFs
  ↓ Métricas calculadas: F1 < 0.85 (baixa!)
  ↓ Sistema DECIDE: "Preciso melhorar!"
  ↓ ATUALIZA PROMPT AUTOMATICAMENTE
  ↓ prompt_v1.yaml → prompt_v2.yaml
  ↓ Adiciona mais exemplos few-shot

PDF 11-30:
  ↓ Usa prompt v2 (melhorado)
  ↓ Performance MELHORA continuamente
  ↓ Sistema aprende padrões de todos os 30 PDFs

RESULTADO FINAL:
  ✅ 20+ padrões aprendidos
  ✅ Prompts auto-atualizados 2-3 vezes
  ✅ Acurácia >90% em seções conhecidas
  ✅ Sistema pronto para produção
```

---

## DECISÕES TÉCNICAS IMPORTANTES

### 1. JSON Storage vs Database
**Escolhido:** JSON files
**Justificativa:**
- Volume baixo (<100 docs inicialmente)
- Simplicidade de debug
- Portabilidade (não requer servidor)
- Git-friendly

### 2. Few-Shot Learning vs Fine-Tuning
**Escolhido:** Few-shot prompting
**Justificativa:**
- Custo: $0 extra (fine-tuning = $$$)
- Flexibilidade: atualização instantânea
- Claude Sonnet 3.5 já excelente com few-shot

### 3. Interactive Validation vs Automated
**Escolhido:** Interactive (manual)
**Justificativa:**
- Fase inicial requer ground truth humano
- 30 PDFs = 3-5h validação (aceitável)
- Qualidade > quantidade

### 4. Prompt Auto-Update Threshold
**Escolhido:** F1 < 0.85 OU 10+ novos exemplos
**Justificativa:**
- Balance estabilidade vs melhoria
- 0.85 = "bom mas não ótimo"

### 5. Por Que SDK É Necessário
**Resposta Técnica:**

O agente PRECISA do SDK para chamar Claude API autonomamente:
```python
from anthropic import Anthropic

client = Anthropic(api_key=...)
response = client.messages.create(...)
```

**Sem SDK:** Agente não consegue "me ligar" (Claude API) para análise.

**Complexidade:** Apenas 5 linhas de código! Não é complexo.

---

## ESTIMATIVA DE CUSTO

**Claude API (Sonnet 3.5):**
- Input: $3/million tokens
- Output: $15/million tokens

**Para 30 PDFs:**
- 30 × 5k tokens input × $0.003 = $0.45
- 30 × 1k tokens output × $0.015 = $0.45
- **Total: ~$0.90**

---

## RISCOS E MITIGAÇÕES

### Risco 1: Token Limits
**Problema:** Documentos >30k chars estouram limite
**Mitigação:** Dividir em chunks, processar separadamente, merge results

### Risco 2: Documentos Sem Estrutura Clara
**Problema:** PDFs antigos, mal formatados
**Mitigação:** Fallback para regex heuristics, confidence score baixo → revisão manual

### Risco 3: Performance vs Custo
**Problema:** Múltiplas chamadas API = custo
**Mitigação:** Cache de resultados (hash do texto)

### Risco 4: Overfitting
**Problema:** Sistema memoriza em vez de generalizar
**Mitigação:** Limitar exemplos (max 10/tipo), rotacionar antigos

### Risco 5: Prompts Degradam
**Problema:** Auto-update piora performance
**Mitigação:** Versionamento obrigatório, A/B testing, rollback fácil

---

## COMPONENTES PRINCIPAIS A IMPLEMENTAR

### 1. Pattern Learner
```python
class PatternLearner:
    """Extrai padrões de documentos validados"""

    def extract_patterns(self, validated_docs) -> list[Pattern]:
        # Analisa documentos validados
        # Identifica marcadores comuns
        # Retorna padrões estruturais
```

### 2. Few-Shot Manager
```python
class FewShotManager:
    """Gerencia biblioteca de exemplos"""

    def add_example(self, doc, quality_score):
        # Adiciona exemplo de qualidade

    def get_examples(self, section_type, n=3):
        # Retorna N melhores exemplos

    def export_for_prompt(self, section_types):
        # Formata para injeção no prompt
```

### 3. Metrics Tracker
```python
class MetricsTracker:
    """Calcula precision, recall, F1"""

    def calculate(self, predictions, ground_truth):
        # Calcula métricas
        # Retorna Metrics object

    def get_trend(self, metric_name, last_n_batches):
        # Retorna tendência (improving/declining/stable)
```

### 4. Self-Improver
```python
class SelfImprover:
    """Auto-melhoria de prompts"""

    def should_update_prompt(self, metrics):
        # Decide se deve atualizar
        # Retorna {should_update, reason, strategy}

    def generate_new_prompt(self, current_metrics):
        # Gera nova versão do prompt
        # Versiona automaticamente
```

### 5. Section Analyzer (ATUALIZADO)
```python
class SectionAnalyzer:
    """Analisa e separa seções (COM SDK)"""

    def __init__(self):
        self.client = Anthropic(api_key=...)

    def analyze(self, text, use_claude=True):
        # Carrega prompt atual
        # Injeta few-shot examples
        # Chama Claude API
        # Parse JSON response
        # Extrai seções
        # Retorna list[Section]
```

---

## WORKFLOW TÍPICO (APÓS IMPLEMENTAÇÃO)

### Processar Batch de PDFs

```bash
# 1. Adicionar PDFs
cp /caminho/*.pdf test-documents/batch_001/

# 2. Processar batch
python scripts/batch_test.py --batch-dir test-documents/batch_001 --batch-id batch_001

# 3. Validar cada documento
python scripts/validate_results.py doc001 data/batches/batch_001/doc001_result.json data/batches/batch_001/doc001_text.txt

# 4. Analisar batch (aprendizado automático)
python scripts/batch_test.py --analyze-batch batch_001

# 5. Gerar relatório
python scripts/export_report.py

# Sistema atualiza prompt automaticamente se necessário!
```

---

## PRÓXIMO PASSO IMEDIATO

**Quando retomar, começar por:**

**MILESTONE 1 - TASK 1.1: Rate Limiting (30min)**

Implementar em `src/analyzers/section_analyzer.py`:
```python
class SectionAnalyzer:
    def __init__(self, max_retries=3, retry_delay=2.0):
        self.client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _call_claude_with_retry(self, prompt: str) -> str:
        """Chama Claude com retry logic"""
        for attempt in range(self.max_retries):
            try:
                message = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text
            except RateLimitError:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise
```

---

## COMANDOS ÚTEIS

### Setup
```bash
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/legal-text-extractor
source .venv/bin/activate

# Criar estrutura
mkdir -p src/{learning,memory,prompts} data/{learning/ground_truth,prompts,checkpoints} scripts

# Instalar extras
pip install matplotlib tqdm pyyaml

# API key
export ANTHROPIC_API_KEY="sk-..."
```

### Debug
```bash
# Ver padrões aprendidos
cat data/learning/learned_patterns.json | jq

# Ver métricas
cat data/learning/metrics_history.json | jq '.[] | {batch: .batch_id, f1: .f1_score}'

# Ver changelog de prompts
cat data/prompts/changelog.md
```

---

## PERGUNTAS DO USUÁRIO (RESPONDIDAS)

1. ✅ **SDK vs Claude direto?** - SDK necessário para autonomia, mas abordagem híbrida recomendada
2. ✅ **Sistema aprende?** - SIM! Via few-shot + memória persistente + auto-update de prompts
3. ✅ **30 PDFs é muito?** - NÃO! É quantidade ideal (dividir em 3 batches de 10)
4. ✅ **Implementar tudo agora?** - SIM! Sistema completo desde o início

---

## STATUS ATUAL

- ✅ Fase 1 completa (extração + limpeza)
- ✅ Plano Fase 2 criado (2300+ linhas)
- ⏸️ Aguardando início da implementação
- 📋 Próximo: Milestone 1 - Task 1.1 (Rate Limiting)

---

**Data:** 2025-11-18
**Contexto salvo para:** Retomada em nova conversa
**Comando para retomar:** "Vamos continuar a implementação do legal-text-extractor Fase 2. Leia a memória de sessão."
