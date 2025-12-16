# Linux Development Environment Setup Scripts

Automated setup scripts for creating a complete development environment on Linux (Ubuntu/Fedora).

## Quick Start

```bash
# Run the bootstrap script
chmod +x bootstrap-linux.sh
./bootstrap-linux.sh

# Follow the interactive menu to select components
# Or run: ./bootstrap-linux.sh
# Then enter: 10 (for all components)
```

## What Gets Installed

### Core Components

1. **Essential Dev Tools**
   - Build tools (gcc, make, etc.)
   - Modern CLI tools (ripgrep, fd, bat, fzf, jq)
   - Network utilities

2. **Python (via pyenv)**
   - Multiple Python versions (3.11, 3.12)
   - Version management
   - Isolated environments

3. **Node.js (via fnm)**
   - Multiple Node versions (18, 20)
   - Fast version switching
   - Global tools (pnpm, yarn, typescript)

4. **Docker**
   - Docker Engine
   - Docker Compose v2
   - BuildKit enabled
   - User added to docker group

5. **Zsh + Oh-My-Zsh**
   - Modern shell
   - Autosuggestions
   - Syntax highlighting
   - Git integration

6. **Starship Prompt**
   - Fast, customizable prompt
   - Git status
   - Python/Node version display
   - Custom DevOps theme

7. **Tmux**
   - Terminal multiplexer
   - Plugin manager (TPM)
   - Vim-style navigation
   - Session persistence

8. **Alacritty**
   - GPU-accelerated terminal
   - Nerd Font installed
   - Custom theme

9. **VS Code**
   - Extensions for Python, Node, Docker
   - Custom settings
   - DevOps-optimized config

## Scripts Overview

### bootstrap-linux.sh
Main installation script with interactive menu.

```bash
./bootstrap-linux.sh
```

### modules/
Individual installation modules for each component:
- `essential-tools.sh` - Base development tools
- `python-pyenv.sh` - Python environment
- `nodejs-fnm.sh` - Node.js environment
- `docker.sh` - Docker installation
- `zsh-setup.sh` - Zsh shell setup
- `starship.sh` - Starship prompt
- `tmux.sh` - Tmux configuration
- `alacritty.sh` - Alacritty terminal
- `vscode.sh` - VS Code installation

### dotfiles-install.sh
Manages dotfiles via symlinks.

```bash
# Create dotfiles structure
./dotfiles-install.sh

# This will:
# - Create ~/dotfiles directory structure
# - Create symlinks from ~/dotfiles to actual config locations
# - Backup existing configs
```

### dotfiles-backup.sh
Backs up current configurations to dotfiles repo.

```bash
# Backup current configs
./dotfiles-backup.sh

# This will copy:
# - Shell configs (.bashrc, .zshrc)
# - Git config
# - Tmux config
# - VS Code settings
# - And more...
```

### verify-installation.sh
Verifies all installations.

```bash
./verify-installation.sh
```

### ansible-setup.yml
Alternative installation via Ansible.

```bash
# Install Ansible first
sudo apt install ansible  # Ubuntu
sudo dnf install ansible  # Fedora

# Run playbook
ansible-playbook ansible-setup.yml
```

## Usage Examples

### Install Only Specific Components

```bash
# Edit bootstrap-linux.sh or run modules directly
./modules/python-pyenv.sh
./modules/docker.sh
```

### Set Up Dotfiles

```bash
# 1. Create dotfiles structure
./dotfiles-install.sh

# 2. Initialize git repo
cd ~/dotfiles
git init
git remote add origin <your-repo-url>

# 3. Backup current configs
../scripts/linux-setup/dotfiles-backup.sh

# 4. Commit and push
git add .
git commit -m "Initial dotfiles"
git push -u origin main

# 5. On new machine, clone and install
git clone <your-repo-url> ~/dotfiles
cd ~/dotfiles
./install.sh
```

### Docker Development

```bash
# Use the provided docker-compose template
cp docker-compose.dev.yml /path/to/your/project/

# Customize services in docker-compose.dev.yml
# Then start:
cd /path/to/your/project
docker compose -f docker-compose.dev.yml up
```

## Post-Installation

### Configure Git

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Set Python Version

```bash
# Global version
pyenv global 3.12.1

# Project-specific version
cd /path/to/project
pyenv local 3.11.7
```

### Set Node Version

```bash
# Global version
fnm default 20

# Auto-switch per directory (uses .node-version or .nvmrc)
echo "20" > .node-version
cd . # fnm will auto-switch
```

### Docker Without Sudo

```bash
# After installation, either:
# 1. Log out and back in
# 2. Or run:
newgrp docker
```

### Start Using Tmux

```bash
# Create new session
tmux new -s dev

# Detach: Ctrl+a d
# Reattach: tmux attach -t dev
# List sessions: tmux ls
```

## Troubleshooting

### Python not found after pyenv install

```bash
# Add to your shell config and reload
exec $SHELL

# Or manually export
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

### Node not found after fnm install

```bash
# Reload shell
exec $SHELL

# Or manually export
eval "$(fnm env --use-on-cd)"
```

### Docker permission denied

```bash
# Check if user is in docker group
groups

# If not, add and reload
sudo usermod -aG docker $USER
newgrp docker
```

### Zsh plugins not loading

```bash
# Reload zsh config
source ~/.zshrc
```

### Starship not showing

```bash
# Check if initialized in shell config
grep starship ~/.zshrc ~/.bashrc

# Add if missing
echo 'eval "$(starship init zsh)"' >> ~/.zshrc
```

## File Structure

```
scripts/linux-setup/
├── bootstrap-linux.sh          # Main installation script
├── modules/                    # Individual component installers
│   ├── essential-tools.sh
│   ├── python-pyenv.sh
│   ├── nodejs-fnm.sh
│   ├── docker.sh
│   ├── zsh-setup.sh
│   ├── starship.sh
│   ├── tmux.sh
│   ├── alacritty.sh
│   └── vscode.sh
├── dotfiles-install.sh         # Dotfiles symlink manager
├── dotfiles-backup.sh          # Dotfiles backup script
├── verify-installation.sh      # Verification script
├── ansible-setup.yml           # Ansible playbook
├── docker-compose.dev.yml      # Docker Compose template
└── README.md                   # This file
```

## Additional Resources

- [LINUX_DEV_SETUP.md](../../LINUX_DEV_SETUP.md) - Detailed setup guide
- [pyenv](https://github.com/pyenv/pyenv)
- [fnm](https://github.com/Schniz/fnm)
- [Oh-My-Zsh](https://ohmyz.sh/)
- [Starship](https://starship.rs/)
- [Tmux](https://github.com/tmux/tmux)
- [Alacritty](https://alacritty.org/)

## Contributing

To add a new component:

1. Create script in `modules/new-component.sh`
2. Add option to `bootstrap-linux.sh` menu
3. Test on Ubuntu and Fedora
4. Update this README

## License

MIT
