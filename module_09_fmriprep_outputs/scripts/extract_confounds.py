"""Extract a confound regression matrix from an fMRIPrep confounds TSV.

This script loads the confounds timeseries TSV produced by fMRIPrep, selects
columns according to a specified denoising strategy, optionally appends a
binary scrubbing column for volumes that exceed a framewise displacement (FD)
threshold, and saves the resulting matrix to a new TSV file.

Three denoising strategies are supported:

minimal
    Six rigid-body motion parameters (trans_x, trans_y, trans_z, rot_x,
    rot_y, rot_z) plus framewise_displacement. Fewest degrees of freedom
    consumed; appropriate as a baseline or for low-motion data.

moderate
    All minimal columns plus global_signal, white_matter, csf, and the
    first six anatomical CompCor components (a_comp_cor_00 through 05).
    Recommended default for task fMRI analyses.

aggressive
    All moderate columns plus the temporal derivatives, squares, and
    derivative-squares of all six motion parameters (24 motion parameters
    total), and all available aCompCor components. Recommended for
    resting-state functional connectivity analyses.

When ``--scrub`` is passed, a binary ``motion_outlier`` column is appended
(1 = volume exceeds the FD threshold and should be excluded; 0 = keep).

Requirements:
    - pandas >= 1.3
    - utils.io_utils.load_tsv, utils.io_utils.save_tsv

Example usage::

    # Moderate strategy, scrubbing at 0.5 mm FD
    python extract_confounds.py \\
        --confounds_tsv /data/fmriprep/sub-01/func/sub-01_task-rest_desc-confounds_timeseries.tsv \\
        --output_tsv /data/confounds/sub-01_task-rest_moderate_confounds.tsv \\
        --strategy moderate \\
        --scrub

    # Minimal strategy with conservative scrubbing
    python extract_confounds.py \\
        --confounds_tsv sub-01_task-rest_desc-confounds_timeseries.tsv \\
        --output_tsv sub-01_minimal_confounds.tsv \\
        --strategy minimal \\
        --fd_threshold 0.2 \\
        --scrub

    # Aggressive strategy, no scrubbing column
    python extract_confounds.py \\
        --confounds_tsv sub-01_task-rest_desc-confounds_timeseries.tsv \\
        --output_tsv sub-01_aggressive_confounds.tsv \\
        --strategy aggressive
"""

import argparse
import os
import sys
import warnings


def parse_args():
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed argument values.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Extract a confound regression matrix from an fMRIPrep confounds TSV "
            "using a specified denoising strategy."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--confounds_tsv",
        required=True,
        metavar="PATH",
        help="Path to the fMRIPrep confounds timeseries TSV file.",
    )
    parser.add_argument(
        "--output_tsv",
        required=True,
        metavar="PATH",
        help="Destination path for the extracted confound matrix TSV.",
    )
    parser.add_argument(
        "--strategy",
        choices=["minimal", "moderate", "aggressive"],
        default="moderate",
        help=(
            "Denoising strategy: "
            "'minimal' (6 motion params + FD), "
            "'moderate' (minimal + global/WM/CSF signals + 6 aCompCor), "
            "'aggressive' (moderate + 24-param motion + full aCompCor)."
        ),
    )
    parser.add_argument(
        "--fd_threshold",
        type=float,
        default=0.5,
        metavar="MM",
        help=(
            "Framewise displacement threshold in mm used to define motion spikes. "
            "Only used when --scrub is set."
        ),
    )
    parser.add_argument(
        "--scrub",
        action="store_true",
        help=(
            "Append a binary 'motion_outlier' column where 1 indicates that the "
            "volume's FD exceeds --fd_threshold (volumes to be censored)."
        ),
    )
    return parser.parse_args()


def build_column_lists(available_columns):
    """Build the column-name lists for each denoising strategy.

    Derives lists based on fMRIPrep naming conventions. Only columns present
    in *available_columns* will appear in the returned lists.

    Args:
        available_columns (list[str]): All column names in the confounds TSV.

    Returns:
        dict: Mapping of strategy name to a list of available column names.
    """
    col_set = set(available_columns)

    MOTION_6 = ["trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z"]

    # Temporal derivatives and their squares (fMRIPrep naming convention)
    MOTION_DERIV    = [f"{p}_derivative1"        for p in MOTION_6]
    MOTION_SQ       = [f"{p}_power2"             for p in MOTION_6]
    MOTION_DERIV_SQ = [f"{p}_derivative1_power2" for p in MOTION_6]

    TISSUE = ["global_signal", "white_matter", "csf"]

    ACOMPCOR_6   = [f"a_comp_cor_{i:02d}" for i in range(6)]
    ACOMPCOR_ALL = sorted([c for c in available_columns if c.startswith("a_comp_cor")])

    strategies = {
        "minimal": MOTION_6 + ["framewise_displacement"],
        "moderate": (
            MOTION_6
            + ["framewise_displacement"]
            + TISSUE
            + ACOMPCOR_6
        ),
        "aggressive": (
            MOTION_6
            + MOTION_DERIV
            + MOTION_SQ
            + MOTION_DERIV_SQ
            + ["framewise_displacement"]
            + TISSUE
            + ACOMPCOR_ALL
        ),
    }

    # Deduplicate while preserving order (dict.fromkeys trick)
    return {
        name: list(dict.fromkeys(col for col in cols if col in col_set))
        for name, cols in strategies.items()
    }


