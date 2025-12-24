#!/bin/bash
# Test script to run tests on multiple Python versions (matching GitHub Actions)
# 
# Best Practice: Test on 1-2 Python versions locally (e.g., your primary version),
# and let GitHub Actions handle the full matrix. This script is optional and
# useful if you want to catch compatibility issues before pushing.
#
# Usage: ./test-matrix.sh

set -e

echo "🧪 Testing on multiple Python versions (matching GitHub Actions)..."
echo ""

# Python versions to test (matching .github/workflows/tests.yml)
VERSIONS=("3.8" "3.9" "3.10" "3.11" "3.12" "3.13")

FAILED_VERSIONS=()
PASSED_VERSIONS=()
SKIPPED_VERSIONS=()

for version in "${VERSIONS[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🐍 Testing Python ${version}..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Check if Python version is available
    # Prefer pyenv versions over system Python
    PYTHON_CMD=""
    ACTUAL_PYTHON=""
    
    # First check pyenv (preferred for version management)
    if command -v pyenv &> /dev/null; then
        # Try pyenv to find the Python executable
        PYENV_VERSION=$(pyenv versions --bare | grep "^${version}\." | head -1)
        if [ -n "$PYENV_VERSION" ]; then
            # Get the actual Python path from pyenv
            PYENV_ROOT="${PYENV_ROOT:-$HOME/.pyenv}"
            ACTUAL_PYTHON="$PYENV_ROOT/versions/$PYENV_VERSION/bin/python${version}"
            # Fallback to python3 if python3.X doesn't exist
            if [ ! -f "$ACTUAL_PYTHON" ]; then
                ACTUAL_PYTHON="$PYENV_ROOT/versions/$PYENV_VERSION/bin/python3"
            fi
            # Verify it exists and is executable
            if [ ! -x "$ACTUAL_PYTHON" ]; then
                echo "⚠️  Python ${version} (${PYENV_VERSION}) found in pyenv but not executable, skipping..."
                SKIPPED_VERSIONS+=("${version}")
                echo ""
                continue
            fi
        else
            echo "⚠️  Python ${version} not found in pyenv, trying system Python..."
            # Fall through to check system Python
        fi
    fi
    
    # Fallback to system Python if pyenv doesn't have it
    if [ -z "$ACTUAL_PYTHON" ] && command -v "python${version}" &> /dev/null; then
        # Direct command available (system Python or in PATH)
        ACTUAL_PYTHON="python${version}"
    fi
    
    # If still not found, skip
    if [ -z "$ACTUAL_PYTHON" ]; then
        echo "⚠️  Python ${version} not found, skipping..."
        SKIPPED_VERSIONS+=("${version}")
        echo ""
        continue
    fi
    
    # Create a temporary virtual environment
    VENV_DIR=".venv-${version}"
    # Temporarily disable set -e for this command
    set +e
    VENV_ERROR=$("$ACTUAL_PYTHON" -m venv "${VENV_DIR}" 2>&1)
    VENV_EXIT=$?
    set -e
    if [ $VENV_EXIT -ne 0 ]; then
        # Check if it's an ensurepip issue (common with pyenv on Debian/Ubuntu)
        if echo "$VENV_ERROR" | grep -q "ensurepip"; then
            echo "⚠️  ensurepip not available, trying --without-pip..."
            set +e
            "$ACTUAL_PYTHON" -m venv --without-pip "${VENV_DIR}" 2>&1 >/dev/null
            VENV_EXIT=$?
            set -e
            if [ $VENV_EXIT -eq 0 ]; then
                echo "✅ Created venv without pip, installing pip manually..."
                # Install pip manually using get-pip.py
                source "${VENV_DIR}/bin/activate"
                curl -s https://bootstrap.pypa.io/get-pip.py | python 2>&1 >/dev/null || {
                    echo "⚠️  Failed to install pip, skipping..."
                    deactivate 2>/dev/null || true
                    rm -rf "${VENV_DIR}" 2>/dev/null || true
                    SKIPPED_VERSIONS+=("${version} (pip install failed)")
                    echo ""
                    continue
                }
                deactivate
            else
                echo "⚠️  Failed to create venv for Python ${version} (skipping)"
                echo "   GitHub Actions will test this version."
                SKIPPED_VERSIONS+=("${version} (venv failed)")
                rm -rf "${VENV_DIR}" 2>/dev/null || true
                echo ""
                continue
            fi
        else
            echo "⚠️  Failed to create venv for Python ${version} (skipping)"
            echo "   GitHub Actions will test this version."
            SKIPPED_VERSIONS+=("${version} (venv failed)")
            rm -rf "${VENV_DIR}" 2>/dev/null || true
            echo ""
            continue
        fi
    fi
    
    # Activate venv and install dependencies
    source "${VENV_DIR}/bin/activate"
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    
    # Run tests
    if pytest tests/ -q; then
        echo "✅ Python ${version}: All tests passed!"
        PASSED_VERSIONS+=("${version}")
    else
        echo "❌ Python ${version}: Tests failed!"
        FAILED_VERSIONS+=("${version}")
    fi
    
    # Deactivate and cleanup
    deactivate
    rm -rf "${VENV_DIR}"
    echo ""
done

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ${#PASSED_VERSIONS[@]} -gt 0 ]; then
    echo "✅ Passed: ${PASSED_VERSIONS[*]}"
fi

if [ ${#SKIPPED_VERSIONS[@]} -gt 0 ]; then
    echo "⚠️  Skipped (not installed): ${SKIPPED_VERSIONS[*]}"
    echo "   Note: GitHub Actions will test these versions"
fi

if [ ${#FAILED_VERSIONS[@]} -gt 0 ]; then
    echo "❌ Failed: ${FAILED_VERSIONS[*]}"
    echo ""
    echo "⚠️  Some tests failed! Fix issues before pushing to GitHub."
    exit 1
elif [ ${#PASSED_VERSIONS[@]} -eq 0 ]; then
    echo ""
    echo "⚠️  No Python versions were tested (none installed)."
    echo "   Install Python 3.8+ to test locally, or rely on GitHub Actions."
    exit 0
else
    echo ""
    echo "🎉 All tested Python versions passed!"
    if [ ${#SKIPPED_VERSIONS[@]} -gt 0 ]; then
        echo "   (Some versions were skipped - GitHub Actions will test them)"
    fi
    exit 0
fi
