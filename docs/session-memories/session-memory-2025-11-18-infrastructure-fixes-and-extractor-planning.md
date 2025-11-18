# Memória de Sessão - Infrastructure Fixes + Legal-Text-Extractor Planning

**Data:** 2025-11-18
**Sessão:** Troubleshooting git/memory/vibe-log + Planning legal-text-extractor Fase 2
**Duração:** ~2h
**Contexto:** Sessão de continuação que desviou para fixes de infraestrutura
**Resultado:** ✅ Infraestrutura corrigida, plano Fase 2 documentado (não implementado)

---

## Resumo Executivo

Sessão iniciou com intenção de implementar legal-text-extractor Fase 2 (SDK + Learning + Auto-improvement), mas desviou completamente para troubleshooting de infraestrutura. Fixes críticos aplicados:

1. ✅ `.claude/settings.local.json` removido do Git (causa de merge conflicts recorrentes)
2. ✅ Sistema de memória explicado (100% manual, sem hooks automáticos)
3. ✅ Decisão: NÃO implementar auto-inject (manter sistema manual)
4. ✅ Vibe-log authentication corrigida pelo usuário
5. ⏳ Investigação statusline integration em andamento

**STATUS CRÍTICO:** Plano completo de legal-text-extractor Fase 2 existe em `docs/session-memories/session-memory-2025-11-18-legal-text-extractor-fase2.md` mas NENHUM CÓDIGO FOI IMPLEMENTADO.

---

## Legal-Text-Extractor Fase 2: Plano Completo (NÃO IMPLEMENTADO)

### Decisão Arquitetural

**User quote:**
> "se formos, de fato, usar SDK, talvez seja melhor implementar isso JÁ e fazer os testes com o agente COMPLETO"

**Decisão:** Implementar sistema completo (SDK + Learning + Auto-improvement) em vez de incremental.

