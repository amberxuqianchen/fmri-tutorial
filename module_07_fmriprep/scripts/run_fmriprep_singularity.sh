#!/usr/bin/env bash
# run_fmriprep_singularity.sh — Run fMRIPrep via Singularity/Apptainer (HPC)
set -euo pipefail

FMRIPREP_VERSION="23.1.4"

usage() {
    echo "Usage: $0 -b BIDS_DIR -o OUTPUT_DIR -l FREESURFER_LICENSE -i SIF_IMAGE [-s SUBJECT]"
    echo "  -b  BIDS directory"
    echo "  -o  Output directory"
    echo "  -l  FreeSurfer license file"
    echo "  -i  Path to fmriprep .sif image"
    echo "  -s  Subject label (optional)"
    exit 1
}

BIDS_DIR="" OUTPUT_DIR="" FS_LICENSE="" SIF="" SUBJECT=""

while getopts "b:o:l:i:s:h" opt; do
    case $opt in
        b) BIDS_DIR="$OPTARG" ;;
        o) OUTPUT_DIR="$OPTARG" ;;
        l) FS_LICENSE="$OPTARG" ;;
        i) SIF="$OPTARG" ;;
        s) SUBJECT="$OPTARG" ;;
        h|*) usage ;;
    esac
done

[[ -z "$BIDS_DIR" || -z "$OUTPUT_DIR" || -z "$FS_LICENSE" || -z "$SIF" ]] && { echo "Error: -b -o -l -i are required."; usage; }
[[ ! -f "$SIF" ]] && { echo "Error: SIF image not found: $SIF"; exit 1; }

mkdir -p "$OUTPUT_DIR" "$OUTPUT_DIR/work"
export TEMPLATEFLOW_HOME="${HOME}/.cache/templateflow"
mkdir -p "$TEMPLATEFLOW_HOME"

CMD=(singularity run --cleanenv
    -B "$(realpath "$BIDS_DIR")":/data:ro
    -B "$(realpath "$OUTPUT_DIR")":/out
    -B "$(realpath "$FS_LICENSE")":/opt/freesurfer/license.txt:ro
    -B "$(realpath "$OUTPUT_DIR")/work":/work
    -B "$TEMPLATEFLOW_HOME":/templateflow
    --env TEMPLATEFLOW_HOME=/templateflow
    "$SIF"
    /data /out participant
    --work-dir /work
    --output-spaces MNI152NLin2009cAsym:res-2 T1w
    --dummy-scans 4
    --fd-spike-threshold 0.5
    --skip-bids-validation
    --nthreads 4 --omp-nthreads 4)

[[ -n "$SUBJECT" ]] && CMD+=(--participant-label "$SUBJECT")

echo "Running: ${CMD[*]}"
LOG="${OUTPUT_DIR}/fmriprep_$(date +%Y%m%d_%H%M%S).log"
"${CMD[@]}" 2>&1 | tee "$LOG"
echo "Done. Log: $LOG"
