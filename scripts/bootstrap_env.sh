#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Bootstrap Environment Script
# Creates virtual environment, installs dependencies, and sets up .env
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"

echo "=== Salesforce AI Assistant: Environment Bootstrap ==="
echo ""

# --- Step 1: Check Python version ---
echo "1. Checking Python version..."
PYTHON_CMD=""
for cmd in python3.11 python3.12 python3.13 python3; do
    if command -v "$cmd" &> /dev/null; then
        PY_VERSION=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        PY_MAJOR=$("$cmd" -c 'import sys; print(sys.version_info.major)')
        PY_MINOR=$("$cmd" -c 'import sys; print(sys.version_info.minor)')
        if [[ "$PY_MAJOR" -ge 3 && "$PY_MINOR" -ge 11 ]]; then
            PYTHON_CMD="$cmd"
            echo "   Found: $cmd (Python $PY_VERSION) ✓"
            break
        fi
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    echo "   ERROR: Python 3.11+ is required but not found."
    echo "   Install Python 3.11+ from https://www.python.org/downloads/"
    exit 1
fi

# --- Step 2: Create virtual environment ---
echo ""
echo "2. Creating virtual environment in .venv/..."
if [[ -d "$VENV_DIR" ]]; then
    echo "   Virtual environment already exists. Skipping creation."
else
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    echo "   Created .venv/ ✓"
fi

# --- Step 3: Activate and install dependencies ---
echo ""
echo "3. Installing dependencies..."
source "${VENV_DIR}/bin/activate"

pip install --upgrade pip -q
pip install -r "${PROJECT_ROOT}/requirements.txt" -q
echo "   Installed requirements.txt ✓"

if [[ -f "${PROJECT_ROOT}/requirements-dev.txt" ]]; then
    pip install -r "${PROJECT_ROOT}/requirements-dev.txt" -q
    echo "   Installed requirements-dev.txt ✓"
fi

# --- Step 4: Copy .env.example to .env ---
echo ""
echo "4. Setting up .env..."
if [[ -f "${PROJECT_ROOT}/.env" ]]; then
    echo "   .env already exists. Skipping copy."
else
    cp "${PROJECT_ROOT}/.env.example" "${PROJECT_ROOT}/.env"
    echo "   Copied .env.example → .env ✓"
fi

# --- Step 5: Print checklist ---
echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Activate the virtual environment:"
echo "     source .venv/bin/activate"
echo ""
echo "  2. Configure .env with your credentials:"
echo "     ┌──────────────────────────────────────────────────────┐"
echo "     │ Required variables:                                  │"
echo "     │   AZURE_AI_PROJECT_ENDPOINT  (from Bicep deployment) │"
echo "     │   AZURE_OPENAI_DEPLOYMENT    (default: gpt-4o)      │"
echo "     │   SF_INSTANCE_URL            (Salesforce My Domain)  │"
echo "     │   SF_ACCESS_TOKEN or SF_CONSUMER_KEY+SECRET          │"
echo "     └──────────────────────────────────────────────────────┘"
echo ""
echo "  3. Run a notebook:"
echo "     jupyter lab notebooks/01_sales_pipeline_summary.ipynb"
echo ""
