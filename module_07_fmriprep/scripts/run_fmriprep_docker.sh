#!/usr/bin/env bash
# run_fmriprep_docker.sh — Run fMRIPrep via Docker for a single subject
set -euo pipefail

FMRIPREP_VERSION="23.1.4"

usage() {
    echo "Usage: $0 -b BIDS_DIR -o OUTPUT_DIR -l FREESURFER_LICENSE [-s SUBJECT] [-t TASK]"
    echo ""
    echo "  -b  Path to BIDS directory"
    echo "  -o  Path to output directory"
    echo "  -l  Path to FreeSurfer license file"
    echo "  -s  Subject label (without sub- prefix, optional)"
    echo "  -t  Task label (optional)"
    exit 1
}

BIDS_DIR="" OUTPUT_DIR="" FS_LICENSE="" SUBJECT="" TASK=""

while getopts "b:o:l:s:t:h" opt; do
    case $opt in
        b) BIDS_DIR="$OPTARG" ;;
        o) OUTPUT_DIR="$OPTARG" ;;
        l) FS_LICENSE="$OPTARG" ;;
        s) SUBJECT="$OPTARG" ;;
        t) TASK="$OPTARG" ;;
        h|*) usage ;;
    esac
done

[[ -z "$BIDS_DIR" || -z "$OUTPUT_DIR" || -z "$FS_LICENSE" ]] && { echo "Error: -b, -o, -l are required."; usage; }
[[ ! -d "$BIDS_DIR" ]] && { echo "Error: BIDS_DIR not found: $BIDS_DIR"; exit 1; }
[[ ! -f "$FS_LICENSE" ]] && { echo "Error: FreeSurfer license not found: $FS_LICENSE"; exit 1; }
docker info &>/dev/null || { echo "Error: Docker is not running."; exit 1; }

mkdir -p "$OUTPUT_DIR" "$OUTPUT_DIR/work"

CMD=(docker run --rm
    -v "$(realpath "$BIDS_DIR")":/data:ro
    -v "$(realpath "$OUTPUT_DIR")":/out
    -v "$(realpath "$FS_LICENSE")":/opt/freesurfer/license.txt:ro
    -v "$(realpath "$OUTPUT_DIR")/work":/work
    --memory=8g --cpus=4
    "nipreps/fmriprep:${FMRIPREP_VERSION}"
    /data /out participant
    --work-dir /work
    --output-spaces MNI152NLin2009cAsym:res-2 T1w
    --dummy-scans 4
    --fd-spike-threshold 0.5
    --skip-bids-validation
    --nthreads 4 --omp-nthreads 4
    --mem-mb 8000)

[[ -n "$SUBJECT" ]] && CMD+=(--participant-label "$SUBJECT")
[[ -n "$TASK" ]] && CMD+=(--task-id "$TASK")

echo "Running: ${CMD[*]}"
LOG="${OUTPUT_DIR}/fmriprep_$(date +%Y%m%d_%H%M%S).log"
"${CMD[@]}" 2>&1 | tee "$LOG"
echo "Done. Log: $LOG"
