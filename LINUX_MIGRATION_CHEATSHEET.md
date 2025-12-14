# Linux Migration Troubleshooting Cheat Sheet

Quick reference guide for common issues when migrating from Windows to Linux as a development machine.

---

## 1. Boot Problems

### Secure Boot Issues
**Symptom:** System won't boot, shows "Secure Boot Violation" or similar

**Solutions:**
```bash
# Option 1: Disable Secure Boot in BIOS/UEFI
# - Reboot → F2/F12/Del (check your manufacturer)
# - Security tab → Disable Secure Boot
# - Save and Exit

# Option 2: Sign kernel modules (for NVIDIA, VirtualBox, etc.)
sudo mokutil --import /var/lib/shim-signed/mok/MOK.der
# Reboot and follow MOK Manager prompts
```

### GRUB Not Showing / Stuck
**Symptom:** Black screen, no OS selection menu

**Solutions:**
```bash
# Boot from USB and mount your system
sudo mount /dev/sdXY /mnt  # Replace X and Y with your partition
sudo mount --bind /dev /mnt/dev
sudo mount --bind /proc /mnt/proc
sudo mount --bind /sys /mnt/sys
sudo chroot /mnt

# Reinstall GRUB
update-grub
grub-install /dev/sdX  # Whole disk, not partition

# Exit and reboot
exit
sudo umount /mnt/dev /mnt/proc /mnt/sys /mnt
reboot
```

### UEFI vs Legacy Boot
**Symptom:** Installed system won't boot, BIOS doesn't show it

**Check:**
```bash
# Verify boot mode (inside live USB or existing Linux)
[ -d /sys/firmware/efi ] && echo "UEFI" || echo "Legacy"

# List EFI entries
efibootmgr -v

# Add EFI entry manually
sudo efibootmgr -c -d /dev/sdX -p Y -L "Ubuntu" -l "\EFI\ubuntu\shimx64.efi"
```

**Fix:** Ensure installation mode matches BIOS setting (both UEFI or both Legacy)

---

## 2. Hardware Problems

### WiFi Not Working
**Symptom:** No WiFi networks showing, adapter not recognized

**Diagnosis:**
```bash
# Check if WiFi hardware is detected
lspci | grep -i wireless
lsusb | grep -i wireless  # For USB adapters

# Check if driver is loaded
lsmod | grep -i wifi
lsmod | grep -i iwl  # Intel
lsmod | grep -i ath  # Atheros
lsmod | grep -i rtw  # Realtek

# Check WiFi interface status
ip link show
nmcli device status
```

**Solutions:**
```bash
# Enable WiFi (if soft-blocked)
rfkill list
sudo rfkill unblock wifi

# Install common WiFi drivers
sudo apt update
sudo apt install linux-firmware  # Ubuntu/Debian
sudo dnf install linux-firmware  # Fedora

# For Intel WiFi
sudo apt install firmware-iwlwifi
sudo modprobe -r iwlwifi && sudo modprobe iwlwifi

# For Broadcom (common in Dell, HP laptops)
sudo apt install broadcom-sta-dkms
sudo modprobe -r b43 b43legacy bcma ssb wl
sudo modprobe wl

# For Realtek
git clone https://github.com/lwfinger/rtw88.git
cd rtw88
make
sudo make install
sudo modprobe rtw88_8822ce  # Adjust for your model
```

### NVIDIA Driver Issues
**Symptom:** Low resolution, screen tearing, poor performance

**Diagnosis:**
```bash
# Check current driver
lspci | grep -i nvidia
nvidia-smi  # If NVIDIA driver installed
lsmod | grep nouveau  # Open-source driver
```

