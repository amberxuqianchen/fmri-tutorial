"""Fit a first-level GLM and compute emotion-regulation contrast maps.

This script loads a preprocessed BOLD image, an events TSV, and a confounds
TSV produced by fMRIPrep, fits a ``FirstLevelModel`` using nilearn, computes
three contrasts of interest, and saves the resulting z-maps as NIfTI files.

Contrasts computed:

Reappraise_vs_Look_Neg
    Cognitive reappraisal > passive viewing of negative images.  Typically
    activates prefrontal cortex (dlPFC, vlPFC) and reduces amygdala response.

Suppress_vs_Look_Neg
    Expressive suppression > passive viewing of negative images.  Associated
    with lateral prefrontal and motor-related suppression circuitry.

Reappraise_vs_Suppress
    Differential engagement of the two emotion regulation strategies.

Three confound-selection strategies are supported (matching ``extract_confounds.py``
from Module 09): minimal, moderate (default), aggressive.

Requirements:
    - nilearn >= 0.9
    - nibabel >= 3.0
    - numpy >= 1.21
    - pandas >= 1.3
    - matplotlib >= 3.5
    - utils.io_utils (load_tsv, save_tsv, ensure_dir)
    - utils.plotting (plot_design_matrix)

Example usage::

    # Fit GLM for subject 01, emotion-regulation task
    python run_first_level_glm.py \\
        --bold /data/fmriprep/sub-01/func/sub-01_task-emotionreg_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz \\
        --events_tsv /data/bids/sub-01/func/sub-01_task-emotionreg_events.tsv \\
        --confounds_tsv /data/fmriprep/sub-01/func/sub-01_task-emotionreg_desc-confounds_timeseries.tsv \\
        --output_dir /data/glm/sub-01 \\
        --tr 2.0 \\
        --subject sub-01

    # With spatial smoothing and aggressive confound strategy
    python run_first_level_glm.py \\
        --bold bold.nii.gz \\
        --events_tsv events.tsv \\
        --confounds_tsv confounds.tsv \\
        --output_dir ./output \\
        --tr 2.0 \\
        --subject sub-02 \\
        --fwhm 6.0 \\
        --strategy aggressive \\
        --fd_threshold 0.2
"""

import argparse
import os
import sys
import warnings

# ---------------------------------------------------------------------------
# Module-level confound column constants (fMRIPrep naming conventions)
# ---------------------------------------------------------------------------
_MOTION_6        = ["trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z"]
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
            "Fit a first-level GLM on preprocessed BOLD data and compute "
            "emotion-regulation contrast z-maps."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--bold",
        required=True,
        metavar="PATH",
        help="Path to the preprocessed BOLD NIfTI image (.nii or .nii.gz).",
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
        "--subject",
        required=True,
        metavar="LABEL",
        help="Subject label used in output filenames (e.g. sub-01).",
    )
    parser.add_argument(
        "--task",
        default="emotionreg",
        metavar="TASK",
        help="Task label used in output filenames.",
    )
    parser.add_argument(
        "--space",
        default="MNI152NLin2009cAsym",
        metavar="SPACE",
        help="Output space label used in output filenames.",
    )
    parser.add_argument(
        "--fwhm",
        type=float,
        default=0.0,
        metavar="MM",
        help=(
            "FWHM of Gaussian spatial smoothing kernel in mm applied before "
            "GLM fitting. Set to 0.0 to skip smoothing."
        ),
    )
    parser.add_argument(
        "--strategy",
        choices=["minimal", "moderate", "aggressive"],
        default="moderate",
        help="Confound selection strategy.",
    )
    parser.add_argument(
        "--fd_threshold",
        type=float,
        default=0.5,
        metavar="MM",
        help=(
            "Framewise displacement threshold in mm. Volumes above this value "
            "are reported as high-motion; a warning is issued if >20%% of "
            "volumes are flagged."
        ),
    )
    return parser.parse_args()


