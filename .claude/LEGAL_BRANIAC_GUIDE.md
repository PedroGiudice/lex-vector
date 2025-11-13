# LEGAL-BRANIAC - GUIA DE USO RÁPIDO 🧠⚖️

**Status**: ✅ ATIVO (auto-invocado no SessionStart do Web)
**Agentes Detectados**: 5 especializados
**Skills Disponíveis**: 34 instaladas
**Última Atualização**: 2025-11-13

---

## O QUE É LEGAL-BRANIAC?

Legal-Braniac é o **orquestrador mestre** do Claude-Code-Projetos. Ele:

- 🎯 **Analisa** tarefas complexas e as decompõe em subtarefas
- 🎭 **Delega** para agentes especializados (analise-dados, documentacao, qualidade-codigo, etc)
- 🔄 **Coordena** execução paralela quando possível
- ✅ **Valida** qualidade cross-agente
- 📦 **Consolida** resultados em entrega unificada

**Princípio**: "A tarefa certa, para o agente certo, no momento certo"

---

## QUANDO USAR

### ✅ USE Legal-Braniac quando:

- Tarefa complexa com múltiplas fases (ex: "implementar feature X de ponta a ponta")
- Precisa coordenar diferentes domínios (planejamento + código + testes + docs)
- Quer execução paralela eficiente de subtarefas independentes
- Precisa de validação cross-agente (ex: código + testes + docs coerentes)
- Tarefa envolve 3+ agentes especializados

### ❌ NÃO USE Legal-Braniac quando:

- Tarefa simples e atômica (ex: "corrigir typo na linha 42")
- Já sabe exatamente qual agente especializado invocar diretamente
- Tarefa puramente exploratória/informacional

---

## COMO INVOCAR

### Invocação Automática (SessionStart - apenas Web)

No **Claude Code Web** (Linux), Legal-Braniac é auto-invocado no início da sessão:

```
[✓] Legal-Braniac detectou 5 agentes + 34 skills
[✓] Pronto para orquestração complexa
```

**Nota**: No **Windows CLI corporativo**, Legal-Braniac é desabilitado automaticamente (EPERM issue conhecida).

### Invocação Manual (qualquer ambiente)

Simplesmente descreva a tarefa complexa:

```
"Implementar filtro de publicações DJEN:
1. Planejar arquitetura
2. Escrever código
3. Adicionar testes
4. Documentar API
5. Auditar qualidade"
```

Legal-Braniac detectará automaticamente a complexidade e orquestrará os agentes.

### Invocação Explícita

Se quiser forçar orquestração:

```
@legal-braniac Coordene a implementação do feature X
```

ou

```
USE legal-braniac para orquestrar esta tarefa complexa
```

---

## AGENTES DISPONÍVEIS (AUTO-DISCOVERY)

Legal-Braniac detecta automaticamente todos os agentes em `.claude/agents/`:

### 1. **planejamento-legal** 📋
- **Quando usar**: Planejar features, quebrar tarefas, definir roadmap
- **Skills**: feature-planning, project-bootstrapper, writing-plans
- **Output**: Task breakdown, dependency graph, estimate

### 2. **desenvolvimento** 💻
- **Quando usar**: Implementar código, refatorar, executar scripts
- **Skills**: code-execution, code-refactor, file-operations, git-pushing
- **Output**: Código funcional, commits, testes passando

### 3. **qualidade-codigo** 🔍
- **Quando usar**: Auditar código, debugar, corrigir bugs
- **Skills**: code-auditor, systematic-debugging, test-driven-development
- **Output**: Audit report, bug fixes, quality score

### 4. **documentacao** 📚
- **Quando usar**: Criar docs técnicos, diagramas, READMEs
- **Skills**: codebase-documenter, architecture-diagram-creator, flowchart-creator
- **Output**: Markdown docs, diagramas, guias

