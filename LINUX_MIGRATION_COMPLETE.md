# MIGRAÇÃO COMPLETA: Windows → Linux

> **Hardware:** ASUS Laptop | i5 10th Gen | 16GB RAM | Intel UHD Graphics
> **Distro:** Ubuntu 24.04 LTS
> **Gerado:** 2025-12-14

---

## INVENTÁRIO TOTAL

| Categoria | Quantidade | Tamanho |
|-----------|------------|---------|
| Arquivos totais | 276+ | ~152 MB |
| requirements.txt | 16 arquivos | - |
| package.json | 1 arquivo | - |
| Docker services | 6 containers | - |
| Hooks ativos | 25+ scripts | - |
| Agents | 29 customizados | - |
| Skills | 15 custom + 7 managed | - |
| Dependências Python | 100+ packages | - |
| Dependências Sistema | 15+ packages | - |

---

# FASE 1: PRÉ-MIGRAÇÃO (WINDOWS)

## 1.1 Backup de Secrets

```
Abra Notepad e salve em arquivo seguro (NÃO no pendrive):

GEMINI_API_KEY=<copiar de legal-workbench/docker/.env>
TRELLO_API_KEY=<copiar de legal-workbench/docker/.env>
TRELLO_API_TOKEN=<copiar de legal-workbench/docker/.env>
TRELLO_BOARD_ID=<copiar de legal-workbench/docker/.env>

Salvar em: Password Manager ou arquivo criptografado
```

## 1.2 Git Push Completo

```cmd
cd %USERPROFILE%\caminho\para\Claude-Code-Projetos
git status
git add -A
git commit -m "pre-migration backup"
git push --all origin
```

## 1.3 Backup Chrome

```
1. Chrome → Configurações → Você e o Google → Ativar sincronização
2. Aguarde 5 minutos (verificar ícone sync)
3. Chrome → Extensões → Copiar lista de extensões instaladas:
   - React Developer Tools
   - Redux DevTools
   - JSON Formatter
   - (liste todas que usa)

4. Bookmarks → Gerenciador → Exportar para HTML
   Salvar: bookmarks_backup.html

5. Senhas → Configurações → Senhas → Exportar
   Salvar: passwords_backup.csv (CUIDADO: arquivo sensível)
```

## 1.4 Backup de Dados Locais

```
Copiar para pendrive (32GB+):

1. Pasta .claude global:
   %USERPROFILE%\.claude\
   → Inclui: settings.json, tokens, cache

2. Dados fora do Git (SE EXISTIR):
   %USERPROFILE%\claude-code-data\
   → DuckDB, caches, outputs

3. SSH Keys:
   %USERPROFILE%\.ssh\
   → id_ed25519, id_ed25519.pub, known_hosts, config

4. Arquivo .env:
   Claude-Code-Projetos\legal-workbench\docker\.env
```

## 1.5 Docker Volumes (SE HOUVER DADOS LOCAIS)

```cmd
REM Verificar se existem volumes Docker com dados
docker volume ls

REM Se stj-duckdb-data existir e tiver dados importantes:
docker run --rm -v stj-duckdb-data:/data -v %cd%:/backup alpine tar czf /backup/stj-data-backup.tar.gz /data

REM Copiar backup para pendrive
```

## 1.6 Download Ubuntu ISO

```
1. Acesse: https://ubuntu.com/download/desktop
2. Baixe: Ubuntu 24.04.1 LTS (64-bit)
3. Aguarde (~5.8GB)
4. Verifique SHA256 (opcional)
```

## 1.7 Criar USB Bootável

```
1. Baixe Rufus: https://rufus.ie/pt_BR/
2. Insira USB vazio (8GB+)
3. Abra Rufus
4. Dispositivo: seu USB
5. Seleção de Boot: clique SELECIONAR → ISO baixada
6. Esquema de partição: GPT
7. Sistema de destino: UEFI
8. Clique INICIAR
9. Modo: Gravar em modo Imagem ISO
10. Aguarde (~5-10 min)
```

---

# FASE 2: INSTALAÇÃO UBUNTU

## 2.1 Configurar BIOS

