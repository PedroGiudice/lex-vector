#!/bin/bash
set -e

echo "Installing Starship prompt..."

# Instalar Starship
if ! command -v starship &> /dev/null; then
    echo "Downloading and installing Starship..."
    curl -sS https://starship.rs/install.sh | sh -s -- -y
else
    echo "Starship already installed, skipping..."
fi

# Adicionar ao bashrc se não existir
if ! grep -q 'starship init' ~/.bashrc; then
    echo "Adding Starship to ~/.bashrc..."
    echo 'eval "$(starship init bash)"' >> ~/.bashrc
fi

# Adicionar ao zshrc se existir
if [ -f ~/.zshrc ] && ! grep -q 'starship init' ~/.zshrc; then
    echo "Adding Starship to ~/.zshrc..."
    echo 'eval "$(starship init zsh)"' >> ~/.zshrc
fi

# Criar configuração customizada
echo "Creating Starship configuration..."
mkdir -p ~/.config
cat > ~/.config/starship.toml << 'EOF'
# Starship Configuration - DevOps Optimized

format = """
[╭─](bold green)$username$hostname$directory$git_branch$git_status$python$nodejs$docker_context$kubernetes$terraform$aws
[╰─](bold green)$character"""

[character]
success_symbol = "[➜](bold green)"
error_symbol = "[✗](bold red)"

[username]
style_user = "bold green"
style_root = "bold red"
format = "[$user]($style) "
disabled = false
show_always = true

[hostname]
ssh_only = false
format = "on [$hostname](bold yellow) "
disabled = false

[directory]
truncation_length = 3
truncate_to_repo = true
format = "in [$path]($style)[$read_only]($read_only_style) "
style = "bold cyan"

[git_branch]
symbol = " "
format = "on [$symbol$branch]($style) "
style = "bold purple"

[git_status]
format = '([\[$all_status$ahead_behind\]]($style) )'
style = "bold red"

[python]
symbol = " "
format = 'via [$symbol$pyenv_prefix($version )]($style)'
style = "yellow"

[nodejs]
symbol = " "
format = 'via [$symbol($version )]($style)'
style = "bold green"

[docker_context]
symbol = " "
format = 'via [$symbol$context]($style) '
style = "bold blue"

[kubernetes]
symbol = "⎈ "
format = 'on [$symbol$context( \($namespace\))]($style) '
disabled = false
style = "bold cyan"

[terraform]
symbol = "💠 "
format = 'via [$symbol$workspace]($style) '

[aws]
symbol = "  "
format = 'on [$symbol($profile )(\($region\) )]($style)'
style = "bold yellow"

[cmd_duration]
min_time = 500
format = "took [$duration]($style) "
style = "bold yellow"

[time]
disabled = false
format = '🕙[\[ $time \]]($style) '
time_format = "%T"
style = "bold white"
EOF

echo "Starship installed successfully!"
starship --version
echo ""
echo "Configuration file created at: ~/.config/starship.toml"
echo "Please restart your terminal or run: exec \$SHELL"
