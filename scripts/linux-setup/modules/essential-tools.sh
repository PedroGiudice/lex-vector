#!/bin/bash
set -e

DISTRO=$(grep ^ID= /etc/os-release | cut -d= -f2 | tr -d '"')

echo "Installing essential development tools for $DISTRO..."

if [[ "$DISTRO" == "ubuntu" ]] || [[ "$DISTRO" == "debian" ]]; then
    sudo apt update
    sudo apt install -y \
        build-essential \
        git \
        curl \
        wget \
        ca-certificates \
        gnupg \
        lsb-release \
        software-properties-common \
        apt-transport-https \
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

    # Criar symlinks para compatibilidade
    echo "Creating symlinks for fd and bat..."
    sudo ln -sf $(which fdfind) /usr/local/bin/fd 2>/dev/null || true
    sudo ln -sf $(which batcat) /usr/local/bin/bat 2>/dev/null || true

elif [[ "$DISTRO" == "fedora" ]]; then
    sudo dnf update -y
    sudo dnf groupinstall -y "Development Tools"
    sudo dnf install -y \
        git \
        curl \
        wget \
        ca-certificates \
        gnupg2 \
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
fi

echo "Essential tools installed successfully!"
echo "Installed: git, curl, wget, vim, neovim, ripgrep, fd, fzf, bat, exa, jq, tree"
