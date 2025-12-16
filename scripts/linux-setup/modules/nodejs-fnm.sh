#!/bin/bash
set -e

echo "Installing Node.js via fnm (Fast Node Manager)..."

# Instalar fnm se não existir
if [ ! -d "$HOME/.local/share/fnm" ]; then
    echo "Installing fnm..."
    curl -fsSL https://fnm.vercel.app/install | bash
else
    echo "fnm already installed, skipping..."
fi

# Adicionar ao bashrc se não existir
if ! grep -q 'fnm env' ~/.bashrc; then
    echo "Adding fnm to ~/.bashrc..."
    echo 'eval "$(fnm env --use-on-cd)"' >> ~/.bashrc
fi

# Adicionar ao zshrc se existir
if [ -f ~/.zshrc ] && ! grep -q 'fnm env' ~/.zshrc; then
    echo "Adding fnm to ~/.zshrc..."
    echo 'eval "$(fnm env --use-on-cd)"' >> ~/.zshrc
fi

# Carregar fnm no shell atual
eval "$(fnm env --use-on-cd)"

# Instalar versões do Node.js
echo "Installing Node.js 20..."
fnm install 20

echo "Installing Node.js 18..."
fnm install 18

# Definir versão padrão
echo "Setting Node.js 20 as default..."
fnm use 20
fnm default 20

# Instalar ferramentas globais essenciais
echo "Installing global npm packages..."
npm install -g \
    pnpm \
    yarn \
    typescript \
    ts-node \
    nodemon \
    prettier \
    eslint

echo "Node.js (fnm) installed successfully!"
node --version
npm --version

echo ""
echo "Available Node.js versions:"
fnm list

echo ""
echo "Global packages installed:"
npm list -g --depth=0