```
1. Desligue notebook
2. Ligue + pressione F2 repetidamente (ASUS)

Na BIOS:
- Security → Secure Boot: DISABLED
- Boot → Fast Boot: DISABLED
- Boot → Boot Option #1: USB
- Advanced → Intel Virtualization: ENABLED

3. F10 → Save & Exit → Yes
```

## 2.2 Boot USB

```
1. Notebook reinicia
2. Tela roxa → "Try or Install Ubuntu" → ENTER
3. Se não bootar: ESC ou F8 para Boot Menu manual
```

## 2.3 Instalação

```
TELA 1 - Idioma:
→ Português (Brasil) ou English
→ Instalar Ubuntu

TELA 2 - Teclado:
→ Portuguese (Brazil) se ABNT2
→ English (US) se internacional
→ Teste: ç ~ ^ ´ `
→ Continuar

TELA 3 - Conexão:
→ Conecte WiFi (facilita downloads)
→ Continuar

TELA 4 - Tipo de instalação:
→ Instalação normal
→ ☑ Baixar atualizações
→ ☑ Software de terceiros
→ Continuar

TELA 5 - Disco:
→ "Apagar disco e reinstalar Ubuntu"
→ Recursos avançados:
  → ☑ Usar LVM
  → ☑ Criptografar instalação (LUKS)
→ OK → Instalar Agora

TELA 6 - Senha LUKS:
→ Senha FORTE (12+ chars)
→ ANOTE ESSA SENHA
→ Continuar

TELA 7 - Fuso:
→ São Paulo
→ Continuar

TELA 8 - Usuário:
→ Nome: Pedro
→ Computador: asus-dev
→ Usuário: pedro
→ Senha: [sua senha]
→ ☑ Solicitar senha
→ Continuar

AGUARDE: 10-20 minutos

FINAL:
→ Reiniciar Agora
→ Remova USB → ENTER
```

---

# FASE 3: PRIMEIRO BOOT

## 3.1 Login

```
1. Senha LUKS (se criptografou)
2. Senha usuário
3. Assistente: Pular tudo
```

## 3.2 Conectar WiFi

```
1. Ícone rede (canto superior direito)
2. WiFi → sua rede → senha → Conectar
```

## 3.3 Atualizar Sistema

```bash
# Abra Terminal: Ctrl+Alt+T

sudo apt update && sudo apt upgrade -y

# Quando perguntar [Y/n]: ENTER
# Senha: digite (não aparece nada)
# Aguarde 5-15 min

sudo reboot
```

---

# FASE 4: DEPENDÊNCIAS DO SISTEMA

## 4.1 Pacotes Essenciais

```bash
sudo apt install -y \
    build-essential \
    curl \
    wget \
    git \
    vim \
    htop \
    tree \
    unzip \
    jq \
    rsync \
    software-properties-common \
    ca-certificates \
    gnupg \
    pkg-config
```

## 4.2 Dependências Python (Compilação)

```bash
sudo apt install -y \
    python3-dev \
    libssl-dev \
    libffi-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    liblzma-dev \
    llvm
```

## 4.3 Dependências OCR/PDF

```bash
sudo apt install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils
```

## 4.4 Dependências OpenCV/Imagem

```bash
sudo apt install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libwebp-dev
```

## 4.5 Dependências XML/BLAS

```bash
sudo apt install -y \
    libxml2-dev \
    libxslt1-dev \
    libblas-dev \
    liblapack-dev
```

---

# FASE 5: AMBIENTE DE DESENVOLVIMENTO

## 5.1 Git

```bash
sudo apt install -y git

