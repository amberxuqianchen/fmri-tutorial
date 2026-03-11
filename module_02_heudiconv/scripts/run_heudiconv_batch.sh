#!/usr/bin/env bash
# =============================================================================
# run_heudiconv_batch.sh
#
# Run HeudiConv DICOM-to-BIDS conversion for multiple subjects.
#
# Usage:
#   bash run_heudiconv_batch.sh [OPTIONS] <DICOM_ROOT> <OUTPUT_DIR> <HEURISTIC_FILE>
#
# Positional arguments:
#   DICOM_ROOT      Root directory whose immediate sub-directories are
#                   per-subject DICOM folders (e.g. /data/dicoms/)
#   OUTPUT_DIR      BIDS dataset root (will be created if absent)
#   HEURISTIC_FILE  Path to HeudiConv heuristic Python file
#
# Options:
#   --subjects FILE   Path to a text file with one subject ID per line.
#                     If omitted, subjects are discovered from sub-directories
#                     in DICOM_ROOT.
#   --parallel N      Run N subjects in parallel (default: 1 = sequential).
#   --help            Show this message and exit.
#
# Environment variables:
#   HEUDICONV_SINGLE_SCRIPT   Path to run_heudiconv_single_subject.sh
#                             (default: same directory as this script)
#
# Examples:
#   # Discover subjects automatically
#   bash run_heudiconv_batch.sh /data/dicoms /data/bids heuristic.py
#
#   # Use a subject list
#   bash run_heudiconv_batch.sh \
#       --subjects subjects.txt \
#       /data/dicoms /data/bids heuristic.py
#
#   # Parallel (4 at a time)
#   bash run_heudiconv_batch.sh --parallel 4 \
#       /data/dicoms /data/bids heuristic.py
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SINGLE_SCRIPT="${HEUDICONV_SINGLE_SCRIPT:-${SCRIPT_DIR}/run_heudiconv_single_subject.sh}"

# ── Colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'
log_info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()      { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_section() { echo -e "\n${CYAN}──────────────────────────────────────────${NC}"; echo -e "${CYAN}  $*${NC}"; echo -e "${CYAN}──────────────────────────────────────────${NC}"; }

# ── Default option values ─────────────────────────────────────────────────────
SUBJECTS_FILE=""
PARALLEL=1

# ── Argument parsing ──────────────────────────────────────────────────────────
usage() {
    sed -n '2,/^# ===*/p' "$0" | sed 's/^# \{0,2\}//'
    exit 0
}

POSITIONAL=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --subjects)  SUBJECTS_FILE="$2"; shift 2 ;;
        --parallel)  PARALLEL="$2";      shift 2 ;;
        --help|-h)   usage ;;
        -*)          log_error "Unknown option: $1"; usage ;;
        *)           POSITIONAL+=("$1"); shift ;;
    esac
done

