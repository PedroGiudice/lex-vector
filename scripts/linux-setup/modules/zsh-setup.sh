#!/bin/bash
set -e

DISTRO=$(grep ^ID= /etc/os-release | cut -d= -f2 | tr -d '"')

echo "Installing Zsh + Oh-My-Zsh..."

# Instalar Zsh
if [[ "$DISTRO" == "ubuntu" ]] || [[ "$DISTRO" == "debian" ]]; then
    echo "Installing Zsh for Ubuntu/Debian..."
    sudo apt install -y zsh
elif [[ "$DISTRO" == "fedora" ]]; then
    echo "Installing Zsh for Fedora..."
    sudo dnf install -y zsh
fi

# Instalar Oh-My-Zsh se não existir
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo "Installing Oh-My-Zsh..."
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
else
    echo "Oh-My-Zsh already installed, skipping..."
fi

# Instalar plugins essenciais
echo "Installing Zsh plugins..."

# zsh-autosuggestions
if [ ! -d "${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions" ]; then
    git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
fi

# zsh-syntax-highlighting
if [ ! -d "${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting" ]; then
    git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
fi

# zsh-completions
if [ ! -d "${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-completions" ]; then
    git clone https://github.com/zsh-users/zsh-completions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-completions
fi

# Configurar plugins no .zshrc
echo "Configuring plugins in .zshrc..."
if [ -f ~/.zshrc ]; then
    # Backup
    cp ~/.zshrc ~/.zshrc.backup

    # Atualizar lista de plugins
    sed -i 's/^plugins=(git)/plugins=(git zsh-autosuggestions zsh-syntax-highlighting zsh-completions docker docker-compose kubectl terraform python node npm)/' ~/.zshrc 2>/dev/null || true
fi

# Definir Zsh como shell padrão
echo "Setting Zsh as default shell..."
chsh -s $(which zsh)

echo "Zsh + Oh-My-Zsh installed successfully!"
echo "Plugins installed: zsh-autosuggestions, zsh-syntax-highlighting, zsh-completions"
echo ""
echo "IMPORTANT: Please restart your terminal or run: exec zsh"