git config --global user.name "Pedro"
git config --global user.email "seu@email.com"
git config --global init.defaultBranch main
```

## 5.2 SSH Keys

```bash
# Opção A: Restaurar do backup
mkdir -p ~/.ssh
cp /media/$USER/PENDRIVE/.ssh/* ~/.ssh/
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_*
chmod 644 ~/.ssh/*.pub

# Opção B: Gerar novas
ssh-keygen -t ed25519 -C "seu@email.com"
# ENTER para aceitar padrão
# Senha opcional

# Adicionar ao GitHub
cat ~/.ssh/id_ed25519.pub
# Copie o texto
# https://github.com/settings/keys → New SSH Key → Cole
```

## 5.3 pyenv + Python

```bash
# Instalar pyenv
curl https://pyenv.run | bash

# Adicionar ao shell
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc

# Instalar Python 3.11
pyenv install 3.11.9
pyenv global 3.11.9

# Verificar
python --version
# Python 3.11.9
```

## 5.4 nvm + Node.js

```bash
# Instalar nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc

# Instalar Node 22
nvm install 22
nvm alias default 22

# Verificar
node --version
# v22.x.x
```

## 5.5 Bun

```bash
curl -fsSL https://bun.sh/install | bash
source ~/.bashrc

# Verificar
bun --version
# 1.x.x
```

## 5.6 Docker

```bash
# Instalar Docker
curl -fsSL https://get.docker.com | sh

# Adicionar usuário ao grupo
sudo usermod -aG docker $USER

# IMPORTANTE: Logout e login novamente
# Ou reinicie: sudo reboot
```

Após relogar:

```bash
# Verificar
docker --version
docker compose version
docker run hello-world
```

## 5.7 Claude Code

```bash
npm install -g @anthropic-ai/claude-code

# Verificar
claude --version

# Autenticar
claude login
# Siga instruções na tela
```

---

# FASE 6: CLONAR REPOSITÓRIO

## 6.1 Estrutura de Diretórios

```bash
mkdir -p ~/claude-work/repos
mkdir -p ~/claude-code-data
```

## 6.2 Clone

```bash
cd ~/claude-work/repos
git clone git@github.com:PedroGiudice/Claude-Code-Projetos.git

# Se perguntar "Are you sure": yes + ENTER

cd Claude-Code-Projetos
ls -la
```

## 6.3 Verificar Clone

```bash
git status
git log --oneline -5
```

---

# FASE 7: RESTAURAR DADOS

## 7.1 Dados do Backup

```bash
# Monte pendrive (geralmente automático)
ls /media/$USER/

# Copiar dados
cp -r /media/$USER/PENDRIVE/claude-code-data/* ~/claude-code-data/

# Verificar
ls -la ~/claude-code-data/
```

## 7.2 Restaurar .claude Global (se houver backup)

```bash
# Se fez backup de ~/.claude do Windows
cp -r /media/$USER/PENDRIVE/.claude/* ~/.claude/
```

## 7.3 Configurar .env

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench/docker

cp .env.example .env
nano .env
```

Preencha:

```
GEMINI_API_KEY=sua_chave_aqui
TRELLO_API_KEY=sua_chave_aqui
TRELLO_API_TOKEN=seu_token_aqui
TRELLO_BOARD_ID=seu_board_id_aqui
```

Salvar: `Ctrl+O` → `ENTER` → `Ctrl+X`

---

# FASE 8: SETUP PYTHON VENVS

## 8.1 Legal Workbench Principal

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

## 8.2 Ferramentas (se necessário)

```bash
# STJ Dados Abertos
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench/ferramentas/stj-dados-abertos
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate

# Legal Text Extractor
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench/ferramentas/legal-text-extractor
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate

# Prompt Library
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench/ferramentas/prompt-library
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
```

## 8.3 PoC FastHTML

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench/poc-fasthtml-stj
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
```

---

# FASE 9: SETUP NODE.JS

## 9.1 PoC React STJ

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench/poc-react-stj
npm install

# Verificar
npm run build
```

---

# FASE 10: DOCKER SERVICES

## 10.1 Build e Start

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench/docker

# Build todos os services
docker compose build

# Start
docker compose up -d

# Aguarde 2-3 minutos para todos ficarem healthy
```

## 10.2 Verificar Status

```bash
docker compose ps
```

Todos devem mostrar `healthy`:

```
NAME                 STATUS
lw-hub               Up (healthy)
lw-text-extractor    Up (healthy)
lw-doc-assembler     Up (healthy)
lw-stj-api           Up (healthy)
lw-fasthtml-stj      Up (healthy)
lw-trello-mcp        Up (healthy)
lw-redis             Up (healthy)
```

## 10.3 Se algum falhar

```bash
# Ver logs do service específico
docker compose logs lw-text-extractor

# Restart específico
docker compose restart lw-text-extractor

# Rebuild específico
docker compose up -d --build lw-text-extractor
```

---

# FASE 11: INSTALAR CHROME

## 11.1 Download e Instalação

```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb

# Se der erro de dependência:
sudo apt --fix-broken install -y
```

## 11.2 Sincronizar Dados

```
1. Abra Chrome
2. Sign in com sua conta Google
3. Turn on sync
4. Aguarde 5-10 minutos
5. Verifique:
   - Bookmarks aparecem?
   - Senhas funcionam?
   - Extensions instalando?
```

## 11.3 Extensions que Precisam Reinstalar

```
Se alguma extension não sincronizou:
1. Chrome Web Store
2. Busque pelo nome
3. Instale manualmente:
   - React Developer Tools
   - Redux DevTools
   - JSON Formatter
   - [suas extensões]
```

## 11.4 Importar Bookmarks (se Sync falhou)

```
1. Chrome → Bookmarks → Importar
2. Selecione: bookmarks_backup.html (do pendrive)
```

---

# FASE 12: CONFIGURAR HOOKS

## 12.1 Verificar Permissões

```bash
cd ~/claude-work/repos/Claude-Code-Projetos

# Dar permissão de execução aos hooks
chmod +x .claude/hooks/*.sh
chmod +x .claude/hooks/*.js
chmod +x .claude/hooks/*.py
chmod +x .claude/hooks/lib/*.js
chmod +x .claude/scripts/*.sh
chmod +x .claude/monitoring/hooks/*.sh
chmod +x .claude/statusline/*.js
chmod +x .claude/tools/*.sh
```

## 12.2 Sincronizar Agents

```bash
# Executar sync manual
.claude/scripts/sync-agents.sh

# Verificar
ls ~/.claude/agents/
```

## 12.3 Testar Hooks

```bash
# Iniciar Claude Code no projeto
cd ~/claude-work/repos/Claude-Code-Projetos
claude

# Verificar logs de hooks (em outro terminal)
tail -f ~/.vibe-log/hooks.log 2>/dev/null || echo "vibe-log não instalado (OK)"
```

---

# FASE 13: ALIASES E BASHRC

## 13.1 Adicionar Aliases

```bash
cat >> ~/.bashrc << 'EOF'

# === Claude Code Projetos ===
export CLAUDE_PROJECT_DIR="$HOME/claude-work/repos/Claude-Code-Projetos"

# Legal Workbench
alias lw='cd $CLAUDE_PROJECT_DIR/legal-workbench && source .venv/bin/activate'
alias lw-run='cd $CLAUDE_PROJECT_DIR/legal-workbench && source .venv/bin/activate && streamlit run app.py'

# Docker
alias lw-docker='cd $CLAUDE_PROJECT_DIR/legal-workbench/docker && docker compose'
alias lw-up='cd $CLAUDE_PROJECT_DIR/legal-workbench/docker && docker compose up -d'
alias lw-down='cd $CLAUDE_PROJECT_DIR/legal-workbench/docker && docker compose down'
alias lw-logs='cd $CLAUDE_PROJECT_DIR/legal-workbench/docker && docker compose logs -f'
alias lw-ps='cd $CLAUDE_PROJECT_DIR/legal-workbench/docker && docker compose ps'
alias lw-restart='cd $CLAUDE_PROJECT_DIR/legal-workbench/docker && docker compose restart'

# Claude Code
alias cc='cd $CLAUDE_PROJECT_DIR && claude'

# Python venv helper
venv() {
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        echo "venv ativado: $(which python)"
    else
        echo "Erro: .venv não encontrado"
    fi
}
EOF

source ~/.bashrc
```

---

# FASE 14: VERIFICAÇÃO FINAL

## 14.1 Checklist de Ferramentas

```bash
echo "=== VERIFICAÇÃO FINAL ==="
echo "Git: $(git --version)"
echo "Python: $(python --version)"
echo "Node: $(node --version)"
echo "Bun: $(bun --version)"
echo "Docker: $(docker --version)"
echo "Docker Compose: $(docker compose version)"
echo "Claude: $(claude --version)"
echo "Chrome: $(google-chrome --version)"
echo "Tesseract: $(tesseract --version | head -1)"
echo "jq: $(jq --version)"
echo "========================="
```

## 14.2 Checklist Docker

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench/docker
docker compose ps | grep -c "healthy"
# Deve retornar: 6 ou 7
```

## 14.3 Teste Legal Workbench

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench
source .venv/bin/activate
streamlit run app.py

# Abrir: http://localhost:8501
# Testar cada módulo
# Ctrl+C para parar
```

## 14.4 Teste FastHTML STJ

```bash
# Verificar container
curl http://localhost:5001/health

# Ou acessar no browser
# http://localhost:5001
```

## 14.5 Teste Claude Code + Hooks

```bash
cd ~/claude-work/repos/Claude-Code-Projetos
claude

# Digitar um prompt e verificar:
# - Hooks executam sem erro
# - Agents disponíveis
# - Skills funcionando
```

---

# TROUBLESHOOTING

## Docker permission denied

```bash
sudo usermod -aG docker $USER
# Logout e login novamente
```

## pyenv não encontrado

```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc
```

## pip install falha com erro de compilação

```bash
sudo apt install -y python3-dev libpq-dev gcc
pip install -r requirements.txt
```

## Tesseract language não encontrado

```bash
sudo apt install tesseract-ocr-por
```

## WiFi não funciona

```bash
# Verificar hardware
lspci | grep -i network

# Se Realtek RTL8821CE:
sudo apt install rtl8821ce-dkms
sudo reboot
```

## Tela preta após boot

```
1. Reinicie → GRUB → pressione 'e'
2. Linha "linux": adicione ao final: nomodeset
3. Ctrl+X para bootar

Se funcionar, faça permanente:
sudo nano /etc/default/grub
# Mude: GRUB_CMDLINE_LINUX_DEFAULT="quiet splash nomodeset"
sudo update-grub
sudo reboot
```

## Chrome profile locked

```bash
rm -f ~/.config/google-chrome/Singleton*
```

## Hooks não executam

```bash
# Verificar permissões
chmod +x ~/claude-work/repos/Claude-Code-Projetos/.claude/hooks/*
chmod +x ~/claude-work/repos/Claude-Code-Projetos/.claude/hooks/lib/*

# Verificar Bun
which bun
bun --version

# Verificar se settings.json está correto
cat ~/claude-work/repos/Claude-Code-Projetos/.claude/settings.json | head -50
```

---

# CHECKLIST RESUMIDO (IMPRIMIR)

## PRÉ-MIGRAÇÃO (Windows)
- [ ] Salvar secrets (.env) em password manager
- [ ] git push --all origin
- [ ] Backup ~/.claude/
- [ ] Backup ~/claude-code-data/
- [ ] Backup ~/.ssh/
- [ ] Export Chrome bookmarks/passwords
- [ ] Ativar Chrome Sync
- [ ] Download Ubuntu ISO
- [ ] Criar USB bootável

## INSTALAÇÃO
- [ ] Desabilitar Secure Boot na BIOS
- [ ] Boot USB
- [ ] Instalar com LUKS encryption
- [ ] Atualizar sistema

## DEPENDÊNCIAS
- [ ] Pacotes essenciais (apt)
- [ ] Dependências Python (apt)
- [ ] OCR/PDF deps
- [ ] OpenCV deps

## AMBIENTE DEV
- [ ] Git configurado
- [ ] SSH keys
- [ ] pyenv + Python 3.11
- [ ] nvm + Node 22
- [ ] Bun
- [ ] Docker
- [ ] Claude Code

## PROJETO
- [ ] Clone repositório
- [ ] Restaurar dados backup
- [ ] Configurar .env
- [ ] venvs Python (legal-workbench + ferramentas)
- [ ] npm install (poc-react-stj)
- [ ] Docker services healthy

## APPS
- [ ] Chrome instalado
- [ ] Chrome sync funcionando
- [ ] Extensions instaladas

## HOOKS
- [ ] Permissões OK
- [ ] Agents sincronizados
- [ ] Hooks executando

## VERIFICAÇÃO
- [ ] Todas ferramentas instaladas
- [ ] Docker 6+ healthy
- [ ] Streamlit funciona
- [ ] FastHTML funciona
- [ ] Claude Code + Hooks OK

---

**TEMPO ESTIMADO:** 2-3 horas
**RISCO:** Baixo (com backups)