set -- "${POSITIONAL[@]}"
[[ $# -lt 3 ]] && { log_error "Insufficient positional arguments."; usage; }

DICOM_ROOT="$1"
OUTPUT_DIR="$2"
HEURISTIC_FILE="$3"

# ── Validate prerequisites ────────────────────────────────────────────────────
[[ -d "$DICOM_ROOT" ]]     || { log_error "DICOM_ROOT not found: $DICOM_ROOT"; exit 1; }
[[ -f "$HEURISTIC_FILE" ]] || { log_error "HEURISTIC_FILE not found: $HEURISTIC_FILE"; exit 1; }
[[ -f "$SINGLE_SCRIPT" ]]  || { log_error "Single-subject script not found: $SINGLE_SCRIPT"; exit 1; }
command -v heudiconv &>/dev/null || { log_error "heudiconv not found."; exit 1; }

mkdir -p "$OUTPUT_DIR"

# ── Build subject list ────────────────────────────────────────────────────────
if [[ -n "$SUBJECTS_FILE" ]]; then
    [[ -f "$SUBJECTS_FILE" ]] || { log_error "Subjects file not found: $SUBJECTS_FILE"; exit 1; }
    # Read file, strip blank lines and comments
    mapfile -t SUBJECTS < <(grep -v '^\s*#' "$SUBJECTS_FILE" | grep -v '^\s*$')
    log_info "Subject list : ${SUBJECTS_FILE} (${#SUBJECTS[@]} subjects)"
else
    # Discover subject directories
    mapfile -t SUBJECTS < <(
        find "$DICOM_ROOT" -mindepth 1 -maxdepth 1 -type d \
            | xargs -I{} basename {} \
            | sort
    )
    log_info "Discovered ${#SUBJECTS[@]} subjects from ${DICOM_ROOT}"
fi

if [[ ${#SUBJECTS[@]} -eq 0 ]]; then
    log_warn "No subjects found. Exiting."
    exit 0
fi

# ── Set up batch log ──────────────────────────────────────────────────────────
BATCH_LOG="${OUTPUT_DIR}/logs/batch_$(date +%Y%m%dT%H%M%S).log"
mkdir -p "$(dirname "$BATCH_LOG")"

log_section "Batch HeudiConv conversion"
log_info "DICOM root    : ${DICOM_ROOT}"
log_info "Output dir    : ${OUTPUT_DIR}"
log_info "Heuristic     : ${HEURISTIC_FILE}"
log_info "Subjects (n=${#SUBJECTS[@]}) : ${SUBJECTS[*]}"
log_info "Parallel jobs : ${PARALLEL}"
log_info "Batch log     : ${BATCH_LOG}"

# ── Worker function ───────────────────────────────────────────────────────────
run_one_subject() {
    local subject="$1"
    local dicom_dir="${DICOM_ROOT}/${subject}"
    local t_start t_end status_str

    t_start=$(date +%s)

    if [[ ! -d "$dicom_dir" ]]; then
        echo "[SKIP] ${subject}: DICOM directory not found (${dicom_dir})" | tee -a "$BATCH_LOG"
        return 0
    fi

    echo "[START] $(date '+%Y-%m-%d %H:%M:%S')  ${subject}" | tee -a "$BATCH_LOG"

    if bash "$SINGLE_SCRIPT" "$subject" "$dicom_dir" "$OUTPUT_DIR" "$HEURISTIC_FILE" \
            >>"$BATCH_LOG" 2>&1; then
        status_str="${GREEN}SUCCESS${NC}"
    else
        status_str="${RED}FAILED${NC}"
    fi

    t_end=$(date +%s)
    elapsed=$(( t_end - t_start ))
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${subject}: ${status_str}  (${elapsed}s)" \
        | tee -a "$BATCH_LOG"
}

export -f run_one_subject
export BATCH_LOG DICOM_ROOT OUTPUT_DIR HEURISTIC_FILE SINGLE_SCRIPT GREEN RED NC

# ── Execute (sequential or parallel) ─────────────────────────────────────────
T_BATCH_START=$(date +%s)

if [[ "$PARALLEL" -le 1 ]]; then
    for subject in "${SUBJECTS[@]}"; do
        run_one_subject "$subject"
    done
else
    # Use GNU parallel if available, otherwise fall back to background jobs
    if command -v parallel &>/dev/null; then
        log_info "Using GNU parallel with ${PARALLEL} jobs."
        printf '%s\n' "${SUBJECTS[@]}" \
            | parallel --jobs "$PARALLEL" run_one_subject
    else
        log_warn "GNU parallel not found — using background jobs (no rate limiting)."
        PIDS=()
        for subject in "${SUBJECTS[@]}"; do
            run_one_subject "$subject" &
            PIDS+=($!)
            # Limit concurrency manually
            while [[ $(jobs -rp | wc -l) -ge $PARALLEL ]]; do
                sleep 1
            done
        done
        # Wait for all remaining jobs
        for pid in "${PIDS[@]}"; do
            wait "$pid" || true
        done
    fi
fi

T_BATCH_END=$(date +%s)
ELAPSED=$(( T_BATCH_END - T_BATCH_START ))

# ── Summary ───────────────────────────────────────────────────────────────────
log_section "Batch complete"
log_info "Total subjects : ${#SUBJECTS[@]}"
log_info "Elapsed time   : ${ELAPSED}s ($(( ELAPSED / 60 ))m $(( ELAPSED % 60 ))s)"
log_info "Batch log      : ${BATCH_LOG}"

# Count successes / failures from the log
NSUCCESS=$(grep -c '\[OK\]\|SUCCESS' "$BATCH_LOG" 2>/dev/null || true)
NFAILED=$(grep -c 'FAILED' "$BATCH_LOG" 2>/dev/null || true)
log_ok  "Succeeded : ${NSUCCESS}"
[[ "$NFAILED" -gt 0 ]] && log_error "Failed    : ${NFAILED} — check ${BATCH_LOG}"