### 5. **analise-dados-legal** 📊
- **Quando usar**: Analisar dados jurídicos, criar dashboards
- **Skills**: dashboard-creator, timeline-creator
- **Output**: Visualizações, métricas, insights

### 6. **legal-braniac** (meta) 🧠
- **Quando usar**: Coordenar tarefas complexas multi-agente
- **Skills**: Todas (visão 360°)
- **Output**: Execução orquestrada + validação cross-agente

---

## WORKFLOW TÍPICO

### Exemplo: "Implementar Feature de Filtro Avançado"

**1. Análise Inicial (Legal-Braniac)**
```
Input: "Implementar filtro avançado de publicações OAB"
↓
Legal-Braniac analisa e decompõe:
- Tarefa 1: Planejamento de arquitetura
- Tarefa 2: Implementação do código
- Tarefa 3: Testes unitários + integração
- Tarefa 4: Documentação de API
- Tarefa 5: Auditoria de qualidade
```

**2. Delegação Paralela (Track 1 + Track 2)**
```
TRACK 1: planejamento-legal → Criar design doc + task breakdown
TRACK 2: documentacao → Preparar template de docs

(Paralelo porque não dependem um do outro)
```

**3. Delegação Sequencial (Track 3)**
```
TRACK 3:
  → desenvolvimento: Implementar código (depende de TRACK 1)
  → desenvolvimento: Escrever testes (depende de código)
  → qualidade-codigo: Auditar implementação (depende de testes)
  → documentacao: Documentar API (depende de código final)
```

**4. Consolidação (Legal-Braniac)**
```
Legal-Braniac valida:
✅ Código implementado e testado
✅ Testes passando (coverage > 80%)
✅ Documentação completa e coerente com código
✅ Auditoria sem issues críticos

Output: Feature completa, commitada, documentada, auditada
```

---

## AUTO-DISCOVERY (SELF-UPDATING)

Legal-Braniac se atualiza automaticamente - **não precisa editar configuração**.

### Como funciona:

1. **Agentes**: Escaneia `.claude/agents/*.md` (exceto legal-braniac.md)
2. **Skills**: Escaneia `skills/*/SKILL.md`
3. **Runtime**: Discovery executa a cada invocação (sempre up-to-date)

### Adicionar Novo Agente:

```bash
# 1. Criar novo agente
cat > .claude/agents/meu-agente.md << 'EOF'
# MEU-AGENTE

**Papel**: Descrição do papel
**Skills**: skill-1, skill-2
...
EOF

# 2. Legal-Braniac detecta automaticamente na próxima invocação
# (não precisa reiniciar ou reconfigurar)
```

### Adicionar Nova Skill:

```bash
# 1. Instalar skill em skills/
mkdir -p skills/minha-skill
cat > skills/minha-skill/SKILL.md << 'EOF'
# Minha Skill
...
EOF

# 2. Legal-Braniac detecta automaticamente
# (auto-discovery runtime)
```

---

## AMBIENTES SUPORTADOS

### ✅ Claude Code Web (Linux)
- **Status**: ✅ TOTALMENTE FUNCIONAL
- **SessionStart hook**: Ativo (auto-invocação)
- **Restrições**: Nenhuma

### ⚠️ Windows CLI (Casa/Pessoal)
- **Status**: ✅ FUNCIONAL (invocação manual)
- **SessionStart hook**: Desabilitado (prevenção de EPERM)
- **Como usar**: Invocação manual via prompt

### ❌ Windows CLI (Corporativo)
- **Status**: ⚠️ DESABILITADO (EPERM loop bug)
- **Motivo**: GPOs corporativas bloqueiam `.claude.json.lock`
- **Workaround**: Use Claude Code Web
- **Bug reportado**: Anthropic ticket aberto

---

## COMANDOS ÚTEIS

### Verificar Agentes Detectados
```bash
# Listar agentes disponíveis
ls -la .claude/agents/*.md

# Ver especialidades
grep "Papel:" .claude/agents/*.md
```

