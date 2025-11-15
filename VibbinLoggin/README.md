# VibbinLoggin 📊

**Analytics & coaching tools** para sessões Claude Code.

---

## 📁 O que é isso?

Este diretório contém ferramentas de **análise e melhoria** do seu trabalho com Claude Code:

- **vibe-log-cli/** - Clone local do [vibe-log-cli](https://github.com/vibe-log/vibe-log-cli)
  - Gera relatórios de produtividade
  - Status line coach (feedback em tempo real)
  - Today's standup (resumo diário)
  - Cloud sync opcional

---

## 🚀 Como Usar

### Opção 1: Usar Localmente (versionado no Git)

```bash
# Navegue para o diretório
cd ~/claude-work/repos/Claude-Code-Projetos/VibbinLoggin/vibe-log-cli

# Execute o CLI
node bin/vibe-log.js
```

**Vantagens:**
- ✅ Código versionado no Git (você controla)
- ✅ Pode customizar livremente
- ✅ Portável entre máquinas (git pull)
- ✅ Não precisa `npm install -g`

**Desvantagens:**
- ⚠️ Precisa rebuild após mudanças (`npm run build`)
- ⚠️ Não atualiza automaticamente

### Opção 2: Usar via npx (não versionado)

```bash
# Executa versão mais recente do npm
npx vibe-log-cli@latest
```

**Vantagens:**
- ✅ Sempre atualizado
- ✅ Não ocupa espaço local
- ✅ Sem manutenção

**Desvantagens:**
- ❌ Não versionado no Git
- ❌ Não pode customizar
- ❌ Depende de internet

---

## 🔧 Setup Inicial

### Primeira Execução

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/VibbinLoggin/vibe-log-cli
node bin/vibe-log.js
```

O CLI vai guiar você pelo setup:
1. **Autenticação** (opcional) - Para cloud sync via GitHub
2. **Status line coach** - Configurar coaching em tempo real
3. **Hooks** - Instalar SessionStart/PreCompact hooks

### Configurações Importantes

**Arquivos de config (NÃO versionados):**
- `~/.vibe-log/config.json` - Configurações gerais
- `~/.vibe-log/hooks.log` - Logs de execução dos hooks
- `~/.vibe-log/hooks-stats.json` - Estatísticas de uso

**Arquivos versionados neste repo:**
- `src/` - Código-fonte TypeScript
- `bin/` - Entry point do CLI
- `package.json` - Dependências e scripts

---

## 🔄 Atualização

### Atualizar Clone Local

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/VibbinLoggin/vibe-log-cli

# Atualizar do upstream
git pull origin main

# Reinstalar dependências
npm install

# Rebuild
npm run build
```

### Sincronizar com Upstream Original

```bash
# Adicionar remote do upstream (fazer uma vez)
git remote add upstream https://github.com/vibe-log/vibe-log-cli.git

# Atualizar do upstream
git fetch upstream
git merge upstream/main

# Resolver conflitos (se houver) e commit
npm install && npm run build
```

---

## 📊 Features Principais

### 1. Today's Standup
```bash
node bin/vibe-log.js
# Selecione "Today's standup"
```
Gera resumo personalizado de atividades recentes:
- O que você trabalhou
- Conquistas-chave
- Próximos passos

### 2. Local Reports
```bash
node bin/vibe-log.js
# Selecione "Generate local report"
```
Análise abrangente usando sub-agentes Claude Code em paralelo.
**100% local** - nada sai da sua máquina.

### 3. Status Line Coach
```bash
node bin/vibe-log.js
# Selecione "Configure prompt coach status line"
```
Assessor estratégico integrado ao Claude Code:
- Analisa prompts em tempo real
- Feedback concreto na status line
- Personalidades: Gordon (tough love), Vibe-Log (encouraging), Custom

### 4. Cloud Sync (Opcional)
```bash
node bin/vibe-log.js
# Autentique via GitHub
# Configure auto-sync
```
Sincroniza dados **sanitizados** para dashboard web:
- Track prompt improvement over time
- Deeper productivity insights
- Peak times/low times analysis

---

## 🔒 Privacidade

**Sanitização automática** antes de qualquer upload:
- ❌ **Removido**: Código, API keys, paths, URLs, emails, env vars
- ✅ **Preservado**: Fluxo de conversa, padrões, contexto

**Auditável:**
- Código sanitizador: [`src/lib/message-sanitizer-v2.ts`](vibe-log-cli/src/lib/message-sanitizer-v2.ts)
- Preview antes de upload
- Open-source 100%

---

## 📚 Documentação

**Documentação completa:**
- [README oficial](vibe-log-cli/README.md)
- [CLAUDE.md (contexto técnico)](vibe-log-cli/CLAUDE.md)
- [CHANGELOG.md](vibe-log-cli/CHANGELOG.md)
- [CONTRIBUTING.md](vibe-log-cli/CONTRIBUTING.md)

**Website:** https://vibe-log.dev

---

## 🛠️ Desenvolvimento

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/VibbinLoggin/vibe-log-cli

# Instalar dependências
npm install

# Build (TypeScript → JavaScript)
npm run build

# Watch mode (rebuild automático)
npm run dev

# Testes
npm run test

# Lint + type check + test + security
npm run check-all
```

---

## 🎯 Por Que Este Nome?

**VibbinLoggin** = "vibe-log" + "vibin'" (gíria) + "loggin'" (logging)

Um trocadilho criativo que mantém a essência da ferramenta original! 😄

---

## 📝 Notas

### Git Workflow

**O que está versionado:**
- ✅ Código-fonte (`src/`, `bin/`, `tests/`)
- ✅ `package.json` (lista de dependências)
- ✅ Configurações de build (`tsconfig.json`, `tsup.config.ts`)

**O que NÃO está versionado:**
- ❌ `node_modules/` (instalado via `npm install`)
- ❌ `dist/` (gerado via `npm run build`)
- ❌ `coverage/` (gerado via `npm run test:coverage`)
- ❌ Configurações pessoais (`~/.vibe-log/`)

### Portabilidade

Ao fazer `git pull` em outra máquina:
```bash
cd ~/claude-work/repos/Claude-Code-Projetos/VibbinLoggin/vibe-log-cli
npm install  # Reinstalar dependências
npm run build  # Rebuildar projeto
```

---

**Última atualização:** 2025-11-15
