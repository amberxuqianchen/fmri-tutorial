"""Inspect fMRIPrep output files for a single subject and summarise motion statistics.

This script locates the preprocessed BOLD, brain mask, confounds TSV, and HTML
report produced by fMRIPrep for a given subject and task, then prints a
structured summary that includes:

1. A listing of all key output files and whether they exist
2. Motion statistics derived from the confounds TSV:
   - Mean and maximum framewise displacement (FD)
   - Number and percentage of volumes above the FD threshold
3. The confound column names grouped by type (motion, tissue, CompCor, etc.)

This script is designed to be run after fMRIPrep has completed so that you can
quickly audit a subject's outputs before proceeding to GLM modelling.

Requirements:
    - pandas >= 1.3
    - utils.io_utils.load_tsv (from this repository's utils/ package)

Example usage::

    python inspect_fmriprep_outputs.py \\
        --fmriprep_dir /data/derivatives/fmriprep \\
        --subject 01 \\
        --task rest

    python inspect_fmriprep_outputs.py \\
        --fmriprep_dir /data/derivatives/fmriprep \\
        --subject 03 \\
        --task socialcognition \\
        --fd_threshold 0.2
"""

import argparse
import os
import sys
import warnings

# Motion parameter names and their physical units (shared by multiple functions)
MOTION_PARAMS = ["trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z"]
MOTION_UNITS  = ["mm", "mm", "mm", "rad", "rad", "rad"]


