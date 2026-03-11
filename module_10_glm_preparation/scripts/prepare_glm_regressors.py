"""Build and save a GLM design matrix and cleaned confounds TSV.

This script loads an events TSV and a confounds TSV produced by fMRIPrep,
constructs a first-level GLM design matrix using nilearn's
``make_first_level_design_matrix()``, and saves the design matrix, the
cleaned confounds matrix, and a design-matrix figure to the output directory.

Three confound-selection strategies are supported (identical to
``extract_confounds.py`` in Module 09):

minimal
    Six rigid-body motion parameters plus framewise displacement.

moderate
    All minimal columns plus global_signal, white_matter, csf, and the
    first six anatomical CompCor components (a_comp_cor_00 through 05).
    Recommended default for task fMRI.

aggressive
    All moderate columns plus the 18 temporal-derivative / power-squared
    motion parameters (24-parameter motion model) and all available
    aCompCor components.

Requirements:
    - nilearn >= 0.9
    - pandas >= 1.3
    - numpy >= 1.21
    - matplotlib >= 3.5
    - utils.io_utils (load_tsv, save_tsv, ensure_dir)
    - utils.plotting (plot_design_matrix)

Example usage::

    # Moderate strategy, TR = 2 s, 200 scans
    python prepare_glm_regressors.py \\
        --events_tsv /data/bids/sub-01/func/sub-01_task-emotionreg_events.tsv \\
        --confounds_tsv /data/fmriprep/sub-01/func/sub-01_task-emotionreg_desc-confounds_timeseries.tsv \\
        --output_dir /data/glm/sub-01 \\
        --tr 2.0 \\
        --n_scans 200

    # Aggressive strategy, custom HRF
    python prepare_glm_regressors.py \\
        --events_tsv events.tsv \\
        --confounds_tsv confounds.tsv \\
        --output_dir ./output \\
        --tr 1.5 \\
        --n_scans 300 \\
        --hrf_model "spm + derivative" \\
        --strategy aggressive
"""

import argparse
import os
import sys
import warnings

# ---------------------------------------------------------------------------
# Module-level confound column constants (fMRIPrep naming conventions)
# ---------------------------------------------------------------------------
_MOTION_6 = ["trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z"]
_MOTION_DERIV    = [f"{p}_derivative1"        for p in _MOTION_6]
_MOTION_SQ       = [f"{p}_power2"             for p in _MOTION_6]
_MOTION_DERIV_SQ = [f"{p}_derivative1_power2" for p in _MOTION_6]
_TISSUE          = ["global_signal", "white_matter", "csf"]
_ACOMPCOR_6      = [f"a_comp_cor_{i:02d}" for i in range(6)]


def parse_args():
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed argument values.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Build a first-level GLM design matrix from an events TSV and a "
            "confounds TSV, and save the design matrix, cleaned confounds, and "
            "a figure to the output directory."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--events_tsv",
        required=True,
        metavar="PATH",
        help="Path to BIDS events TSV (columns: onset, duration, trial_type).",
    )
    parser.add_argument(
        "--confounds_tsv",
        required=True,
        metavar="PATH",
        help="Path to fMRIPrep confounds timeseries TSV.",
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        metavar="DIR",
        help="Output directory; will be created if it does not exist.",
    )
    parser.add_argument(
        "--tr",
        required=True,
        type=float,
        metavar="SEC",
        help="Repetition time of the BOLD acquisition in seconds.",
    )
    parser.add_argument(
        "--n_scans",
        required=True,
        type=int,
        metavar="N",
        help="Number of volumes (timepoints) in the BOLD run.",
    )
    parser.add_argument(
        "--hrf_model",
        default="spm",
        metavar="MODEL",
        help=(
            "HRF model passed to make_first_level_design_matrix(). "
            "Common choices: 'spm', 'spm + derivative', 'glover'."
        ),
    )
    parser.add_argument(
        "--high_pass",
        type=float,
        default=128.0,
        metavar="SEC",
        help="High-pass filter period in seconds (used as drift cutoff).",
    )
    parser.add_argument(
        "--strategy",
        choices=["minimal", "moderate", "aggressive"],
        default="moderate",
        help="Confound selection strategy.",
    )
    return parser.parse_args()


def build_column_lists(available_columns):
    """Return per-strategy confound column lists filtered to available columns.

    Args:
        available_columns (list[str]): All column names present in the
            confounds TSV.

    Returns:
        dict[str, list[str]]: Mapping of strategy name → list of column names.
    """
    col_set      = set(available_columns)
    acompcor_all = sorted(c for c in available_columns if c.startswith("a_comp_cor"))

    raw = {
        "minimal": _MOTION_6 + ["framewise_displacement"],
        "moderate": (
            _MOTION_6 + ["framewise_displacement"] + _TISSUE + _ACOMPCOR_6
        ),
        "aggressive": (
            _MOTION_6
            + _MOTION_DERIV
            + _MOTION_SQ
            + _MOTION_DERIV_SQ
            + ["framewise_displacement"]
            + _TISSUE
            + acompcor_all
        ),
    }
    return {
        name: list(dict.fromkeys(c for c in cols if c in col_set))
        for name, cols in raw.items()
    }


