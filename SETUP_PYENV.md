# Setting Up pyenv for Local Multi-Version Testing

This guide shows how to set up pyenv to test with Python 3.8 and 3.12 locally.

## Step 1: Install pyenv (if not already installed)

```bash
# On Ubuntu/Debian
curl https://pyenv.run | bash

# Add to your ~/.bashrc or ~/.zshrc:
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Reload your shell
source ~/.bashrc  # or source ~/.zshrc
```

## Step 2: Install Python versions

```bash
# Install Python 3.8
pyenv install 3.8.18

# Install Python 3.12
pyenv install 3.12.7

# Install Python 3.13 (if not already installed)
pyenv install 3.13.0
```

**Note**: You can check available versions with:
```bash
pyenv install --list | grep "^\s*3\."
```

## Step 3: Verify pyenv setup

The `test-matrix.sh` script automatically detects and uses pyenv-installed Python versions. No manual symlinks needed! The script will:

1. Check for direct `python3.8` / `python3.12` commands (system Python)
2. If not found, check pyenv for installed versions
3. Use pyenv's Python executables directly from `$PYENV_ROOT/versions/`

No additional setup required - pyenv handles everything!

## Step 3: Verify installation

```bash
# Check that pyenv has the versions installed
pyenv versions

# Test the matrix script (it will automatically find pyenv-installed versions)
./test-matrix.sh
```

The script automatically detects pyenv-installed Python versions - no symlinks needed!

## Step 4: Set local Python version for the project (optional)

If you want to use Python 3.12 as the default for this project:

```bash
cd ~/Projects/Crypto/Utils/get-current-prices
pyenv local 3.12.7
```

This creates a `.python-version` file that pyenv will use when you're in this directory.

## Troubleshooting

**"Python 3.8 not found in pyenv"**
- Verify the version is installed: `pyenv versions`
- Install it if missing: `pyenv install 3.8.18`
- The script automatically finds pyenv-installed versions - no symlinks needed

**"Failed to create venv"**
- Make sure the Python version has the `venv` module: `python3.8 -m venv --help`
- Some pyenv installations may need additional dependencies

**pyenv not working**
- Make sure `eval "$(pyenv init -)"` is in your shell config
- Restart your terminal or run `source ~/.bashrc`
