# WSL Setup - Claude Code Projetos

**Versão:** 1.0
**Data:** 2025-11-15
**Ambiente:** Ubuntu 24.04 LTS (WSL2)

---

## 📍 Estrutura de Diretórios Padronizada

Este projeto usa estrutura de diretórios **consistente cross-machine**:

| Máquina | Localização |
|---------|-------------|
| **Windows (trabalho)** | `C:\claude-work\repos\Claude-Code-Projetos` |
| **WSL (casa)** | `~/claude-work/repos/Claude-Code-Projetos` |

**Razão:** Mesma estrutura relativa facilita:
- Scripts portáveis
- Documentação única
- Hooks funcionando em ambos ambientes

---

## 🔄 Migração de ~/projects/ para ~/claude-work/repos/

Se você clonou em `~/projects/` anteriormente, migre:

```bash
# Criar estrutura padrão
mkdir -p ~/claude-work/repos

# Mover repositório (preserva .git, .venv, node_modules)
mv ~/projects/Claude-Code-Projetos ~/claude-work/repos/

# Navegar
cd ~/claude-work/repos/Claude-Code-Projetos

# Validar
git status  # Deve estar limpo
pwd         # Deve mostrar ~/claude-work/repos/Claude-Code-Projetos
```

**⚠️ Importante:** Não esqueça de atualizar workspaces do VSCode/IDE.

---

## 🧠 SessionStart Hooks (WSL)

Hooks JavaScript funcionam **nativamente** no WSL se Node.js está instalado:

```bash
# Testar hooks manualmente
node .claude/hooks/session-context-hybrid.js
node .claude/hooks/invoke-legal-braniac-hybrid.js

# Output esperado
{"continue":true,"systemMessage":"🧠 Legal-Braniac: Orquestrador ativo..."}
```

**Hooks instalados:**
- `invoke-legal-braniac-hybrid.js` - Orquestrador (auto-invoca agentes)
- `session-context-hybrid.js` - Contexto do projeto
- `venv-check.js` - Valida virtual environments
- `git-status-watcher.js` - Monitora git changes
- `dependency-drift-checker.js` - Alerta sobre deps desatualizadas
- `data-layer-validator.js` - Valida separação CODE/ENV/DATA
- `corporate-detector.js` - Detecta ambiente corporativo
- `hook-wrapper.js` - Wrapper para tracking
- `skill-activation-prompt.ts` - Auto-ativa skills relevantes

**Funcionamento automático:** Claude Code executa esses hooks em eventos como SessionStart e UserPromptSubmit.

---

## 🐍 Python Virtual Environments (WSL)

Cada agente tem seu próprio venv:

```bash
# Ativar venv (sintaxe Linux/WSL)
cd agentes/oab-watcher
source .venv/bin/activate  # ⚠️ Diferente do Windows: .venv\Scripts\activate

# Verificar ativação
which python  # Deve apontar para .../oab-watcher/.venv/bin/python
pip list      # Mostra apenas deps do projeto

# Instalar/atualizar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Desativar
deactivate
```

**Agentes com venv:**
1. `agentes/djen-tracker/.venv`
2. `agentes/legal-articles-finder/.venv`
3. `agentes/legal-lens/.venv`
4. `agentes/legal-rag/.venv`
5. `agentes/oab-watcher/.venv`

---

## 📦 npm Packages (WSL)

**MCP Server:** `mcp-servers/djen-mcp-server/`

```bash
cd mcp-servers/djen-mcp-server

# Instalar dependencies
npm install

# Verificar
ls node_modules/ | wc -l  # ~340 packages

# Executar server (se aplicável)
npm start
```

**Vulnerabilidades conhecidas:**
- 5 moderate (esbuild, vite, vitest)
- Impacto: Apenas DEV tools, não produção
- Decisão: Não corrigir agora (breaking changes com vitest@4)

---

## 🔀 Git Workflow Cross-Machine

### PC Casa (WSL) - Fim do dia

```bash
cd ~/claude-work/repos/Claude-Code-Projetos

# Fazer alterações...
git add .
git commit -m "feat: implementa parser DJEN no WSL"
git push
```

### PC Trabalho (Windows) - Manhã seguinte

```powershell
cd C:\claude-work\repos\Claude-Code-Projetos

git pull

# Continuar trabalho...
```