**Solutions:**
```bash
# Ubuntu/Pop!_OS (recommended method)
sudo ubuntu-drivers devices
sudo ubuntu-drivers autoinstall
# Or manually:
sudo apt install nvidia-driver-535  # Check latest version

# Fedora
sudo dnf install akmod-nvidia
sudo dnf install xorg-x11-drv-nvidia-cuda  # For CUDA

# Arch
sudo pacman -S nvidia nvidia-utils

# Disable nouveau (NVIDIA open-source driver)
sudo bash -c "echo blacklist nouveau > /etc/modprobe.d/blacklist-nvidia-nouveau.conf"
sudo bash -c "echo options nouveau modeset=0 >> /etc/modprobe.d/blacklist-nvidia-nouveau.conf"
sudo update-initramfs -u
sudo reboot

# If stuck in login loop after driver install
# Ctrl+Alt+F3 → login
sudo apt remove --purge nvidia-*
sudo apt install nvidia-driver-535  # Reinstall
sudo reboot
```

### Bluetooth Not Working
**Symptom:** Bluetooth toggle missing, devices not pairing

**Solutions:**
```bash
# Check Bluetooth status
systemctl status bluetooth
rfkill list bluetooth

# Enable Bluetooth
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
rfkill unblock bluetooth

# Restart Bluetooth service
sudo systemctl restart bluetooth

# If device pairs but doesn't connect (audio)
sudo apt install pulseaudio-module-bluetooth
pulseaudio -k  # Kill and auto-restart

# Reset Bluetooth
sudo rmmod btusb
sudo modprobe btusb
```

### Touchpad/Mouse Issues
**Symptom:** Touchpad not working, gestures disabled, wrong sensitivity

**Solutions:**
```bash
# Check if detected
xinput list
libinput list-devices

# Enable touchpad if disabled
xinput list  # Find device ID
xinput set-prop <ID> "Device Enabled" 1

# Configure libinput (GNOME)
gsettings set org.gnome.desktop.peripherals.touchpad tap-to-click true
gsettings set org.gnome.desktop.peripherals.touchpad natural-scroll true
gsettings set org.gnome.desktop.peripherals.touchpad two-finger-scrolling-enabled true

# Install touchpad GUI (for detailed config)
sudo apt install gnome-tweaks  # GNOME
# Settings → Keyboard & Mouse → Mouse Click Emulation

# For Synaptics touchpads
sudo apt install xserver-xorg-input-synaptics
# Create /etc/X11/xorg.conf.d/70-synaptics.conf
```

**Mouse acceleration fix:**
```bash
# Disable mouse acceleration (GNOME)
gsettings set org.gnome.desktop.peripherals.mouse accel-profile 'flat'

# Or via xinput
xinput list  # Find mouse ID
xinput set-prop <ID> "libinput Accel Profile Enabled" 0, 1
```

---

## 3. Development Environment Problems

### Docker Permission Issues
**Symptom:** "permission denied while trying to connect to Docker daemon socket"

**Solutions:**
```bash
# Add user to docker group (logout required)
sudo usermod -aG docker $USER
newgrp docker  # Or logout/login

# Verify
groups
docker run hello-world

# If still fails, check Docker socket permissions
ls -la /var/run/docker.sock
sudo chmod 666 /var/run/docker.sock  # Quick fix (not persistent)

# Proper fix: ensure docker group owns socket
sudo chown root:docker /var/run/docker.sock
sudo systemctl restart docker
```

### Python Path Issues
**Symptom:** "ModuleNotFoundError", wrong Python version, pip installs to wrong location

**Diagnosis:**
```bash
which python
which python3
python --version
python3 --version

which pip
which pip3
pip --version

# Check Python paths
python3 -m site
```

**Solutions:**
```bash
# Use python3 explicitly (Ubuntu doesn't symlink 'python')
sudo apt install python-is-python3  # Creates 'python' symlink

# Always use virtual environments
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Fix pip path issues
python3 -m pip install --user <package>  # User install
# Or use venv (recommended)

# Update alternatives (set default Python)
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1
sudo update-alternatives --config python

# Never use 'sudo pip install' globally!
# Use venv or --user flag
```

### Node/npm Global Permissions
**Symptom:** "EACCES: permission denied" when installing global packages

**Solutions:**
```bash
# Option 1: Use nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
# Restart terminal
nvm install --lts
nvm use --lts
npm install -g yarn pnpm  # No sudo needed!

# Option 2: Change npm default directory
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# Option 3: Fix existing permissions (not recommended)
sudo chown -R $(whoami) ~/.npm
sudo chown -R $(whoami) /usr/local/lib/node_modules

# Verify
npm config get prefix  # Should be ~/.npm-global or nvm path
```

