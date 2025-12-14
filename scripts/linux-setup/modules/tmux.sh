#!/bin/bash
set -e

DISTRO=$(grep ^ID= /etc/os-release | cut -d= -f2 | tr -d '"')

echo "Installing Tmux..."

# Instalar Tmux
if [[ "$DISTRO" == "ubuntu" ]] || [[ "$DISTRO" == "debian" ]]; then
    sudo apt install -y tmux
elif [[ "$DISTRO" == "fedora" ]]; then
    sudo dnf install -y tmux
fi

# Instalar TPM (Tmux Plugin Manager) se não existir
if [ ! -d "$HOME/.tmux/plugins/tpm" ]; then
    echo "Installing TPM (Tmux Plugin Manager)..."
    git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
else
    echo "TPM already installed, skipping..."
fi

# Criar configuração do Tmux
echo "Creating Tmux configuration..."
cat > ~/.tmux.conf << 'EOF'
# ==========================
# Tmux Configuration - DevOps Optimized
# ==========================

# Prefix key (Ctrl-a instead of Ctrl-b)
unbind C-b
set-option -g prefix C-a
bind-key C-a send-prefix

# Reload config
bind r source-file ~/.tmux.conf \; display "Config reloaded!"

# Split panes using | and -
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"
unbind '"'
unbind %

# Navigate panes (vim-style)
bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R

# Resize panes
bind -r H resize-pane -L 5
bind -r J resize-pane -D 5
bind -r K resize-pane -U 5
bind -r L resize-pane -R 5

# Mouse mode
set -g mouse on

# Start windows and panes at 1, not 0
set -g base-index 1
set -g pane-base-index 1
set-window-option -g pane-base-index 1
set-option -g renumber-windows on

# Terminal colors
set -g default-terminal "screen-256color"
set -ga terminal-overrides ",*256col*:Tc"

# Status bar
set -g status-position bottom
set -g status-justify left
set -g status-style 'bg=colour234 fg=colour137'
set -g status-left ''
set -g status-right '#[fg=colour233,bg=colour241,bold] %d/%m #[fg=colour233,bg=colour245,bold] %H:%M:%S '
set -g status-right-length 50
set -g status-left-length 20

# Window status
setw -g window-status-current-style 'fg=colour1 bg=colour19 bold'
setw -g window-status-current-format ' #I#[fg=colour249]:#[fg=colour255]#W#[fg=colour249]#F '
setw -g window-status-style 'fg=colour9 bg=colour18'
setw -g window-status-format ' #I#[fg=colour237]:#[fg=colour250]#W#[fg=colour244]#F '

# Pane borders
set -g pane-border-style 'fg=colour238'
set -g pane-active-border-style 'fg=colour51'

# Vi mode
set-window-option -g mode-keys vi
bind-key -T copy-mode-vi v send-keys -X begin-selection
bind-key -T copy-mode-vi C-v send-keys -X rectangle-toggle
bind-key -T copy-mode-vi y send-keys -X copy-selection-and-cancel

# ==========================
# Plugins
# ==========================
set -g @plugin 'tmux-plugins/tpm'
set -g @plugin 'tmux-plugins/tmux-sensible'
set -g @plugin 'tmux-plugins/tmux-yank'
set -g @plugin 'tmux-plugins/tmux-resurrect'
set -g @plugin 'tmux-plugins/tmux-continuum'
set -g @plugin 'christoomey/vim-tmux-navigator'

# Plugin settings
set -g @continuum-restore 'on'
set -g @resurrect-capture-pane-contents 'on'

# Initialize TPM (keep this line at the very bottom)
run '~/.tmux/plugins/tpm/tpm'
EOF

# Instalar plugins
echo "Installing Tmux plugins..."
~/.tmux/plugins/tpm/bin/install_plugins

echo "Tmux installed successfully!"
tmux -V
echo ""
echo "Configuration file created at: ~/.tmux.conf"
echo ""
echo "Tmux shortcuts:"
echo "  Ctrl+a | - Split vertical"
echo "  Ctrl+a - - Split horizontal"
echo "  Ctrl+a h/j/k/l - Navigate panes"
echo "  Ctrl+a d - Detach session"
echo "  Ctrl+a r - Reload config"
