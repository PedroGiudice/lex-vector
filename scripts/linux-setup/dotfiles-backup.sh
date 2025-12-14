#!/bin/bash
set -e

# ==========================
# Dotfiles Backup Script
# Backs up current configs to dotfiles repo
# ==========================

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DOTFILES_DIR="$HOME/dotfiles"

# Verificar se dotfiles existe
if [ ! -d "$DOTFILES_DIR" ]; then
    echo -e "${YELLOW}Creating dotfiles directory structure...${NC}"
    mkdir -p "$DOTFILES_DIR"/{shell,git,vim,tmux,vscode,starship,alacritty,scripts}
fi

echo -e "${GREEN}Backing up current configurations to dotfiles repo...${NC}"

# Shell
echo "Backing up shell configurations..."
[ -f ~/.bashrc ] && cp ~/.bashrc "$DOTFILES_DIR/shell/.bashrc"
[ -f ~/.zshrc ] && cp ~/.zshrc "$DOTFILES_DIR/shell/.zshrc"
[ -f ~/.bash_aliases ] && cp ~/.bash_aliases "$DOTFILES_DIR/shell/.bash_aliases"
[ -f ~/.zsh_aliases ] && cp ~/.zsh_aliases "$DOTFILES_DIR/shell/.zsh_aliases"

# Git
echo "Backing up Git configurations..."
[ -f ~/.gitconfig ] && cp ~/.gitconfig "$DOTFILES_DIR/git/.gitconfig"
[ -f ~/.gitignore_global ] && cp ~/.gitignore_global "$DOTFILES_DIR/git/.gitignore_global"

# Tmux
echo "Backing up Tmux configuration..."
[ -f ~/.tmux.conf ] && cp ~/.tmux.conf "$DOTFILES_DIR/tmux/.tmux.conf"

# Vim
echo "Backing up Vim configuration..."
[ -f ~/.vimrc ] && cp ~/.vimrc "$DOTFILES_DIR/vim/.vimrc"

# Starship
echo "Backing up Starship configuration..."
[ -f ~/.config/starship.toml ] && cp ~/.config/starship.toml "$DOTFILES_DIR/starship/starship.toml"

# Alacritty
echo "Backing up Alacritty configuration..."
[ -f ~/.config/alacritty/alacritty.toml ] && cp ~/.config/alacritty/alacritty.toml "$DOTFILES_DIR/alacritty/alacritty.toml"

# VS Code
echo "Backing up VS Code settings..."
mkdir -p "$DOTFILES_DIR/vscode"
[ -f ~/.config/Code/User/settings.json ] && cp ~/.config/Code/User/settings.json "$DOTFILES_DIR/vscode/settings.json"
[ -f ~/.config/Code/User/keybindings.json ] && cp ~/.config/Code/User/keybindings.json "$DOTFILES_DIR/vscode/keybindings.json"

# Criar README se não existir
if [ ! -f "$DOTFILES_DIR/README.md" ]; then
    cat > "$DOTFILES_DIR/README.md" << 'EOF'
# Dotfiles

Personal development environment configurations.

## Structure

- `shell/` - Shell configurations (.bashrc, .zshrc, aliases)
- `git/` - Git configuration and global gitignore
- `vim/` - Vim configuration
- `tmux/` - Tmux configuration
- `vscode/` - VS Code settings and keybindings
- `starship/` - Starship prompt configuration
- `alacritty/` - Alacritty terminal configuration
- `scripts/` - Utility scripts

## Installation

Run the install script to create symlinks:

```bash
./install.sh
```

## Backup

To backup current configurations:

```bash
./backup.sh
```

## Git Setup

After installing, configure Git with your details:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```
EOF
fi

# Copiar scripts de install/backup para o repo
cp "$(dirname "$0")/dotfiles-install.sh" "$DOTFILES_DIR/install.sh" 2>/dev/null || true
cp "$(dirname "$0")/dotfiles-backup.sh" "$DOTFILES_DIR/backup.sh" 2>/dev/null || true
chmod +x "$DOTFILES_DIR/install.sh" "$DOTFILES_DIR/backup.sh" 2>/dev/null || true

echo -e "\n${GREEN}Backup complete!${NC}"
echo -e "${YELLOW}Files backed up to: $DOTFILES_DIR${NC}"
echo ""
echo "Next steps:"
echo "  cd $DOTFILES_DIR"
echo "  git add ."
echo "  git commit -m 'Update dotfiles'"
echo "  git push"