### VS Code Extensions Not Working
**Symptom:** Extensions crash, features missing, remote development issues

**Solutions:**
```bash
# Install proper VS Code (not Snap version)
# Download from https://code.visualstudio.com/
sudo apt install ./<file>.deb

# Or use official repo
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
sudo apt update
sudo apt install code

# Remove Snap version
sudo snap remove code

# Fix extension issues
# Ctrl+Shift+P → "Developer: Reload Window"
# Or delete extension cache:
rm -rf ~/.vscode/extensions/*
# Reinstall extensions

# For Remote-SSH issues
ssh-keygen -t ed25519 -C "your_email@example.com"
ssh-copy-id user@remote-host

# Fix Python extension issues
code --install-extension ms-python.python
# Ctrl+Shift+P → "Python: Select Interpreter"
```

---

## 4. Productivity Issues

### Font Rendering (Blurry/Ugly Fonts)
**Symptom:** Text looks blurry, jagged, or different from Windows

**Solutions:**
```bash
# Install Microsoft fonts
sudo apt install ttf-mscorefonts-installer
sudo fc-cache -f -v

# Install better fonts
sudo apt install fonts-noto fonts-roboto fonts-ubuntu
sudo apt install fonts-firacode  # For coding

# Enable font antialiasing (GNOME)
gsettings set org.gnome.desktop.interface font-antialiasing 'rgba'
gsettings set org.gnome.desktop.interface font-hinting 'slight'

# Or use GNOME Tweaks
sudo apt install gnome-tweaks
# Tweaks → Fonts → Hinting: Slight, Antialiasing: Subpixel

# Create ~/.config/fontconfig/fonts.conf
mkdir -p ~/.config/fontconfig
cat > ~/.config/fontconfig/fonts.conf << 'EOF'
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <match target="font">
    <edit name="antialias" mode="assign">
      <bool>true</bool>
    </edit>
    <edit name="hinting" mode="assign">
      <bool>true</bool>
    </edit>
    <edit name="hintstyle" mode="assign">
      <const>hintslight</const>
    </edit>
    <edit name="rgba" mode="assign">
      <const>rgb</const>
    </edit>
    <edit name="lcdfilter" mode="assign">
      <const>lcddefault</const>
    </edit>
  </match>
</fontconfig>
EOF
fc-cache -f -v
```

### Keyboard Shortcuts Different
**Quick Reference (GNOME):**

| Windows | Linux (GNOME) | Action |
|---------|---------------|--------|
| Win+E | Files app / `nautilus` | File Explorer |
| Win+L | Super+L | Lock screen |
| Ctrl+Alt+Del | Ctrl+Alt+Del | System monitor |
| Win+Tab | Super+Tab | Activities/Overview |
| Alt+Tab | Alt+Tab | Switch windows |
| Win+D | Super+D | Show desktop |
| Win+Arrow | Super+Arrow | Window snapping |
| Print Screen | Print Screen | Screenshot |
| Win+Shift+S | Shift+Print | Area screenshot |
| Ctrl+C/V/X | Ctrl+C/V/X | Copy/Paste/Cut |
| Ctrl+Shift+C/V | (Terminal) | Copy/Paste in terminal |

**Customize shortcuts:**
```bash
# GNOME Settings → Keyboard → Keyboard Shortcuts
# Or via gsettings:

# Custom screenshot to Win+Shift+S
gsettings set org.gnome.shell.keybindings screenshot "['<Super><Shift>s']"

# File manager
gsettings set org.gnome.settings-daemon.plugins.media-keys home "['<Super>e']"

# Close window (Alt+F4 is default, but you can change)
gsettings set org.gnome.desktop.wm.keybindings close "['<Alt>F4']"
```

