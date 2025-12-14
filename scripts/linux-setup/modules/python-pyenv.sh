#!/bin/bash
set -e

DISTRO=$(grep ^ID= /etc/os-release | cut -d= -f2 | tr -d '"')

echo "Installing Python via pyenv..."

# Instalar dependências do pyenv
if [[ "$DISTRO" == "ubuntu" ]] || [[ "$DISTRO" == "debian" ]]; then
    echo "Installing pyenv dependencies for Ubuntu/Debian..."
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

elif [[ "$DISTRO" == "fedora" ]]; then
    echo "Installing pyenv dependencies for Fedora..."
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
fi

# Instalar pyenv se não existir
if [ ! -d "$HOME/.pyenv" ]; then
    echo "Installing pyenv..."
    curl https://pyenv.run | bash
else
    echo "pyenv already installed, skipping..."
fi

# Adicionar ao bashrc se não existir
if ! grep -q 'PYENV_ROOT' ~/.bashrc; then
    echo "Adding pyenv to ~/.bashrc..."
    cat >> ~/.bashrc << 'EOFPY'

# Pyenv configuration
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
EOFPY
fi

# Adicionar ao zshrc se existir
if [ -f ~/.zshrc ] && ! grep -q 'PYENV_ROOT' ~/.zshrc; then
    echo "Adding pyenv to ~/.zshrc..."
    cat >> ~/.zshrc << 'EOFPY'

# Pyenv configuration
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
EOFPY
fi

# Carregar pyenv no shell atual
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Instalar versões do Python
echo "Installing Python 3.12.1..."
pyenv install -s 3.12.1

echo "Installing Python 3.11.7..."
pyenv install -s 3.11.7

# Definir versão global
echo "Setting Python 3.12.1 as global version..."
pyenv global 3.12.1

# Atualizar pip
echo "Updating pip..."
pip install --upgrade pip

echo "Python (pyenv) installed successfully!"
python --version
pip --version

echo ""
echo "Available Python versions:"
pyenv versions
