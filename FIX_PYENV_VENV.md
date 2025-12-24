# Fixing pyenv venv Issues (ensurepip not available)

If you get "ensurepip is not available" errors when creating virtual environments with pyenv-installed Python versions, here are the solutions:

## Quick Fix: Use --without-pip (Script Handles This Automatically)

The `test-matrix.sh` script now automatically tries `--without-pip` if ensurepip fails, then installs pip manually. This should work out of the box.

## Manual Fix Options

### Option 1: Reinstall Python with ensurepip support (Recommended)

Reinstall Python 3.8 via pyenv with proper SSL and ensurepip support:

```bash
# Uninstall the current version
pyenv uninstall 3.8.18

# Reinstall with proper configuration
# Make sure you have required system packages
sudo apt-get update
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
  libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
  libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev

# Reinstall Python 3.8
pyenv install 3.8.18
```

### Option 2: Use --without-pip and install pip manually

```bash
# Create venv without pip
python3.8 -m venv --without-pip myenv

# Activate it
source myenv/bin/activate

# Install pip manually
curl https://bootstrap.pypa.io/get-pip.py | python

# Now you can use pip normally
pip install requests
```

### Option 3: Install system python3.8-venv package (may not work with pyenv)

```bash
sudo apt-get install python3.8-venv
```

**Note**: This might not work if pyenv's Python 3.8 is separate from the system Python.

## Why This Happens

When Python is compiled via pyenv, it might not include `ensurepip` if:
- SSL libraries weren't available during compilation
- Python was built without the `--with-ensurepip` flag (default)
- System dependencies were missing

## Verify Fix

After fixing, test:

```bash
python3.8 -m venv test-venv
source test-venv/bin/activate
pip --version
deactivate
rm -rf test-venv
```

If this works, the `test-matrix.sh` script should now work with Python 3.8.