### Screenshots & Screen Recording
**Built-in Tools:**
```bash
# GNOME Screenshot (default)
Print Screen                    # Full screen
Shift+Print Screen              # Select area
Alt+Print Screen                # Current window
Ctrl+Shift+Alt+R                # Record screen (GNOME 3.38+)

# Save screenshots to custom folder
gsettings set org.gnome.gnome-screenshot auto-save-directory "file:///home/$USER/Pictures/Screenshots"
```

**Better Tools:**
```bash
# Flameshot (like Snipping Tool++)
sudo apt install flameshot
flameshot gui
# Set custom shortcut: flameshot gui

# Shutter (advanced editing)
sudo apt install shutter

# OBS Studio (screen recording/streaming)
sudo apt install obs-studio

# SimpleScreenRecorder (lightweight)
sudo apt install simplescreenrecorder

# Peek (GIF recorder)
sudo apt install peek
```

### Password Manager Integration
**Symptom:** Browser extensions don't work, autofill broken

**Solutions:**
```bash
# 1Password
# Download from https://1password.com/downloads/linux/
# Works with browser extensions

# Bitwarden (open-source)
sudo snap install bitwarden
# Or AppImage from https://bitwarden.com/download/

# KeePassXC
sudo apt install keepassxc
# Enable browser integration:
# Tools → Settings → Browser Integration → Enable

# GNOME Keyring (built-in)
# Usually works automatically, but if not:
sudo apt install gnome-keyring seahorse
# "seahorse" is the GUI manager
```

---

## 5. Emergency Commands

### Black Screen / GUI Won't Start
**Symptom:** Boot succeeds but stuck on black screen or login loop

**Access TTY:**
```bash
# Press: Ctrl+Alt+F3 (or F2, F4, F5, F6)
# Login with your username and password
```

**Diagnosis:**
```bash
# Check display manager status
systemctl status gdm  # GNOME
systemctl status lightdm  # XFCE
systemctl status sddm  # KDE

# Check graphics driver
lsmod | grep -i nvidia
lsmod | grep -i nouveau
lsmod | grep -i amdgpu

# Check Xorg logs
cat /var/log/Xorg.0.log | grep -i error
journalctl -b -0 | grep -i failed
```

**Quick Fixes:**
```bash
# Restart display manager
sudo systemctl restart gdm  # Or lightdm/sddm

# Reinstall desktop environment
sudo apt install --reinstall ubuntu-desktop  # Ubuntu
sudo apt install --reinstall gnome-shell  # GNOME

# Remove problematic driver
sudo apt remove --purge nvidia-*
sudo ubuntu-drivers autoinstall
sudo reboot

# Reconfigure X server
sudo dpkg-reconfigure xserver-xorg

# Boot to recovery mode
# Reboot → Hold Shift → Select "Advanced options" → "Recovery mode"
# → Resume normal boot or Drop to root shell
```

### System Frozen / Unresponsive
**Magic SysRq Keys (kernel-level recovery):**

```bash
# IMPORTANT: Type slowly, wait 1-2 seconds between keys
# "REISUB" = Raising Elephants Is So Utterly Boring

Alt+SysRq+R  # Take keyboard control from X
Alt+SysRq+E  # Send SIGTERM to all processes
Alt+SysRq+I  # Send SIGKILL to all processes
Alt+SysRq+S  # Sync disks
Alt+SysRq+U  # Unmount disks (read-only)
Alt+SysRq+B  # Reboot

# If SysRq not working, enable it:
echo 1 | sudo tee /proc/sys/kernel/sysrq
# Make permanent:
echo "kernel.sysrq = 1" | sudo tee -a /etc/sysctl.conf
```

**Kill Frozen Process:**
```bash
# From TTY (Ctrl+Alt+F3)
top  # Find PID
kill <PID>
kill -9 <PID>  # Force kill

# Or
pkill -f <process-name>
killall <process-name>

# Kill all processes by user (DANGER!)
sudo pkill -u username
```

