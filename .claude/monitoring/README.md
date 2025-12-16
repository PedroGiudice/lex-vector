# Sistema de Monitoramento Multi-Agent para Claude Code

Sistema completo de tracking em tempo real de agentes, hooks e skills no Claude Code.

## 🎯 O Que Foi Implementado

### Componentes

1. **simple_tracker.py** - Core tracker com SQLite database
   - Tracking de agentes (spawn, ativo, idle, stopped)
   - Tracking de hooks (execuções, timestamps)
   - Tracking de skills (detecção automática)
   - CLI commands: agent, hook, skill, status, statusline, cleanup

2. **Hooks de Detecção** (`.claude/monitoring/hooks/`)
   - `detect_agents.sh` - Detecta spawn de agentes via transcript analysis
   - `detect_skills.sh` - Detecta uso de skills (git, bash, docx, pdf, etc)
   - `log_hook.sh` - Log genérico de execução de hooks

3. **Statusline Integrada**
   - Base: `professional-statusline.js` (v6.0)
   - Display elegante com blinking indicators
   - Integração com simple_tracker.py para dados real-time
   - Fallback para legal-braniac-session.json

4. **Configuração Global** (`~/.claude/settings.json`)
   - StatusLine: professional-statusline.js
   - Hooks configurados: PrePrompt, PostResponse, Stop
   - Backup criado: settings.json.backup.*

## 📊 Estrutura de Arquivos

```
.claude/monitoring/
├── simple_tracker.py          # ⭐ Core tracker
├── tracking.db                # SQLite database
├── hooks/
│   ├── detect_agents.sh       # Detecção de agentes
│   ├── detect_skills.sh       # Detecção de skills
│   └── log_hook.sh            # Log de hooks
└── README.md                  # Esta documentação

.claude/statusline/
└── professional-statusline.js # Statusline integrada
```

## 🚀 Como Usar

### Ver Status em Tempo Real

```bash
# Status resumido (última 5 minutos)
./.claude/monitoring/simple_tracker.py status

# Monitor contínuo
watch -n 2 './.claude/monitoring/simple_tracker.py status'
```

### Comandos Disponíveis

```bash
# Tracking manual
./simple_tracker.py agent <name> <status> <session_id>
./simple_tracker.py hook <name> <session_id>
./simple_tracker.py skill <name> <session_id>

# Visualização
./simple_tracker.py status        # Status detalhado
./simple_tracker.py statusline    # Output compacto para statusline

# Manutenção
./simple_tracker.py cleanup [days]  # Limpar dados antigos (default 7 dias)
```

### Exemplos

```bash
# Registrar agente
./simple_tracker.py agent backend-dev active abc123

# Registrar hook
./simple_tracker.py hook PostResponse abc123

# Registrar skill
./simple_tracker.py skill git abc123

# Ver statusline output
./simple_tracker.py statusline
# Output: 🤖 1/1 │ ⚡ 1 │ 🛠️ git
```

## 📈 Statusline Display

**Formato:**
```
▸ Gordon ◆ Legal-Braniac ● 13m ◆ Session 13m ··· ● 7 agents ◇ ● 35 skills ◇ ● 7 hooks ◇ venv ○ ◇ git main*
```

**Indicators:**
- `●` (blinking) = Atividade nos últimos 5s
- `●` (static) = Ativo
- `○` = Inativo
- `*` = Git uncommitted changes

**Cores:**
- Cyan: Gordon/vibe-log
- Magenta: Legal-Braniac
- Yellow: Status/timestamps
- Green: Agents
- Purple: Skills
- Orange: Hooks
- Pink: Git
- Teal: Branch name

## 🔧 Hooks Configurados

### PrePrompt
1. `detect_agents.sh` - Detecta spawn de agentes via patterns (@agent-name, "creating subagent")
2. `log_hook.sh PrePrompt` - Registra execução do hook

### PostResponse
1. `log_hook.sh PostResponse` - Registra execução
2. `detect_skills.sh` - Detecta skills usadas (git, bash, docx, pdf, etc)

### Stop
1. `stop-hook-git-check.sh` - Git safety check (existente)
2. `simple_tracker.py cleanup 7` - Limpa dados >7 dias

