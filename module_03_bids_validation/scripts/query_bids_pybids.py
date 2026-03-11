#!/usr/bin/env python3
"""query_bids_pybids.py

Demonstrate PyBIDS queries and print a dataset summary.

Usage
-----
    python query_bids_pybids.py --bids_dir /data/bids
    python query_bids_pybids.py --bids_dir /data/bids --subject sub-01 --task rest
    python query_bids_pybids.py --bids_dir /data/bids --subject sub-01 --task nback --run 1

Output
------
Prints a structured summary to stdout including:
  - Number of subjects, sessions, tasks
  - Count of BOLD, T1w, and field-map files
  - Filtered file listing when --subject / --task / --run are given
  - Per-task run counts and any missing event files
"""

import argparse
import json
import pathlib
import sys
from typing import Optional


def check_pybids() -> bool:
    """Return True if PyBIDS is importable."""
    try:
        import bids  # noqa: F401
        return True
    except ImportError:
        return False


def load_layout(bids_dir: pathlib.Path, validate: bool = False):
    """Load and return a BIDSLayout, or exit with a helpful message."""
    from bids import BIDSLayout

    if not bids_dir.exists():
        print(f"ERROR: BIDS directory not found: {bids_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading BIDSLayout: {bids_dir} ...")
    layout = BIDSLayout(str(bids_dir), validate=validate)
    print("Layout loaded.\n")
    return layout


# ── Dataset summary ───────────────────────────────────────────────────────────

def print_dataset_summary(layout) -> None:
    """Print a structured overview of the entire dataset."""
    subjects  = layout.get_subjects()
    sessions  = layout.get_sessions()
    tasks     = layout.get_tasks()
    runs      = layout.get_runs()

    bold_files = layout.get(suffix="bold",       extension=".nii.gz")
    t1w_files  = layout.get(suffix="T1w",        extension=".nii.gz")
    fmap_files = layout.get(datatype="fmap",     extension=".nii.gz")
    event_files = layout.get(suffix="events",    extension=".tsv")

    print("Dataset summary")
    print("=" * 55)
    print(f"  Path              : {layout.root}")
    print(f"  Subjects  (n={len(subjects):>3}) : {', '.join(subjects)}")
    print(f"  Sessions          : {', '.join(sessions) if sessions else 'n/a'}")
    print(f"  Tasks             : {', '.join(tasks) if tasks else 'none'}")
    print(f"  Runs              : {', '.join(str(r) for r in runs) if runs else 'n/a'}")
    print()
    print(f"  BOLD runs         : {len(bold_files)}")
    print(f"  T1w scans         : {len(t1w_files)}")
    print(f"  Field maps        : {len(fmap_files)}")
    print(f"  Events files      : {len(event_files)}")
    print()

    # Per-task breakdown
    if tasks:
        print("  Per-task breakdown:")
        print(f"    {'Task':<25} {'BOLD':>6} {'Events':>8} {'Missing events':>16}")
        print(f"    {'-'*25} {'------':>6} {'--------':>8} {'----------------':>16}")
        for task in tasks:
            task_bold = layout.get(suffix="bold", task=task, extension=".nii.gz")
            task_events = layout.get(suffix="events", task=task, extension=".tsv")
            missing = len(task_bold) - len(task_events)
            missing_str = str(missing) if missing > 0 else "-"
            print(f"    {task:<25} {len(task_bold):>6} {len(task_events):>8} {missing_str:>16}")
        print()


# ── Filtered file listing ─────────────────────────────────────────────────────

def print_filtered_files(
    layout,
    subject: Optional[str],
    task: Optional[str],
    run: Optional[int],
) -> None:
    """Print files matching the given filter criteria."""
    filters: dict = {}
    if subject:
        # Strip "sub-" prefix — PyBIDS uses bare labels
        filters["subject"] = subject.lstrip("sub-").lstrip("-") if subject.startswith("sub-") else subject
    if task:
        filters["task"] = task
    if run is not None:
        filters["run"] = run

    labels = ", ".join(f"{k}={v}" for k, v in filters.items())
    print(f"Filtered query: {labels or 'all'}")
    print("-" * 55)

    bids_root = pathlib.Path(layout.root)

    for suffix, label in [("bold", "BOLD"), ("T1w", "T1w"), ("events", "Events")]:
        files = layout.get(suffix=suffix, extension=(".nii.gz" if suffix != "events" else ".tsv"), **filters)
        if not files:
            continue
        print(f"\n  {label} ({len(files)}):")
        for f in files:
            try:
                rel = pathlib.Path(f.path).relative_to(bids_root)
            except (AttributeError, ValueError):
                rel = pathlib.Path(str(f))
            print(f"    {rel}")

    # Field maps are not task-specific — only show without task filter
    if not task:
        fmap_kw = {k: v for k, v in filters.items() if k != "task"}
        fmap_files = layout.get(datatype="fmap", extension=".nii.gz", **fmap_kw)
        if fmap_files:
            print(f"\n  Field maps ({len(fmap_files)}):")
            for f in fmap_files:
                try:
                    rel = pathlib.Path(f.path).relative_to(bids_root)
                except (AttributeError, ValueError):
                    rel = pathlib.Path(str(f))
                print(f"    {rel}")

    print()


# ── Metadata inspection ───────────────────────────────────────────────────────

def print_metadata_sample(layout, subject: Optional[str], task: Optional[str]) -> None:
    """Print selected metadata fields from the first BOLD sidecar found."""
    filters: dict = {"suffix": "bold", "extension": ".json"}
    if subject:
        filters["subject"] = subject.lstrip("sub-").lstrip("-") if subject.startswith("sub-") else subject
    if task:
        filters["task"] = task

    json_files = layout.get(**filters)
    if not json_files:
        return

    first = json_files[0]
    try:
        path = pathlib.Path(first.path)
    except AttributeError:
        path = pathlib.Path(str(first))

    print(f"BOLD sidecar metadata sample ({path.name}):")
    print("-" * 55)
    try:
        with open(path) as fh:
            meta = json.load(fh)
    except Exception as exc:
        print(f"  Could not read {path}: {exc}")
        return

    for field in (
        "RepetitionTime",
        "EchoTime",
        "FlipAngle",
        "PhaseEncodingDirection",
        "EffectiveEchoSpacing",
        "TotalReadoutTime",
        "TaskName",
        "SliceTimingCorrected",
    ):
        val = meta.get(field, "<not present>")
        print(f"  {field:<30} {val}")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print a PyBIDS dataset summary and demonstrate queries.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--bids_dir",
        required=True,
        help="Root directory of the BIDS dataset.",
    )
    parser.add_argument(
        "--subject",
        default=None,
        help="Filter to a specific subject (e.g. sub-01 or 01).",
    )
    parser.add_argument(
        "--task",
        default=None,
        help="Filter to a specific task name (e.g. rest, nback).",
    )
    parser.add_argument(
        "--run",
        type=int,
        default=None,
        help="Filter to a specific run number (e.g. 1, 2).",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        default=False,
        help="Enable PyBIDS BIDS validation on load (slower).",
    )
    args = parser.parse_args()

    if not check_pybids():
        print("ERROR: PyBIDS is not installed.", file=sys.stderr)
        print("  Install with: pip install pybids", file=sys.stderr)
        sys.exit(1)

    bids_dir = pathlib.Path(args.bids_dir).resolve()
    layout = load_layout(bids_dir, validate=args.validate)

    print_dataset_summary(layout)
    print_filtered_files(layout, args.subject, args.task, args.run)
    print_metadata_sample(layout, args.subject, args.task)


if __name__ == "__main__":
    main()
