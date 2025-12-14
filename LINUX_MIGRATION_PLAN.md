# Plano de Migração Windows → Linux - Dev Machine

> **Para:** Pedro (PGR)
> **Objetivo:** Migrar PC de Windows para Linux como dev machine dedicada
> **Gerado:** 2025-12-14

---

## Sumário Executivo

| Distro Recomendada | Ubuntu 24.04 LTS |
|-------------------|------------------|
| Filesystem | ext4 |
| Encryption | LUKS (Full Disk) |
| Tempo Estimado | 2-3 horas |
| Risco | Baixo (com backup) |

---

## Arquivos de Suporte Criados

| Arquivo | Propósito |
|---------|-----------|
| `LINUX_DEV_SETUP.md` | Guia detalhado de setup do ambiente dev |
| `LINUX_MIGRATION_CHEATSHEET.md` | Troubleshooting rápido |
| `scripts/linux-setup/` | Scripts de automação (19 arquivos) |

---

## FASE 1: PRÉ-INSTALAÇÃO (ainda no Windows)

### 1.1 Backup de Dados Críticos

```
PRIORIDADE MÁXIMA - Fazer backup ANTES de qualquer outra coisa:

[ ] 1. Git push de TODOS os branches locais:
    git push --all origin

[ ] 2. Exportar ~/.claude/ (config global do Claude Code)
    - Inclui: settings.json global, tokens, cache

[ ] 3. Dados em ~/claude-code-data/ (NÃO está no Git):
    - DuckDB databases (stj.duckdb, etc.)
    - Caches, outputs processados
    → COPIAR PARA USB EXTERNO

[ ] 4. Arquivo .env com secrets:
    - legal-workbench/docker/.env (GEMINI_API_KEY, TRELLO_*)
    → SALVAR EM LOCAL SEGURO (password manager)

[ ] 5. SSH Keys (se houver):
    - ~/.ssh/id_* → Copiar para USB criptografado

[ ] 6. Browser data:
    - Bookmarks, extensões, senhas
```

### 1.2 Download e Preparação

```bash
# Recomendação: Ubuntu 24.04 LTS
# Download: https://ubuntu.com/download/desktop

[ ] ISO: ubuntu-24.04.1-desktop-amd64.iso (~5.8GB)
[ ] Verificar SHA256 checksum após download
[ ] Criar USB bootável com Rufus ou Ventoy (8GB+)
```

### 1.3 Configurar BIOS/UEFI

```
[ ] Entrar na BIOS (F2/F12/Del ao ligar)
[ ] Desabilitar Secure Boot (temporariamente)
[ ] Desabilitar Fast Boot
[ ] Boot order: USB primeiro
[ ] Salvar e sair
```

---

## FASE 2: INSTALAÇÃO

### 2.1 Particionamento Recomendado

**Opção Simples (Recomendada):**
- Usar "Erase disk and install Ubuntu"
- Marcar "Encrypt the new Ubuntu installation"
- Definir senha FORTE (guardar no password manager)

**Opção Avançada (Manual):**

| Partição | Tamanho | Filesystem | Mount Point |
|----------|---------|------------|-------------|
| EFI | 512MB | FAT32 | /boot/efi |
| / | 50GB | ext4 | / |
| /home | resto | ext4 | /home |
| swap | RAM*1.5 | swap | - |

### 2.2 Pós-Instalação Imediata

```bash
# Primeiro boot:
sudo apt update && sudo apt upgrade -y

sudo apt install -y \
    build-essential curl wget git vim htop tree unzip \
    software-properties-common

# Drivers proprietários (se necessário)
sudo ubuntu-drivers autoinstall

sudo reboot
```

---

## FASE 3: CONFIGURAÇÃO DEV ENVIRONMENT

### 3.1 Prioridade 1 - Fundação (Primeira Hora)

```bash
# Git
sudo apt install git
git config --global user.name "Pedro"
git config --global user.email "seu@email.com"

# SSH Keys (restaurar do backup OU gerar novas)
ssh-keygen -t ed25519 -C "seu@email.com"
cat ~/.ssh/id_ed25519.pub
# → Adicionar ao GitHub

# Clone do repositório
mkdir -p ~/claude-work/repos
cd ~/claude-work/repos
git clone git@github.com:PedroGiudice/Claude-Code-Projetos.git
```

### 3.2 Prioridade 2 - Python (pyenv)

