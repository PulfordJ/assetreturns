# Asset Returns Calculator

A Python project for calculating asset returns with Jupyter notebook support, managed using Nix flakes and uv2nix for reproducible environments.

## Prerequisites

- Nix with flakes enabled ([installation guide](INSTALL-NIX.md))
- Git

## Quick Start

### Running Jupyter Notebook

```bash
# Launch Jupyter notebook
nix run

# Or explicitly
nix run .#notebook

# Launch Jupyter Lab instead
nix run .#lab
```

### Development Environment

```bash
# Enter development shell with all dependencies
nix develop

# Inside the shell, you have access to:
jupyter notebook  # Start Jupyter notebook
jupyter lab       # Start Jupyter Lab
python            # Python interpreter with all dependencies
uv                # UV package manager
```

## Project Management

### Adding Dependencies

1. Edit `pyproject.toml` to add new dependencies
2. Regenerate the lock file using the pinned UV version:
   ```bash
   nix develop .#bootstrap -c uv lock
   ```
3. Add the updated lock file to git:
   ```bash
   git add uv.lock
   ```

### Bootstrap Shell

The bootstrap shell is a minimal environment with just Python and UV, used for generating the `uv.lock` file before the full environment is built:

```bash
nix develop .#bootstrap
```

## Reproducibility

This project uses:
- **Nix flakes** for system-level reproducibility
- **uv2nix** to convert UV's lock file to Nix expressions
- **uv.lock** generated with a pinned UV version for Python dependency reproducibility

The Jupyter notebook version is specified in `pyproject.toml` and locked in `uv.lock`, ensuring the same version is used across Linux, macOS, and other systems (when using Nix).

## Project Structure

- `pyproject.toml` - Python project configuration and dependencies
- `flake.nix` - Nix flake configuration with uv2nix integration
- `uv.lock` - UV lock file for Python dependencies
- `assetreturns.py` - Main Python module
- `test_assetreturns.py` - Tests