## 🗄️ Database Schema

**Tabela: events**
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    type TEXT CHECK(type IN ('agent', 'hook', 'skill')),
    name TEXT NOT NULL,
    status TEXT,
    session_id TEXT,
    metadata JSON
);

CREATE INDEX idx_recent ON events(type, timestamp DESC);
```

**Queries úteis:**
```bash
# Ver todos eventos recentes
sqlite3 .claude/monitoring/tracking.db "SELECT * FROM events ORDER BY timestamp DESC LIMIT 20"

# Ver agentes ativos
sqlite3 .claude/monitoring/tracking.db "SELECT * FROM events WHERE type='agent' AND status='active' ORDER BY timestamp DESC"

# Contar hooks por tipo
sqlite3 .claude/monitoring/tracking.db "SELECT name, COUNT(*) as count FROM events WHERE type='hook' GROUP BY name ORDER BY count DESC"
```

## 🎨 Integração com Sistema Existente

O sistema foi implementado de forma **híbrida** para integrar com a infraestrutura existente:

### Lê de:
- `legal-braniac-session.json` - Agentes/skills disponíveis
- `hooks-status.json` - Timestamps de última execução
- `tracking.db` - Dados em tempo real (novo)

### Escreve para:
- `tracking.db` - Todas as detecções e eventos

### Fallback Strategy:
1. Tenta ler de `tracking.db` (dados real-time)
2. Se vazio, fallback para `legal-braniac-session.json`
3. Blinking indicators baseados em `hooks-status.json` (<5s)

## 🐛 Troubleshooting

### Statusline não aparece
```bash
# Testar manualmente
echo '{"session_id":"test"}' | ./.claude/statusline/professional-statusline.js

# Verificar permissões
chmod +x ./.claude/statusline/professional-statusline.js
```

### Hooks não executam
```bash
# Verificar settings.json
cat ~/.claude/settings.json | jq '.hooks'

# Testar hook manualmente
echo '{"session_id":"test"}' | ./.claude/monitoring/hooks/log_hook.sh TestHook

# Verificar permissões
chmod +x ./.claude/monitoring/hooks/*.sh
```

### Database não cria
```bash
# Verificar diretório
ls -la ./.claude/monitoring/

# Criar manualmente
./. claude/monitoring/simple_tracker.py status

# Verificar Python sqlite3
python3 -c "import sqlite3; print('OK')"
```

### Performance lenta (>500ms)
```bash
# Verificar tempo
time echo '{}' | ./.claude/statusline/professional-statusline.js

# Se lento, desabilitar temporary:
# - Comentar chamada a getTrackerData() no professional-statusline.js
# - Usar apenas legal-braniac-session.json
```

## 📝 Próximos Passos (Opcional)

### Fase Avançada
- [ ] Dashboard web (Flask/FastAPI)
- [ ] Métricas de custo (tokens, USD)
- [ ] Alertas (agent stuck, hook failing)
- [ ] Grafana integration
- [ ] Agent auto-recovery

### Melhorias
- [ ] Caching strategy (evitar queries SQLite a cada render)
- [ ] WAL mode no SQLite (evitar locks)
- [ ] Agent metadata tracking (task description, parent session)
- [ ] Hook performance metrics (duration_ms, success rate)

## ✅ Validação

Sistema testado e validado:
- [x] simple_tracker.py executa sem erros
- [x] Database criado em .claude/monitoring/tracking.db
- [x] Hooks têm permissão de execução
- [x] Statusline retorna output válido
- [x] settings.json configurado corretamente
- [x] JSON válido (jq test passed)
- [x] Hooks registram eventos no database
- [x] Integração com legal-braniac-session.json funciona
- [x] Blinking indicators funcionam (<5s detection)

## 🔒 Backup

Backup automático criado em:
```
~/.claude/settings.json.backup.YYYYMMDD_HHMMSS
```

Para restaurar:
```bash
cp ~/.claude/settings.json.backup.* ~/.claude/settings.json
```

---

**Implementado em:** 2025-11-18
**Tempo de implementação:** ~2.5 horas
**Status:** ✅ Funcional e testado

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota
