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
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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
read -p "Enter your choices (space-separated, e.g., 1 2 3 or just 10 for all): " choices

# Função para instalar componentes
install_component() {
    local component=$1
    local script_path="$SCRIPT_DIR/modules/${component}.sh"

    if [ -f "$script_path" ]; then
        echo -e "\n${GREEN}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}Installing: $component${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}\n"
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
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}║  Setup Complete!                                          ║${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Restart your terminal or run: ${GREEN}exec \$SHELL${NC}"
echo "2. Verify installations with: ${GREEN}python --version, node --version, docker --version${NC}"
echo "3. Configure your dotfiles in ~/dotfiles"
echo "4. Set up Git: ${GREEN}git config --global user.name \"Your Name\"${NC}"
echo ""
echo -e "${BLUE}For more information, see: LINUX_DEV_SETUP.md${NC}"
echo ""