def parse_args():
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed argument values.
    """
    parser = argparse.ArgumentParser(
        description=(
            "List fMRIPrep output files and print motion statistics "
            "for a single subject/task."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--fmriprep_dir",
        required=True,
        metavar="PATH",
        help="Path to the fMRIPrep derivatives directory (e.g. derivatives/fmriprep).",
    )
    parser.add_argument(
        "--subject",
        required=True,
        metavar="LABEL",
        help="Subject label without the 'sub-' prefix (e.g. '01').",
    )
    parser.add_argument(
        "--task",
        required=True,
        metavar="LABEL",
        help="Task label (e.g. 'rest' or 'socialcognition').",
    )
    parser.add_argument(
        "--fd_threshold",
        type=float,
        default=0.5,
        metavar="MM",
        help="Framewise displacement threshold in mm for flagging motion spikes.",
    )
    return parser.parse_args()


def find_subject_files(fmriprep_dir, subject, task):
    """Locate fMRIPrep output files for a subject and task.

    Searches the func/ subdirectory for preprocessed BOLD, brain mask, and
    confounds TSV matching the subject/task combination. Also checks for the
    subject-level HTML report.

    Args:
        fmriprep_dir (str): Path to the fMRIPrep derivatives root.
        subject (str): Subject label without 'sub-' prefix.
        task (str): Task label.

    Returns:
        dict: Mapping of file role to absolute path (or None if not found).
    """
    import glob as _glob

    sub_label = f"sub-{subject}"
    func_dir = os.path.join(fmriprep_dir, sub_label, "func")
    anat_dir = os.path.join(fmriprep_dir, sub_label, "anat")

    def _first_match(directory, pattern):
        """Return the first file matching pattern in directory, or None."""
        if not os.path.isdir(directory):
            return None
        matches = sorted(_glob.glob(os.path.join(directory, pattern)))
        return matches[0] if matches else None

    task_prefix = f"{sub_label}_task-{task}"

    files = {
        "Preprocessed BOLD": _first_match(
            func_dir, f"{task_prefix}*_desc-preproc_bold.nii.gz"
        ),
        "Functional brain mask": _first_match(
            func_dir, f"{task_prefix}*_desc-brain_mask.nii.gz"
        ),
        "Confounds TSV": _first_match(
            func_dir, f"{task_prefix}*_desc-confounds_timeseries.tsv"
        ),
        "Confounds JSON": _first_match(
            func_dir, f"{task_prefix}*_desc-confounds_timeseries.json"
        ),
        "BOLD reference image": _first_match(
            func_dir, f"{task_prefix}*_boldref.nii.gz"
        ),
        "T1w preprocessed": _first_match(
            anat_dir, f"{sub_label}_desc-preproc_T1w.nii.gz"
        ),
        "T1w brain mask": _first_match(
            anat_dir, f"{sub_label}_desc-brain_mask.nii.gz"
        ),
        "HTML report": os.path.join(fmriprep_dir, f"{sub_label}.html"),
    }

    # Replace paths that don't exist with None
    files = {
        role: path if (path and os.path.exists(path)) else None
        for role, path in files.items()
    }

    return files


def compute_motion_stats(confounds_df, fd_threshold=0.5):
    """Compute motion summary statistics from a confounds DataFrame.

    Args:
        confounds_df (pandas.DataFrame): Confounds table loaded from fMRIPrep.
        fd_threshold (float): Framewise displacement threshold in mm.

    Returns:
        dict: Dictionary of motion statistics, or None if FD column is absent.
    """
    import pandas as pd
    import numpy as np

    if "framewise_displacement" not in confounds_df.columns:
        warnings.warn("'framewise_displacement' column not found in confounds TSV.")
        return None

    fd = pd.to_numeric(confounds_df["framewise_displacement"], errors="coerce")
    fd_valid = fd.dropna()
    n_total = len(fd)
    n_valid = len(fd_valid)

    if n_valid == 0:
        warnings.warn("No valid framewise displacement values found.")
        return None

    n_spikes = int((fd_valid > fd_threshold).sum())

    stats = {
        "n_volumes": n_total,
        "n_valid_fd": n_valid,
        "mean_fd_mm": float(fd_valid.mean()),
        "median_fd_mm": float(fd_valid.median()),
        "max_fd_mm": float(fd_valid.max()),
        "std_fd_mm": float(fd_valid.std()),
        "fd_threshold_mm": fd_threshold,
        "n_spikes": n_spikes,
        "pct_spikes": 100.0 * n_spikes / n_valid,
        "pct_remaining": 100.0 * (n_valid - n_spikes) / n_valid,
    }

    # Also summarise the motion parameter range
    for col in MOTION_PARAMS:
        if col in confounds_df.columns:
            vals = pd.to_numeric(confounds_df[col], errors="coerce").dropna()
            stats[f"{col}_range_mm"] = float(vals.max() - vals.min())

    return stats


def group_confound_columns(columns):
    """Group confound column names by type.

    Args:
        columns (list[str]): List of column names from the confounds TSV.

    Returns:
        dict: Mapping of group name to list of column names.
    """
    col_set = set(columns)

    groups = {
        "Motion (6-param)": [
            c for c in columns
            if c in {"trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z"}
        ],
        "Motion derivatives": [
            c for c in columns
            if "derivative1" in c and "power2" not in c
        ],
        "Motion squares": [
            c for c in columns if c.endswith("_power2") and "derivative" not in c
        ],
        "Motion derivative squares": [
            c for c in columns if "derivative1_power2" in c
        ],
        "Motion summary": [
            c for c in columns if c in {"framewise_displacement", "rmsd"}
        ],
        "Tissue signals": [
            c for c in columns if c in {"global_signal", "white_matter", "csf"}
        ],
        "aCompCor": [c for c in columns if c.startswith("a_comp_cor")],
        "tCompCor": [c for c in columns if c.startswith("t_comp_cor")],
        "ICA-AROMA": [c for c in columns if "aroma" in c.lower()],
        "Cosine drift": [c for c in columns if c.startswith("cosine")],
    }

    labelled = {c for cols in groups.values() for c in cols}
    groups["Other"] = [c for c in columns if c not in labelled]

    # Remove empty groups
    return {k: v for k, v in groups.items() if v}


def print_section(title, width=60):
    """Print a section header line."""
    print(f"\n{'='*width}")
    print(f"  {title}")
    print(f"{'='*width}")


def main():
    """Entry point: locate files, load confounds, print summary report."""
    args = parse_args()

    # Ensure utils/ on sys.path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    try:
        from utils.io_utils import load_tsv
    except ImportError:
        import pandas as _pd
        load_tsv = lambda p, **kw: _pd.read_csv(p, sep="\t", **kw)
        warnings.warn("utils.io_utils not found; using pandas.read_csv directly.")

    fmriprep_dir = os.path.abspath(args.fmriprep_dir)

    print_section(
        f"fMRIPrep Output Inspector — sub-{args.subject}, task-{args.task}"
    )
    print(f"  fMRIPrep dir : {fmriprep_dir}")
    print(f"  Subject      : sub-{args.subject}")
    print(f"  Task         : {args.task}")
    print(f"  FD threshold : {args.fd_threshold} mm")

    # ── 1. File listing ──────────────────────────────────────────────────────
    print_section("Output Files")
    files = find_subject_files(fmriprep_dir, args.subject, args.task)

    n_found = 0
    for role, path in files.items():
        if path:
            size_mb = os.path.getsize(path) / 1e6
            print(f"  [FOUND]   {role}")
            print(f"            {path}  ({size_mb:.1f} MB)")
            n_found += 1
        else:
            print(f"  [MISSING] {role}")

    print(f"\n  {n_found}/{len(files)} expected files found.")

    # ── 2. Motion statistics ─────────────────────────────────────────────────
    confounds_path = files.get("Confounds TSV")
    if confounds_path is None:
        print_section("Motion Statistics")
        print("  Cannot compute motion statistics: confounds TSV not found.")
        sys.exit(0)

    try:
        confounds_df = load_tsv(confounds_path)
    except Exception as exc:
        print(f"\n  ERROR loading confounds TSV: {exc}")
        sys.exit(1)

    print_section("Motion Statistics")
    stats = compute_motion_stats(confounds_df, fd_threshold=args.fd_threshold)

    if stats is None:
        print("  Could not compute FD statistics (missing column).")
    else:
        print(f"  Volumes total    : {stats['n_volumes']}")
        print(f"  Mean FD          : {stats['mean_fd_mm']:.4f} mm")
        print(f"  Median FD        : {stats['median_fd_mm']:.4f} mm")
        print(f"  Max FD           : {stats['max_fd_mm']:.4f} mm")
        print(f"  Std FD           : {stats['std_fd_mm']:.4f} mm")
        print(f"  FD threshold     : {stats['fd_threshold_mm']} mm")
        print(f"  Motion spikes    : {stats['n_spikes']} ({stats['pct_spikes']:.1f}%)")
        print(f"  Remaining vols   : {stats['n_valid_fd'] - stats['n_spikes']} "
              f"({stats['pct_remaining']:.1f}%)")

        # Print motion parameter ranges
        print("\n  Translation / rotation parameter ranges:")
        for col, unit in zip(MOTION_PARAMS, MOTION_UNITS):
            key = f"{col}_range_mm"
            if key in stats:
                print(f"    {col:<12}: range = {stats[key]:.4f} {unit}")

        # Quality flag
        print()
        if stats["pct_spikes"] > 20:
            print("  ⚠  WARNING: >20% of volumes exceed FD threshold — "
                  "consider excluding this run.")
        elif stats["mean_fd_mm"] > 0.5:
            print("  ⚠  WARNING: Mean FD > 0.5 mm — run has elevated motion.")
        else:
            print("  ✓  Motion levels appear acceptable.")

    # ── 3. Confound column summary ───────────────────────────────────────────
    print_section("Available Confound Columns")
    print(f"  Total columns: {len(confounds_df.columns)}\n")

    groups = group_confound_columns(confounds_df.columns.tolist())
    for group_name, cols in groups.items():
        print(f"  {group_name} ({len(cols)}):")
        # Print up to 8 names per line
        for i in range(0, len(cols), 8):
            print(f"    {', '.join(cols[i:i+8])}")

    print(f"\n{'='*60}")
    print("  Done.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
