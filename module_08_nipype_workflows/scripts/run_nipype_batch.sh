#!/usr/bin/env bash
# run_nipype_batch.sh — Batch Nipype preprocessing across multiple BIDS subjects
#
# Loops over subjects discovered in a BIDS directory (or listed in a subjects
# file) and calls run_nipype_preproc.py for each one.  Progress is logged with
# timestamps so you can monitor long-running batches.
#
# Usage:
#   bash run_nipype_batch.sh --bids_dir /data/bids --output_dir /data/out [OPTIONS]
#
# Example (all subjects, default settings):
#   bash run_nipype_batch.sh \
#       --bids_dir /data/bids \
#       --output_dir /data/nipype_output
#
# Example (subset of subjects, 4-core MultiProc):
#   bash run_nipype_batch.sh \
#       --bids_dir /data/bids \
#       --output_dir /data/nipype_output \
#       --subjects_file participants.txt \
#       --plugin MultiProc \
#       --n_procs 4 \
#       --fwhm 8.0

set -euo pipefail

# ---------------------------------------------------------------------------
# Resolve the directory that contains this script so we can find the sibling
# run_nipype_preproc.py regardless of the caller's working directory.
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREPROC_SCRIPT="${SCRIPT_DIR}/run_nipype_preproc.py"

# ---------------------------------------------------------------------------
# usage()
# ---------------------------------------------------------------------------
usage() {
    cat <<EOF
Usage: $(basename "$0") --bids_dir PATH --output_dir PATH [OPTIONS]

Required:
  --bids_dir      PATH   Root of the BIDS dataset (must exist).
  --output_dir    PATH   Directory for Nipype outputs and working files.

Optional:
  --subjects_file FILE   Plain-text file with one subject label per line
                         (without the 'sub-' prefix). If omitted, all
                         sub-* directories in BIDS_DIR are processed.
  --task          LABEL  BOLD task label (e.g. 'rest'). Passed to
                         run_nipype_preproc.py. Default: auto-detect.
  --fwhm          MM     Smoothing kernel FWHM in mm. Default: 6.0.
  --plugin        NAME   Nipype plugin: Linear | MultiProc | SLURM | SGE.
                         Default: Linear.
  --n_procs       N      Parallel processes for MultiProc. Default: 1.
  --workflow_name NAME   Nipype workflow name / working subdirectory.
                         Default: minimal_preproc.
  --log_dir       PATH   Directory for per-subject log files.
                         Default: <output_dir>/logs.
  -h, --help             Print this message and exit.

Exit codes:
  0  All subjects completed successfully.
  1  One or more subjects failed (check per-subject logs).
EOF
    exit "${1:-0}"
}

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
BIDS_DIR=""
OUTPUT_DIR=""
SUBJECTS_FILE=""
TASK_FLAG=""
FWHM="6.0"
PLUGIN="Linear"
N_PROCS="1"
WORKFLOW_NAME="minimal_preproc"
LOG_DIR=""

# ---------------------------------------------------------------------------
# Argument parsing (long-form options via manual loop)
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --bids_dir)      BIDS_DIR="$2";       shift 2 ;;
        --output_dir)    OUTPUT_DIR="$2";     shift 2 ;;
        --subjects_file) SUBJECTS_FILE="$2";  shift 2 ;;
        --task)          TASK_FLAG="$2";      shift 2 ;;
        --fwhm)          FWHM="$2";           shift 2 ;;
        --plugin)        PLUGIN="$2";         shift 2 ;;
        --n_procs)       N_PROCS="$2";        shift 2 ;;
        --workflow_name) WORKFLOW_NAME="$2";  shift 2 ;;
        --log_dir)       LOG_DIR="$2";        shift 2 ;;
        -h|--help)       usage 0 ;;
        *)
            echo "ERROR: Unknown option: $1" >&2
            usage 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Validate required arguments
# ---------------------------------------------------------------------------
if [[ -z "$BIDS_DIR" || -z "$OUTPUT_DIR" ]]; then
    echo "ERROR: --bids_dir and --output_dir are required." >&2
    usage 1
fi

if [[ ! -d "$BIDS_DIR" ]]; then
    echo "ERROR: BIDS directory not found: $BIDS_DIR" >&2
    exit 1
fi

if [[ ! -f "$PREPROC_SCRIPT" ]]; then
    echo "ERROR: run_nipype_preproc.py not found at: $PREPROC_SCRIPT" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Prepare output and log directories
# ---------------------------------------------------------------------------
mkdir -p "$OUTPUT_DIR"
LOG_DIR="${LOG_DIR:-${OUTPUT_DIR}/logs}"
mkdir -p "$LOG_DIR"

# ---------------------------------------------------------------------------
# Collect subject list
# ---------------------------------------------------------------------------
declare -a SUBJECTS

