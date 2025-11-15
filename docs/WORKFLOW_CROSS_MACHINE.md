# Workflow Cross-Machine - PC Casa + PC Trabalho

**Versão:** 1.0
**Data:** 2025-11-15
**Objetivo:** Documentar como trabalhar entre PC casa (WSL) e PC trabalho (WSL + servidor)

---

## Arquitetura de Ambientes

### PC Casa (WSL Ubuntu 24.04)

**Localização:**
- Código: `~/claude-work/repos/Claude-Code-Projetos`
- Dados: `~/claude-code-data/` (APIs, processamento local)

**Características:**
- Sprint 1 + 2: Concluídos ✅
- WSL2 funcionando
- Python venvs (5 agentes)
- Claude Code 2.0.42
- Hooks ativos
- **Acesso servidor:** NÃO (fora da rede corporativa)

**Uso:**
- Desenvolvimento de código
- Planejamento de features
- Processamento de dados de APIs públicas (DJEN web, OAB scraping)
- Testes locais

---

### PC Trabalho (WSL Ubuntu 24.04 + Windows)

**Localização:**
- Código: `~/claude-work/repos/Claude-Code-Projetos` (WSL)
- Código: `C:\claude-work\repos\Claude-Code-Projetos` (Windows - mesmo repo)
- Servidor: `/mnt/servidor/documentos-juridicos/` (WSL via CIFS)
- Servidor: `\\SERVIDOR\documentos-juridicos\` (Windows nativo)
- Cache: `~/documentos-juridicos-cache/` (WSL - rsync do servidor)

**Características:**
- Sprint 1 + 2 + 3: A concluir (ver `docs/SPRINT_3_ROADMAP.md`)
- WSL2 (após Sprint 3)
- Python venvs (após Sprint 3)
- Claude Code (após Sprint 3)
- Hooks: Possivelmente desabilitados (se EPERM ocorrer)
- **Acesso servidor:** SIM (rede corporativa)

**Uso:**
- Processamento de documentos do servidor corporativo
- Desenvolvimento com acesso a dados reais
- Outputs enviados de volta para servidor

---

## Sincronização de Código (Git)

### O que sincroniza via Git

**Sincronizado entre PCs:**
- ✅ Código Python (`.py`)
- ✅ Configurações (`.json`, `.md`)
- ✅ Hooks (`.js`, `.ts`)
- ✅ Documentação (`.md`)
- ✅ Scripts (`.sh`, `.ps1`)
- ✅ Requirements (`.txt`)

**NÃO sincronizado (em `.gitignore`):**
- ❌ Virtual environments (`.venv/`)
- ❌ Node modules (`node_modules/`)
- ❌ Dados processados (`~/claude-code-data/`)
- ❌ Cache servidor (`~/documentos-juridicos-cache/`)
- ❌ Logs (`~/logs/`)
- ❌ Configurações locais (`.claude/settings.local.json`)

### Workflow Git Diário

**Fim do dia - PC Casa:**

```bash
cd ~/claude-work/repos/Claude-Code-Projetos

# Verificar mudanças
git status

# Adicionar arquivos
git add .

# Commit descritivo
git commit -m "feat: implementa parser DJEN v2

- Adiciona extração de partes processuais
- Melhora regex para datas
- Corrige bug em processos multi-página
"

# Push
git push
```

**Manhã seguinte - PC Trabalho:**

```bash
cd ~/claude-work/repos/Claude-Code-Projetos

# Pull latest
git pull

# Verificar mudanças recebidas
git log --oneline -5

# Continuar trabalho...
```

---

## Sincronização de Dados (NÃO via Git)

### Dados do Servidor Corporativo (PC Trabalho → Outputs)

**Fluxo:**

```
Servidor (\\SERVIDOR\docs)
    ↓ (montado em /mnt/servidor OU cache via robocopy)
PC Trabalho WSL (processamento)
    ↓ (resultados em ~/claude-code-data/outputs/)
Sincronização manual/script
    ↓
Servidor (\\SERVIDOR\outputs-processados)
```

**Script de sincronização outputs (PC Trabalho):**

```bash
# ~/bin/sync-outputs-servidor.sh
#!/bin/bash

OUTPUTS_WSL="$HOME/claude-code-data/outputs"
OUTPUTS_SERVIDOR="/mnt/servidor/outputs-processados"

mkdir -p "$OUTPUTS_SERVIDOR"

rsync -avz --exclude='*.tmp' --exclude='.git/' \
    "$OUTPUTS_WSL/" "$OUTPUTS_SERVIDOR/"

