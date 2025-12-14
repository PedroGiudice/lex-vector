#!/bin/bash
set -e

# ==========================
# Dotfiles Installation Script
# Manages dotfiles via symlinks
# ==========================

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DOTFILES_DIR="$HOME/dotfiles"
BACKUP_DIR="$HOME/dotfiles_backup_$(date +%Y%m%d_%H%M%S)"

# Verificar se dotfiles existe
if [ ! -d "$DOTFILES_DIR" ]; then
    echo -e "${RED}Dotfiles directory not found at $DOTFILES_DIR${NC}"
    echo -e "${YELLOW}Creating dotfiles structure...${NC}"
    mkdir -p "$DOTFILES_DIR"/{shell,git,vim,tmux,vscode,starship,alacritty,scripts}
    echo -e "${GREEN}Dotfiles structure created. Please populate it with your configurations.${NC}"
    exit 0
fi

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

    if [ -e "$target" ] && [ ! -L "$target" ]; then
        backup_file "$target"
        rm -rf "$target"
    elif [ -L "$target" ]; then
        rm "$target"
    fi

    echo -e "${GREEN}Linking $source -> $target${NC}"
    ln -sf "$source" "$target"
}

echo -e "${GREEN}Installing dotfiles...${NC}"

# Shell configurations
if [ -f "$DOTFILES_DIR/shell/.bashrc" ]; then
    create_symlink "$DOTFILES_DIR/shell/.bashrc" "$HOME/.bashrc"
fi

if [ -f "$DOTFILES_DIR/shell/.zshrc" ]; then
    create_symlink "$DOTFILES_DIR/shell/.zshrc" "$HOME/.zshrc"
fi

if [ -f "$DOTFILES_DIR/shell/.bash_aliases" ]; then
    create_symlink "$DOTFILES_DIR/shell/.bash_aliases" "$HOME/.bash_aliases"
fi

if [ -f "$DOTFILES_DIR/shell/.zsh_aliases" ]; then
    create_symlink "$DOTFILES_DIR/shell/.zsh_aliases" "$HOME/.zsh_aliases"
fi

# Git configurations
if [ -f "$DOTFILES_DIR/git/.gitconfig" ]; then
    create_symlink "$DOTFILES_DIR/git/.gitconfig" "$HOME/.gitconfig"
fi

if [ -f "$DOTFILES_DIR/git/.gitignore_global" ]; then
    create_symlink "$DOTFILES_DIR/git/.gitignore_global" "$HOME/.gitignore_global"
fi

# Tmux configuration
if [ -f "$DOTFILES_DIR/tmux/.tmux.conf" ]; then
    create_symlink "$DOTFILES_DIR/tmux/.tmux.conf" "$HOME/.tmux.conf"
fi

# Vim configuration
if [ -f "$DOTFILES_DIR/vim/.vimrc" ]; then
    create_symlink "$DOTFILES_DIR/vim/.vimrc" "$HOME/.vimrc"
fi

# Starship configuration
mkdir -p "$HOME/.config"
if [ -f "$DOTFILES_DIR/starship/starship.toml" ]; then
    create_symlink "$DOTFILES_DIR/starship/starship.toml" "$HOME/.config/starship.toml"
fi

# Alacritty configuration
mkdir -p "$HOME/.config/alacritty"
if [ -f "$DOTFILES_DIR/alacritty/alacritty.toml" ]; then
    create_symlink "$DOTFILES_DIR/alacritty/alacritty.toml" "$HOME/.config/alacritty/alacritty.toml"
fi

# VS Code settings (Linux)
mkdir -p "$HOME/.config/Code/User"
if [ -f "$DOTFILES_DIR/vscode/settings.json" ]; then
    create_symlink "$DOTFILES_DIR/vscode/settings.json" "$HOME/.config/Code/User/settings.json"
fi

if [ -f "$DOTFILES_DIR/vscode/keybindings.json" ]; then
    create_symlink "$DOTFILES_DIR/vscode/keybindings.json" "$HOME/.config/Code/User/keybindings.json"
fi

echo -e "\n${GREEN}Dotfiles installed successfully!${NC}"
if [ -d "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}Backups saved to: $BACKUP_DIR${NC}"
fi

echo -e "\n${GREEN}Symlinks created:${NC}"
ls -la ~/ | grep ' -> ' | grep -E '(bashrc|zshrc|gitconfig|tmux|vimrc)' || echo "None in home directory"
ls -la ~/.config/ | grep ' -> ' || echo "None in .config"
