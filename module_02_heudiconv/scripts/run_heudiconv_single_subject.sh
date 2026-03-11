#!/usr/bin/env bash
# =============================================================================
# run_heudiconv_single_subject.sh
#
# Run HeudiConv DICOM-to-BIDS conversion for a single subject.
#
# Usage:
#   bash run_heudiconv_single_subject.sh \
#       <SUBJECT_ID> <DICOM_DIR> <OUTPUT_DIR> <HEURISTIC_FILE>
#
# Arguments:
#   SUBJECT_ID      Subject label (e.g. sub-01 or just 01)
#   DICOM_DIR       Root directory containing DICOMs for this subject
#   OUTPUT_DIR      BIDS dataset root (will be created if absent)
#   HEURISTIC_FILE  Path to HeudiConv heuristic Python file
#
# Environment variables (optional):
#   HEUDICONV_EXTRA_ARGS   Additional flags passed to heudiconv
#   DCMTEMPLATE            Override the DICOM glob template
#                          (default: <DICOM_DIR>/*/*.dcm)
#
# Examples:
#   bash run_heudiconv_single_subject.sh \
#       sub-01 /data/dicoms/sub-01 /data/bids heuristic.py
# =============================================================================
set -euo pipefail

# ── Colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'
log_info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()      { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ── Usage ─────────────────────────────────────────────────────────────────────
usage() {
    sed -n '2,/^# ===*/p' "$0" | sed 's/^# \{0,2\}//'
    exit 1
}

[[ $# -lt 4 ]] && { log_error "Insufficient arguments."; usage; }

SUBJECT_ID="$1"
DICOM_DIR="$2"
OUTPUT_DIR="$3"
HEURISTIC_FILE="$4"

# Normalise subject label: strip leading "sub-" so heudiconv gets bare label
SUBJECT_BARE="${SUBJECT_ID#sub-}"

# ── Input validation ──────────────────────────────────────────────────────────
log_info "Validating inputs ..."

if [[ ! -d "$DICOM_DIR" ]]; then
    log_error "DICOM_DIR does not exist: $DICOM_DIR"
    exit 1
fi

if [[ ! -f "$HEURISTIC_FILE" ]]; then
    log_error "HEURISTIC_FILE does not exist: $HEURISTIC_FILE"
    exit 1
fi

if ! command -v heudiconv &>/dev/null; then
    log_error "heudiconv not found. Install with: pip install heudiconv[all]"
    exit 1
fi

log_ok "Inputs validated."

# ── Setup ─────────────────────────────────────────────────────────────────────
mkdir -p "$OUTPUT_DIR"

# DICOM glob template — adjust for your site's DICOM layout if needed
DCMTEMPLATE="${DCMTEMPLATE:-${DICOM_DIR}/{subject}/*/*.dcm}"

LOG_FILE="${OUTPUT_DIR}/logs/heudiconv_${SUBJECT_BARE}_$(date +%Y%m%dT%H%M%S).log"
mkdir -p "$(dirname "$LOG_FILE")"

# ── Print configuration ───────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  HeudiConv single-subject conversion"
echo "============================================================"
log_info "Subject ID    : sub-${SUBJECT_BARE}"
log_info "DICOM dir     : ${DICOM_DIR}"
log_info "DCM template  : ${DCMTEMPLATE}"
log_info "Output dir    : ${OUTPUT_DIR}"
log_info "Heuristic     : ${HEURISTIC_FILE}"
log_info "Log file      : ${LOG_FILE}"
echo ""

# ── Dry run first (discovery only) ───────────────────────────────────────────
log_info "Step 1/2 — dry run (series discovery) ..."
T_DRY_START=$(date +%s)

heudiconv \
    --subjects "${SUBJECT_BARE}" \
    --dicom_dir_template "${DCMTEMPLATE}" \
    --heuristic "${HEURISTIC_FILE}" \
    --outdir "${OUTPUT_DIR}" \
    --bids \
    --overwrite \
    --dry_run \
    2>&1 | tee "${LOG_FILE}.dryrun"

T_DRY_END=$(date +%s)
log_ok "Dry run complete in $(( T_DRY_END - T_DRY_START ))s."

# ── Full conversion ───────────────────────────────────────────────────────────
log_info "Step 2/2 — full conversion ..."
T_START=$(date +%s)

heudiconv \
    --subjects "${SUBJECT_BARE}" \
    --dicom_dir_template "${DCMTEMPLATE}" \
    --heuristic "${HEURISTIC_FILE}" \
    --outdir "${OUTPUT_DIR}" \
    --bids \
    --overwrite \
    ${HEUDICONV_EXTRA_ARGS:-} \
    2>&1 | tee "${LOG_FILE}"

T_END=$(date +%s)
ELAPSED=$(( T_END - T_START ))

echo ""
echo "============================================================"
log_ok "Conversion complete for sub-${SUBJECT_BARE}"
log_info "Elapsed time  : ${ELAPSED}s ($(( ELAPSED / 60 ))m $(( ELAPSED % 60 ))s)"
log_info "Output        : ${OUTPUT_DIR}/sub-${SUBJECT_BARE}/"
log_info "Log           : ${LOG_FILE}"
echo "============================================================"

# ── Quick file count ──────────────────────────────────────────────────────────
SUB_DIR="${OUTPUT_DIR}/sub-${SUBJECT_BARE}"
if [[ -d "$SUB_DIR" ]]; then
    NII_COUNT=$(find "$SUB_DIR" -name "*.nii.gz" | wc -l)
    JSON_COUNT=$(find "$SUB_DIR" -name "*.json" | wc -l)
    log_info "NIfTI files created : ${NII_COUNT}"
    log_info "JSON sidecars       : ${JSON_COUNT}"
else
    log_warn "Subject output directory not found: ${SUB_DIR}"
    log_warn "Check the log: ${LOG_FILE}"
    exit 1
fi