def extract_confounds(
    confounds_df,
    strategy,
    fd_threshold=0.5,
    add_scrubbing=False,
):
    """Select confound columns from a DataFrame using the requested strategy.

    Args:
        confounds_df (pandas.DataFrame): Full confounds DataFrame from fMRIPrep.
        strategy (str): One of 'minimal', 'moderate', or 'aggressive'.
        fd_threshold (float): FD threshold in mm for scrubbing column.
        add_scrubbing (bool): If True, append a binary 'motion_outlier' column.

    Returns:
        pandas.DataFrame: DataFrame containing only the selected columns.

    Raises:
        ValueError: If *strategy* is not recognised.
    """
    import pandas as pd

    valid_strategies = ("minimal", "moderate", "aggressive")
    if strategy not in valid_strategies:
        raise ValueError(
            f"Unknown strategy '{strategy}'. Choose from: {valid_strategies}"
        )

    available = confounds_df.columns.tolist()

    # Reuse build_column_lists() as the single source of truth for strategy definitions.
    # That function already resolves dynamic columns (e.g. all aCompCor) and filters
    # to only columns present in *available*.
    strategy_map = build_column_lists(available)
    selected = strategy_map[strategy]

    # Compute the full desired list (before availability filtering) to warn about gaps
    MOTION_6 = ["trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z"]
    MOTION_DERIV    = [f"{p}_derivative1"        for p in MOTION_6]
    MOTION_SQ       = [f"{p}_power2"             for p in MOTION_6]
    MOTION_DERIV_SQ = [f"{p}_derivative1_power2" for p in MOTION_6]
    TISSUE = ["global_signal", "white_matter", "csf"]
    ACOMPCOR_6 = [f"a_comp_cor_{i:02d}" for i in range(6)]
    full_desired = {
        "minimal":    MOTION_6 + ["framewise_displacement"],
        "moderate":   MOTION_6 + ["framewise_displacement"] + TISSUE + ACOMPCOR_6,
        "aggressive": MOTION_6 + MOTION_DERIV + MOTION_SQ + MOTION_DERIV_SQ
                      + ["framewise_displacement"] + TISSUE + ACOMPCOR_6,
    }
    missing = [c for c in full_desired[strategy] if c not in set(available)]
    if missing:
        warnings.warn(
            f"Strategy '{strategy}': {len(missing)} column(s) not found in confounds TSV "
            f"and will be skipped: {missing}",
            stacklevel=2,
        )

    if not selected:
        raise RuntimeError(
            f"No columns from strategy '{strategy}' were found in the confounds TSV."
        )

    result = confounds_df[selected].copy()

    if add_scrubbing:
        if "framewise_displacement" not in confounds_df.columns:
            warnings.warn(
                "'framewise_displacement' not found; skipping scrubbing column.",
                stacklevel=2,
            )
        else:
            fd_vals = pd.to_numeric(
                confounds_df["framewise_displacement"], errors="coerce"
            )
            result["motion_outlier"] = (fd_vals > fd_threshold).astype(int)

    return result


def main():
    """Entry point: load confounds, extract strategy columns, save output."""
    args = parse_args()

    # Add repo root to sys.path so utils/ is importable from any working directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    try:
        from utils.io_utils import load_tsv, save_tsv
    except ImportError:
        import pandas as _pd
        load_tsv = lambda p, **kw: _pd.read_csv(p, sep="\t", **kw)
        save_tsv = lambda df, p: (df.to_csv(p, sep="\t", index=False) or os.path.abspath(p))
        warnings.warn("utils.io_utils not found; using pandas directly.")

    confounds_path = os.path.abspath(args.confounds_tsv)
    output_path    = os.path.abspath(args.output_tsv)

    print("=" * 60)
    print("  Extract Confounds")
    print("=" * 60)
    print(f"  Input TSV   : {confounds_path}")
    print(f"  Output TSV  : {output_path}")
    print(f"  Strategy    : {args.strategy}")
    print(f"  FD threshold: {args.fd_threshold} mm")
    print(f"  Scrubbing   : {'yes' if args.scrub else 'no'}")

    if not os.path.isfile(confounds_path):
        print(f"\n  ERROR: Input file not found: {confounds_path}")
        sys.exit(1)

    # Load
    try:
        confounds_df = load_tsv(confounds_path)
    except Exception as exc:
        print(f"\n  ERROR loading confounds TSV: {exc}")
        sys.exit(1)

    print(f"\n  Loaded {confounds_df.shape[0]} volumes × {confounds_df.shape[1]} columns.")

    # Extract
    try:
        result_df = extract_confounds(
            confounds_df,
            strategy=args.strategy,
            fd_threshold=args.fd_threshold,
            add_scrubbing=args.scrub,
        )
    except Exception as exc:
        print(f"\n  ERROR extracting confounds: {exc}")
        sys.exit(1)

    print(f"\n  Selected {result_df.shape[1]} column(s) for '{args.strategy}' strategy:")
    for col in result_df.columns:
        n_nan = result_df[col].isna().sum()
        nan_note = f"  ({n_nan} NaN — first volume expected)" if n_nan > 0 else ""
        print(f"    {col}{nan_note}")

    if args.scrub and "motion_outlier" in result_df.columns:
        n_flagged = int(result_df["motion_outlier"].sum())
        pct       = 100.0 * n_flagged / len(result_df)
        print(f"\n  Scrubbing: {n_flagged} volumes flagged ({pct:.1f}%) above "
              f"{args.fd_threshold} mm FD.")
        if pct > 20:
            print("  ⚠  WARNING: >20% of volumes flagged — consider excluding this run.")

    # Save
    try:
        saved_path = save_tsv(result_df, output_path)
        print(f"\n  Saved to: {saved_path}")
    except Exception as exc:
        print(f"\n  ERROR saving output TSV: {exc}")
        sys.exit(1)

    print("=" * 60)
    print("  Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
