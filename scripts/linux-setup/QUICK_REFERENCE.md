# Linux Dev Environment - Quick Reference Card

## Installation

```bash
# Quick install (all components)
cd /home/user/Claude-Code-Projetos/scripts/linux-setup
./bootstrap-linux.sh
# Select option: 10

# Verify installation
./verify-installation.sh
```

## Python (pyenv)

```bash
# List available versions
pyenv install --list

# Install version
pyenv install 3.12.1

# Set global version
pyenv global 3.12.1

# Set local version (per project)
pyenv local 3.11.7

# List installed versions
pyenv versions

# Create virtual environment
python -m venv .venv
source .venv/bin/activate
```

## Node.js (fnm)

```bash
# List available versions
fnm list-remote

# Install version
fnm install 20

# Set default version
fnm default 20

# Use specific version
fnm use 18

# Auto-switch with .node-version file
echo "20" > .node-version

# List installed versions
fnm list
```

## Docker

```bash
# Basic commands
docker ps                    # List running containers
docker ps -a                 # List all containers
docker images                # List images
docker logs <container>      # View logs

# Docker Compose
docker compose up            # Start services
docker compose up -d         # Start in background
docker compose down          # Stop services
docker compose logs -f       # Follow logs
docker compose ps            # List services

# Clean up
docker system prune -a       # Remove unused data
docker volume prune          # Remove unused volumes

# Build
docker build -t myapp .
docker buildx build --platform linux/amd64,linux/arm64 -t myapp .
```

## Git

```bash
# Configuration
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# Useful aliases (already configured)
git st                       # git status
git co <branch>              # git checkout
git br                       # git branch
git lg                       # Pretty log graph
git last                     # Show last commit
git unstage <file>           # Unstage file
git amend                    # Amend last commit
git pushf                    # Force push with lease
```

## Tmux

```bash
# Session management
tmux new -s <name>           # New session
tmux ls                      # List sessions
tmux attach -t <name>        # Attach to session
tmux kill-session -t <name>  # Kill session

# Shortcuts (Prefix: Ctrl+a)
Ctrl+a |                     # Split vertical
Ctrl+a -                     # Split horizontal
Ctrl+a h/j/k/l               # Navigate panes
Ctrl+a H/J/K/L               # Resize panes
Ctrl+a d                     # Detach
Ctrl+a r                     # Reload config
Ctrl+a [                     # Scroll mode (q to exit)
```

## Shell (Zsh)

```bash
# Oh-My-Zsh
omz update                   # Update Oh-My-Zsh
omz reload                   # Reload config

# Navigation
cd -                         # Go to previous directory
..                           # cd ..
...                          # cd ../..

# Aliases (customize in ~/.zsh_aliases)
ll                           # ls -lah
la                           # ls -A
l                            # ls -CF
```

## Modern CLI Tools

```bash
# ripgrep (faster grep)
rg "pattern" [path]
rg -i "case-insensitive"
rg -t py "pattern"           # Search only Python files

# fd (faster find)
fd "filename"
fd -e py                     # Find Python files
fd -H "hidden"               # Include hidden files

# bat (better cat)
bat file.txt                 # Syntax highlighted cat
bat --paging=never file.txt  # No pager

# fzf (fuzzy finder)
Ctrl+r                       # Search command history
Ctrl+t                       # Search files
Alt+c                        # Search directories
```

## VS Code

```bash
# Launch
code .                       # Open current directory
code file.txt                # Open file
code --diff file1 file2      # Compare files

# Extensions
code --list-extensions       # List installed
code --install-extension <ext>
```

## Dotfiles

```bash
# Backup current configs
cd ~/dotfiles
./backup.sh
git add .
git commit -m "Update configs"
git push

# Install on new machine
git clone <your-repo> ~/dotfiles
cd ~/dotfiles
./install.sh
```

## Troubleshooting

```bash
# Python not found
exec $SHELL
pyenv global 3.12.1

# Node not found
exec $SHELL
fnm use 20

# Docker permission denied
newgrp docker
# or logout/login

# Zsh plugins not loading
source ~/.zshrc

# Check what's using a port
sudo lsof -i :3000

# System info
neofetch                     # Pretty system info
htop                         # Process monitor
df -h                        # Disk space
free -h                      # Memory usage
```

## Package Management

```bash
# Ubuntu/Debian
sudo apt update
sudo apt upgrade
sudo apt install <package>
sudo apt remove <package>
sudo apt autoremove

# Fedora
sudo dnf update
sudo dnf upgrade
sudo dnf install <package>
sudo dnf remove <package>
sudo dnf autoremove
```

## Networking

```bash
# Check connectivity
ping google.com
curl -I https://example.com

# DNS lookup
nslookup example.com
dig example.com

# Port scanning
nc -zv localhost 3000
ss -tulpn                    # List open ports

# IP address
ip addr show
hostname -I
```

## Performance

```bash
# CPU info
lscpu
cat /proc/cpuinfo

# Memory
free -h
cat /proc/meminfo

# Disk
df -h
du -sh *
ncdu                         # Interactive disk usage

# Processes
ps aux
top
htop
btop                         # Better top
```

## File Operations

```bash
# Find files
fd "pattern"
find . -name "*.py"

# Search in files
rg "pattern"
grep -r "pattern" .

# Permissions
chmod +x file.sh             # Make executable
chmod 644 file.txt           # rw-r--r--
chmod 755 dir/               # rwxr-xr-x
chown user:group file

# Archives
tar -czf archive.tar.gz dir/
tar -xzf archive.tar.gz
zip -r archive.zip dir/
unzip archive.zip
```

## System Services

```bash
# Systemd
sudo systemctl start <service>
sudo systemctl stop <service>
sudo systemctl restart <service>
sudo systemctl status <service>
sudo systemctl enable <service>   # Start on boot
sudo systemctl disable <service>

# Logs
journalctl -u <service>
journalctl -f                     # Follow logs
journalctl --since today
```

## SSH

```bash
# Generate key
ssh-keygen -t ed25519 -C "your@email.com"

# Copy to server
ssh-copy-id user@host

# Config (~/.ssh/config)
Host myserver
    HostName server.com
    User username
    IdentityFile ~/.ssh/id_ed25519
    Port 22

# Connect
ssh myserver
```

## Quick Scripts

```bash
# Port forward
ssh -L 8080:localhost:80 user@host

# Tunnel
ssh -D 9090 user@host

# Copy via SSH
scp file.txt user@host:/path/
rsync -avz dir/ user@host:/path/

# HTTP server
python -m http.server 8000
# or
npx http-server -p 8000
```

---

**Print this card and keep it handy!**
