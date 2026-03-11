#!/usr/bin/env bash
# run_mriqc_single_subject.sh
#
# Run MRIQC participant-level analysis for a single subject using either
# Docker or Singularity/Apptainer.
#
# Usage
# -----
#   bash run_mriqc_single_subject.sh [--docker|--singularity] \
#       BIDS_DIR OUTPUT_DIR SUBJECT_ID
#
# Arguments
# ---------
#   --docker        Use Docker to run MRIQC (default if neither flag given
#                   and Docker is available).
#   --singularity   Use Singularity/Apptainer to run MRIQC.
#   BIDS_DIR        Absolute path to the BIDS dataset root.
#   OUTPUT_DIR      Absolute path to the MRIQC output directory.
#   SUBJECT_ID      Subject label WITHOUT the 'sub-' prefix (e.g., '01').
#
# Environment variables (optional overrides)
# ------------------------------------------
#   MRIQC_VERSION   MRIQC Docker/Singularity image version tag.
#                   Default: 23.1.0
#   MRIQC_SIF       Path to a Singularity .sif file (Singularity mode only).
#                   Default: ${HOME}/singularity/mriqc_${MRIQC_VERSION}.sif
#   NPROCS          Number of parallel processes. Default: 4
#   MEM_GB          Memory limit in GB.          Default: 8
#
# Examples
# --------
#   # Docker
#   bash run_mriqc_single_subject.sh --docker \
#       /data/bids /data/mriqc 01
#
#   # Singularity
#   bash run_mriqc_single_subject.sh --singularity \
#       /data/bids /data/mriqc 01

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

if [[ $# -lt 3 ]]; then
    usage 1
fi

BIDS_DIR="$(realpath "$1")"
OUTPUT_DIR="$(realpath "$2")"
SUBJECT_ID="$3"

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
        echo "[ERROR] Neither Docker nor Singularity/Apptainer found. " \
             "Install one and re-run." >&2
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

if [[ ! -d "${BIDS_DIR}/sub-${SUBJECT_ID}" ]]; then
    echo "[ERROR] Subject directory not found: ${BIDS_DIR}/sub-${SUBJECT_ID}" >&2
    exit 1
fi

mkdir -p "${OUTPUT_DIR}"

# A writable scratch directory for MRIQC intermediate files
WORK_DIR="${OUTPUT_DIR}/work"
mkdir -p "${WORK_DIR}"

echo "=================================================="
echo "MRIQC Participant-Level Run"
echo "=================================================="
echo "Mode       : ${RUN_MODE}"
echo "MRIQC ver  : ${MRIQC_VERSION}"
echo "BIDS dir   : ${BIDS_DIR}"
echo "Output dir : ${OUTPUT_DIR}"
echo "Work dir   : ${WORK_DIR}"
echo "Subject    : sub-${SUBJECT_ID}"
echo "nprocs     : ${NPROCS}"
echo "mem_gb     : ${MEM_GB}"
echo "=================================================="

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
        /data /out participant \
        --participant-label "${SUBJECT_ID}" \
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
        echo "SIF image not found at ${sif}."
        echo "Pulling from Docker Hub (requires internet access)..."
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
        /data /out participant \
        --participant-label "${SUBJECT_ID}" \
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
echo "MRIQC participant-level complete for sub-${SUBJECT_ID}."
echo "HTML report: ${OUTPUT_DIR}/sub-${SUBJECT_ID}/"