def select_confounds(confounds_df, strategy):
    """Select and clean confound columns according to the chosen strategy.

    Missing columns are warned about and skipped; NaN values (e.g., first-volume
    derivatives) are filled with zero.

    Args:
        confounds_df (pandas.DataFrame): Full confounds DataFrame from fMRIPrep.
        strategy (str): One of 'minimal', 'moderate', 'aggressive'.

    Returns:
        pandas.DataFrame: Cleaned confounds matrix ready for inclusion in the
            design matrix.

    Raises:
        RuntimeError: If no columns from the requested strategy are found.
    """
    import pandas as pd

    available = confounds_df.columns.tolist()
    strategy_map = build_column_lists(available)
    selected = strategy_map[strategy]

    if not selected:
        raise RuntimeError(
            f"No columns from strategy '{strategy}' were found in the confounds TSV."
        )

    full_desired = {
        "minimal":    _MOTION_6 + ["framewise_displacement"],
        "moderate":   _MOTION_6 + ["framewise_displacement"] + _TISSUE + _ACOMPCOR_6,
        "aggressive": _MOTION_6 + ["framewise_displacement"] + _TISSUE + _ACOMPCOR_6,
    }
    missing = [c for c in full_desired.get(strategy, []) if c not in set(available)]
    if missing:
        warnings.warn(
            f"Strategy '{strategy}': {len(missing)} column(s) not found and skipped: "
            f"{missing}"
        )

    result = confounds_df[selected].copy()
    n_nan = result.isna().sum().sum()
    result = result.fillna(0)
    return result, n_nan


