#!/usr/bin/env python3
"""Load and analyze MRIQC output: flag outliers and create summary plots.

This script:
1. Loads the group-level IQM TSV file(s) produced by MRIQC.
2. Flags statistical outliers using the IQR method (via utils.mriqc_helpers).
3. Creates histogram plots of key metrics.
4. Writes an exclusion candidate list as a TSV and a plain-text report.

Example
-------
    python analyze_mriqc_output.py \\
        --mriqc_dir /data/mriqc_output \\
        --output_dir /data/mriqc_output/qc_figures
"""

import argparse
import os
import sys

# ---------------------------------------------------------------------------
# Ensure the repo root is on sys.path so utils can be imported regardless of
# the working directory.
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import pandas as pd  # noqa: E402

from utils.mriqc_helpers import (  # noqa: E402
    flag_outliers,
    generate_exclusion_report,
    load_group_iqms,
    plot_iqm_distributions,
)

# ---------------------------------------------------------------------------
# Key metrics to focus on for each modality
# ---------------------------------------------------------------------------
_BOLD_KEY_METRICS = [
    "tsnr",
    "dvars_nstd",
    "fd_mean",
    "aor",
    "aqi",
    "gsr_x",
    "gsr_y",
    "snr",
]

_T1W_KEY_METRICS = [
    "cnr",
    "snr_wm",
    "cjv",
    "efc",
    "fber",
    "wm2max",
]


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------


def _available_metrics(df: pd.DataFrame, wanted: list[str]) -> list[str]:
    """Return the subset of *wanted* that are actually columns in *df*."""
    return [m for m in wanted if m in df.columns]


def analyze_modality(
    mriqc_dir: str,
    output_dir: str,
    modality: str,
    key_metrics: list[str],
    threshold: float,
) -> int:
    """Run the full analysis pipeline for one modality.

    Args:
        mriqc_dir: Path to the MRIQC output directory.
        output_dir: Directory where plots and reports are saved.
        modality: Either ``'bold'`` or ``'T1w'``.
        key_metrics: List of preferred metric column names to highlight.
        threshold: IQR multiplier used for outlier detection.

    Returns:
        Number of flagged (outlier) scans.
    """
    print(f"\n{'=' * 50}")
    print(f"Analyzing modality: {modality}")
    print("=" * 50)

    try:
        df = load_group_iqms(mriqc_dir, modality=modality)
    except FileNotFoundError as exc:
        print(f"[SKIP] {exc}")
        return 0

    print(f"Loaded {len(df)} scan(s), {len(df.columns)} columns.")

    metrics = _available_metrics(df, key_metrics)
    if not metrics:
        print(
            f"[WARNING] None of the preferred key metrics were found. "
            f"Falling back to all numeric columns."
        )
        metrics = None  # let flag_outliers and plot choose automatically

    # --- Outlier flags -------------------------------------------------------
    flags = flag_outliers(df, metrics=metrics, threshold=threshold)
    n_flagged = int(flags["any_outlier"].sum())
    print(f"Flagged {n_flagged} / {len(df)} scan(s) as potential outliers.")

    # --- Exclusion list -------------------------------------------------------
    id_col = next((c for c in ("bids_name", "subject") if c in df.columns), None)
    flagged_ids = (
        df.loc[flags["any_outlier"], id_col].tolist() if id_col else
        df.index[flags["any_outlier"]].tolist()
    )

    excl_tsv = os.path.join(output_dir, f"exclusion_candidates_{modality}.tsv")
    if flagged_ids:
        excl_df = df.loc[flags["any_outlier"]].copy()
        excl_df.to_csv(excl_tsv, sep="\t", index=False)
        print(f"Exclusion candidates written to: {excl_tsv}")
    else:
        print("No exclusion candidates — all scans within normal range.")

    # --- Text report ---------------------------------------------------------
    report_path = os.path.join(output_dir, f"exclusion_report_{modality}.txt")
    generate_exclusion_report(df, output_path=report_path)
    print(f"Exclusion report written to: {report_path}")

    # --- Distribution plots --------------------------------------------------
    plot_path = os.path.join(output_dir, f"iqm_distributions_{modality}.png")
    try:
        plot_iqm_distributions(df, metrics=metrics, save_path=plot_path)
        print(f"IQM distribution plot saved to: {plot_path}")
    except ImportError as exc:
        print(f"[WARNING] Cannot create plots: {exc}")

    return n_flagged


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load MRIQC group IQMs, flag outliers, and create summary plots.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mriqc_dir",
        required=True,
        metavar="MRIQC_DIR",
        help="Absolute path to the MRIQC output directory containing group TSV files.",
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        metavar="OUTPUT_DIR",
        help="Absolute path to the directory where figures and reports will be saved.",
    )
    parser.add_argument(
        "--modality",
        choices=["bold", "T1w", "both"],
        default="both",
        help="Which modality to analyze.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=2.5,
        metavar="IQR_THRESHOLD",
        help="IQR multiplier for outlier detection (default: 2.5).",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    """Entry point.

    Returns:
        0 on success, 1 on error.
    """
    args = parse_args(argv)

    mriqc_dir = os.path.abspath(args.mriqc_dir)
    output_dir = os.path.abspath(args.output_dir)

    if not os.path.isdir(mriqc_dir):
        print(f"[ERROR] MRIQC directory not found: {mriqc_dir}")
        return 1

    os.makedirs(output_dir, exist_ok=True)
    print(f"MRIQC directory : {mriqc_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Outlier threshold (IQR multiplier): {args.threshold}")

    modalities = (
        ["bold", "T1w"] if args.modality == "both" else [args.modality]
    )
    key_metrics_map = {
        "bold": _BOLD_KEY_METRICS,
        "T1w": _T1W_KEY_METRICS,
    }

    total_flagged = 0
    for modality in modalities:
        total_flagged += analyze_modality(
            mriqc_dir,
            output_dir,
            modality,
            key_metrics_map[modality],
            args.threshold,
        )

    print(f"\nTotal flagged scans across all modalities: {total_flagged}")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
