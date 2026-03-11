#!/usr/bin/env bash
# download_openneuro.sh
#
# Downloads OpenNeuro datasets from the public AWS S3 bucket (openneuro.org).
# No AWS account is required; requests are made with --no-sign-request.
#
# Usage:
#   bash download_openneuro.sh [OPTIONS]
#
# Options:
#   -d DATASET_ID   OpenNeuro accession number (e.g. ds000108).
#                   Can be specified multiple times or comma-separated.
#                   Defaults to ds000108 and ds000228.
#   -o OUTPUT_DIR   Directory where datasets will be saved.
#                   Defaults to ./openneuro_data
#   -h              Show this help message and exit.
#
# Examples:
#   bash download_openneuro.sh
#   bash download_openneuro.sh -o data/openneuro_data
#   bash download_openneuro.sh -d ds000108 -o /tmp/neuro
#   bash download_openneuro.sh -d ds000108 -d ds000228 -o ./data

set -euo pipefail

# --------------------------------------------------------------------------- #
# Defaults
# --------------------------------------------------------------------------- #
DEFAULT_DATASETS=("ds000108" "ds000228")
OUTPUT_DIR="./openneuro_data"
DATASETS=()
S3_BUCKET="s3://openneuro.org"

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
usage() {
    sed -n '/^# Usage:/,/^# Examples:/{ /^# Examples:/q; p }' "$0" | sed 's/^# \?//'
    cat <<'EOF'
Examples:
  bash download_openneuro.sh
  bash download_openneuro.sh -o data/openneuro_data
  bash download_openneuro.sh -d ds000108 -o /tmp/neuro
  bash download_openneuro.sh -d ds000108 -d ds000228 -o ./data
EOF
}

info()  { echo "[INFO]  $*"; }
warn()  { echo "[WARN]  $*" >&2; }
error() { echo "[ERROR] $*" >&2; exit 1; }

check_aws_cli() {
    if ! command -v aws &>/dev/null; then
        error "AWS CLI not found. Install it with:
  pip install awscli
or visit https://aws.amazon.com/cli/ for OS-specific instructions."
    fi
    local version
    version=$(aws --version 2>&1 | head -n1)
    info "Using ${version}"
}

download_dataset() {
    local dataset_id="$1"
    local dest="${OUTPUT_DIR}/${dataset_id}"

    info "Downloading ${dataset_id} → ${dest}"
    mkdir -p "${dest}"

    aws s3 sync \
        --no-sign-request \
        --only-show-errors \
        "${S3_BUCKET}/${dataset_id}/" \
        "${dest}/"

    info "Finished ${dataset_id}"
}

# --------------------------------------------------------------------------- #
# Parse arguments
# --------------------------------------------------------------------------- #
while getopts ":d:o:h" opt; do
    case "${opt}" in
        d)
            # Support comma-separated list in a single -d argument
            IFS=',' read -ra _ids <<< "${OPTARG}"
            DATASETS+=("${_ids[@]}")
            ;;
        o) OUTPUT_DIR="${OPTARG}" ;;
        h) usage; exit 0 ;;
        :) error "Option -${OPTARG} requires an argument." ;;
        \?) error "Unknown option: -${OPTARG}. Use -h for help." ;;
    esac
done

# Use defaults when no datasets were specified
if [[ ${#DATASETS[@]} -eq 0 ]]; then
    DATASETS=("${DEFAULT_DATASETS[@]}")
fi

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
check_aws_cli

info "Output directory : ${OUTPUT_DIR}"
info "Datasets         : ${DATASETS[*]}"
echo ""

for ds in "${DATASETS[@]}"; do
    download_dataset "${ds}"
    echo ""
done

info "All downloads complete."
info "Data saved to: $(realpath "${OUTPUT_DIR}" 2>/dev/null || echo "${OUTPUT_DIR}")"