def print_section(title):
    """Print a formatted section header.

    Args:
        title (str): Section title text.
    """
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def main():
    """Entry point: build design matrix and confounds, save outputs."""
    args = parse_args()

    # Resolve repo root so utils/ is importable regardless of working directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root  = os.path.abspath(os.path.join(script_dir, "..", ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    try:
        from utils.io_utils import load_tsv, save_tsv, ensure_dir
    except ImportError:
        import pandas as _pd
        load_tsv  = lambda p, **kw: _pd.read_csv(p, sep="\t", **kw)
        save_tsv  = lambda df, p: (df.to_csv(p, sep="\t", index=False) or os.path.abspath(p))
        ensure_dir = lambda p: (os.makedirs(p, exist_ok=True) or p)
        warnings.warn("utils.io_utils not found; using pandas/os directly.")

    try:
        from utils.plotting import plot_design_matrix as _plot_dm
    except ImportError:
        _plot_dm = None
        warnings.warn("utils.plotting not found; will use nilearn directly for figures.")

    try:
        import numpy as np
        from nilearn.glm.first_level import make_first_level_design_matrix
    except ImportError as exc:
        print(f"ERROR: nilearn and numpy are required. Install with: pip install nilearn numpy")
        print(f"  Detail: {exc}")
        sys.exit(1)

    events_path    = os.path.abspath(args.events_tsv)
    confounds_path = os.path.abspath(args.confounds_tsv)
    output_dir     = os.path.abspath(args.output_dir)

    print_section("Prepare GLM Regressors")
    print(f"  Events TSV    : {events_path}")
    print(f"  Confounds TSV : {confounds_path}")
    print(f"  Output dir    : {output_dir}")
    print(f"  TR            : {args.tr} s")
    print(f"  N scans       : {args.n_scans}")
    print(f"  HRF model     : {args.hrf_model}")
    print(f"  High-pass     : {args.high_pass} s")
    print(f"  Strategy      : {args.strategy}")

    # ------------------------------------------------------------------
    # 1. Load inputs
    # ------------------------------------------------------------------
    for label, path in [("events TSV", events_path), ("confounds TSV", confounds_path)]:
        if not os.path.isfile(path):
            print(f"\n  ERROR: {label} not found: {path}")
            sys.exit(1)

    print_section("Loading Inputs")
    try:
        events_df = load_tsv(events_path)
    except Exception as exc:
        print(f"  ERROR loading events TSV: {exc}")
        sys.exit(1)

    required_cols = {"onset", "duration", "trial_type"}
    missing_cols  = required_cols - set(events_df.columns)
    if missing_cols:
        print(f"  ERROR: events TSV is missing required columns: {missing_cols}")
        sys.exit(1)

    try:
        confounds_raw = load_tsv(confounds_path)
    except Exception as exc:
        print(f"  ERROR loading confounds TSV: {exc}")
        sys.exit(1)

    n_conf_rows = confounds_raw.shape[0]
    if n_conf_rows != args.n_scans:
        warnings.warn(
            f"Confounds TSV has {n_conf_rows} rows but --n_scans={args.n_scans}. "
            f"Using confounds as-is; verify TR and n_scans are correct."
        )

    print(f"  Events        : {len(events_df)} trials")
    print(f"  Trial types   : {sorted(events_df['trial_type'].unique())}")
    print(f"  Confounds raw : {confounds_raw.shape[0]} volumes × {confounds_raw.shape[1]} columns")

    # ------------------------------------------------------------------
    # 2. Select confound columns
    # ------------------------------------------------------------------
    print_section("Selecting Confound Regressors")
    try:
        confounds_clean, n_nan_filled = select_confounds(confounds_raw, args.strategy)
    except RuntimeError as exc:
        print(f"  ERROR: {exc}")
        sys.exit(1)

    print(f"  Strategy      : {args.strategy}")
    print(f"  Columns kept  : {confounds_clean.shape[1]}")
    print(f"  NaN filled    : {n_nan_filled}")
    for col in confounds_clean.columns:
        print(f"    {col}")

    # ------------------------------------------------------------------
    # 3. Build design matrix
    # ------------------------------------------------------------------
    print_section("Building Design Matrix")
    frame_times = np.arange(args.n_scans) * args.tr

    try:
        design_matrix = make_first_level_design_matrix(
            frame_times=frame_times,
            events=events_df,
            hrf_model=args.hrf_model,
            drift_model="cosine",
            high_pass=1.0 / args.high_pass,
            add_regs=confounds_clean,
        )
    except Exception as exc:
        print(f"  ERROR building design matrix: {exc}")
        sys.exit(1)

    print(f"  Design matrix shape : {design_matrix.shape}")
    print(f"  Condition regressors: {[c for c in design_matrix.columns if c in events_df['trial_type'].unique()]}")
    print(f"  Total regressors    : {design_matrix.shape[1]}")

    # ------------------------------------------------------------------
    # 4. Rank check
    # ------------------------------------------------------------------
    dm_array = design_matrix.values
    rank     = int(np.linalg.matrix_rank(dm_array))
    n_cols   = design_matrix.shape[1]
    rank_status = "FULL RANK ✓" if rank == n_cols else f"RANK DEFICIENT ✗ ({rank}/{n_cols})"
    print(f"  Rank              : {rank_status}")
    if rank < n_cols:
        warnings.warn(
            f"Design matrix is rank deficient ({rank}/{n_cols}). "
            "Check for collinear or constant regressors."
        )

    # ------------------------------------------------------------------
    # 5. Save outputs
    # ------------------------------------------------------------------
    print_section("Saving Outputs")
    ensure_dir(output_dir)

    dm_tsv_path  = os.path.join(output_dir, "design_matrix.tsv")
    conf_tsv_path = os.path.join(output_dir, "cleaned_confounds.tsv")
    fig_path     = os.path.join(output_dir, "design_matrix.png")

    try:
        saved = save_tsv(design_matrix, dm_tsv_path)
        print(f"  Design matrix TSV : {saved}")
    except Exception as exc:
        print(f"  ERROR saving design matrix TSV: {exc}")
        sys.exit(1)

    try:
        saved = save_tsv(confounds_clean, conf_tsv_path)
        print(f"  Confounds TSV     : {saved}")
    except Exception as exc:
        print(f"  ERROR saving confounds TSV: {exc}")
        sys.exit(1)

    # Save design matrix figure
    try:
        if _plot_dm is not None:
            fig = _plot_dm(design_matrix, save_path=fig_path)
        else:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from nilearn.plotting import plot_design_matrix as _nilearn_pdm
            fig, ax = plt.subplots(figsize=(10, 6))
            _nilearn_pdm(design_matrix, ax=ax)
            ax.set_title("GLM Design Matrix")
            fig.tight_layout()
            fig.savefig(fig_path, dpi=150, bbox_inches="tight")
            plt.close(fig)
        print(f"  Design matrix PNG : {os.path.abspath(fig_path)}")
    except Exception as exc:
        warnings.warn(f"Could not save design matrix figure: {exc}")

    # ------------------------------------------------------------------
    # 6. Summary
    # ------------------------------------------------------------------
    print_section("Summary")
    print(f"  Design matrix   : {design_matrix.shape[0]} timepoints × {design_matrix.shape[1]} regressors")
    print(f"  Conditions      : {[c for c in design_matrix.columns if c in events_df['trial_type'].unique()]}")
    print(f"  Confound cols   : {confounds_clean.shape[1]} ({args.strategy} strategy)")
    print(f"  Rank            : {rank}/{n_cols}")
    print(f"\n  Outputs written to: {output_dir}")
    print("=" * 60)
    print("  Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