if [[ -n "$SUBJECTS_FILE" ]]; then
    if [[ ! -f "$SUBJECTS_FILE" ]]; then
        echo "ERROR: subjects file not found: $SUBJECTS_FILE" >&2
        exit 1
    fi
    # Read non-empty, non-comment lines; strip leading 'sub-' if present
    while IFS= read -r line || [[ -n "$line" ]]; do
        line="${line//[$'\t\r\n']}"   # strip carriage returns / tabs
        [[ -z "$line" || "$line" == \#* ]] && continue
        SUBJECTS+=("${line#sub-}")
    done < "$SUBJECTS_FILE"
else
    # Auto-discover from BIDS directory
    while IFS= read -r -d '' sub_dir; do
        SUBJECTS+=("$(basename "$sub_dir" | sed 's/^sub-//')")
    done < <(find "$BIDS_DIR" -maxdepth 1 -name 'sub-*' -type d -print0 | sort -z)
fi

if [[ ${#SUBJECTS[@]} -eq 0 ]]; then
    echo "ERROR: No subjects found in '$BIDS_DIR'." >&2
    echo "       Create a subjects file with --subjects_file or add sub-* directories." >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Print run summary
# ---------------------------------------------------------------------------
TIMESTAMP_START="$(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"
echo " Nipype Batch Preprocessing"
echo "============================================================"
echo " Start time    : $TIMESTAMP_START"
echo " BIDS dir      : $BIDS_DIR"
echo " Output dir    : $OUTPUT_DIR"
echo " Log dir       : $LOG_DIR"
echo " Subjects      : ${#SUBJECTS[@]}"
echo " Task          : ${TASK_FLAG:-(auto-detect)}"
echo " FWHM          : ${FWHM} mm"
echo " Plugin        : $PLUGIN"
[[ "$PLUGIN" == "MultiProc" ]] && echo " n_procs       : $N_PROCS"
echo " Workflow name : $WORKFLOW_NAME"
echo "============================================================"
echo ""

# ---------------------------------------------------------------------------
# Build base Python command arguments (shared across subjects)
# ---------------------------------------------------------------------------
BASE_ARGS=(
    --bids_dir    "$BIDS_DIR"
    --output_dir  "$OUTPUT_DIR"
    --fwhm        "$FWHM"
    --plugin      "$PLUGIN"
    --n_procs     "$N_PROCS"
    --workflow_name "$WORKFLOW_NAME"
)
[[ -n "$TASK_FLAG" ]] && BASE_ARGS+=(--task "$TASK_FLAG")

# ---------------------------------------------------------------------------
# Process each subject
# ---------------------------------------------------------------------------
FAILED_SUBJECTS=()
SUCCESS_COUNT=0

for sub in "${SUBJECTS[@]}"; do
    SUBJECT_LOG="${LOG_DIR}/sub-${sub}.log"
    TS="$(date '+%Y-%m-%d %H:%M:%S')"

    echo "[${TS}] Processing sub-${sub} ..."

    if python3 "$PREPROC_SCRIPT" \
            --subject "$sub" \
            "${BASE_ARGS[@]}" \
            > "$SUBJECT_LOG" 2>&1; then

        TS_DONE="$(date '+%Y-%m-%d %H:%M:%S')"
        echo "[${TS_DONE}]   sub-${sub} DONE  (log: $SUBJECT_LOG)"
        (( SUCCESS_COUNT++ )) || true

    else
        TS_FAIL="$(date '+%Y-%m-%d %H:%M:%S')"
        echo "[${TS_FAIL}]   sub-${sub} FAILED (see log: $SUBJECT_LOG)" >&2
        # Print the tail of the log to stderr for quick debugging
        echo "--- last 20 lines of ${SUBJECT_LOG} ---" >&2
        tail -n 20 "$SUBJECT_LOG" >&2
        echo "---------------------------------------" >&2
        FAILED_SUBJECTS+=("$sub")
    fi
done

# ---------------------------------------------------------------------------
# Final summary
# ---------------------------------------------------------------------------
TIMESTAMP_END="$(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "============================================================"
echo " Batch complete"
echo "============================================================"
echo " End time      : $TIMESTAMP_END"
echo " Succeeded     : ${SUCCESS_COUNT} / ${#SUBJECTS[@]}"
echo " Failed        : ${#FAILED_SUBJECTS[@]}"
if [[ ${#FAILED_SUBJECTS[@]} -gt 0 ]]; then
    echo " Failed subs   : ${FAILED_SUBJECTS[*]}"
fi
echo " Logs          : $LOG_DIR"
echo "============================================================"

# Exit with non-zero status if any subject failed
if [[ ${#FAILED_SUBJECTS[@]} -gt 0 ]]; then
    exit 1
fi
exit 0