echo "Outputs sincronizados para servidor"
```

**Execução:**
- Manual: `~/bin/sync-outputs-servidor.sh`
- Automática: Cron a cada 2h (se configurado Sprint 4)

### Dados de APIs (PC Casa)

**Fluxo:**

```
APIs públicas (DJEN, OAB, etc)
    ↓ (download via scripts Python)
PC Casa WSL (~/claude-code-data/inbox/)
    ↓ (processamento)
PC Casa WSL (~/claude-code-data/outputs/)
    ↓ (commit para Git LFS OU compartilhamento manual)
```

**Importante:** Dados de APIs processados no PC casa geralmente NÃO precisam ir para servidor corporativo (são públicos e experimentais).

---

## Casos de Uso Comuns

### Caso 1: Desenvolver nova feature (PC Casa)

```bash
# 1. Criar branch
git checkout -b feature/parser-sentencas

# 2. Desenvolver código
# Editar agentes/legal-lens/parser.py

# 3. Testar localmente (dados mock ou APIs)
cd agentes/legal-lens
source .venv/bin/activate
python parser.py --test

# 4. Commit
git add .
git commit -m "feat: adiciona parser de sentenças"

# 5. Push
git push -u origin feature/parser-sentencas

# 6. Criar PR (via GitHub web)
```

### Caso 2: Processar dados reais do servidor (PC Trabalho)

```bash
# 1. Pull latest code
git pull

# 2. Validar servidor montado
mount | grep servidor

# 3. Processar batch
cd agentes/legal-lens
source .venv/bin/activate
python main.py --input /mnt/servidor/processos/2024/ --batch 100

# 4. Verificar outputs
ls ~/claude-code-data/outputs/legal-lens/

# 5. Sincronizar outputs para servidor
~/bin/sync-outputs-servidor.sh

# 6. Se houver melhorias no código: commit
git add .
git commit -m "fix: corrige parsing de processos 2024"
git push
```

### Caso 3: Testar código do PC trabalho no PC casa

```bash
# PC Casa
git pull

# Testar com dados mock (sem servidor)
cd agentes/legal-lens
source .venv/bin/activate
python main.py --input ~/claude-code-data/mock-data/ --test
```

### Caso 4: Urgência - processar de casa com dados do servidor

**Opções:**

**A) VPN + SSH (se PC trabalho ligado):**

```bash
# PC Casa - SSH para PC trabalho
ssh usuario@pc-trabalho

# Executar processamento remotamente
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/legal-lens
source .venv/bin/activate
python main.py --batch 50
```

**B) Download manual (se poucos arquivos):**

```bash
# PC Trabalho - Copiar para cloud temporário
# Windows: Copiar \\SERVIDOR\processos\ARQUIVO.pdf para OneDrive

# PC Casa - Download OneDrive
# Processar localmente
```

**C) Esperar retorno ao escritório (recomendado):**
- Dados sensíveis do servidor não devem sair da rede corporativa sem aprovação TI

---

## Configurações Específicas por PC

### PC Casa - `.bashrc` customizado

```bash
# Adicionar ao ~/.bashrc no PC CASA

# Alias úteis
alias ccp="cd ~/claude-work/repos/Claude-Code-Projetos"
alias venv-activate="source .venv/bin/activate"

# Variável de ambiente (opcional)
export CLAUDE_ENV="home"
export CLAUDE_DATA_ROOT="$HOME/claude-code-data"

# Git prompt customizado
export PS1="\[\e[32m\]PC-CASA\[\e[m\] \w \$ "
```

### PC Trabalho - `.bashrc` customizado

```bash
# Adicionar ao ~/.bashrc no PC TRABALHO

# Alias úteis
alias ccp="cd ~/claude-work/repos/Claude-Code-Projetos"
alias venv-activate="source .venv/bin/activate"
alias check-servidor="mount | grep servidor"

# Variáveis de ambiente
export CLAUDE_ENV="work"
export CLAUDE_DATA_ROOT="$HOME/claude-code-data"
export SERVIDOR_DOCS="/mnt/servidor/documentos-juridicos"

# Git prompt customizado
export PS1="\[\e[31m\]PC-TRABALHO\[\e[m\] \w \$ "
```

**Aplicar:**

```bash
source ~/.bashrc
```

---

## Checklist Cross-Machine

### Ao terminar no PC Casa

- [ ] `git status` limpo (sem uncommitted changes)
- [ ] `git push` executado
- [ ] Venvs desativados (`deactivate`)
- [ ] WSL desligado (se Windows: `wsl --shutdown`)

### Ao iniciar no PC Trabalho

- [ ] WSL iniciado (`wsl`)
- [ ] `git pull` executado
- [ ] Servidor montado (`mount | grep servidor`)
- [ ] Venv ativado (se processar)

### Ao terminar no PC Trabalho

- [ ] Outputs sincronizados para servidor (`~/bin/sync-outputs-servidor.sh`)
- [ ] Código commitado e pushed (se houver mudanças)
- [ ] Servidor desmontado (opcional: `sudo umount /mnt/servidor`)
- [ ] WSL desligado (se fim do dia)

### Ao iniciar no PC Casa

- [ ] `git pull` executado
- [ ] Verificar se há mudanças relevantes (`git log -5`)
- [ ] Continuar desenvolvimento

---

## Troubleshooting Cross-Machine

### Problema: Git pull falha com "Your local changes would be overwritten"

**Causa:** Mudanças não commitadas no PC anterior.

**Solução:**

```bash
# Opção 1: Stash (salvar temporariamente)
git stash
git pull
git stash pop