def build_column_lists(available_columns):
    """Return per-strategy confound column lists filtered to available columns.

    Args:
        available_columns (list[str]): All column names in the confounds TSV.

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


def select_confounds(confounds_df, strategy, fd_threshold):
    """Select confound columns, fill NaN values, and report high-motion volumes.

    Args:
        confounds_df (pandas.DataFrame): Full fMRIPrep confounds DataFrame.
        strategy (str): One of 'minimal', 'moderate', 'aggressive'.
        fd_threshold (float): FD threshold in mm for motion reporting.

    Returns:
        tuple[pandas.DataFrame, dict]: Cleaned confounds DataFrame and a dict
            with motion statistics (n_flagged, pct_flagged, n_nan_filled).

    Raises:
        RuntimeError: If no columns from the requested strategy are found.
    """
    available = confounds_df.columns.tolist()
    strategy_map = build_column_lists(available)
    selected = strategy_map[strategy]

    if not selected:
        raise RuntimeError(
            f"No columns from strategy '{strategy}' found in confounds TSV."
        )

    full_desired = {
        "minimal":    _MOTION_6 + ["framewise_displacement"],
        "moderate":   _MOTION_6 + ["framewise_displacement"] + _TISSUE + _ACOMPCOR_6,
        "aggressive": (
            _MOTION_6
            + _MOTION_DERIV
            + _MOTION_SQ
            + _MOTION_DERIV_SQ
            + ["framewise_displacement"]
            + _TISSUE
            + _ACOMPCOR_6
        ),
    }
    missing = [c for c in full_desired.get(strategy, []) if c not in set(available)]
    if missing:
        warnings.warn(
            f"Strategy '{strategy}': {len(missing)} column(s) skipped (not found): {missing}"
        )

    result = confounds_df[selected].copy()
    n_nan  = int(result.isna().sum().sum())
    result = result.fillna(0)

    # Motion statistics
    motion_stats = {"n_flagged": 0, "pct_flagged": 0.0, "n_nan_filled": n_nan}
    if "framewise_displacement" in confounds_df.columns:
        import pandas as pd
        fd = pd.to_numeric(confounds_df["framewise_displacement"], errors="coerce")
        n_flagged = int((fd > fd_threshold).sum())
        pct       = 100.0 * n_flagged / max(len(fd), 1)
        motion_stats.update({"n_flagged": n_flagged, "pct_flagged": pct})

    return result, motion_stats


def print_section(title):
    """Print a formatted section header.

    Args:
        title (str): Section title text.
    """
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def make_output_filename(subject, task, space, contrast_name):
    """Build a BIDS-style output filename for a contrast z-map.

    Args:
        subject (str): Subject label (e.g. 'sub-01').
        task (str): Task label (e.g. 'emotionreg').
        space (str): Output space label.
        contrast_name (str): Contrast identifier.

    Returns:
        str: Filename string (no directory component).
    """
    return (
        f"{subject}_task-{task}_space-{space}"
        f"_contrast-{contrast_name}_stat-z_statmap.nii.gz"
    )


def main():
    """Entry point: fit first-level GLM and save contrast z-maps."""
    args = parse_args()

    # Make utils/ importable from any working directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root  = os.path.abspath(os.path.join(script_dir, "..", ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    try:
        from utils.io_utils import load_tsv, save_tsv, ensure_dir
    except ImportError:
        import pandas as _pd
        load_tsv   = lambda p, **kw: _pd.read_csv(p, sep="\t", **kw)
        save_tsv   = lambda df, p: (df.to_csv(p, sep="\t", index=False) or os.path.abspath(p))
        ensure_dir = lambda p: (os.makedirs(p, exist_ok=True) or p)
        warnings.warn("utils.io_utils not found; using pandas/os directly.")

    try:
        from utils.plotting import plot_design_matrix as _plot_dm
    except ImportError:
        _plot_dm = None
        warnings.warn("utils.plotting not found; will use nilearn directly for figures.")

    try:
        import nibabel as nib
        import numpy as np
        from nilearn.glm.first_level import FirstLevelModel
        from nilearn import image as nib_image
    except ImportError as exc:
        print(f"ERROR: nilearn, nibabel, and numpy are required. Install with: pip install nilearn nibabel numpy")
        print(f"  Detail: {exc}")
        sys.exit(1)

    bold_path      = os.path.abspath(args.bold)
    events_path    = os.path.abspath(args.events_tsv)
    confounds_path = os.path.abspath(args.confounds_tsv)
    output_dir     = os.path.abspath(args.output_dir)

    print_section("Run First-Level GLM")
    print(f"  Subject       : {args.subject}")
    print(f"  Task          : {args.task}")
    print(f"  Space         : {args.space}")
    print(f"  BOLD          : {bold_path}")
    print(f"  Events TSV    : {events_path}")
    print(f"  Confounds TSV : {confounds_path}")
    print(f"  Output dir    : {output_dir}")
    print(f"  TR            : {args.tr} s")
    print(f"  FWHM          : {args.fwhm} mm")
    print(f"  Strategy      : {args.strategy}")
    print(f"  FD threshold  : {args.fd_threshold} mm")

    # ------------------------------------------------------------------
    # 1. Validate inputs
    # ------------------------------------------------------------------
    for label, path in [
        ("BOLD image", bold_path),
        ("events TSV", events_path),
        ("confounds TSV", confounds_path),
    ]:
        if not os.path.isfile(path):
            print(f"\n  ERROR: {label} not found: {path}")
            sys.exit(1)

    # ------------------------------------------------------------------
    # 2. Load BOLD image
    # ------------------------------------------------------------------
    print_section("Loading BOLD Image")
    try:
        bold_img = nib.load(bold_path)
    except Exception as exc:
        print(f"  ERROR loading BOLD image: {exc}")
        sys.exit(1)

    if bold_img.ndim != 4:
        print(f"  ERROR: Expected a 4-D BOLD image, got shape {bold_img.shape}.")
        sys.exit(1)

    n_scans = bold_img.shape[3]
    header_tr = float(bold_img.header.get_zooms()[3])
    if header_tr > 0 and abs(header_tr - args.tr) > 0.01:
        warnings.warn(
            f"Header TR ({header_tr} s) differs from --tr ({args.tr} s). "
            f"Using --tr value."
        )

    print(f"  BOLD shape    : {bold_img.shape}  (x, y, z, time)")
    print(f"  N scans       : {n_scans}")
    print(f"  TR            : {args.tr} s")

    # Optional spatial smoothing
    if args.fwhm > 0:
        print(f"  Smoothing BOLD with FWHM = {args.fwhm} mm ...")
        try:
            bold_img = nib_image.smooth_img(bold_img, fwhm=args.fwhm)
            print(f"  Smoothing complete.")
        except Exception as exc:
            warnings.warn(f"Could not smooth BOLD image: {exc}. Proceeding without smoothing.")

    # ------------------------------------------------------------------
    # 3. Load events and confounds
    # ------------------------------------------------------------------
    print_section("Loading Events and Confounds")
    try:
        events_df = load_tsv(events_path)
    except Exception as exc:
        print(f"  ERROR loading events TSV: {exc}")
        sys.exit(1)

    required_event_cols = {"onset", "duration", "trial_type"}
    missing_event_cols  = required_event_cols - set(events_df.columns)
    if missing_event_cols:
        print(f"  ERROR: events TSV missing columns: {missing_event_cols}")
        sys.exit(1)

    try:
        confounds_raw = load_tsv(confounds_path)
    except Exception as exc:
        print(f"  ERROR loading confounds TSV: {exc}")
        sys.exit(1)

    if confounds_raw.shape[0] != n_scans:
        warnings.warn(
            f"Confounds TSV has {confounds_raw.shape[0]} rows but BOLD has "
            f"{n_scans} volumes. They should match."
        )

    print(f"  Events        : {len(events_df)} trials")
    print(f"  Trial types   : {sorted(events_df['trial_type'].unique())}")
    print(f"  Confounds raw : {confounds_raw.shape}")

    # ------------------------------------------------------------------
    # 4. Select confound regressors
    # ------------------------------------------------------------------
    print_section("Selecting Confound Regressors")
    try:
        confounds_clean, motion_stats = select_confounds(
            confounds_raw, args.strategy, args.fd_threshold
        )
    except RuntimeError as exc:
        print(f"  ERROR: {exc}")
        sys.exit(1)

    print(f"  Columns kept  : {confounds_clean.shape[1]}")
    print(f"  NaN filled    : {motion_stats['n_nan_filled']}")
    print(f"  FD > {args.fd_threshold} mm : "
          f"{motion_stats['n_flagged']} volumes "
          f"({motion_stats['pct_flagged']:.1f}%)")
    if motion_stats["pct_flagged"] > 20:
        print("  ⚠  WARNING: >20% high-motion volumes — consider excluding this run.")

    # ------------------------------------------------------------------
    # 5. Fit FirstLevelModel
    # ------------------------------------------------------------------
    print_section("Fitting FirstLevelModel")
    glm = FirstLevelModel(
        t_r=args.tr,
        hrf_model="spm",
        drift_model="cosine",
        high_pass=1.0 / 128.0,
        standardize=False,
        signal_scaling=False,
        noise_model="ar1",
        n_jobs=1,
        verbose=1,
    )

    try:
        glm.fit(
            run_imgs=bold_img,
            events=events_df,
            confounds=confounds_clean,
        )
        print("  GLM fit complete.")
    except Exception as exc:
        print(f"  ERROR fitting GLM: {exc}")
        sys.exit(1)

    fitted_dm = glm.design_matrices_[0]
    print(f"  Design matrix : {fitted_dm.shape}")
    cond_cols = [c for c in fitted_dm.columns if c in events_df["trial_type"].unique()]
    print(f"  Conditions    : {cond_cols}")

    # Rank check
    dm_rank = int(np.linalg.matrix_rank(fitted_dm.values))
    n_dm_cols = fitted_dm.shape[1]
    if dm_rank < n_dm_cols:
        warnings.warn(
            f"Design matrix is rank deficient ({dm_rank}/{n_dm_cols}). "
            "Contrasts may be unreliable. Check for collinear regressors."
        )

    # ------------------------------------------------------------------
    # 6. Define contrasts
    # ------------------------------------------------------------------
    dm_col_set = set(fitted_dm.columns)
    baseline_cond = (
        "Look_Neg" if "Look_Neg" in dm_col_set else
        ("Look" if "Look" in dm_col_set else None)
    )

    CONTRASTS = {}
    if "Reappraise" in dm_col_set and baseline_cond is not None:
        CONTRASTS[f"Reappraise_vs_{baseline_cond}"] = f"Reappraise - {baseline_cond}"
    if "Suppress" in dm_col_set and baseline_cond is not None:
        CONTRASTS[f"Suppress_vs_{baseline_cond}"] = f"Suppress - {baseline_cond}"
    if {"Reappraise", "Suppress"}.issubset(dm_col_set):
        CONTRASTS["Reappraise_vs_Suppress"] = "Reappraise - Suppress"

    if not CONTRASTS:
        warnings.warn(
            "No valid contrasts could be constructed from the design matrix columns. "
            "Need Reappraise/Suppress and either Look_Neg or Look."
        )
        sys.exit(1)

    # ------------------------------------------------------------------
    # 7. Compute contrasts and save z-maps
    # ------------------------------------------------------------------
    print_section("Computing Contrast Maps")
    ensure_dir(output_dir)

    saved_contrasts = []
    for contrast_name, contrast_expr in CONTRASTS.items():
        try:
            z_map = glm.compute_contrast(
                contrast_def=contrast_expr,
                stat_type="t",
                output_type="z_score",
            )
            out_fname = make_output_filename(
                args.subject, args.task, args.space, contrast_name
            )
            out_path = os.path.join(output_dir, out_fname)
            nib.save(z_map, out_path)

            z_data      = z_map.get_fdata()
            finite_vals = z_data[np.isfinite(z_data)]
            z_range     = (
                f"[{finite_vals.min():.2f}, {finite_vals.max():.2f}]"
                if len(finite_vals) > 0
                else "[n/a]"
            )
            saved_contrasts.append((contrast_name, contrast_expr, out_path, z_range))
            print(f"  ✓ {contrast_name}")
            print(f"      expression : {contrast_expr}")
            print(f"      z range    : {z_range}")
            print(f"      saved to   : {out_path}")
        except Exception as exc:
            print(f"  ✗ {contrast_name}: ERROR — {exc}")

    # ------------------------------------------------------------------
    # 8. Save design matrix figure
    # ------------------------------------------------------------------
    dm_fig_path = os.path.join(output_dir, "design_matrix.png")
    try:
        if _plot_dm is not None:
            _plot_dm(fitted_dm, save_path=dm_fig_path)
        else:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from nilearn.plotting import plot_design_matrix as _nilearn_pdm
            fig, ax = plt.subplots(figsize=(12, 6))
            _nilearn_pdm(fitted_dm, ax=ax)
            ax.set_title(f"Design Matrix — {args.subject} {args.task}")
            fig.tight_layout()
            fig.savefig(dm_fig_path, dpi=150, bbox_inches="tight")
            plt.close(fig)
        print(f"\n  Design matrix figure: {dm_fig_path}")
    except Exception as exc:
        warnings.warn(f"Could not save design matrix figure: {exc}")

    # ------------------------------------------------------------------
    # 9. Save design matrix TSV
    # ------------------------------------------------------------------
    dm_tsv_path = os.path.join(output_dir, "design_matrix.tsv")
    try:
        save_tsv(fitted_dm, dm_tsv_path)
        print(f"  Design matrix TSV  : {dm_tsv_path}")
    except Exception as exc:
        warnings.warn(f"Could not save design matrix TSV: {exc}")

    # ------------------------------------------------------------------
    # 10. Summary table
    # ------------------------------------------------------------------
    print_section("Summary")
    print(f"  Subject          : {args.subject}")
    print(f"  Task             : {args.task}")
    print(f"  BOLD shape       : {bold_img.shape}")
    print(f"  TR               : {args.tr} s")
    print(f"  FWHM             : {args.fwhm} mm")
    print(f"  Strategy         : {args.strategy} ({confounds_clean.shape[1]} confound regressors)")
    print(f"  Design matrix    : {fitted_dm.shape}")
    print(f"  Rank             : {dm_rank}/{n_dm_cols}")
    print(f"  High-motion vols : {motion_stats['n_flagged']} / {n_scans} "
          f"({motion_stats['pct_flagged']:.1f}%)")
    print(f"\n  Contrasts computed ({len(saved_contrasts)}/{len(CONTRASTS)}):")
    print(f"  {'Contrast':<35} {'Expression':<35} {'z range'}")
    print(f"  {'-'*35} {'-'*35} {'-'*20}")
    for cname, cexpr, cpath, zr in saved_contrasts:
        print(f"  {cname:<35} {cexpr:<35} {zr}")

    print(f"\n  Output directory : {output_dir}")
    print("=" * 60)
    print("  Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
