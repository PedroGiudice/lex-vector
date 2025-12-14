#!/bin/bash
set -e

DISTRO=$(grep ^ID= /etc/os-release | cut -d= -f2 | tr -d '"')

echo "Installing VS Code..."

# Instalar VS Code
if [[ "$DISTRO" == "ubuntu" ]] || [[ "$DISTRO" == "debian" ]]; then
    # Adicionar repositório da Microsoft
    echo "Adding Microsoft repository..."
    wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
    sudo install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg
    sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
    rm -f packages.microsoft.gpg

    # Instalar
    sudo apt update
    sudo apt install -y code

elif [[ "$DISTRO" == "fedora" ]]; then
    # Adicionar repositório
    echo "Adding Microsoft repository..."
    sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc
    sudo sh -c 'echo -e "[code]\nname=Visual Studio Code\nbaseurl=https://packages.microsoft.com/yumrepos/vscode\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc" > /etc/yum.repos.d/vscode.repo'

    # Instalar
    sudo dnf check-update
    sudo dnf install -y code
fi

# Instalar extensões essenciais
echo "Installing essential VS Code extensions..."

extensions=(
    "ms-python.python"
    "ms-python.vscode-pylance"
    "dbaeumer.vscode-eslint"
    "esbenp.prettier-vscode"
    "ms-azuretools.vscode-docker"
    "hashicorp.terraform"
    "ms-vscode-remote.remote-containers"
    "ms-vscode-remote.remote-ssh"
    "eamodio.gitlens"
    "usernamehw.errorlens"
    "bradlc.vscode-tailwindcss"
    "christian-kohler.path-intellisense"
    "yzhang.markdown-all-in-one"
    "redhat.vscode-yaml"
    "ms-kubernetes-tools.vscode-kubernetes-tools"
)

for ext in "${extensions[@]}"; do
    echo "Installing extension: $ext"
    code --install-extension "$ext" --force
done

# Criar configuração básica
echo "Creating VS Code settings..."
mkdir -p ~/.config/Code/User

cat > ~/.config/Code/User/settings.json << 'EOF'
{
    "editor.fontSize": 14,
    "editor.fontFamily": "'JetBrainsMono Nerd Font', 'Droid Sans Mono', 'monospace'",
    "editor.fontLigatures": true,
    "editor.lineNumbers": "on",
    "editor.rulers": [80, 120],
    "editor.tabSize": 2,
    "editor.insertSpaces": true,
    "editor.detectIndentation": true,
    "editor.formatOnSave": true,
    "editor.formatOnPaste": false,
    "editor.minimap.enabled": true,
    "editor.bracketPairColorization.enabled": true,
    "editor.guides.bracketPairs": true,

    "workbench.colorTheme": "Default Dark+",
    "workbench.iconTheme": "vs-seti",

    "terminal.integrated.fontSize": 13,
    "terminal.integrated.fontFamily": "JetBrainsMono Nerd Font",
    "terminal.integrated.shell.linux": "/bin/zsh",

    "files.autoSave": "onFocusChange",
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true,

    "python.defaultInterpreterPath": "python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",

    "[javascript]": {
        "editor.defaultFormatter": "esbenp.prettier-vscode"
    },
    "[typescript]": {
        "editor.defaultFormatter": "esbenp.prettier-vscode"
    },
    "[json]": {
        "editor.defaultFormatter": "esbenp.prettier-vscode"
    },
    "[python]": {
        "editor.tabSize": 4
    },

    "git.autofetch": true,
    "git.confirmSync": false,
    "git.enableSmartCommit": true,

    "docker.showStartPage": false
}
EOF

echo "VS Code installed successfully!"
code --version
echo ""
echo "Installed extensions:"
code --list-extensions
echo ""
echo "Settings file created at: ~/.config/Code/User/settings.json"
