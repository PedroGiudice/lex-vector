#!/bin/bash

# ==========================
# Linux Development Environment Verification
# ==========================

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   Development Environment Verification                   ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}\n"

# Função para verificar comando
check_command() {
    local cmd=$1
    local name=$2
    local version_flag=${3:---version}

    if command -v $cmd &> /dev/null; then
        version=$($cmd $version_flag 2>&1 | head -1)
        echo -e "${GREEN}✓${NC} $name: ${GREEN}$version${NC}"
        return 0
    else
        echo -e "${RED}✗${NC} $name: ${RED}Not installed${NC}"
        return 1
    fi
}

# Contador de falhas
FAILURES=0

# Sistema
echo -e "${YELLOW}=== System ===${NC}"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '"')"
echo "Kernel: $(uname -r)"
echo ""

# Build essentials
echo -e "${YELLOW}=== Build Tools ===${NC}"
check_command "gcc" "GCC" --version || ((FAILURES++))
check_command "make" "Make" --version || ((FAILURES++))
check_command "git" "Git" --version || ((FAILURES++))
echo ""

# Modern CLI tools
echo -e "${YELLOW}=== Modern CLI Tools ===${NC}"
check_command "rg" "ripgrep" --version || ((FAILURES++))
check_command "fd" "fd" --version || ((FAILURES++))
check_command "bat" "bat" --version || ((FAILURES++))
check_command "fzf" "fzf" --version || ((FAILURES++))
check_command "jq" "jq" --version || ((FAILURES++))
echo ""

# Python
echo -e "${YELLOW}=== Python ===${NC}"
check_command "pyenv" "pyenv" --version || ((FAILURES++))
check_command "python" "Python" --version || ((FAILURES++))
check_command "pip" "pip" --version || ((FAILURES++))
if command -v pyenv &> /dev/null; then
    echo -e "  Installed versions: ${BLUE}$(pyenv versions --bare | tr '\n' ' ')${NC}"
fi
echo ""

# Node.js
echo -e "${YELLOW}=== Node.js ===${NC}"
check_command "fnm" "fnm" --version || check_command "nvm" "nvm" --version || ((FAILURES++))
check_command "node" "Node.js" --version || ((FAILURES++))
check_command "npm" "npm" --version || ((FAILURES++))
check_command "pnpm" "pnpm" --version
check_command "yarn" "yarn" --version
if command -v fnm &> /dev/null; then
    echo -e "  Installed versions: ${BLUE}$(fnm list | grep -v 'system' | awk '{print $2}' | tr '\n' ' ')${NC}"
fi
echo ""

# Docker
echo -e "${YELLOW}=== Docker ===${NC}"
check_command "docker" "Docker" --version || ((FAILURES++))
check_command "docker" "Docker Compose" "compose version" || ((FAILURES++))
if command -v docker &> /dev/null; then
    if docker ps &> /dev/null; then
        echo -e "${GREEN}✓${NC} Docker daemon: ${GREEN}Running${NC}"
    else
        echo -e "${RED}✗${NC} Docker daemon: ${RED}Not running or permission denied${NC}"
        echo -e "  ${YELLOW}Tip: Run 'newgrp docker' or log out and back in${NC}"
        ((FAILURES++))
    fi
fi
echo ""

# Shell
echo -e "${YELLOW}=== Shell ===${NC}"
echo "Current shell: $SHELL"
check_command "zsh" "Zsh" --version
if [ -d "$HOME/.oh-my-zsh" ]; then
    echo -e "${GREEN}✓${NC} Oh-My-Zsh: ${GREEN}Installed${NC}"
else
    echo -e "${YELLOW}!${NC} Oh-My-Zsh: ${YELLOW}Not installed${NC}"
fi
check_command "starship" "Starship" --version
echo ""

# Terminal tools
echo -e "${YELLOW}=== Terminal Tools ===${NC}"
check_command "tmux" "Tmux" -V
if [ -d "$HOME/.tmux/plugins/tpm" ]; then
    echo -e "${GREEN}✓${NC} TPM: ${GREEN}Installed${NC}"
else
    echo -e "${YELLOW}!${NC} TPM: ${YELLOW}Not installed${NC}"
fi
check_command "alacritty" "Alacritty" --version
echo ""

# Editors
echo -e "${YELLOW}=== Editors ===${NC}"
check_command "vim" "Vim" --version
check_command "nvim" "Neovim" --version
check_command "code" "VS Code" --version
echo ""

# Fonts
echo -e "${YELLOW}=== Fonts ===${NC}"
if fc-list | grep -qi "JetBrains.*Nerd"; then
    echo -e "${GREEN}✓${NC} JetBrainsMono Nerd Font: ${GREEN}Installed${NC}"
else
    echo -e "${YELLOW}!${NC} JetBrainsMono Nerd Font: ${YELLOW}Not found${NC}"
fi
echo ""

# Dotfiles
echo -e "${YELLOW}=== Dotfiles ===${NC}"
if [ -d "$HOME/dotfiles" ]; then
    echo -e "${GREEN}✓${NC} Dotfiles directory: ${GREEN}$HOME/dotfiles${NC}"
    if [ -L "$HOME/.bashrc" ] || [ -L "$HOME/.zshrc" ]; then
        echo -e "${GREEN}✓${NC} Dotfiles symlinks: ${GREEN}Active${NC}"
    else
        echo -e "${YELLOW}!${NC} Dotfiles symlinks: ${YELLOW}Not configured${NC}"
    fi
else
    echo -e "${YELLOW}!${NC} Dotfiles directory: ${YELLOW}Not found${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✓ All critical components installed successfully!${NC}"
else
    echo -e "${YELLOW}! $FAILURES critical component(s) missing or not working${NC}"
    echo -e "${YELLOW}Review the output above and re-run the bootstrap script if needed${NC}"
fi
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Quick reference
echo -e "${YELLOW}Quick Reference:${NC}"
echo "  Python version: pyenv global 3.12.1"
echo "  Node version: fnm use 20"
echo "  Docker test: docker run hello-world"
echo "  Tmux shortcuts: Ctrl+a | (split), Ctrl+a d (detach)"
echo "  Dotfiles backup: cd ~/dotfiles && ./backup.sh"
echo ""
