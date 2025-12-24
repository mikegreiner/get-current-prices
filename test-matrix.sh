#!/bin/bash
# Test script to run tests on multiple Python versions (matching GitHub Actions)
# Usage: ./test-matrix.sh

set -e

echo "🧪 Testing on multiple Python versions (matching GitHub Actions)..."
echo ""

# Python versions to test (matching .github/workflows/tests.yml)
VERSIONS=("3.8" "3.9" "3.10" "3.11" "3.12")

FAILED_VERSIONS=()
PASSED_VERSIONS=()

for version in "${VERSIONS[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🐍 Testing Python ${version}..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Check if Python version is available
    if ! command -v "python${version}" &> /dev/null; then
        echo "⚠️  Python ${version} not found, skipping..."
        FAILED_VERSIONS+=("${version} (not installed)")
        echo ""
        continue
    fi
    
    # Create a temporary virtual environment
    VENV_DIR=".venv-${version}"
    "python${version}" -m venv "${VENV_DIR}" 2>/dev/null || {
        echo "❌ Failed to create venv for Python ${version}"
        FAILED_VERSIONS+=("${version} (venv creation failed)")
        echo ""
        continue
    }
    
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

if [ ${#FAILED_VERSIONS[@]} -gt 0 ]; then
    echo "❌ Failed: ${FAILED_VERSIONS[*]}"
    echo ""
    echo "⚠️  Some tests failed! Fix issues before pushing to GitHub."
    exit 1
else
    echo ""
    echo "🎉 All available Python versions passed tests!"
    exit 0
fi