**⚠️ Atenção:**
- `.venv/` está no `.gitignore` (não sincroniza entre máquinas)
- `node_modules/` está no `.gitignore` (não sincroniza)
- Recriar venvs/dependencies em cada máquina se necessário

---

## 🛠️ Ferramentas Instaladas (WSL)

### Node.js (via nvm)

```bash
node --version  # v24.11.1
npm --version   # 11.6.2
nvm --version   # 0.39.7

# Gerenciar versões Node
nvm ls          # Listar versões instaladas
nvm use 24      # Trocar versão
```

### Python

```bash
python3 --version  # 3.12.3
pip3 --version     # pip 24.x
```

### Claude Code

```bash
claude --version  # 2.0.42 (Claude Code)
which claude      # ~/.nvm/versions/node/v24.11.1/bin/claude

# Executar
claude
```

### Build Tools

```bash
gcc --version       # GCC 13.x
make --version      # GNU Make 4.3
git --version       # git 2.43.x
```

---

## 🐛 Troubleshooting

### Hooks não executam

**Problema:** Hooks JavaScript não rodam automaticamente

**Diagnóstico:**
```bash
# Verificar Node.js instalado
node --version

# Verificar permissões
ls -la .claude/hooks/*.js

# Testar manualmente
node .claude/hooks/invoke-legal-braniac-hybrid.js
```

**Solução:**
- Garantir Node.js instalado via nvm
- Hooks devem ser executáveis: `chmod +x .claude/hooks/*.js`

---

### Python não encontrado

**Problema:** `python: command not found`

**Solução:**
```bash
# Ubuntu usa python3
sudo apt install python3 python3-pip python3-venv python3-dev

# Criar alias (opcional)
echo "alias python=python3" >> ~/.bashrc
source ~/.bashrc
```

---

### Git push pede senha sempre

**Problema:** Git pede credenciais a cada push

**Solução 1 - Credential helper:**
```bash
git config --global credential.helper store
# Próximo push vai pedir senha, depois salva
```

**Solução 2 - SSH keys:**
```bash
# Gerar SSH key
ssh-keygen -t ed25519 -C "seu@email.com"

# Adicionar ao ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copiar chave pública e adicionar no GitHub
cat ~/.ssh/id_ed25519.pub
```

---

### venv não ativa (pip: required file not found)

**Problema:** `.venv/bin/pip: cannot execute: required file not found`

**Causa:** venv corrompido ou criado em outro sistema

**Solução:**
```bash
# Remover venv corrompido
cd agentes/oab-watcher
rm -rf .venv

# Recriar
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

### WSL lento ou travando

**Problema:** Performance ruim do WSL

**Solução 1 - Verificar .wslconfig:**
```ini
# C:\Users\[Username]\.wslconfig
[wsl2]
memory=4GB      # Ajustar conforme RAM disponível
processors=2
swap=1GB
```

**Solução 2 - Reiniciar WSL:**
```powershell
# PowerShell (Windows)
wsl --shutdown
# Aguardar 10 segundos
wsl
```

**Solução 3 - Excluir do Windows Defender:**
```powershell
# PowerShell como Admin
Add-MpPreference -ExclusionPath "$env:USERPROFILE\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu24.04LTS_79rhkp1fndgsc"
```

---

## 📚 Referências

- **CLAUDE.md** - Regras arquiteturais do projeto
- **DISASTER_HISTORY.md** - Lições aprendidas (3-day disaster)
- **README.md** - Visão geral do projeto
- **docs/plano-migracao-wsl2.md** - Plano completo de migração (6 sprints)
- **docs/wsl-pro-claude-code-analise-completa.md** - Análise de performance WSL

---

## ✅ Checklist Pós-Setup

Após configurar WSL, validar:

- [ ] Estrutura em `~/claude-work/repos/Claude-Code-Projetos`
- [ ] `git status` limpo
- [ ] Node.js v24+ instalado (`node --version`)
- [ ] Claude Code instalado (`claude --version`)
- [ ] Hooks funcionando (`node .claude/hooks/invoke-legal-braniac-hybrid.js`)
- [ ] Pelo menos 1 venv Python ativável
- [ ] npm packages MCP server instalados
- [ ] Git push/pull funcionando sem erro

---

**Última atualização:** 2025-11-15
**Responsável:** Migração Sprint 2 - WSL2 Setup
