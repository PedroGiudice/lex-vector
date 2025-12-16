# Linux Development Environment Setup

Guia completo e executável para configuração de ambiente de desenvolvimento em Linux (Ubuntu/Fedora).

## Visão Geral

Este setup cria um ambiente de desenvolvimento moderno, otimizado para DevOps e desenvolvimento full-stack, com:
- Tooling essencial automatizado
- Shell configurado para produtividade máxima
- Container-based development
- Dotfiles versionados e portáveis

## Índice

1. [Quick Start](#quick-start)
2. [Ferramentas Essenciais](#1-ferramentas-essenciais)
3. [Shell e Terminal](#2-shell-e-terminal)
4. [Dotfiles Strategy](#3-dotfiles-strategy)
5. [Container Development](#4-container-development)
6. [Scripts de Automação](#5-scripts-de-automação)
7. [Verificação e Troubleshooting](#verificação)

---

## Quick Start

```bash
# Clone este repo (se ainda não tiver)
cd ~
git clone https://github.com/your-org/Claude-Code-Projetos.git
cd Claude-Code-Projetos

# Execute o bootstrap script
chmod +x scripts/linux-setup/bootstrap-linux.sh
./scripts/linux-setup/bootstrap-linux.sh

# Reinicie o terminal ou recarregue o shell
exec $SHELL
```

---

## 1. Ferramentas Essenciais

### 1.1 Sistema Base

#### Ubuntu/Debian
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Build essentials
sudo apt install -y \
  build-essential \
  git \
  curl \
  wget \
  ca-certificates \
  gnupg \
  lsb-release \
  software-properties-common \
  apt-transport-https

# Ferramentas de desenvolvimento
sudo apt install -y \
  vim \
  neovim \
  htop \
  btop \
  ripgrep \
  fd-find \
  fzf \
  bat \
  exa \
  jq \
  yq \
  tree \
  unzip \
  zip \
  net-tools \
  dnsutils

# Symlinks para compatibilidade
sudo ln -s $(which fdfind) /usr/local/bin/fd 2>/dev/null || true
sudo ln -s $(which batcat) /usr/local/bin/bat 2>/dev/null || true
```

#### Fedora/RHEL
```bash
# Atualizar sistema
sudo dnf update -y

# Build essentials
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y \
  git \
  curl \
  wget \
  ca-certificates \
  gnupg2

# Ferramentas de desenvolvimento
sudo dnf install -y \
  vim \
  neovim \
  htop \
  btop \
  ripgrep \
  fd-find \
  fzf \
  bat \
  exa \
  jq \
  yq \
  tree \
  unzip \
  zip \
  bind-utils
```

**Checklist:**
- [ ] Sistema atualizado
- [ ] Build tools instalados
- [ ] Git configurado
- [ ] CLI tools modernos instalados

---

### 1.2 Python (pyenv)

```bash
# Dependências do pyenv (Ubuntu/Debian)
sudo apt install -y \
  libssl-dev \
  zlib1g-dev \
  libbz2-dev \
  libreadline-dev \
  libsqlite3-dev \
  llvm \
  libncursesw5-dev \
  xz-utils \
  tk-dev \
  libxml2-dev \
  libxmlsec1-dev \
  libffi-dev \
  liblzma-dev

# Dependências do pyenv (Fedora)
sudo dnf install -y \
  zlib-devel \
  bzip2 \
  bzip2-devel \
  readline-devel \
  sqlite \
  sqlite-devel \
  openssl-devel \
  tk-devel \
  libffi-devel \
  xz-devel

# Instalar pyenv
curl https://pyenv.run | bash

# Adicionar ao shell (será feito automaticamente pelo bootstrap)
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# Recarregar shell
exec $SHELL

# Instalar versões do Python
pyenv install 3.11.7
pyenv install 3.12.1
pyenv global 3.12.1

# Verificar
python --version
pip --version
```

**Checklist:**
- [ ] pyenv instalado
- [ ] Python 3.11 e 3.12 instalados
- [ ] Global version configurada
- [ ] pip atualizado

---

### 1.3 Node.js (fnm - Fast Node Manager)

```bash
# Instalar fnm (mais rápido que nvm)
curl -fsSL https://fnm.vercel.app/install | bash

# Adicionar ao shell (será feito automaticamente pelo bootstrap)
echo 'eval "$(fnm env --use-on-cd)"' >> ~/.bashrc

# Recarregar shell
exec $SHELL

# Instalar versões do Node.js
fnm install 20
fnm install 18
fnm use 20
fnm default 20

# Verificar
node --version
npm --version

# Ferramentas globais essenciais
npm install -g \
  pnpm \
  yarn \
  typescript \
  ts-node \
  nodemon \
  prettier \
  eslint \
  @biomejs/biome
```

**Alternativa: NVM**
```bash
# Se preferir nvm ao invés de fnm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
exec $SHELL
nvm install 20
nvm use 20
nvm alias default 20
```

**Checklist:**
- [ ] fnm (ou nvm) instalado
- [ ] Node.js 18 e 20 instalados
- [ ] Default version configurada
- [ ] pnpm/yarn instalados
- [ ] TypeScript toolchain instalado

---

### 1.4 Docker + Docker Compose

#### Opção 1: Docker Engine (Standard)

**Ubuntu/Debian:**
```bash
# Remover versões antigas
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do
  sudo apt remove -y $pkg 2>/dev/null || true
done

# Adicionar repositório oficial
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Verificar
docker --version
docker compose version
docker run hello-world
```

**Fedora:**
```bash
# Remover versões antigas
sudo dnf remove -y docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-selinux docker-engine-selinux docker-engine

# Adicionar repositório
sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo

# Instalar
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Iniciar e habilitar
sudo systemctl start docker
sudo systemctl enable docker

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Verificar
docker --version
docker compose version
```

#### Opção 2: Docker Rootless (Recomendado para Segurança)

```bash
# Instalar uidmap (Ubuntu/Debian)
sudo apt install -y uidmap dbus-user-session

# Instalar uidmap (Fedora)
sudo dnf install -y shadow-utils

# Desabilitar Docker system-wide se existir
sudo systemctl disable --now docker.service docker.socket

# Instalar Docker rootless
curl -fsSL https://get.docker.com/rootless | sh

# Adicionar ao PATH
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
echo 'export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock' >> ~/.bashrc

# Habilitar serviço
systemctl --user start docker
systemctl --user enable docker

# Configurar para iniciar no boot
sudo loginctl enable-linger $(whoami)

# Verificar
docker --version
docker run hello-world
```

**Configurações de Performance:**
```bash
# Criar daemon.json
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-address-pools": [
    {
      "base": "172.80.0.0/16",
      "size": 24
    }
  ],
  "features": {
    "buildkit": true
  }
}
EOF

# Restart Docker
sudo systemctl restart docker
```

**Checklist:**
- [ ] Docker instalado (standard ou rootless)
- [ ] Docker Compose plugin instalado
- [ ] Usuário no grupo docker
- [ ] BuildKit habilitado
- [ ] hello-world executado com sucesso

---

### 1.5 Editor: VS Code

#### Ubuntu/Debian
```bash
# Instalar via snap (mais simples)
sudo snap install code --classic

# OU via repositório oficial
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg
sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
rm -f packages.microsoft.gpg
sudo apt update
sudo apt install -y code
```

#### Fedora
```bash
# Adicionar repositório
sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc
sudo sh -c 'echo -e "[code]\nname=Visual Studio Code\nbaseurl=https://packages.microsoft.com/yumrepos/vscode\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc" > /etc/yum.repos.d/vscode.repo'

# Instalar
sudo dnf check-update
sudo dnf install -y code
```

**Extensões Essenciais:**
```bash
# Instalar extensões via CLI
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension dbaeumer.vscode-eslint
code --install-extension esbenp.prettier-vscode
code --install-extension ms-azuretools.vscode-docker
code --install-extension hashicorp.terraform
code --install-extension ms-vscode-remote.remote-containers
code --install-extension GitHub.copilot
code --install-extension eamodio.gitlens
code --install-extension usernamehw.errorlens
code --install-extension bradlc.vscode-tailwindcss
code --install-extension christian-kohler.path-intellisense
```

**Alternativas:**
- **Neovim + LazyVim**: Setup completo em `~/.config/nvim`
- **Zed**: Editor moderno e rápido (https://zed.dev)
- **IntelliJ IDEA Community**: Para Java/Kotlin

**Checklist:**
- [ ] VS Code instalado
- [ ] Extensões essenciais instaladas
- [ ] Settings sync habilitado

---

## 2. Shell e Terminal

### 2.1 Zsh + Oh-My-Zsh

```bash
# Instalar Zsh
# Ubuntu/Debian
sudo apt install -y zsh

# Fedora
sudo dnf install -y zsh

# Definir Zsh como shell padrão
chsh -s $(which zsh)

# Instalar Oh-My-Zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Plugins essenciais
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
git clone https://github.com/zsh-users/zsh-completions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-completions

# Editar ~/.zshrc
sed -i 's/^plugins=(git)/plugins=(git zsh-autosuggestions zsh-syntax-highlighting zsh-completions docker docker-compose kubectl terraform python node npm)/' ~/.zshrc
```

**Alternativa: Fish Shell**
```bash
# Ubuntu/Debian
sudo apt-add-repository ppa:fish-shell/release-3
sudo apt update
sudo apt install -y fish

# Fedora
sudo dnf install -y fish

# Definir como padrão
chsh -s $(which fish)

# Instalar Fisher (plugin manager)
fish
curl -sL https://raw.githubusercontent.com/jorgebucaran/fisher/main/functions/fisher.fish | source && fisher install jorgebucaran/fisher

# Plugins essenciais
fisher install jethrokuan/z
fisher install PatrickF1/fzf.fish
fisher install jorgebucaran/autopair.fish
```

**Checklist:**
- [ ] Zsh ou Fish instalado
- [ ] Shell padrão alterado
- [ ] Plugins de autocompletion instalados
- [ ] Syntax highlighting funcionando

---

### 2.2 Starship Prompt

```bash
# Instalar Starship
curl -sS https://starship.rs/install.sh | sh

# Adicionar ao shell
# Para Zsh
echo 'eval "$(starship init zsh)"' >> ~/.zshrc

# Para Bash
echo 'eval "$(starship init bash)"' >> ~/.bashrc

# Para Fish
echo 'starship init fish | source' >> ~/.config/fish/config.fish

# Criar configuração customizada
mkdir -p ~/.config
cat > ~/.config/starship.toml << 'EOF'
# Configuração Starship otimizada para DevOps

format = """
[╭─](bold green)$username$hostname$directory$git_branch$git_status$python$nodejs$docker_context$kubernetes$terraform$aws
[╰─](bold green)$character"""

[character]
success_symbol = "[➜](bold green)"
error_symbol = "[✗](bold red)"

[username]
style_user = "bold green"
style_root = "bold red"
format = "[$user]($style) "
disabled = false
show_always = true

[hostname]
ssh_only = false
format = "on [$hostname](bold yellow) "
disabled = false

[directory]
truncation_length = 3
truncate_to_repo = true
format = "in [$path]($style)[$read_only]($read_only_style) "
style = "bold cyan"

[git_branch]
symbol = " "
format = "on [$symbol$branch]($style) "
style = "bold purple"

[git_status]
format = '([\[$all_status$ahead_behind\]]($style) )'
style = "bold red"

[python]
symbol = " "
format = 'via [$symbol$pyenv_prefix($version )]($style)'
style = "yellow"

[nodejs]
symbol = " "
format = 'via [$symbol($version )]($style)'
style = "bold green"

[docker_context]
symbol = " "
format = 'via [$symbol$context]($style) '
style = "bold blue"

[kubernetes]
symbol = "⎈ "
format = 'on [$symbol$context( \($namespace\))]($style) '
disabled = false
style = "bold cyan"

[terraform]
symbol = "💠 "
format = 'via [$symbol$workspace]($style) '

[aws]
symbol = "  "
format = 'on [$symbol($profile )(\($region\) )]($style)'
style = "bold yellow"

[cmd_duration]
min_time = 500
format = "took [$duration]($style) "
style = "bold yellow"
EOF

# Recarregar shell
exec $SHELL
```

**Checklist:**
- [ ] Starship instalado
- [ ] Configuração customizada criada
- [ ] Prompt exibindo corretamente
- [ ] Git status visível

---

### 2.3 Terminal Emulators

#### Alacritty (Recomendado - GPU-accelerated)

```bash
# Ubuntu/Debian
sudo add-apt-repository ppa:aslatter/ppa
sudo apt update
sudo apt install -y alacritty

# Fedora
sudo dnf install -y alacritty

# Criar configuração
mkdir -p ~/.config/alacritty
cat > ~/.config/alacritty/alacritty.toml << 'EOF'
[window]
padding = { x = 10, y = 10 }
decorations = "full"
opacity = 0.95

[font]
normal = { family = "JetBrainsMono Nerd Font", style = "Regular" }
bold = { family = "JetBrainsMono Nerd Font", style = "Bold" }
italic = { family = "JetBrainsMono Nerd Font", style = "Italic" }
size = 12.0

[colors.primary]
background = "#1e1e2e"
foreground = "#cdd6f4"

[colors.cursor]
text = "#1e1e2e"
cursor = "#f5e0dc"

[cursor]
style = { shape = "Block", blinking = "On" }

[keyboard]
bindings = [
  { key = "V", mods = "Control|Shift", action = "Paste" },
  { key = "C", mods = "Control|Shift", action = "Copy" },
  { key = "N", mods = "Control|Shift", action = "SpawnNewInstance" },
]
EOF
```

#### Kitty (Alternativa rápida)

```bash
# Ubuntu/Debian
sudo apt install -y kitty

# Fedora
sudo dnf install -y kitty

# Configuração
mkdir -p ~/.config/kitty
cat > ~/.config/kitty/kitty.conf << 'EOF'
# Font
font_family      JetBrainsMono Nerd Font
bold_font        auto
italic_font      auto
bold_italic_font auto
font_size 12.0

# Theme
background_opacity 0.95
background #1e1e2e
foreground #cdd6f4

# Cursor
cursor_shape block
cursor_blink_interval 0.5

# Tabs
tab_bar_style powerline
tab_powerline_style round
EOF
```

**Instalar Nerd Fonts:**
```bash
# Baixar e instalar JetBrainsMono Nerd Font
mkdir -p ~/.local/share/fonts
cd ~/.local/share/fonts
curl -fLo "JetBrains Mono Regular Nerd Font Complete.ttf" \
  https://github.com/ryanoasis/nerd-fonts/raw/master/patched-fonts/JetBrainsMono/Ligatures/Regular/JetBrainsMonoNerdFont-Regular.ttf
curl -fLo "JetBrains Mono Bold Nerd Font Complete.ttf" \
  https://github.com/ryanoasis/nerd-fonts/raw/master/patched-fonts/JetBrainsMono/Ligatures/Bold/JetBrainsMonoNerdFont-Bold.ttf
fc-cache -fv
```

**Checklist:**
- [ ] Terminal emulator instalado (Alacritty/Kitty)
- [ ] Nerd Font instalada
- [ ] Configuração customizada criada
- [ ] Opacity e tema funcionando

---

### 2.4 Tmux Setup

```bash
# Instalar Tmux
# Ubuntu/Debian
sudo apt install -y tmux

# Fedora
sudo dnf install -y tmux

# Instalar TPM (Tmux Plugin Manager)
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm

# Criar configuração otimizada
cat > ~/.tmux.conf << 'EOF'
# ==========================
# Tmux Configuration
# ==========================

# Prefix key (Ctrl-a ao invés de Ctrl-b)
unbind C-b
set-option -g prefix C-a
bind-key C-a send-prefix

# Reload config
bind r source-file ~/.tmux.conf \; display "Config reloaded!"

# Split panes usando | e -
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"
unbind '"'
unbind %

# Navegação entre panes (vim-style)
bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R

# Resize panes
bind -r H resize-pane -L 5
bind -r J resize-pane -D 5
bind -r K resize-pane -U 5
bind -r L resize-pane -R 5

# Mouse mode
set -g mouse on

# Start windows and panes at 1, not 0
set -g base-index 1
set -g pane-base-index 1
set-window-option -g pane-base-index 1
set-option -g renumber-windows on

# Terminal colors
set -g default-terminal "screen-256color"
set -ga terminal-overrides ",*256col*:Tc"

# Status bar
set -g status-position bottom
set -g status-justify left
set -g status-style 'bg=colour234 fg=colour137'
set -g status-left ''
set -g status-right '#[fg=colour233,bg=colour241,bold] %d/%m #[fg=colour233,bg=colour245,bold] %H:%M:%S '
set -g status-right-length 50
set -g status-left-length 20

# Window status
setw -g window-status-current-style 'fg=colour1 bg=colour19 bold'
setw -g window-status-current-format ' #I#[fg=colour249]:#[fg=colour255]#W#[fg=colour249]#F '
setw -g window-status-style 'fg=colour9 bg=colour18'
setw -g window-status-format ' #I#[fg=colour237]:#[fg=colour250]#W#[fg=colour244]#F '

# Pane borders
set -g pane-border-style 'fg=colour238'
set -g pane-active-border-style 'fg=colour51'

# Vi mode
set-window-option -g mode-keys vi
bind-key -T copy-mode-vi v send-keys -X begin-selection
bind-key -T copy-mode-vi C-v send-keys -X rectangle-toggle
bind-key -T copy-mode-vi y send-keys -X copy-selection-and-cancel

# ==========================
# Plugins
# ==========================
set -g @plugin 'tmux-plugins/tpm'
set -g @plugin 'tmux-plugins/tmux-sensible'
set -g @plugin 'tmux-plugins/tmux-yank'
set -g @plugin 'tmux-plugins/tmux-resurrect'
set -g @plugin 'tmux-plugins/tmux-continuum'
set -g @plugin 'christoomey/vim-tmux-navigator'

# Plugin settings
set -g @continuum-restore 'on'
set -g @resurrect-capture-pane-contents 'on'

# Initialize TPM (keep this line at the very bottom)
run '~/.tmux/plugins/tpm/tpm'
EOF

# Instalar plugins
tmux source ~/.tmux.conf
~/.tmux/plugins/tpm/bin/install_plugins
```

**Comandos Essenciais:**
- `Ctrl+a |` - Split vertical
- `Ctrl+a -` - Split horizontal
- `Ctrl+a h/j/k/l` - Navegar entre panes
- `Ctrl+a d` - Detach session
- `tmux attach` - Reattach session
- `Ctrl+a r` - Reload config

**Checklist:**
- [ ] Tmux instalado
- [ ] TPM instalado
- [ ] Configuração customizada criada
- [ ] Plugins instalados
- [ ] Mouse mode funcionando

---

## 3. Dotfiles Strategy

### 3.1 Estrutura de Dotfiles

```bash
# Criar repositório de dotfiles
mkdir -p ~/dotfiles
cd ~/dotfiles
git init

# Estrutura recomendada
mkdir -p {shell,git,vim,tmux,vscode,scripts}

# Estrutura final:
# ~/dotfiles/
# ├── shell/
# │   ├── .bashrc
# │   ├── .zshrc
# │   ├── .bash_aliases
# │   └── .zsh_aliases
# ├── git/
# │   ├── .gitconfig
# │   └── .gitignore_global
# ├── vim/
# │   └── .vimrc
# ├── tmux/
# │   └── .tmux.conf
# ├── vscode/
# │   ├── settings.json
# │   └── keybindings.json
# ├── scripts/
# │   ├── install.sh
# │   └── backup.sh
# └── README.md
```

### 3.2 Install Script (Symlink Management)

```bash
# Criar script de instalação
cat > ~/dotfiles/install.sh << 'EOF'
#!/bin/bash
set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

DOTFILES_DIR="$HOME/dotfiles"
BACKUP_DIR="$HOME/dotfiles_backup_$(date +%Y%m%d_%H%M%S)"

# Função para criar backup
backup_file() {
    local file=$1
    if [ -f "$file" ] || [ -d "$file" ]; then
        echo -e "${YELLOW}Backing up $file${NC}"
        mkdir -p "$BACKUP_DIR"
        cp -r "$file" "$BACKUP_DIR/"
    fi
}

# Função para criar symlink
create_symlink() {
    local source=$1
    local target=$2

    if [ -e "$target" ]; then
        backup_file "$target"
        rm -rf "$target"
    fi

    echo -e "${GREEN}Linking $source -> $target${NC}"
    ln -sf "$source" "$target"
}

echo -e "${GREEN}Installing dotfiles...${NC}"

# Shell
create_symlink "$DOTFILES_DIR/shell/.bashrc" "$HOME/.bashrc"
create_symlink "$DOTFILES_DIR/shell/.zshrc" "$HOME/.zshrc"
create_symlink "$DOTFILES_DIR/shell/.bash_aliases" "$HOME/.bash_aliases"

# Git
create_symlink "$DOTFILES_DIR/git/.gitconfig" "$HOME/.gitconfig"
create_symlink "$DOTFILES_DIR/git/.gitignore_global" "$HOME/.gitignore_global"

# Tmux
create_symlink "$DOTFILES_DIR/tmux/.tmux.conf" "$HOME/.tmux.conf"

# Vim
create_symlink "$DOTFILES_DIR/vim/.vimrc" "$HOME/.vimrc"

# VS Code (Linux)
mkdir -p "$HOME/.config/Code/User"
create_symlink "$DOTFILES_DIR/vscode/settings.json" "$HOME/.config/Code/User/settings.json"
create_symlink "$DOTFILES_DIR/vscode/keybindings.json" "$HOME/.config/Code/User/keybindings.json"

# Starship
mkdir -p "$HOME/.config"
if [ -f "$DOTFILES_DIR/starship/starship.toml" ]; then
    create_symlink "$DOTFILES_DIR/starship/starship.toml" "$HOME/.config/starship.toml"
fi

# Alacritty
mkdir -p "$HOME/.config/alacritty"
if [ -f "$DOTFILES_DIR/alacritty/alacritty.toml" ]; then
    create_symlink "$DOTFILES_DIR/alacritty/alacritty.toml" "$HOME/.config/alacritty/alacritty.toml"
fi

echo -e "${GREEN}Dotfiles installed successfully!${NC}"
if [ -d "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}Backups saved to: $BACKUP_DIR${NC}"
fi
EOF

chmod +x ~/dotfiles/install.sh
```

### 3.3 Backup Script

```bash
# Criar script de backup
cat > ~/dotfiles/backup.sh << 'EOF'
#!/bin/bash
set -e

DOTFILES_DIR="$HOME/dotfiles"

echo "Backing up current configurations to dotfiles repo..."

# Shell
cp ~/.bashrc "$DOTFILES_DIR/shell/.bashrc" 2>/dev/null || true
cp ~/.zshrc "$DOTFILES_DIR/shell/.zshrc" 2>/dev/null || true
cp ~/.bash_aliases "$DOTFILES_DIR/shell/.bash_aliases" 2>/dev/null || true

# Git
cp ~/.gitconfig "$DOTFILES_DIR/git/.gitconfig" 2>/dev/null || true
cp ~/.gitignore_global "$DOTFILES_DIR/git/.gitignore_global" 2>/dev/null || true

# Tmux
cp ~/.tmux.conf "$DOTFILES_DIR/tmux/.tmux.conf" 2>/dev/null || true

# Vim
cp ~/.vimrc "$DOTFILES_DIR/vim/.vimrc" 2>/dev/null || true

# VS Code
mkdir -p "$DOTFILES_DIR/vscode"
cp ~/.config/Code/User/settings.json "$DOTFILES_DIR/vscode/settings.json" 2>/dev/null || true
cp ~/.config/Code/User/keybindings.json "$DOTFILES_DIR/vscode/keybindings.json" 2>/dev/null || true

# Starship
mkdir -p "$DOTFILES_DIR/starship"
cp ~/.config/starship.toml "$DOTFILES_DIR/starship/starship.toml" 2>/dev/null || true

# Alacritty
mkdir -p "$DOTFILES_DIR/alacritty"
cp ~/.config/alacritty/alacritty.toml "$DOTFILES_DIR/alacritty/alacritty.toml" 2>/dev/null || true

echo "Backup complete! Don't forget to commit and push changes."
EOF

chmod +x ~/dotfiles/backup.sh
```

### 3.4 Git Configuration

```bash
# Criar .gitconfig base
cat > ~/dotfiles/git/.gitconfig << 'EOF'
[user]
    name = Your Name
    email = your.email@example.com

[core]
    editor = vim
    excludesfile = ~/.gitignore_global
    autocrlf = input
    pager = delta

[interactive]
    diffFilter = delta --color-only

[delta]
    navigate = true
    light = false
    side-by-side = true
    line-numbers = true

[merge]
    conflictstyle = diff3

[diff]
    colorMoved = default

[alias]
    st = status
    ci = commit
    co = checkout
    br = branch
    lg = log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit
    last = log -1 HEAD
    unstage = reset HEAD --
    amend = commit --amend
    pushf = push --force-with-lease

[pull]
    rebase = true

[push]
    default = current
    autoSetupRemote = true

[init]
    defaultBranch = main

[fetch]
    prune = true
EOF

# Criar .gitignore_global
cat > ~/dotfiles/git/.gitignore_global << 'EOF'
# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
.pytest_cache/

# Node
node_modules/
npm-debug.log
yarn-error.log

# Env files
.env
.env.local

# Build outputs
dist/
build/
*.log
EOF
```

**Checklist:**
- [ ] Dotfiles repo criado
- [ ] Estrutura de diretórios configurada
- [ ] Install script criado e testado
- [ ] Backup script criado
- [ ] Gitconfig configurado

---

## 4. Container Development

### 4.1 Docker vs Rootless Docker vs Podman

**Comparação:**

| Feature | Docker (Standard) | Docker Rootless | Podman |
|---------|------------------|-----------------|--------|
| Requer root | Sim (daemon) | Não | Não |
| Security | Médio | Alto | Alto |
| Performance | Melhor | Boa | Boa |
| Compose support | Nativo | Nativo | Via plugin |
| Drop-in replacement | - | - | Sim |

### 4.2 Dev Containers (VS Code)

```bash
# Instalar extensão
code --install-extension ms-vscode-remote.remote-containers

# Exemplo de .devcontainer/devcontainer.json
mkdir -p .devcontainer
cat > .devcontainer/devcontainer.json << 'EOF'
{
  "name": "Python 3.12 Dev",
  "image": "mcr.microsoft.com/devcontainers/python:3.12",

  "features": {
    "ghcr.io/devcontainers/features/node:1": {
      "version": "20"
    },
    "ghcr.io/devcontainers/features/git:1": {},
    "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  },

  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python"
      }
    }
  },

  "forwardPorts": [8000, 3000, 5432],

  "postCreateCommand": "pip install -r requirements.txt",

  "remoteUser": "vscode"
}
EOF
```

### 4.3 Docker Compose Templates

**Full-stack Development:**
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  # Backend API
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    volumes:
      - ./backend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://postgres:password@db:5432/mydb
    depends_on:
      - db
      - redis
    command: npm run dev

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:3000
    command: npm run dev

  # Database
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=mydb
    ports:
      - "5432:5432"

  # Redis cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Adminer (DB management)
  adminer:
    image: adminer
    ports:
      - "8080:8080"
    depends_on:
      - db

volumes:
  postgres_data:
  redis_data:
```

### 4.4 Podman como Alternativa

```bash
# Instalar Podman (Ubuntu)
sudo apt update
sudo apt install -y podman podman-compose

# Instalar Podman (Fedora)
sudo dnf install -y podman podman-compose

# Configurar para usar como drop-in replacement do Docker
echo 'alias docker=podman' >> ~/.bashrc
echo 'alias docker-compose=podman-compose' >> ~/.bashrc

# Habilitar socket para compatibilidade
systemctl --user enable --now podman.socket
echo 'export DOCKER_HOST=unix:///run/user/$UID/podman/podman.sock' >> ~/.bashrc

# Verificar
podman --version
podman run hello-world
```

**Checklist:**
- [ ] Docker ou Podman configurado
- [ ] Docker Compose funcionando
- [ ] Dev Containers extension instalada (se usar VS Code)
- [ ] Template de compose criado
- [ ] Volumes persistentes testados

---

## 5. Scripts de Automação

### 5.1 Bootstrap Script Principal

```bash
# Criar scripts/linux-setup/bootstrap-linux.sh
mkdir -p scripts/linux-setup
cat > scripts/linux-setup/bootstrap-linux.sh << 'EOFMAIN'
#!/bin/bash

set -e

# ==========================
# Linux Development Environment Bootstrap
# ==========================

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Detectar distro
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    else
        echo -e "${RED}Cannot detect Linux distribution${NC}"
        exit 1
    fi
}

# Banner
echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   Linux Development Environment Setup                    ║
║   Automated Bootstrap Script                             ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

detect_distro
echo -e "${GREEN}Detected: $DISTRO $VERSION${NC}\n"

# Verificar se está executando como root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Please do not run as root${NC}"
    exit 1
fi

# Menu de seleção
echo -e "${YELLOW}Select components to install:${NC}"
echo "1) Essential Dev Tools"
echo "2) Python (pyenv)"
echo "3) Node.js (fnm)"
echo "4) Docker"
echo "5) Zsh + Oh-My-Zsh"
echo "6) Starship Prompt"
echo "7) Tmux"
echo "8) Alacritty Terminal"
echo "9) VS Code"
echo "10) All of the above"
echo "0) Exit"
echo ""
read -p "Enter your choices (space-separated, e.g., 1 2 3): " choices

# Função para instalar componentes
install_component() {
    local component=$1
    local script_path="scripts/linux-setup/modules/${component}.sh"

    if [ -f "$script_path" ]; then
        echo -e "\n${GREEN}Installing $component...${NC}"
        bash "$script_path"
    else
        echo -e "${YELLOW}Script not found: $script_path${NC}"
    fi
}

# Processar escolhas
for choice in $choices; do
    case $choice in
        1) install_component "essential-tools" ;;
        2) install_component "python-pyenv" ;;
        3) install_component "nodejs-fnm" ;;
        4) install_component "docker" ;;
        5) install_component "zsh-setup" ;;
        6) install_component "starship" ;;
        7) install_component "tmux" ;;
        8) install_component "alacritty" ;;
        9) install_component "vscode" ;;
        10)
            install_component "essential-tools"
            install_component "python-pyenv"
            install_component "nodejs-fnm"
            install_component "docker"
            install_component "zsh-setup"
            install_component "starship"
            install_component "tmux"
            install_component "alacritty"
            install_component "vscode"
            ;;
        0) exit 0 ;;
        *) echo -e "${RED}Invalid choice: $choice${NC}" ;;
    esac
done

echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Setup Complete!                                          ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Restart your terminal or run: exec \$SHELL"
echo "2. Verify installations with: python --version, node --version, docker --version"
echo "3. Configure your dotfiles"
echo ""
EOFMAIN

chmod +x scripts/linux-setup/bootstrap-linux.sh
```

### 5.2 Módulos de Instalação

```bash
# Criar estrutura de módulos
mkdir -p scripts/linux-setup/modules

# Módulo: Essential Tools
cat > scripts/linux-setup/modules/essential-tools.sh << 'EOF'
#!/bin/bash
set -e

DISTRO=$(grep ^ID= /etc/os-release | cut -d= -f2 | tr -d '"')

if [[ "$DISTRO" == "ubuntu" ]] || [[ "$DISTRO" == "debian" ]]; then
    sudo apt update
    sudo apt install -y \
        build-essential git curl wget ca-certificates gnupg \
        vim neovim htop ripgrep fd-find fzf bat exa jq tree unzip

    # Symlinks
    sudo ln -sf $(which fdfind) /usr/local/bin/fd 2>/dev/null || true
    sudo ln -sf $(which batcat) /usr/local/bin/bat 2>/dev/null || true

elif [[ "$DISTRO" == "fedora" ]]; then
    sudo dnf groupinstall -y "Development Tools"
    sudo dnf install -y \
        git curl wget ca-certificates gnupg2 \
        vim neovim htop ripgrep fd-find fzf bat exa jq tree unzip
fi

echo "Essential tools installed successfully!"
EOF

# Módulo: Python (pyenv)
cat > scripts/linux-setup/modules/python-pyenv.sh << 'EOF'
#!/bin/bash
set -e

DISTRO=$(grep ^ID= /etc/os-release | cut -d= -f2 | tr -d '"')

# Dependências
if [[ "$DISTRO" == "ubuntu" ]] || [[ "$DISTRO" == "debian" ]]; then
    sudo apt install -y libssl-dev zlib1g-dev libbz2-dev libreadline-dev \
        libsqlite3-dev llvm libncursesw5-dev xz-utils tk-dev libxml2-dev \
        libxmlsec1-dev libffi-dev liblzma-dev
elif [[ "$DISTRO" == "fedora" ]]; then
    sudo dnf install -y zlib-devel bzip2 bzip2-devel readline-devel \
        sqlite sqlite-devel openssl-devel tk-devel libffi-devel xz-devel
fi

# Instalar pyenv
if [ ! -d "$HOME/.pyenv" ]; then
    curl https://pyenv.run | bash
fi

# Adicionar ao shell
if ! grep -q 'PYENV_ROOT' ~/.bashrc; then
    cat >> ~/.bashrc << 'EOFPY'

# Pyenv
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
EOFPY
fi

if [ -f ~/.zshrc ] && ! grep -q 'PYENV_ROOT' ~/.zshrc; then
    cat >> ~/.zshrc << 'EOFPY'

# Pyenv
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
EOFPY
fi

# Source para usar imediatamente
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Instalar versões do Python
pyenv install -s 3.12.1
pyenv install -s 3.11.7
pyenv global 3.12.1

echo "Python (pyenv) installed successfully!"
python --version
EOF

# Módulo: Node.js (fnm)
cat > scripts/linux-setup/modules/nodejs-fnm.sh << 'EOF'
#!/bin/bash
set -e

# Instalar fnm
if [ ! -d "$HOME/.local/share/fnm" ]; then
    curl -fsSL https://fnm.vercel.app/install | bash
fi

# Adicionar ao shell
if ! grep -q 'fnm env' ~/.bashrc; then
    echo 'eval "$(fnm env --use-on-cd)"' >> ~/.bashrc
fi

if [ -f ~/.zshrc ] && ! grep -q 'fnm env' ~/.zshrc; then
    echo 'eval "$(fnm env --use-on-cd)"' >> ~/.zshrc
fi

# Source para usar imediatamente
eval "$(fnm env --use-on-cd)"

# Instalar Node.js
fnm install 20
fnm install 18
fnm use 20
fnm default 20

# NPM global tools
npm install -g pnpm yarn typescript ts-node prettier eslint

echo "Node.js (fnm) installed successfully!"
node --version
npm --version
EOF

# Módulo: Docker
cat > scripts/linux-setup/modules/docker.sh << 'EOF'
#!/bin/bash
set -e

DISTRO=$(grep ^ID= /etc/os-release | cut -d= -f2 | tr -d '"')

if [[ "$DISTRO" == "ubuntu" ]] || [[ "$DISTRO" == "debian" ]]; then
    # Remover versões antigas
    for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do
        sudo apt remove -y $pkg 2>/dev/null || true
    done

    # Adicionar repo oficial
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

elif [[ "$DISTRO" == "fedora" ]]; then
    sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
    sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo systemctl start docker
    sudo systemctl enable docker
fi

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

echo "Docker installed successfully!"
echo "Please log out and back in for group changes to take effect"
EOF

# Módulo: Zsh
cat > scripts/linux-setup/modules/zsh-setup.sh << 'EOF'
#!/bin/bash
set -e

DISTRO=$(grep ^ID= /etc/os-release | cut -d= -f2 | tr -d '"')

# Instalar Zsh
if [[ "$DISTRO" == "ubuntu" ]] || [[ "$DISTRO" == "debian" ]]; then
    sudo apt install -y zsh
elif [[ "$DISTRO" == "fedora" ]]; then
    sudo dnf install -y zsh
fi

# Instalar Oh-My-Zsh
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

# Plugins
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions 2>/dev/null || true
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting 2>/dev/null || true
git clone https://github.com/zsh-users/zsh-completions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-completions 2>/dev/null || true

# Configurar plugins
sed -i 's/^plugins=(git)/plugins=(git zsh-autosuggestions zsh-syntax-highlighting zsh-completions docker docker-compose kubectl python node npm)/' ~/.zshrc 2>/dev/null || true

# Definir como shell padrão
chsh -s $(which zsh)

echo "Zsh + Oh-My-Zsh installed successfully!"
EOF

# Tornar todos executáveis
chmod +x scripts/linux-setup/modules/*.sh
```

### 5.3 Ansible Playbook (Opcional)

```bash
# Criar playbook Ansible para setup completo
cat > scripts/linux-setup/ansible-setup.yml << 'EOF'
---
- name: Linux Development Environment Setup
  hosts: localhost
  connection: local
  become: false

  vars:
    python_versions:
      - 3.12.1
      - 3.11.7
    node_versions:
      - 20
      - 18

  tasks:
    - name: Detect distribution
      ansible.builtin.setup:
        gather_subset:
          - '!all'
          - '!min'
          - distribution

    - name: Install essential tools (Ubuntu/Debian)
      ansible.builtin.apt:
        name:
          - build-essential
          - git
          - curl
          - wget
          - vim
          - neovim
          - htop
          - ripgrep
          - fd-find
          - fzf
          - bat
          - exa
          - jq
          - tree
        state: present
        update_cache: yes
      become: yes
      when: ansible_distribution in ['Ubuntu', 'Debian']

    - name: Install essential tools (Fedora)
      ansible.builtin.dnf:
        name:
          - '@Development Tools'
          - git
          - curl
          - wget
          - vim
          - neovim
          - htop
          - ripgrep
          - fd-find
          - fzf
          - bat
          - exa
          - jq
          - tree
        state: present
      become: yes
      when: ansible_distribution == 'Fedora'

    - name: Install pyenv
      ansible.builtin.shell: |
        curl https://pyenv.run | bash
      args:
        creates: "{{ ansible_env.HOME }}/.pyenv"

    - name: Install fnm
      ansible.builtin.shell: |
        curl -fsSL https://fnm.vercel.app/install | bash
      args:
        creates: "{{ ansible_env.HOME }}/.local/share/fnm"

    - name: Install Zsh
      ansible.builtin.package:
        name: zsh
        state: present
      become: yes

    - name: Install Oh-My-Zsh
      ansible.builtin.shell: |
        sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
      args:
        creates: "{{ ansible_env.HOME }}/.oh-my-zsh"

    - name: Install Starship
      ansible.builtin.shell: |
        curl -sS https://starship.rs/install.sh | sh -s -- -y
      args:
        creates: /usr/local/bin/starship
      become: yes

    - name: Install Docker (Ubuntu/Debian)
      block:
        - name: Add Docker GPG key
          ansible.builtin.apt_key:
            url: https://download.docker.com/linux/ubuntu/gpg
            state: present

        - name: Add Docker repository
          ansible.builtin.apt_repository:
            repo: "deb [arch=amd64] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
            state: present

        - name: Install Docker
          ansible.builtin.apt:
            name:
              - docker-ce
              - docker-ce-cli
              - containerd.io
              - docker-buildx-plugin
              - docker-compose-plugin
            state: present
            update_cache: yes

        - name: Add user to docker group
          ansible.builtin.user:
            name: "{{ ansible_env.USER }}"
            groups: docker
            append: yes
      become: yes
      when: ansible_distribution in ['Ubuntu', 'Debian']
EOF
```

**Checklist:**
- [ ] Bootstrap script criado
- [ ] Módulos de instalação criados
- [ ] Scripts testados
- [ ] Ansible playbook criado (opcional)
- [ ] Documentação atualizada

---

## Verificação

### Checklist Final

Execute estes comandos para verificar a instalação:

```bash
# Sistema
echo "=== System ===" && uname -a

# Git
echo "=== Git ===" && git --version

# Python
echo "=== Python ===" && python --version && pip --version

# Node.js
echo "=== Node.js ===" && node --version && npm --version

# Docker
echo "=== Docker ===" && docker --version && docker compose version

# Shell
echo "=== Shell ===" && echo $SHELL

# Starship
echo "=== Starship ===" && starship --version

# Tmux
echo "=== Tmux ===" && tmux -V

# VS Code
echo "=== VS Code ===" && code --version

# Modern CLI tools
echo "=== Modern Tools ==="
rg --version | head -1
fd --version
bat --version | head -1
```

### Troubleshooting

**Python/pyenv não encontrado:**
```bash
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

**Node/fnm não encontrado:**
```bash
eval "$(fnm env --use-on-cd)"
```

**Docker permission denied:**
```bash
# Relogin ou execute:
newgrp docker
```

**Zsh plugins não carregando:**
```bash
# Recarregar zsh
source ~/.zshrc
```

---

## Próximos Passos

1. **Configurar Git:**
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

2. **Instalar delta (better git diff):**
   ```bash
   # Ubuntu
   wget https://github.com/dandavison/delta/releases/download/0.16.5/git-delta_0.16.5_amd64.deb
   sudo dpkg -i git-delta_0.16.5_amd64.deb

   # Fedora
   sudo dnf install git-delta
   ```

3. **Configurar SSH keys:**
   ```bash
   ssh-keygen -t ed25519 -C "your.email@example.com"
   eval "$(ssh-agent -s)"
   ssh-add ~/.ssh/id_ed25519
   ```

4. **Sincronizar dotfiles:**
   ```bash
   cd ~/dotfiles
   ./backup.sh
   git add .
   git commit -m "Update dotfiles"
   git push
   ```

---

## Recursos Adicionais

- [Oh-My-Zsh Plugins](https://github.com/ohmyzsh/ohmyzsh/wiki/Plugins)
- [Starship Configuration](https://starship.rs/config/)
- [Tmux Cheat Sheet](https://tmuxcheatsheet.com/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [VS Code Tips and Tricks](https://code.visualstudio.com/docs/getstarted/tips-and-tricks)

---

## Contribuindo

Para adicionar novos módulos ao bootstrap:

1. Criar script em `scripts/linux-setup/modules/nome-do-modulo.sh`
2. Adicionar opção no menu do `bootstrap-linux.sh`
3. Testar em Ubuntu e Fedora
4. Documentar neste README

---

**Última atualização:** 2025-12-14
**Maintainers:** DevOps Team
