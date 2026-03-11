#!/usr/bin/env bash
# run_fmriprep_batch.sh — Run fMRIPrep on multiple subjects
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    echo "Usage: $0 -b BIDS_DIR -o OUTPUT_DIR -l FS_LICENSE [-f SUBJECTS_FILE] [--docker|--singularity SIF]"
    echo "  -b  BIDS directory"
    echo "  -o  Output directory"
    echo "  -l  FreeSurfer license"
    echo "  -f  Text file with one subject per line (default: auto-discover from BIDS)"
    echo "  --docker        Use Docker (default)"
    echo "  --singularity   Use Singularity, requires SIF path as next arg"
    exit 1
}

BIDS_DIR="" OUTPUT_DIR="" FS_LICENSE="" SUBJECTS_FILE="" MODE="docker" SIF=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -b) BIDS_DIR="$2"; shift 2 ;;
        -o) OUTPUT_DIR="$2"; shift 2 ;;
        -l) FS_LICENSE="$2"; shift 2 ;;
        -f) SUBJECTS_FILE="$2"; shift 2 ;;
        --docker) MODE="docker"; shift ;;
        --singularity) MODE="singularity"; SIF="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) echo "Unknown arg: $1"; usage ;;
    esac
done

[[ -z "$BIDS_DIR" || -z "$OUTPUT_DIR" || -z "$FS_LICENSE" ]] && { echo "Error: -b -o -l required."; usage; }

if [[ -n "$SUBJECTS_FILE" ]]; then
    mapfile -t SUBJECTS < "$SUBJECTS_FILE"
else
    mapfile -t SUBJECTS < <(find "$BIDS_DIR" -maxdepth 1 -name 'sub-*' -type d | xargs -I{} basename {} | sed 's/sub-//' | sort)
fi

echo "Found ${#SUBJECTS[@]} subjects: ${SUBJECTS[*]}"
mkdir -p "$OUTPUT_DIR"

for sub in "${SUBJECTS[@]}"; do
    echo "=== Processing sub-${sub} ==="
    if [[ "$MODE" == "docker" ]]; then
        bash "${SCRIPT_DIR}/run_fmriprep_docker.sh" -b "$BIDS_DIR" -o "$OUTPUT_DIR" -l "$FS_LICENSE" -s "$sub"
    else
        bash "${SCRIPT_DIR}/run_fmriprep_singularity.sh" -b "$BIDS_DIR" -o "$OUTPUT_DIR" -l "$FS_LICENSE" -i "$SIF" -s "$sub"
    fi
done

echo "Batch complete for ${#SUBJECTS[@]} subjects."