### Arquitetura Planejada (3 Camadas)

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: PDF Processing (Existing)                         │
│ - pytesseract OCR                                           │
│ - pdf2image conversion                                      │
│ - Text extraction                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: Claude SDK Integration (NEW - Milestone 1)        │
│ - API Client (anthropic SDK)                                │
│ - Rate limiting (20 req/min)                                │
│ - Prompt engineering for section separation                 │
│ - JSON response parsing                                     │
│ - Error handling + retries                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: Learning System (NEW - Milestone 2)               │
│ - Pattern extraction from successful PDFs                   │
│ - Few-shot example storage (SQLite)                         │
│ - Metrics tracking (accuracy, confidence)                   │
│ - Feedback collection                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 4: Self-Improvement (NEW - Milestone 3)              │
│ - Prompt versioning system                                  │
│ - A/B testing (old vs improved prompts)                     │
│ - Automatic prompt updates based on success rate           │
│ - Rollback mechanism                                        │
└─────────────────────────────────────────────────────────────┘
```

### Milestones e Timeline

#### Milestone 1: SDK Integration (6-8h) ❌ NOT STARTED

**Files to Create/Modify:**
- `agentes/legal-text-extractor/claude_extractor.py` (NEW - 200-250 lines)
- `agentes/legal-text-extractor/prompts/section_separator.txt` (NEW - prompt template)
- `agentes/legal-text-extractor/requirements.txt` (ADD: anthropic, tenacity)

**Tasks:**
1. Task 1.1: Setup API Client with Rate Limiting (1.5h)
   - Install `anthropic` SDK
   - Create `ClaudeAPIClient` class with tenacity retry logic
   - Implement rate limiter (20 req/min = 3s between calls)

2. Task 1.2: Create Base Prompt for Section Separation (2h)
   - Design prompt for identifying sections (cabeçalho, decisão, partes, advogados)
   - Test with 3-5 sample PDFs
   - Iterate on prompt wording

3. Task 1.3: Implement JSON Response Parsing (1h)
   - Use `response_format={"type": "json_object"}` in API calls
   - Pydantic schemas for response validation
   - Error handling for malformed JSON

4. Task 1.4: Implement Section Extraction (1.5h)
   - `extract_sections(pdf_path) -> Dict[str, str]`
   - Integration with existing OCR pipeline
   - Section boundary detection

5. Task 1.5: Add Edge Case Handling (1h)
   - Multi-page headers
   - Split decisions across pages
   - Missing sections (partial documents)

**Deliverable:** Working `extract_sections()` function that returns structured JSON.

#### Milestone 2: Learning System (8-10h) ❌ NOT STARTED

**Files to Create:**
- `agentes/legal-text-extractor/learning/pattern_extractor.py` (NEW - 150 lines)
- `agentes/legal-text-extractor/learning/few_shot_manager.py` (NEW - 200 lines)
- `agentes/legal-text-extractor/learning/metrics_tracker.py` (NEW - 100 lines)
- `agentes/legal-text-extractor/learning/schemas.py` (NEW - 80 lines)
- `agentes/legal-text-extractor/data/learning.db` (NEW - SQLite database)

**Tasks:**
1. Task 2.1: Create Pydantic Schemas (1.5h)
   - `ExtractionResult` schema
   - `FewShotExample` schema
   - `PerformanceMetrics` schema

2. Task 2.2: Implement Storage Persistence (2h)
   - SQLite tables: `extractions`, `few_shot_examples`, `metrics`
   - CRUD operations
   - Migration system (Alembic or simple versioning)

3. Task 2.3: Implement Pattern Extraction Logic (2.5h)
   - Analyze successful extractions
   - Identify common patterns (regex, positions, keywords)
   - Store patterns in database

4. Task 2.4: Implement Few-Shot Manager (2h)
   - Select top N best examples (by confidence score)
   - Inject examples into prompt dynamically
   - Update example pool over time

5. Task 2.5: Implement Metrics Tracker (1h)
   - Calculate accuracy (correct sections / total sections)
   - Calculate confidence scores
   - Store per-PDF and aggregate metrics

**Deliverable:** Learning system that improves extraction accuracy over time.

#### Milestone 3: Self-Improvement (6-8h) ❌ NOT STARTED

**Files to Create:**
- `agentes/legal-text-extractor/self_improver/prompt_versioner.py` (NEW - 150 lines)
- `agentes/legal-text-extractor/self_improver/ab_tester.py` (NEW - 180 lines)
- `agentes/legal-text-extractor/prompts/versions/` (NEW - directory for versioned prompts)

**Tasks:**
1. Task 3.1: Create Prompt Versioning System (2h)
   - Store prompts as `v1.txt`, `v2.txt`, etc.
   - Track which version used for each extraction
   - Metadata: creation date, success rate, sample size

2. Task 3.2: Implement Self-Improver Logic (3h)
   - Analyze errors from current prompt version
   - Generate improved prompt using Claude (meta-prompting!)
   - Save as new version
   - Trigger A/B test

3. Task 3.3: Implement A/B Testing (2h)
   - Split new PDFs 50/50 between old and new prompt
   - Compare accuracy metrics after N PDFs (N=10?)
   - Auto-promote winning version
   - Rollback if new version underperforms

**Deliverable:** System that automatically improves its own prompts based on performance.

#### Milestone 4: End-to-End Testing (10-12h) ❌ NOT STARTED

**Process:**
1. Task 4.1: Create Validation Interface (3h)
   - Web UI or CLI for human validation
   - Show extracted sections side-by-side with PDF
   - Collect feedback: correct/incorrect/partial

2. Task 4.2: Create Batch Testing Script (2h)
   - Process 30 PDFs in 3 batches (10 each)
   - Batch 1: Baseline (no learning)
   - Batch 2: With few-shot learning
   - Batch 3: With self-improved prompts

3. Task 4.3: Create Report Generation (2h)
   - Accuracy per batch
   - Improvement over time
   - Cost analysis (tokens used)
   - Error categories

4. Run 30 PDFs through system (3-5h human validation time)

**Deliverable:** Complete metrics report proving system improvements.

### Total Effort Estimate

- **Milestone 1:** 6-8 hours (SDK integration)
- **Milestone 2:** 8-10 hours (learning system)
- **Milestone 3:** 6-8 hours (self-improvement)
- **Milestone 4:** 10-12 hours (testing + validation)

**Total:** 30-38 hours of development + testing

### Cost Estimate

**Per PDF Processing:**
- OCR text: ~2000 tokens (input)
- Section separation: ~500 tokens (output)
- Cost per PDF: ~$0.03 (Claude Sonnet 4.5 pricing)

**30 PDFs:** ~$0.90 total

**With learning/testing overhead:** ~$2-3 total (includes prompt iterations, A/B tests)

### Files to Reference

**Complete planning document:**
`docs/session-memories/session-memory-2025-11-18-legal-text-extractor-fase2.md`

**Contains:**
- Full discussion about SDK vs direct Claude usage
- Decision rationale for complete implementation
- Detailed task breakdowns
- Architecture diagrams
- Example prompts
- Pydantic schemas
- Database schemas

---

## Infrastructure Fixes Applied

### Fix 1: `.claude/settings.local.json` Causing Merge Conflicts

**Problem:** File was being committed by both Web and CLI versions, causing recurring merge conflicts.

**Root Cause:** `settings.local.json` is session-specific (runtime permissions) but was tracked by Git.

**User Quote:**
> "Esse arquivo de settings tem sido commitado pelo Claude Code Web Version, acho que é esse o problema!"

**Solution Applied:**
1. Added `.claude/settings.local.json` to `.gitignore`
2. Removed from Git tracking: `git rm --cached .claude/settings.local.json`
3. Committed change (commit `01bbd52`)

**File:** `.gitignore` (line 70)
```gitignore
# Claude Code Runtime Files (session state, temporary tracking)
.claude/*-session.json
.claude/legal-braniac-session.json
.claude/legal-braniac-active.json
.claude/settings.local.json  # ← ADDED
```

**Impact:** Prevents future merge conflicts between Web/CLI sessions.

### Fix 2: Session Memory in Wrong Location

**Problem:** Memory file created in `.tmp/` instead of `docs/session-memories/`

**User Question:**
> "quando eu falo 'salva na memória persistente', o que você entendo?"

**Solution Applied:**
Moved file to correct location:
```bash
mv .tmp/session-memory-legal-text-extractor-fase2.md \
   docs/session-memories/session-memory-2025-11-18-legal-text-extractor-fase2.md
```

**Convention Explained:**
- User says "add to memory" → Create file in `docs/session-memories/`
- User says "read session-memory-X" → Use Read tool to load
- No automatic hooks exist - 100% manual system

### Fix 3: Vibe-log Not Authenticated

**Problem:** All vibe-log hooks failing with "Not authenticated" error

**Error in Logs:**
```
[2025-11-18T18:09:43.416Z] Hook send: Not authenticated
VibelogError: Not authenticated
Error: No authentication token found
```

**Investigation:**
- `~/.vibe-log/config.json` missing auth token
- SessionStart, PreCompact, SessionEnd hooks all failing silently
- Dashboard inaccessible

**Solution Applied by User:**
User completed `npx vibe-log-cli auth` independently and can now access dashboard at https://app.vibe-log.dev

**User Feedback:**
> "Já fizemos as 'correções' do vibe-log várias vezes e nunca deu certo definitivamente"

Indicates ongoing frustration with vibe-log reliability.

---

## Memory System Decision: Keep Manual

### User's Question

> "Existe algum hook que serve pra automáticamente salvar contexto e automaticamente injetar contexto?"

### Investigation Results

**Available Hooks for Implementation:**
- **SessionStart** - Could inject context from previous session
- **SessionEnd / PreCompact** - Could save session summary
- **UserPromptSubmit** - Could enhance prompts with historical context

**Analysis Provided:**
- ✅ Technically possible to implement
- ❌ Pros: Automatic continuity
- ❌ Cons: Token waste, irrelevant context, maintenance overhead

### User's Decision

> "Talvez manter como está seja melhr"

**Reasoning:**
1. User has focused sessions, knows where they left off
2. Manual = precision and control over what context is loaded
3. Vibe-log already provides analytics/tracking
4. Better to invest time in features (legal-text-extractor) than meta-infrastructure

**Outcome:** Agreed manual system is optimal for user's workflow.

---

## Vibe-log Statusline Integration (In Progress)

### User's Expectation

> "Só realmente estava sob a impressão de que as coisas seriam mostradas diretamente no statusline. Lembro-me de que havia essa indicação no repositório do vibe-log-cli (algo como um daily to-do tasks que apareciam na statusline)."

### Current Implementation

**File:** `.claude/statusline/professional-statusline.js`

**Gordon Integration (lines 128-140):**
```javascript
function getVibeLogLine() {
  return getCachedData('vibe-log', () => {
    try {
      const output = execSync('npx vibe-log-cli statusline --format compact', {
        timeout: 3000,
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'ignore']
      }).trim();
      return output || 'Gordon';
    } catch (error) {
      return 'Gordon'; // Fallback if vibe-log fails
    }
  });
}
```

**Cache Configuration:**
```javascript
const CACHE_TTL = {
  'vibe-log': 30,  // Gordon analysis updates every 30s
  'git-status': 5,
  'tracker': 2
};
```

**Display Location (line 412):**
```javascript
const left = `${colors.cyan}▸${colors.reset} ${colors.bright}${gordon}${colors.reset} ◆ ${colors.magenta}Legal-Braniac${colors.reset} ...`;
```

### What's Known

✅ Statusline DOES call vibe-log CLI
✅ Result cached for 30 seconds
✅ Displayed in LEFT section: `▸ Gordon ◆ Legal-Braniac ...`
✅ User now authenticated and can access dashboard

### What's Unknown

❓ Does vibe-log CLI have daily tasks/standup feature?
❓ What does `npx vibe-log-cli statusline --format compact` actually return?
❓ How to make Gordon feedback visible in CLI?
❓ Does vibe-log support daily to-do lists in statusline output?

### Next Investigation Step

Test vibe-log CLI directly:
```bash
# See what statusline returns
npx vibe-log-cli statusline --format compact

# Check for daily/standup features
npx vibe-log-cli help | grep -i "standup\|daily\|tasks"

# Check analyzed prompts
ls -lah ~/.vibe-log/analyzed-prompts/
```

---

## Commits This Session

### Commit `01bbd52` - "fix: remove settings.local.json from git tracking"

**Changes:**
1. `.gitignore` - Added `.claude/settings.local.json`
2. Removed `settings.local.json` from Git index
3. Moved session memory to correct location

**Files Modified:**
- `.gitignore` (+1 line)
- `docs/session-memories/` (added session-memory-2025-11-18-legal-text-extractor-fase2.md)

---

## Armadilhas Evitadas

### ❌ Implementing Auto-Inject Without User Buy-In

**Initial thought:** Automatic context injection would be useful

**User's perspective:** "parece muito esforço pra pouco resultado"

**Learning:** Always check if automation is worth the overhead for user's specific workflow. Manual can be better.

### ❌ Assuming Vibe-log Is Broken

**Initial diagnosis:** Vibe-log not working due to hooks

**Actual issue:** Simple authentication missing

**Learning:** Check auth/config first before debugging complex hook logic.

### ❌ Starting Implementation Before Resolving Infraestrutura

**Good decision:** Fixed git conflicts BEFORE attempting Fase 2 implementation

**Why important:** Clean foundation prevents compounding errors

---

## Contexto da Sessão (Meta)

### Início: Tentativa de Continuar Tarefa Anterior

User requested: "Please continue the conversation from where we left it off"

**Expected:** Start implementing legal-text-extractor Fase 2
**Actual:** Completely sidetracked by infrastructure issues

### Git Merge Conflicts

Session started with rebase conflicts in:
- `.claude/settings.local.json` (permissions array)
- `.claude/hooks/legal-braniac-session.json` (sessionId, timestamps)

**Resolution:** Accepted remote (HEAD) versions, added rebase permission to settings

### Memory System Clarification

User revealed misunderstanding about memory system:
- Thought there might be automatic hooks
- Unclear about "add to memory" command meaning
- Discovered 100% manual convention

**Outcome:** Clear understanding, decided to keep manual

### Vibe-log Reliability Concerns

**User quote:**
> "Já fizemos as 'correções' do vibe-log várias vezes e nunca deu certo definitivamente"

**Historical context:**
- Previous fix 2025-11-17: Removed `--background` flag
- Current issue: Missing auth token (different problem)

**User's skepticism:** "Essa alteração seria interessante?" - questioning ROI

**Current status:** User authenticated independently, statusline integration unclear

---

## Próximos Passos (Roadmap)

### Curto Prazo (Próxima Sessão)

#### OPTION A: Implement Legal-Text-Extractor Fase 2 (Original Task)
- [ ] Start Milestone 1: SDK Integration (6-8h)
- [ ] Task 1.1: Setup Claude API client with rate limiting
- [ ] Task 1.2: Create base prompt for section separation
- [ ] Test with 3-5 sample PDFs

**Pros:** Addresses original user request, high value feature
**Cons:** Large time investment (30-38h total)

#### OPTION B: Complete Vibe-log Statusline Investigation (Current Tangent)
- [ ] Test `npx vibe-log-cli statusline --format compact` to see output
- [ ] Check if daily tasks/standup features exist
- [ ] Modify statusline to show more vibe-log data if available
- [ ] Document findings

**Pros:** Quick (1-2h), resolves user's expectation mismatch
**Cons:** Low priority compared to PDF extractor

### Médio Prazo (Próximas Semanas)

**If implementing Fase 2:**
- [ ] Complete Milestone 2: Learning System (8-10h)
- [ ] Complete Milestone 3: Self-Improvement (6-8h)
- [ ] Complete Milestone 4: End-to-End Testing (10-12h)
- [ ] Process 30 test PDFs with human validation
- [ ] Generate performance metrics report

### Longo Prazo (Possíveis Enhancements)

**Legal-Text-Extractor:**
- [ ] Multi-document type support (not just TJ-RJ)
- [ ] API endpoint for other agents to use
- [ ] Integration with djen-tracker for automatic processing

**Memory System (If User Changes Mind):**
- [ ] SessionStart auto-inject hook
- [ ] SessionEnd auto-save hook
- [ ] Context compression for token efficiency

**Vibe-log:**
- [ ] Daily standup integration in statusline
- [ ] Gordon feedback visible in CLI (not just dashboard)
- [ ] Push-up challenge reminders in statusline

---

## Métricas de Código

### Arquivos Modificados
- `.gitignore`: +1 line (added settings.local.json)
- `docs/session-memories/`: +1 file (moved from .tmp/)

### Arquivos Lidos (Investigation)
- `.claude/hooks/vibe-analyze-prompt.js` (290 lines)
- `.claude/statusline/professional-statusline.js` (150 lines)
- `.claude/hooks/VIBE_LOG_FIX_2025-11-17.md` (80 lines)
- `~/.vibe-log/config.json`
- `~/.vibe-log/hooks.log`

### Commits
1. `01bbd52` - fix: remove settings.local.json from git tracking

### Lines of Planning (Not Code)
- Session memory file: ~400 lines (complete Fase 2 plan)
- This session memory: ~600 lines (troubleshooting documentation)

**Total documentation:** ~1000 lines of planning without implementation

---

## Tags de Busca

`legal-text-extractor` `fase-2` `sdk-integration` `learning-system` `self-improvement` `few-shot-learning` `prompt-engineering` `git-conflicts` `settings-local` `memory-system` `manual-vs-auto` `vibe-log` `statusline` `gordon` `authentication` `infrastructure` `troubleshooting` `planning` `not-implemented` `wsl2`

---

## Referências

### Arquivos Relacionados
- `docs/session-memories/session-memory-2025-11-18-legal-text-extractor-fase2.md` - Complete Fase 2 plan
- `.claude/hooks/vibe-analyze-prompt.js` - Gordon AI Coach hook
- `.claude/statusline/professional-statusline.js` - Statusline with vibe-log integration
- `.claude/hooks/VIBE_LOG_FIX_2025-11-17.md` - Previous vibe-log fix documentation
- `.gitignore` - Now excludes settings.local.json

### Documentação do Projeto
- `CLAUDE.md` - Instruções para agentes (já documenta memory system como manual)
- `WSL_SETUP.md` - Setup WSL2 (contexto da stack)
- `DISASTER_HISTORY.md` - História de desastres prevenidos

### Commits Relacionados
- `01bbd52` - fix: remove settings.local.json from git tracking
- Previous session: legal-text-extractor planning (not committed, only documented)

---

**Criado por:** Claude Code + PedroGiudice
**Data:** 2025-11-18 (sessão continuação após compactação)
**Ambiente:** WSL2 Ubuntu on Corporate Windows
**Status:** ✅ Infraestrutura corrigida, ⏳ Fase 2 planejada mas não implementada

**DECISÃO CRÍTICA PENDENTE:** Próxima sessão deve implementar Fase 2 ou continuar investigação vibe-log?