### Rollback Broken Updates
**Ubuntu/Debian:**
```bash
# List recent package changes
grep " install " /var/log/dpkg.log
grep " upgrade " /var/log/dpkg.log

# Downgrade specific package
sudo apt install <package>=<old-version>
# Hold package version
sudo apt-mark hold <package>

# Full system snapshot rollback (if using Timeshift)
sudo timeshift --list
sudo timeshift --restore --snapshot "<snapshot-name>"

# APT package cache (if still available)
ls /var/cache/apt/archives/
sudo dpkg -i /var/cache/apt/archives/<old-package>.deb
```

**Fedora:**
```bash
# List recent transactions
sudo dnf history

# Undo last transaction
sudo dnf history undo last

# Rollback to specific transaction
sudo dnf history rollback <transaction-id>
```

**Arch:**
```bash
# Downgrade from cache
ls /var/cache/pacman/pkg/
sudo pacman -U /var/cache/pacman/pkg/<old-package>

# Or use downgrade tool
yay -S downgrade
sudo downgrade <package>
```

### Boot to Previous Kernel
**Symptom:** New kernel breaks hardware/drivers

**Steps:**
```bash
# 1. Reboot and hold Shift
# 2. GRUB menu → "Advanced options"
# 3. Select older kernel
# 4. Once booted, remove problematic kernel:

# List installed kernels
dpkg --list | grep linux-image

# Remove specific kernel
sudo apt remove linux-image-5.15.0-xx-generic

# Or prevent auto-updates
sudo apt-mark hold linux-image-generic
```

### Fix Broken Package Manager
**Symptom:** "dpkg was interrupted", "unmet dependencies"

**Solutions:**
```bash
# Reconfigure interrupted packages
sudo dpkg --configure -a

# Fix broken dependencies
sudo apt --fix-broken install
sudo apt autoremove

# Clear package cache
sudo apt clean
sudo apt autoclean

# Nuclear option: force reinstall
sudo apt install --reinstall <package>

# If APT is completely broken
sudo dpkg --force-all -i /var/cache/apt/archives/*.deb

# Last resort: chroot from live USB
# Boot live USB → mount system → chroot → fix packages
```

---

## Quick Diagnostic Commands

```bash
# System info
neofetch                    # Overview
uname -a                    # Kernel version
lsb_release -a              # Distro version

# Hardware
lspci                       # PCI devices
lsusb                       # USB devices
lsblk                       # Block devices/drives
lshw -short                 # All hardware
inxi -Fxz                   # Detailed system info

# Processes & Performance
top / htop                  # Process monitor
ps aux                      # All processes
systemctl status <service>  # Service status
journalctl -xe              # System logs (recent)
dmesg | tail -50            # Kernel messages

# Network
ip addr show                # IP addresses
nmcli device status         # NetworkManager status
ping -c 4 8.8.8.8          # Test connectivity
traceroute google.com       # Route tracing

# Disk
df -h                       # Disk usage
du -sh *                    # Directory sizes
lsblk -f                    # Filesystem types
sudo smartctl -a /dev/sda   # Drive health

# Boot & Services
systemctl list-units --failed      # Failed services
journalctl -b -p err              # Boot errors
systemctl get-default             # Boot target (GUI/CLI)
```

---

## Common Aliases for Ex-Windows Users

Add to `~/.bashrc`:

```bash
# Windows-like commands
alias cls='clear'
alias dir='ls -la'
alias ipconfig='ip addr show'
alias ping='ping -c 4'

# Shortcuts
alias update='sudo apt update && sudo apt upgrade -y'
alias install='sudo apt install'
alias remove='sudo apt remove'

# Safety
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# Docker
alias dps='docker ps'
alias dimg='docker images'
alias dstop='docker stop $(docker ps -aq)'

# Git
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
```

Then run: `source ~/.bashrc`

---

## Resources

- **Ubuntu/Debian Help:** https://askubuntu.com
- **Arch Wiki:** https://wiki.archlinux.org (works for all distros)
- **Hardware Compatibility:** https://linux-hardware.org
- **Distro Selector:** https://distrochooser.de
- **r/linuxquestions:** https://reddit.com/r/linuxquestions

---

**Pro Tip:** Before reporting a bug, run:
```bash
journalctl -b -0 > boot.log
dmesg > dmesg.log
```
Attach these logs when asking for help!
