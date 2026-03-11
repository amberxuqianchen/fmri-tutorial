#!/usr/bin/env python3
"""check_heudiconv_output.py

Validate HeudiConv BIDS output for one or more subjects.

Checks that expected files were created, reports missing or unexpected files,
and summarises JSON sidecar metadata.

Usage
-----
    python check_heudiconv_output.py --bids_dir /data/bids --expected_subjects sub-01 sub-02
    python check_heudiconv_output.py --bids_dir /data/bids  # check all subjects found
    python check_heudiconv_output.py --bids_dir /data/bids --report_json report.json
"""

import argparse
import json
import os
import pathlib
import sys
from typing import NamedTuple


# ── Expected BIDS file patterns ───────────────────────────────────────────────
# Each entry is (relative_glob_pattern, required)
# {subject} is replaced at runtime.
EXPECTED_PATTERNS: list[tuple[str, bool]] = [
    ("{subject}/anat/{subject}_T1w.nii.gz", True),
    ("{subject}/anat/{subject}_T1w.json", True),
    ("{subject}/func/{subject}_task-*_bold.nii.gz", True),
    ("{subject}/func/{subject}_task-*_bold.json", True),
]

ROOT_FILES: list[tuple[str, bool]] = [
    ("dataset_description.json", True),
    ("participants.tsv", True),
    ("README", False),
    (".bidsignore", False),
]


class SubjectReport(NamedTuple):
    subject: str
    missing_required: list[str]
    missing_optional: list[str]
    present: list[str]
    sidecar_issues: list[str]


# ── Helpers ───────────────────────────────────────────────────────────────────

def find_subjects(bids_dir: pathlib.Path) -> list[str]:
    """Return all sub-* directories found in bids_dir."""
    return sorted(
        d.name
        for d in bids_dir.iterdir()
        if d.is_dir() and d.name.startswith("sub-")
    )


def glob_pattern(bids_dir: pathlib.Path, pattern: str, subject: str) -> list[pathlib.Path]:
    """Expand a pattern with {subject} and glob against bids_dir."""
    expanded = pattern.replace("{subject}", subject)
    return sorted(bids_dir.glob(expanded))


def check_sidecar(json_path: pathlib.Path) -> list[str]:
    """Return a list of issues found in a JSON sidecar."""
    issues: list[str] = []
    try:
        with open(json_path) as fh:
            meta = json.load(fh)
    except json.JSONDecodeError as exc:
        issues.append(f"Invalid JSON in {json_path.name}: {exc}")
        return issues

    if "bold" in json_path.name.lower():
        for field in ("RepetitionTime", "EchoTime"):
            if field not in meta:
                issues.append(f"{json_path.name}: missing required field '{field}'")
    return issues


def check_subject(bids_dir: pathlib.Path, subject: str) -> SubjectReport:
    """Run all checks for a single subject."""
    missing_required: list[str] = []
    missing_optional: list[str] = []
    present: list[str] = []
    sidecar_issues: list[str] = []

    for pattern, required in EXPECTED_PATTERNS:
        matches = glob_pattern(bids_dir, pattern, subject)
        if matches:
            for m in matches:
                present.append(str(m.relative_to(bids_dir)))
                if m.suffix == ".json" or m.name.endswith(".json"):
                    sidecar_issues.extend(check_sidecar(m))
        else:
            expanded = pattern.replace("{subject}", subject)
            if required:
                missing_required.append(expanded)
            else:
                missing_optional.append(expanded)

    # Also check JSON sidecars found under func/
    for json_file in (bids_dir / subject / "func").glob("*.json") if (bids_dir / subject / "func").exists() else []:
        sidecar_issues.extend(check_sidecar(json_file))

    # Deduplicate sidecar issues while preserving order
    seen: set[str] = set()
    sidecar_issues = [x for x in sidecar_issues if not (x in seen or seen.add(x))]

    return SubjectReport(
        subject=subject,
        missing_required=missing_required,
        missing_optional=missing_optional,
        present=present,
        sidecar_issues=sidecar_issues,
    )


# ── Report printing ───────────────────────────────────────────────────────────

