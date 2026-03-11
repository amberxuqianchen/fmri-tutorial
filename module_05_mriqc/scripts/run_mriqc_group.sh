#!/usr/bin/env bash
# run_mriqc_group.sh
#
# Run MRIQC group-level aggregation after all participant-level runs are done.
# Produces group_bold.tsv, group_T1w.tsv and group HTML reports.
#
# Usage
# -----
#   bash run_mriqc_group.sh [--docker|--singularity] BIDS_DIR OUTPUT_DIR
#
# Arguments
# ---------
#   --docker        Use Docker (default if Docker is available).
#   --singularity   Use Singularity/Apptainer.
#   BIDS_DIR        Absolute path to the BIDS dataset root.
#   OUTPUT_DIR      Absolute path to the MRIQC output directory where
#                   participant-level results already exist.
#
# Environment variables (optional overrides)
# ------------------------------------------
#   MRIQC_VERSION   MRIQC image version tag. Default: 23.1.0
#   MRIQC_SIF       Path to Singularity .sif (Singularity mode only).
#   NPROCS          Parallel processes. Default: 4
#   MEM_GB          Memory limit in GB. Default: 8
#
# Examples
# --------
#   bash run_mriqc_group.sh --docker /data/bids /data/mriqc
#   bash run_mriqc_group.sh --singularity /data/bids /data/mriqc

set -euo pipefail

usage() {
    sed -n '2,/^set -euo pipefail/p' "$0" | sed 's/^# \{0,1\}//' | sed '$d'
    exit "${1:-0}"
}

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
MRIQC_VERSION="${MRIQC_VERSION:-23.1.0}"
NPROCS="${NPROCS:-4}"
MEM_GB="${MEM_GB:-8}"
RUN_MODE=""

# ---------------------------------------------------------------------------
# Parse flags
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --docker)
            RUN_MODE="docker"
            shift
            ;;
        --singularity)
            RUN_MODE="singularity"
            shift
            ;;
        -h|--help)
            usage 0
            ;;
        -*)
            echo "Unknown option: $1" >&2
            usage 1
            ;;
        *)
            break
            ;;
    esac
done

if [[ $# -lt 2 ]]; then
    usage 1
fi

BIDS_DIR="$(realpath "$1")"
OUTPUT_DIR="$(realpath "$2")"

# ---------------------------------------------------------------------------
# Auto-detect run mode
# ---------------------------------------------------------------------------
if [[ -z "${RUN_MODE}" ]]; then
    if command -v docker &>/dev/null; then
        RUN_MODE="docker"
        echo "Auto-detected Docker."
    elif command -v singularity &>/dev/null || command -v apptainer &>/dev/null; then
        RUN_MODE="singularity"
        echo "Auto-detected Singularity/Apptainer."
    else
        echo "[ERROR] Neither Docker nor Singularity/Apptainer found." >&2
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# Validate inputs
# ---------------------------------------------------------------------------
if [[ ! -d "${BIDS_DIR}" ]]; then
    echo "[ERROR] BIDS directory not found: ${BIDS_DIR}" >&2
    exit 1
fi

if [[ ! -d "${OUTPUT_DIR}" ]]; then
    echo "[ERROR] Output directory not found: ${OUTPUT_DIR}." \
         "Run participant-level MRIQC first." >&2
    exit 1
fi

WORK_DIR="${OUTPUT_DIR}/work"
mkdir -p "${WORK_DIR}"

echo "=================================================="
echo "MRIQC Group-Level Run"
echo "=================================================="
echo "Mode       : ${RUN_MODE}"
echo "MRIQC ver  : ${MRIQC_VERSION}"
echo "BIDS dir   : ${BIDS_DIR}"
echo "Output dir : ${OUTPUT_DIR}"
echo "Work dir   : ${WORK_DIR}"
echo "nprocs     : ${NPROCS}"
echo "mem_gb     : ${MEM_GB}"
echo "=================================================="

# ---------------------------------------------------------------------------
# Count participants present in output dir
# ---------------------------------------------------------------------------
N_SUBJECTS=$(find "${OUTPUT_DIR}" -maxdepth 1 -type d -name "sub-*" | wc -l)
echo "Found ${N_SUBJECTS} participant-level output director(ies)."
if [[ "${N_SUBJECTS}" -eq 0 ]]; then
    echo "[ERROR] No sub-* directories found in ${OUTPUT_DIR}." \
         "Run participant-level MRIQC first." >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------
run_docker() {
    local image="nipreps/mriqc:${MRIQC_VERSION}"

    echo "Pulling image (if not cached): ${image}"
    docker pull "${image}"

    docker run --rm \
        -v "${BIDS_DIR}:/data:ro" \
        -v "${OUTPUT_DIR}:/out" \
        -v "${WORK_DIR}:/work" \
        "${image}" \
        /data /out group \
        --work-dir /work \
        --nprocs "${NPROCS}" \
        --mem_gb "${MEM_GB}" \
        --no-sub \
        -v
}

# ---------------------------------------------------------------------------
# Singularity / Apptainer
# ---------------------------------------------------------------------------
run_singularity() {
    local sif="${MRIQC_SIF:-${HOME}/singularity/mriqc_${MRIQC_VERSION}.sif}"
    local singularity_cmd
    singularity_cmd="$(command -v apptainer 2>/dev/null || command -v singularity)"

    if [[ ! -f "${sif}" ]]; then
        echo "SIF image not found at ${sif}. Pulling from Docker Hub..."
        mkdir -p "$(dirname "${sif}")"
        "${singularity_cmd}" pull "${sif}" \
            "docker://nipreps/mriqc:${MRIQC_VERSION}"
    fi

    "${singularity_cmd}" run \
        --cleanenv \
        -B "${BIDS_DIR}:/data:ro" \
        -B "${OUTPUT_DIR}:/out" \
        -B "${WORK_DIR}:/work" \
        "${sif}" \
        /data /out group \
        --work-dir /work \
        --nprocs "${NPROCS}" \
        --mem_gb "${MEM_GB}" \
        --no-sub \
        -v
}

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
case "${RUN_MODE}" in
    docker)
        run_docker
        ;;
    singularity)
        run_singularity
        ;;
    *)
        echo "[ERROR] Unknown run mode: ${RUN_MODE}" >&2
        exit 1
        ;;
esac

echo ""
echo "MRIQC group-level complete."
echo "Group IQM files:"
for tsv in "${OUTPUT_DIR}"/group_*.tsv; do
    [[ -f "${tsv}" ]] && echo "  ${tsv}"
done
echo ""
echo "Group HTML reports:"
for html in "${OUTPUT_DIR}"/group_*.html; do
    [[ -f "${html}" ]] && echo "  ${html}"
done