# Opção 2: Commit forçado
git add .
git commit -m "wip: trabalho em progresso"
git pull
```

### Problema: Venv corrompido após pull

**Causa:** `.venv/` foi acidentalmente commitado ou recriado em outro Python.

**Solução:**

```bash
cd agentes/[nome-agente]
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Problema: Código funciona no PC casa mas falha no PC trabalho

**Diagnóstico:**

```bash
# Verificar versões Python
python3 --version

# Verificar pacotes instalados
pip list

# Verificar se requirements.txt está atualizado
pip freeze > requirements-atual.txt
diff requirements.txt requirements-atual.txt
```

**Solução:**
- Atualizar `requirements.txt` no PC que funciona
- Commit e push
- Pull no outro PC
- Reinstalar venv

### Problema: Servidor desmonta após `wsl --shutdown`

**Esperado:** Comportamento normal. fstab monta novamente no próximo boot WSL.

**Validar:**

```bash
# Após wsl --shutdown (PowerShell) + wsl
mount | grep servidor

# Se não montou automaticamente:
sudo mount -a
```

---

## Boas Práticas

1. **Sempre pull antes de começar a trabalhar**
   - Evita merge conflicts

2. **Commit frequentemente**
   - Pequenos commits > um commit gigante ao fim do dia

3. **Use branches para features**
   - `main` sempre estável
   - Features em `feature/nome-da-feature`

4. **Não commitar dados ou venvs**
   - Verificar `.gitignore` está correto

5. **Testar em ambos PCs antes de merge**
   - Especialmente se código depende de filesystem

6. **Documentar decisões de arquitetura**
   - Atualizar `CLAUDE.md` quando mudar camadas

7. **Sincronizar outputs do servidor regularmente**
   - Não deixar acumular semanas de processamento sem backup

---

## Roadmap Sprints por PC

### PC Casa

- ✅ Sprint 1: Estrutura inicial (concluído)
- ✅ Sprint 2: WSL2 setup (concluído)
- ⏭️ Sprint 3: SKIP (sem acesso servidor)
- 🔄 Sprint 4: Cache APIs (opcional - se processar grande volume)
- 🔄 Sprint 5: Adaptar código para usar `~/claude-code-data/`
- 🔄 Sprint 6: Infraestrutura .claude/ (agents, skills)

### PC Trabalho

- ⏳ Sprint 1: Estrutura inicial (executar quando chegar)
- ⏳ Sprint 2: WSL2 setup (executar quando chegar)
- ⏳ Sprint 3: Servidor corporativo (executar quando chegar - ver `SPRINT_3_ROADMAP.md`)
- ⏳ Sprint 4: Cache híbrido servidor (se benchmark >200ms)
- ⏳ Sprint 5: Adaptar código para usar `/mnt/servidor` ou cache
- ⏳ Sprint 6: Infraestrutura .claude/

---

## Diagrama de Fluxo

```
┌─────────────────────────────────────────────────────────────┐
│                        GITHUB (CENTRAL)                      │
│            Código sincronizado entre PCs                     │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
             │ git pull/push                  │ git pull/push
             │                                │
     ┌───────▼────────┐              ┌────────▼────────┐
     │   PC CASA      │              │  PC TRABALHO    │
     │   (WSL)        │              │  (WSL + Win)    │
     ├────────────────┤              ├─────────────────┤
     │ - Código       │              │ - Código        │
     │ - APIs dados   │              │ - Servidor      │
     │ - Venv Python  │              │ - Venv Python   │
     │ - Claude Code  │              │ - Claude Code   │
     └────────────────┘              └─────────────────┘
             │                                │
             │                                │
             ▼                                ▼
     ~/claude-code-data/            /mnt/servidor/
     (APIs, outputs)                (docs corporativos)
                                            │
                                            ▼
                                    ~/claude-code-data/outputs/
                                            │
                                            ▼ (rsync)
                                    /mnt/servidor/outputs/
```

---

**Última atualização:** 2025-11-15
**Responsável:** Workflow Cross-Machine Documentation
