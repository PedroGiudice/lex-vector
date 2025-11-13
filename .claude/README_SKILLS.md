# SISTEMA DE AUTO-ATIVAÇÃO DE SKILLS

**Status**: ✅ ATIVO
**Skills configuradas**: 34
**Agentes especializados**: 6 (incluindo Legal-Braniac orquestrador)
**Hooks instalados**: UserPromptSubmit + SessionStart

---

## COMO FUNCIONA

### Auto-Ativação de Skills

O sistema usa um **hook UserPromptSubmit** que:
1. Intercepta seu prompt ANTES do Claude processar
2. Analisa keywords e patterns em `skill-rules.json`
3. Injeta skills relevantes no contexto automaticamente
4. Claude recebe sugestão de quais skills usar

**Exemplo**:
```
Você digita: "Preciso auditar o código do parser DJEN"
↓
Hook detecta: "audit" + "code" → skill: code-auditor
↓
Claude recebe contexto: [SYSTEM: Relevant skills: code-auditor (critical)]
↓
Claude usa code-auditor automaticamente
```

### Agentes Especializados

Agentes têm **skills pré-configuradas** e workflows específicos:

```
@legal-braniac → 🧠 ORQUESTRADOR MESTRE (coordena todos os outros agentes)
  ├─ usa TODAS as skills (visão 360°)
  ├─ delega para agentes especializados
  ├─ executa subtarefas em paralelo quando possível
  └─ valida qualidade cross-agente

@planejamento-legal → usa feature-planning, project-bootstrapper
@qualidade-codigo → usa code-auditor, systematic-debugging
@documentacao → usa codebase-documenter, architecture-diagram-creator
@analise-dados-legal → usa dashboard-creator, timeline-creator
@desenvolvimento → usa code-execution, git-pushing
```

**📖 Guia completo do Legal-Braniac**: `.claude/LEGAL_BRANIAC_GUIDE.md`

---

## SKILLS INSTALADAS (34)

### Planejamento (4)
- feature-planning, writing-plans, executing-plans, ship-learn-next

### Qualidade & Testing (6)
- code-auditor, test-fixing, test-driven-development
- systematic-debugging, root-cause-tracing, verification-before-completion

### Documentação (5)
- codebase-documenter, technical-doc-creator
- architecture-diagram-creator, flowchart-creator, timeline-creator

### Visualização (2)
- dashboard-creator, timeline-creator

### Desenvolvimento (7)
- code-execution, code-refactor, code-transfer, file-operations
- project-bootstrapper, review-implementing, git-pushing

### Documentos (4)
- docx, pdf, pptx, xlsx

### Content Extraction (3)
- article-extractor, youtube-transcript, deep-parser

### OCR & Recognition (2)
- ocr-pro, sign-recognition

### Meta (2)
- conversation-analyzer, skill-creator

---

## COMO USAR

### Uso Implícito (Automático)
```
# Apenas faça o pedido naturalmente
"Auditar código do módulo X"  → code-auditor ativado
"Criar diagrama de arquitetura" → architecture-diagram-creator ativado
"Planejar implementação de Y" → feature-planning ativado
```

### Uso Explícito (Manual)
```
# Mencione a skill específica
"USE code-auditor para analisar parser.py"
"USE feature-planning para quebrar esta feature"
```

### Uso com Agentes
```
# Orquestrador (tarefas complexas multi-agente)
@legal-braniac Implementar feature X de ponta a ponta

# Agentes especializados (tarefas de domínio específico)
@planejamento-legal Preciso implementar filtro DJEN
@qualidade-codigo Auditar todo o projeto
@documentacao Criar docs completos
```

---

## CONFIGURAÇÃO

### Arquivos Principais
- `.claude/skills/skill-rules.json` - Regras de ativação
- `.claude/hooks/skill-activation-prompt.ts` - Lógica do hook UserPromptSubmit
- `.claude/hooks/invoke-legal-braniac.js` - Hook SessionStart (orquestrador)
- `.claude/settings.json` - Configuração de hooks
- `.claude/agents/*.md` - Agentes especializados (6)
- `.claude/LEGAL_BRANIAC_GUIDE.md` - Guia completo do orquestrador

### Modificar Trigger Patterns

Edite `.claude/skills/skill-rules.json`:

```json
{
  "skills": {
    "sua-skill": {
      "promptTriggers": {
        "keywords": ["novo", "termo"],
        "intentPatterns": ["(criar|fazer).*?coisa"]
      }
    }
  }
}
```

### Criar Novo Agente

1. Crie `.claude/agents/seu-agente.md`
2. Defina skills obrigatórias
3. Especifique workflow
4. Use: `@seu-agente seu pedido`

---

## TROUBLESHOOTING

### Skills não ativam automaticamente

**Causa**: Hook não está executando
**Debug**:
```bash
# Verificar settings.json
cat .claude/settings.json | grep UserPromptSubmit

# Testar hook manualmente
echo '{"prompt":"audit code"}' | .claude/hooks/skill-activation-prompt.sh
```

### Hook retorna erro

**Causa**: Node.js ou TypeScript não disponível
**Solução**:
```bash
# Instalar Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Instalar dependências
cd .claude/hooks
npm install
```

### Skill detectada mas não usada

**Causa**: Claude ignorou sugestão (enforcement: "suggest")
**Solução**:
- Mude para "warn" ou "block" em skill-rules.json
- OU mencione skill explicitamente no prompt

---

## MANUTENÇÃO

### Adicionar Nova Skill

1. Instalar skill em `skills/`
2. Adicionar entrada em `skill-rules.json`
3. Definir keywords e patterns
4. Testar ativação

### Atualizar Agente

1. Editar `.claude/agents/agente.md`
2. Modificar skills obrigatórias
3. Ajustar workflow
4. Sem necessidade de restart

### Monitorar Uso

```bash
# Ver logs de ativação (se implementado)
tail -f .claude/logs/skill-activation.log
```

---

## PRÓXIMOS PASSOS

- [x] Criar orquestrador Legal-Braniac (✅ DIA 4 - 2025-11-13)
- [x] Implementar auto-discovery de agentes + skills (✅)
- [x] SessionStart hook para invocação automática (✅)
- [ ] Testar Legal-Braniac com tarefas complexas reais
- [ ] Invocar cada agente pelo menos uma vez
- [ ] Ajustar trigger patterns conforme necessário
- [ ] Adicionar logging estruturado de orquestração
- [ ] Criar métricas de performance por agente

## REFERÊNCIAS IMPORTANTES

- **Legal-Braniac Guia Completo**: `.claude/LEGAL_BRANIAC_GUIDE.md`
- **DISASTER_HISTORY**: `../DISASTER_HISTORY.md` (DIA 4 - EPERM loop bug)
- **Corporate Detector**: `.claude/hooks/corporate-detector.js`
- **Diagnóstico Windows**: `../diagnose-corporate-env.ps1`