### Verificar Skills Instaladas
```bash
# Listar skills
ls -d skills/*/

# Count total
ls -d skills/*/ | wc -l
```

### Testar Auto-Discovery
```bash
# Executar hook manualmente
node .claude/hooks/invoke-legal-braniac.js
```

### Verificar Configuração SessionStart
```bash
# Ver hooks configurados
cat .claude/settings.json | grep -A 20 SessionStart
```

---

## TROUBLESHOOTING

### Legal-Braniac não está sendo invocado automaticamente

**Diagnóstico**:
```bash
# 1. Verificar ambiente
echo $TERM_PROGRAM  # Deve ser: vscode (Web) ou algo como warp (CLI)

# 2. Verificar settings.json
cat .claude/settings.json | grep invoke-legal-braniac

# 3. Testar hook manualmente
node .claude/hooks/invoke-legal-braniac.js
```

**Soluções comuns**:
- Se Web (Linux): Hook deve estar ativo
- Se Windows CLI: Invocação manual é esperada
- Se Windows CLI corporativo: Use Claude Code Web

### Erro "EPERM: operation not permitted"

**Causa**: Ambiente corporativo Windows com GPO restritivo

**Solução**:
1. Use Claude Code **Web** (Linux) - funciona perfeitamente
2. OU execute `diagnose-corporate-env.ps1` no Windows para diagnóstico completo
3. OU invoque manualmente (sem SessionStart hook)

**Detalhes técnicos**: Ver `DISASTER_HISTORY.md` - DIA 4

### Agente não está sendo detectado

**Diagnóstico**:
```bash
# Verificar arquivo existe
ls -la .claude/agents/meu-agente.md

# Verificar formato
head -20 .claude/agents/meu-agente.md
```

**Requisitos**:
- Arquivo deve estar em `.claude/agents/`
- Extensão deve ser `.md`
- Arquivo deve ter formato válido (header com `# NOME`)

### Skill não está disponível

**Diagnóstico**:
```bash
# Verificar diretório existe
ls -la skills/minha-skill/

# Verificar SKILL.md existe
cat skills/minha-skill/SKILL.md
```

**Requisitos**:
- Diretório em `skills/<nome>/`
- Arquivo `SKILL.md` deve existir no diretório
- Formato deve ser válido

---

## EXEMPLOS PRÁTICOS

### Exemplo 1: Feature Completa de Ponta a Ponta

```
Prompt: "Implementar endpoint /publicacoes/filtrar no DJEN API:
- Aceitar query params (data_inicio, data_fim, keywords)
- Retornar JSON com publicações filtradas
- Adicionar testes
- Documentar no README
- Auditar qualidade do código"

Legal-Braniac:
1. planejamento-legal → Design API (5min)
2. desenvolvimento → Implementar endpoint (15min)
3. desenvolvimento → Escrever testes (10min)
4. documentacao → Atualizar README (5min)
5. qualidade-codigo → Auditar código (5min)

Total: ~40min orquestrado vs ~2h sem orquestração
```

### Exemplo 2: Refatoração Complexa

```
Prompt: "Refatorar módulo parser.py:
- Quebrar função monolítica extract_data() em funções menores
- Adicionar type hints
- Melhorar cobertura de testes (atual: 45% → meta: 80%)
- Atualizar documentação inline
- Validar não quebrou testes existentes"

Legal-Braniac:
TRACK 1 (paralelo):
  → qualidade-codigo: Auditar parser.py atual (identificar pontos de quebra)
  → documentacao: Preparar template de docstrings

TRACK 2 (sequencial):
  → desenvolvimento: Refatorar extract_data() (depende de audit)
  → desenvolvimento: Adicionar type hints (depende de refactor)
  → desenvolvimento: Expandir testes (depende de type hints)
  → qualidade-codigo: Validar cobertura atingida (depende de testes)
  → documentacao: Atualizar docstrings (depende de código final)

Output: Refatoração completa, testada, documentada, validada
```

