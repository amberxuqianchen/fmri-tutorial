#!/usr/bin/env bash
# =============================================================================
# validate_dataset.sh
#
# Run bids-validator on a BIDS dataset directory and save a report.
#
# Usage:
#   bash validate_dataset.sh <BIDS_DIR> [--json]
#
# Arguments:
#   BIDS_DIR   Root directory of the BIDS dataset (required)
#   --json     Also save a machine-readable JSON report
#
# Output:
#   <BIDS_DIR>/bids_validation_report/bids_validator_output.txt
#   <BIDS_DIR>/bids_validation_report/bids_validator_report.json  (--json only)
#
# Dependencies:
#   Node.js + npm  — https://nodejs.org
#   bids-validator — npm install -g bids-validator
#
# Examples:
#   bash validate_dataset.sh /data/bids
#   bash validate_dataset.sh /data/bids --json
# =============================================================================
set -euo pipefail

# ── Colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'
log_info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()      { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ── Parse arguments ───────────────────────────────────────────────────────────
usage() {
    sed -n '2,/^# ===*/p' "$0" | sed 's/^# \{0,2\}//'
    exit 0
}

[[ $# -lt 1 ]] && { log_error "BIDS_DIR is required."; usage; }

BIDS_DIR=""
JSON_FLAG=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)   JSON_FLAG=true; shift ;;
        --help|-h) usage ;;
        -*)        log_error "Unknown option: $1"; usage ;;
        *)
            if [[ -z "$BIDS_DIR" ]]; then
                BIDS_DIR="$1"
            else
                log_error "Unexpected argument: $1"
                usage
            fi
            shift
            ;;
    esac
done

[[ -z "$BIDS_DIR" ]] && { log_error "BIDS_DIR is required."; usage; }

# ── Validate inputs ───────────────────────────────────────────────────────────
if [[ ! -d "$BIDS_DIR" ]]; then
    log_error "Directory not found: $BIDS_DIR"
    exit 1
fi

# ── Check for bids-validator ──────────────────────────────────────────────────
if ! command -v bids-validator &>/dev/null; then
    log_error "bids-validator not found."
    echo ""
    echo "  Install options:"
    echo "    npm install -g bids-validator"
    echo ""
    echo "  If npm/Node.js is not installed:"
    echo "    macOS  : brew install node"
    echo "    Ubuntu : sudo apt-get install -y nodejs npm"
    echo "    conda  : conda install -c conda-forge nodejs"
    echo ""
    echo "  Docker alternative (no Node.js required):"
    echo "    docker run -ti --rm -v \"${BIDS_DIR}\":/data:ro bids/validator /data"
    exit 1
fi

VALIDATOR_VERSION=$(bids-validator --version 2>/dev/null || echo "unknown")
log_info "bids-validator version : ${VALIDATOR_VERSION}"
log_info "BIDS directory         : ${BIDS_DIR}"

# ── Set up output directory ───────────────────────────────────────────────────
REPORT_DIR="${BIDS_DIR}/bids_validation_report"
mkdir -p "$REPORT_DIR"

TEXT_REPORT="${REPORT_DIR}/bids_validator_output.txt"
JSON_REPORT="${REPORT_DIR}/bids_validator_report.json"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# ── Run bids-validator (text) ─────────────────────────────────────────────────
log_info "Running bids-validator ..."
echo ""

{
    echo "bids-validator report"
    echo "Generated  : ${TIMESTAMP}"
    echo "Validator  : ${VALIDATOR_VERSION}"
    echo "BIDS dir   : ${BIDS_DIR}"
    echo "============================================================"
} > "$TEXT_REPORT"

T_START=$(date +%s)

# Run bids-validator; capture output but also display it
# Return code is non-zero when there are errors — we handle that ourselves
set +e
bids-validator "$BIDS_DIR" 2>&1 | tee -a "$TEXT_REPORT"
VALIDATOR_RC=${PIPESTATUS[0]}
set -e

T_END=$(date +%s)
ELAPSED=$(( T_END - T_START ))

echo ""
echo "Elapsed time: ${ELAPSED}s" >> "$TEXT_REPORT"

log_ok "Text report saved to: ${TEXT_REPORT}"

# ── Run bids-validator (JSON) if requested ────────────────────────────────────
if [[ "$JSON_FLAG" == true ]]; then
    log_info "Running bids-validator --json ..."
    set +e
    bids-validator "$BIDS_DIR" --json > "$JSON_REPORT" 2>&1
    JSON_RC=$?
    set -e

    if [[ "$JSON_RC" -eq 0 ]] || [[ -s "$JSON_REPORT" ]]; then
        log_ok "JSON report saved to: ${JSON_REPORT}"

        # Quick summary from JSON if python is available
        if command -v python3 &>/dev/null; then
            python3 - "$JSON_REPORT" <<'PYEOF'
import json, sys, pathlib

report_path = pathlib.Path(sys.argv[1])
try:
    data = json.loads(report_path.read_text())
except Exception as e:
    print(f"Could not parse JSON report: {e}")
    sys.exit(0)

issues = data.get("issues", {})
errors   = issues.get("errors",   [])
warnings = issues.get("warnings", [])
summary  = data.get("summary",    {})

print()
print("  Validator summary:")
print(f"    Subjects  : {summary.get('subjects', [])}")
print(f"    Tasks     : {summary.get('tasks', [])}")
print(f"    Errors    : {len(errors)}")
print(f"    Warnings  : {len(warnings)}")

if errors:
    print()
    print("  Errors:")
    for e in errors:
        print(f"    [{e.get('key','?')}] {e.get('reason','')}")

PYEOF
        fi
    else
        log_warn "JSON validation may have failed — check: ${JSON_REPORT}"
    fi
fi

# ── Final result ──────────────────────────────────────────────────────────────
echo ""
if [[ "$VALIDATOR_RC" -eq 0 ]]; then
    log_ok "Validation PASSED ✓"
else
    log_warn "Validation completed with issues (return code ${VALIDATOR_RC})."
    log_warn "Review the report: ${TEXT_REPORT}"
fi

exit "$VALIDATOR_RC"