def print_report(
    bids_dir: pathlib.Path,
    reports: list[SubjectReport],
    root_issues: list[str],
) -> int:
    """Print the full validation report. Returns the number of errors found."""
    total_errors = 0

    print()
    print("=" * 65)
    print("  HeudiConv Output Validation Report")
    print(f"  BIDS dir: {bids_dir}")
    print("=" * 65)

    # Root-level files
    if root_issues:
        print("\n[ROOT] Missing files:")
        for issue in root_issues:
            print(f"  ✗ {issue}")
        total_errors += len(root_issues)
    else:
        print("\n[ROOT] All root-level files present ✓")

    # Per-subject
    for rep in reports:
        errors = len(rep.missing_required) + len(rep.sidecar_issues)
        warnings = len(rep.missing_optional)
        status = "✓" if errors == 0 else "✗"
        print(f"\n[{rep.subject}]  {status}  "
              f"{len(rep.present)} files present, "
              f"{errors} errors, {warnings} warnings")

        for path in rep.present:
            print(f"    ✓  {path}")

        for path in rep.missing_required:
            print(f"    ✗  MISSING (required): {path}")

        for path in rep.missing_optional:
            print(f"    ⚠  missing (optional): {path}")

        for issue in rep.sidecar_issues:
            print(f"    ⚠  sidecar: {issue}")

        total_errors += errors

    # Final summary
    print()
    print("-" * 65)
    if total_errors == 0:
        print(f"  RESULT: PASSED — {len(reports)} subject(s), no errors ✓")
    else:
        print(f"  RESULT: FAILED — {total_errors} error(s) across {len(reports)} subject(s) ✗")
    print("-" * 65)
    print()

    return total_errors


# ── Main ──────────────────────────────────────────────────────────────────────

def build_report_dict(
    bids_dir: pathlib.Path,
    reports: list[SubjectReport],
    root_issues: list[str],
) -> dict:
    """Build a JSON-serialisable report dictionary."""
    return {
        "bids_dir": str(bids_dir),
        "root_issues": root_issues,
        "subjects": [
            {
                "subject": r.subject,
                "present": r.present,
                "missing_required": r.missing_required,
                "missing_optional": r.missing_optional,
                "sidecar_issues": r.sidecar_issues,
            }
            for r in reports
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate HeudiConv BIDS output for one or more subjects.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--bids_dir",
        required=True,
        help="Root directory of the BIDS dataset to validate.",
    )
    parser.add_argument(
        "--expected_subjects",
        nargs="*",
        default=None,
        metavar="SUBJECT",
        help=(
            "One or more subject labels to check (e.g. sub-01 sub-02). "
            "If omitted, all sub-* directories found in BIDS_DIR are checked."
        ),
    )
    parser.add_argument(
        "--report_json",
        default=None,
        metavar="PATH",
        help="If given, also write a JSON report to this path.",
    )
    args = parser.parse_args()

    bids_dir = pathlib.Path(args.bids_dir).resolve()

    if not bids_dir.exists():
        print(f"ERROR: BIDS directory not found: {bids_dir}", file=sys.stderr)
        sys.exit(1)

    # Determine subject list
    if args.expected_subjects:
        subjects = args.expected_subjects
    else:
        subjects = find_subjects(bids_dir)
        if not subjects:
            print(f"No sub-* directories found in {bids_dir}.", file=sys.stderr)
            sys.exit(1)

    # Check root-level files
    root_issues: list[str] = []
    for rel_path, required in ROOT_FILES:
        if not (bids_dir / rel_path).exists() and required:
            root_issues.append(rel_path)

    # Check each subject
    reports: list[SubjectReport] = []
    for subject in subjects:
        if not (bids_dir / subject).exists():
            reports.append(
                SubjectReport(
                    subject=subject,
                    missing_required=[f"{subject}/ (directory not found)"],
                    missing_optional=[],
                    present=[],
                    sidecar_issues=[],
                )
            )
        else:
            reports.append(check_subject(bids_dir, subject))

    # Print report
    total_errors = print_report(bids_dir, reports, root_issues)

    # Optional JSON output
    if args.report_json:
        report_path = pathlib.Path(args.report_json)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_dict = build_report_dict(bids_dir, reports, root_issues)
        with open(report_path, "w") as fh:
            json.dump(report_dict, fh, indent=2)
        print(f"JSON report written to: {report_path}")

    sys.exit(0 if total_errors == 0 else 1)


if __name__ == "__main__":
    main()
