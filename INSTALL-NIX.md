# Installing Nix

This guide will help you install Nix with flakes support on macOS, Linux, or Windows (WSL).

## Quick Install

### macOS

1. Install Nix using the official installer:
   ```bash
   sh <(curl -L https://nixos.org/nix/install)
   ```

2. Enable flakes by creating or editing `~/.config/nix/nix.conf`:
   ```bash
   mkdir -p ~/.config/nix
   echo "experimental-features = nix-command flakes" >> ~/.config/nix/nix.conf
   ```

3. Restart your terminal or run:
   ```bash
   source ~/.nix-profile/etc/profile.d/nix.sh
   ```

**Note for macOS 15 Sequoia users**: If you encounter issues, see the [troubleshooting guide](https://github.com/NixOS/nix/issues/10892).

### Linux

1. Install Nix (multi-user installation recommended):
   ```bash
   sh <(curl -L https://nixos.org/nix/install) --daemon
   ```

2. Enable flakes by creating or editing `/etc/nix/nix.conf` (or `~/.config/nix/nix.conf` for single-user):
   ```bash
   sudo mkdir -p /etc/nix
   echo "experimental-features = nix-command flakes" | sudo tee -a /etc/nix/nix.conf
   ```

3. Restart the Nix daemon:
   ```bash
   sudo systemctl restart nix-daemon
   ```

### Windows (WSL2)

1. Install WSL2 if you haven't already:
   ```powershell
   wsl --install
   ```

2. Inside your WSL2 Linux distribution, install Nix:
   ```bash
   sh <(curl -L https://nixos.org/nix/install) --daemon
   ```

3. Enable flakes by creating or editing `/etc/nix/nix.conf`:
   ```bash
   sudo mkdir -p /etc/nix
   echo "experimental-features = nix-command flakes" | sudo tee -a /etc/nix/nix.conf
   ```

4. Restart the Nix daemon:
   ```bash
   sudo systemctl restart nix-daemon
   ```

## Verifying Installation

After installation, verify that Nix is working:

```bash
nix --version
```

You should see output like `nix (Nix) 2.x.x`.

Test flakes support:
```bash
nix flake --help
```

If this shows help text without errors, you're ready to go!

## Optional: Automate with direnv

[direnv](https://direnv.net/) automatically loads the Nix development environment when you enter the project directory, so you don't need to manually run `nix develop` each time.

### Installing direnv

**macOS (with Homebrew)**:
```bash
brew install direnv
```

**Linux**:
```bash
# Using your package manager (example for Ubuntu/Debian)
sudo apt install direnv

# Or using Nix itself
nix profile install nixpkgs#direnv
```

### Setting up direnv

1. Add direnv hook to your shell configuration:

   **Bash** (`~/.bashrc` or `~/.bash_profile`):
   ```bash
   eval "$(direnv hook bash)"
   ```

   **Zsh** (`~/.zshrc`):
   ```bash
   eval "$(direnv hook zsh)"
   ```

2. Restart your terminal or source your shell configuration:
   ```bash
   source ~/.bashrc  # or ~/.zshrc for Zsh
   ```

3. Navigate to the project directory and allow direnv:
   ```bash
   cd /path/to/assetreturns
   direnv allow
   ```

Now, whenever you enter the project directory, the Nix development environment will automatically activate!

## Alternative Installation Methods

For more installation options (including single-user installations or Docker), see the [official Nix download page](https://nixos.org/download).

## Troubleshooting

### "command not found: nix"

Make sure to source the Nix profile in your shell configuration:

**Bash** (`~/.bashrc` or `~/.bash_profile`):
```bash
if [ -e ~/.nix-profile/etc/profile.d/nix.sh ]; then
  . ~/.nix-profile/etc/profile.d/nix.sh
fi
```

**Zsh** (`~/.zshrc`):
```zsh
if [ -e ~/.nix-profile/etc/profile.d/nix.sh ]; then
  . ~/.nix-profile/etc/profile.d/nix.sh
fi
```

### "experimental Nix feature 'flakes' is disabled"

Make sure you've enabled flakes in your Nix configuration (see step 2 in each OS section above).

### Permission Errors

If you see permission errors, you may need to run the installer with the `--daemon` flag for multi-user installation, or without it for single-user installation.

## Next Steps

Once Nix is installed, return to the [README](README.md) to get started with the project!
