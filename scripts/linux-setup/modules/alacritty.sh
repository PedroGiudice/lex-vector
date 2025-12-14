#!/bin/bash
set -e

DISTRO=$(grep ^ID= /etc/os-release | cut -d= -f2 | tr -d '"')

echo "Installing Alacritty terminal emulator..."

# Instalar Alacritty
if [[ "$DISTRO" == "ubuntu" ]] || [[ "$DISTRO" == "debian" ]]; then
    echo "Adding Alacritty PPA..."
    sudo add-apt-repository ppa:aslatter/ppa -y
    sudo apt update
    sudo apt install -y alacritty
elif [[ "$DISTRO" == "fedora" ]]; then
    echo "Installing Alacritty from Fedora repos..."
    sudo dnf install -y alacritty
fi

# Instalar JetBrainsMono Nerd Font
echo "Installing JetBrainsMono Nerd Font..."
mkdir -p ~/.local/share/fonts
cd ~/.local/share/fonts

# Download Nerd Font
if [ ! -f "JetBrainsMonoNerdFont-Regular.ttf" ]; then
    echo "Downloading JetBrainsMono Nerd Font..."
    curl -fLo "JetBrainsMonoNerdFont-Regular.ttf" \
        https://github.com/ryanoasis/nerd-fonts/raw/master/patched-fonts/JetBrainsMono/Ligatures/Regular/JetBrainsMonoNerdFont-Regular.ttf
    curl -fLo "JetBrainsMonoNerdFont-Bold.ttf" \
        https://github.com/ryanoasis/nerd-fonts/raw/master/patched-fonts/JetBrainsMono/Ligatures/Bold/JetBrainsMonoNerdFont-Bold.ttf
    curl -fLo "JetBrainsMonoNerdFont-Italic.ttf" \
        https://github.com/ryanoasis/nerd-fonts/raw/master/patched-fonts/JetBrainsMono/Ligatures/Italic/JetBrainsMonoNerdFont-Italic.ttf
fi

# Rebuild font cache
fc-cache -fv

# Criar configuração do Alacritty
echo "Creating Alacritty configuration..."
mkdir -p ~/.config/alacritty
cat > ~/.config/alacritty/alacritty.toml << 'EOF'
# Alacritty Configuration - DevOps Optimized

[window]
padding = { x = 10, y = 10 }
decorations = "full"
opacity = 0.95
dynamic_padding = false

[font]
normal = { family = "JetBrainsMono Nerd Font", style = "Regular" }
bold = { family = "JetBrainsMono Nerd Font", style = "Bold" }
italic = { family = "JetBrainsMono Nerd Font", style = "Italic" }
size = 12.0

[font.offset]
x = 0
y = 0

[colors.primary]
background = "#1e1e2e"
foreground = "#cdd6f4"

[colors.cursor]
text = "#1e1e2e"
cursor = "#f5e0dc"

[colors.normal]
black = "#45475a"
red = "#f38ba8"
green = "#a6e3a1"
yellow = "#f9e2af"
blue = "#89b4fa"
magenta = "#f5c2e7"
cyan = "#94e2d5"
white = "#bac2de"

[colors.bright]
black = "#585b70"
red = "#f38ba8"
green = "#a6e3a1"
yellow = "#f9e2af"
blue = "#89b4fa"
magenta = "#f5c2e7"
cyan = "#94e2d5"
white = "#a6adc8"

[cursor]
style = { shape = "Block", blinking = "On" }
blink_interval = 500

[[keyboard.bindings]]
key = "V"
mods = "Control|Shift"
action = "Paste"

[[keyboard.bindings]]
key = "C"
mods = "Control|Shift"
action = "Copy"

[[keyboard.bindings]]
key = "N"
mods = "Control|Shift"
action = "SpawnNewInstance"

[[keyboard.bindings]]
key = "Plus"
mods = "Control"
action = "IncreaseFontSize"

[[keyboard.bindings]]
key = "Minus"
mods = "Control"
action = "DecreaseFontSize"

[[keyboard.bindings]]
key = "Key0"
mods = "Control"
action = "ResetFontSize"
EOF

echo "Alacritty installed successfully!"
echo ""
echo "Configuration file created at: ~/.config/alacritty/alacritty.toml"
echo "Font installed: JetBrainsMono Nerd Font"
echo ""
echo "You can now launch Alacritty from your application menu or run: alacritty"