### Exemplo 3: Debugging Complexo

```
Prompt: "Bug: Parser DJEN trava com publicações > 100 páginas. Debugar e corrigir."

Legal-Braniac:
1. qualidade-codigo → Reproduzir bug (criar minimal test case)
2. qualidade-codigo → Root cause analysis (5 Whys)
3. desenvolvimento → Implementar correção
4. desenvolvimento → Adicionar regression test
5. qualidade-codigo → Validar correção (run full test suite)
6. documentacao → Documentar causa + solução no changelog

Output: Bug corrigido, testado, documentado, prevenido no futuro
```

---

## MÉTRICAS DE PERFORMANCE

Legal-Braniac otimiza execução via:

### Paralelização Inteligente

```
Ganho típico: 40-60% redução de tempo total

Sem orquestração:
  Task A (10min) → Task B (10min) → Task C (10min)
  Total: 30min

Com Legal-Braniac (A e B independentes):
  Task A (10min) ┐
                  ├→ Task C (10min)
  Task B (10min) ┘
  Total: 20min (-33%)
```

### Validação Proativa

```
Previne retrabalho:

Sem orquestração:
  Implementar código (20min)
  → Testes falham (descoberto após 20min)
  → Corrigir (10min)
  Total: 30min

Com Legal-Braniac:
  Planejar + validar approach (5min)
  → Implementar código (20min)
  → Testes passam (validação antecipada)
  Total: 25min (-17%)
```

### Cache de Contexto

```
Reutiliza descobertas entre agentes:

Sem cache:
  Agente 1 lê arquitetura (2min)
  Agente 2 lê arquitetura (2min)
  Agente 3 lê arquitetura (2min)
  Total overhead: 6min

Com Legal-Braniac cache:
  Legal-Braniac lê arquitetura (2min)
  → Compartilha com todos os agentes
  Total overhead: 2min (-67%)
```

---

## ROADMAP

### Em Desenvolvimento
- [ ] Logging estruturado de decisões de orquestração
- [ ] Métricas de performance por agente
- [ ] Dashboard de uso de skills
- [ ] Sugestões proativas de otimização

### Planejado
- [ ] Aprendizado de padrões de delegação (ML-based)
- [ ] Auto-ajuste de paralelização baseado em hardware
- [ ] Integração com CI/CD (GitHub Actions)
- [ ] Plugin de VS Code para invocação visual

---

## REFERÊNCIAS

- **Especificação completa**: `.claude/agents/legal-braniac.md` (566 linhas)
- **Hook de invocação**: `.claude/hooks/invoke-legal-braniac.js` (320+ linhas)
- **Detector corporativo**: `.claude/hooks/corporate-detector.js` (280+ linhas)
- **Histórico de desastres**: `DISASTER_HISTORY.md` (DIA 4 - EPERM loop)
- **Configuração**: `.claude/settings.json`

---

## CONTRIBUINDO

### Relatar Bug

Se encontrar problemas:
1. Executar `diagnose-corporate-env.ps1` (se Windows)
2. Coletar output de `node .claude/hooks/invoke-legal-braniac.js`
3. Abrir issue no repositório

### Melhorar Orquestração

Se identificar padrão de delegação ineficiente:
1. Documentar caso de uso
2. Propor nova estratégia de paralelização
3. Testar com workload real

### Adicionar Agente Especializado

1. Criar `.claude/agents/novo-agente.md`
2. Definir papel, skills, workflow
3. Testar invocação via Legal-Braniac
4. Documentar exemplos de uso

---

**Última atualização**: 2025-11-13
**Versão Legal-Braniac**: 1.0.0
**Compatibilidade**: Claude Code v2.0.31+

**Dúvidas?** Consulte `.claude/agents/legal-braniac.md` para especificação técnica completa.