```bash
curl https://pyenv.run | bash

# Adicionar ao ~/.bashrc:
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc

pyenv install 3.11.9
pyenv global 3.11.9
python --version  # Deve mostrar 3.11.x
```

### 3.3 Prioridade 3 - Node.js (nvm)

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc

nvm install 22
nvm use 22
nvm alias default 22
node --version  # v22.x
```

### 3.4 Prioridade 4 - Bun (para hooks JS)

```bash
curl -fsSL https://bun.sh/install | bash
bun --version  # 1.x
```

### 3.5 Prioridade 5 - Docker

```bash
# Instalar Docker
curl -fsSL https://get.docker.com | sh

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
# LOGOUT e LOGIN novamente

docker --version
docker compose version
```

### 3.6 Prioridade 6 - Claude Code

```bash
npm install -g @anthropic-ai/claude-code
claude login
claude --version
```

### 3.7 Dependências do Sistema

```bash
# Para PDF extraction
sudo apt install -y tesseract-ocr tesseract-ocr-por poppler-utils

# OpenCV dependencies
sudo apt install -y libgl1-mesa-glx libglib2.0-0
```

---

## FASE 4: MIGRAÇÃO DE PROJETOS

### 4.1 Setup de venvs

```bash
# Legal Workbench
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
```

### 4.2 Restaurar Dados

```bash
# Do USB/backup
mkdir -p ~/claude-code-data
cp -r /media/usb/claude-code-data/* ~/claude-code-data/
```

### 4.3 Configurar .env

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench/docker
cp .env.example .env
nano .env
# Preencher: GEMINI_API_KEY, TRELLO_API_KEY, TRELLO_API_TOKEN
```

### 4.4 Levantar Docker Services

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench/docker
docker compose up -d --build
docker compose ps  # Todos "healthy"
```

---

## FASE 5: VERIFICAÇÃO FINAL

### Checklist de Sanidade

```bash
echo "=== VERIFICAÇÃO FINAL ==="
echo "Git: $(git --version)"
echo "Python: $(python --version)"
echo "Node: $(node --version)"
echo "Bun: $(bun --version)"
echo "Docker: $(docker --version)"
echo "Docker Compose: $(docker compose version)"
echo "Claude: $(claude --version)"
echo "Tesseract: $(tesseract --version | head -1)"
echo "=========================="
```

### Teste Legal Workbench

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench
source .venv/bin/activate
streamlit run app.py
# Acessar: http://localhost:8501
```

---

## Automação Disponível

Para setup mais rápido, use os scripts criados:

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/scripts/linux-setup
./bootstrap-linux.sh  # Menu interativo
./verify-installation.sh  # Verificar tudo
```

---

## Troubleshooting Rápido

| Problema | Solução |
|----------|---------|
| Docker permission denied | `sudo usermod -aG docker $USER` + logout/login |
| pyenv não encontrado | Verificar ~/.bashrc tem exports corretos |
| Tesseract lang não encontrado | `sudo apt install tesseract-ocr-por` |
| Claude Code auth falhou | `claude logout && claude login` |
| Hooks não executam | `chmod +x` nos scripts |

**Referência completa:** `LINUX_MIGRATION_CHEATSHEET.md`

---

## Checklist Resumido (para imprimir)

```
PRÉ-INSTALAÇÃO:
[ ] git push --all origin
[ ] Backup ~/.claude/
[ ] Backup ~/claude-code-data/
[ ] Salvar .env secrets
[ ] Backup SSH keys
[ ] Download Ubuntu 24.04 ISO
[ ] Criar USB bootável
[ ] Desabilitar Secure Boot

INSTALAÇÃO:
[ ] Boot USB
[ ] Full Disk Encryption habilitado
[ ] apt update && upgrade

DEV ENVIRONMENT:
[ ] Git configurado
[ ] SSH keys
[ ] pyenv + Python 3.11
[ ] nvm + Node v22
[ ] Bun
[ ] Docker + Compose
[ ] Claude Code

MIGRAÇÃO:
[ ] Repositório clonado
[ ] venvs criados
[ ] Dados restaurados
[ ] .env configurado
[ ] Docker services healthy
[ ] Teste final OK
```

---

## Recursos de Suporte

- **Setup detalhado:** `LINUX_DEV_SETUP.md`
- **Troubleshooting:** `LINUX_MIGRATION_CHEATSHEET.md`
- **Scripts:** `scripts/linux-setup/`
- **Quick reference:** `scripts/linux-setup/QUICK_REFERENCE.md`
