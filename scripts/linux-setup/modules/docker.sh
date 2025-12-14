#!/bin/bash
set -e

DISTRO=$(grep ^ID= /etc/os-release | cut -d= -f2 | tr -d '"')

echo "Installing Docker..."

if [[ "$DISTRO" == "ubuntu" ]] || [[ "$DISTRO" == "debian" ]]; then
    # Remover versões antigas
    echo "Removing old Docker versions..."
    for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do
        sudo apt remove -y $pkg 2>/dev/null || true
    done

    # Adicionar repositório oficial
    echo "Adding Docker official repository..."
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Instalar Docker
    echo "Installing Docker packages..."
    sudo apt update
    sudo apt install -y \
        docker-ce \
        docker-ce-cli \
        containerd.io \
        docker-buildx-plugin \
        docker-compose-plugin

elif [[ "$DISTRO" == "fedora" ]]; then
    # Remover versões antigas
    echo "Removing old Docker versions..."
    sudo dnf remove -y docker docker-client docker-client-latest docker-common \
        docker-latest docker-latest-logrotate docker-logrotate docker-selinux \
        docker-engine-selinux docker-engine 2>/dev/null || true

    # Adicionar repositório oficial
    echo "Adding Docker official repository..."
    sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo

    # Instalar Docker
    echo "Installing Docker packages..."
    sudo dnf install -y \
        docker-ce \
        docker-ce-cli \
        containerd.io \
        docker-buildx-plugin \
        docker-compose-plugin

    # Iniciar e habilitar Docker
    sudo systemctl start docker
    sudo systemctl enable docker
fi

# Adicionar usuário ao grupo docker
echo "Adding current user to docker group..."
sudo usermod -aG docker $USER

# Configurar daemon.json para melhor performance
echo "Configuring Docker daemon..."
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

echo "Docker installed successfully!"
docker --version
docker compose version

echo ""
echo "IMPORTANT: You need to log out and log back in for docker group changes to take effect."
echo "Alternatively, run: newgrp docker"
