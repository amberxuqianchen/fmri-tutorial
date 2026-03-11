#!/usr/bin/env bash
# setup_environment.sh – interactive helper to create and register an fmri-tutorial
# conda environment and register it as a Jupyter kernel.

set -euo pipefail

# ── Colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # no colour

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ── Locate this script's directory so we can find the YAML files ──────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── 1. Check conda is available ───────────────────────────────────────────────
if ! command -v conda &>/dev/null; then
    error "conda is not installed or not on PATH."
    echo
    echo "Please install Miniconda (recommended) or Anaconda first:"
    echo "  https://docs.conda.io/en/latest/miniconda.html"
    echo
    echo "After installation, open a new terminal (or run 'conda init') and"
    echo "re-run this script."
    exit 1
fi

CONDA_VERSION=$(conda --version 2>&1)
success "Found ${CONDA_VERSION}"

# ── 2. Ask user which environment to create ───────────────────────────────────
echo
echo "Which environment would you like to set up?"
echo
echo "  1) full    – complete environment (nilearn, mriqc, nipype, scikit-learn, …)"
echo "  2) minimal – lightweight environment for notebook browsing (nibabel, pybids)"
echo "  3) nipype  – nipype + nilearn for pipeline building"
echo "              (NOTE: FSL and ANTs must be installed separately)"
echo
read -rp "Enter choice [1/2/3] (default: 1): " CHOICE
CHOICE="${CHOICE:-1}"

case "${CHOICE}" in
    1|full)
        ENV_FILE="${SCRIPT_DIR}/environment_full.yml"
        ENV_NAME="fmri-tutorial-full"
        ;;
    2|minimal)
        ENV_FILE="${SCRIPT_DIR}/environment_minimal.yml"
        ENV_NAME="fmri-tutorial-minimal"
        ;;
    3|nipype)
        ENV_FILE="${SCRIPT_DIR}/environment_nipype.yml"
        ENV_NAME="fmri-tutorial-nipype"
        warn "Remember to install FSL and ANTs separately and add them to PATH."
        ;;
    *)
        error "Invalid choice '${CHOICE}'. Please re-run and enter 1, 2, or 3."
        exit 1
        ;;
esac

if [[ ! -f "${ENV_FILE}" ]]; then
    error "Environment file not found: ${ENV_FILE}"
    exit 1
fi

# ── 3. Create the conda environment ───────────────────────────────────────────
info "Creating conda environment '${ENV_NAME}' from ${ENV_FILE} …"
echo "(This may take several minutes on first run.)"
echo

if conda env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
    warn "Environment '${ENV_NAME}' already exists."
    read -rp "Update it? [y/N]: " UPDATE
    if [[ "${UPDATE,,}" == "y" ]]; then
        conda env update --name "${ENV_NAME}" --file "${ENV_FILE}" --prune
        success "Environment updated."
    else
        info "Skipping environment creation."
    fi
else
    conda env create --name "${ENV_NAME}" --file "${ENV_FILE}"
    success "Environment '${ENV_NAME}' created."
fi

# ── 4. Register as a Jupyter kernel ───────────────────────────────────────────
info "Registering '${ENV_NAME}' as a Jupyter kernel …"

# Resolve python inside the new env without requiring 'conda activate'
CONDA_BASE=$(conda info --base)
ENV_PYTHON="${CONDA_BASE}/envs/${ENV_NAME}/bin/python"

if [[ ! -x "${ENV_PYTHON}" ]]; then
    error "Cannot locate python at ${ENV_PYTHON}. Did the environment install correctly?"
    exit 1
fi

"${ENV_PYTHON}" -m ipykernel install \
    --user \
    --name "${ENV_NAME}" \
    --display-name "Python (${ENV_NAME})"

success "Jupyter kernel '${ENV_NAME}' registered."

# ── 5. Next steps ──────────────────────────────────────────────────────────────
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Setup complete!${NC} Next steps:"
echo
echo "  1. Activate the environment:"
echo "       conda activate ${ENV_NAME}"
echo
echo "  2. Launch JupyterLab:"
echo "       jupyter lab"
echo
echo "  3. In any Jupyter notebook, select the kernel:"
echo "       'Python (${ENV_NAME})'"
echo

if [[ "${CHOICE}" == "3" || "${CHOICE}" == "nipype" ]]; then
    echo -e "${YELLOW}  ⚠  Nipype reminder:${NC}"
    echo "     Install FSL:  https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation"
    echo "     Install ANTs: https://github.com/ANTsX/ANTs/releases"
    echo "     Then add both to PATH before running Nipype workflows."
    echo
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
