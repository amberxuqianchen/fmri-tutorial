"""MRIQC helper utilities for loading and analysing image quality metrics."""

import os

import numpy as np
import pandas as pd


def load_group_iqms(mriqc_dir, modality="bold"):
    """Load the group-level IQM TSV produced by MRIQC.

    MRIQC writes a file named ``group_<modality>.tsv`` at the root of its
    output directory.

    Args:
        mriqc_dir (str): Path to the MRIQC output directory.
        modality (str, optional): Image modality, either ``'bold'`` or
            ``'T1w'``. Defaults to ``'bold'``.

    Returns:
        pandas.DataFrame: Group IQM table with one row per subject/run.

    Raises:
        FileNotFoundError: If mriqc_dir or the group TSV file does not exist.
        ValueError: If the TSV file cannot be parsed.
    """
    abs_dir = os.path.abspath(mriqc_dir)
    if not os.path.isdir(abs_dir):
        raise FileNotFoundError(f"MRIQC directory not found: {abs_dir}")

    tsv_path = os.path.join(abs_dir, f"group_{modality}.tsv")
    if not os.path.isfile(tsv_path):
        raise FileNotFoundError(
            f"Group IQM file not found: {tsv_path}. "
            f"Make sure MRIQC was run with the group-level step."
        )

    try:
        df = pd.read_csv(tsv_path, sep="\t")
    except Exception as exc:
        raise ValueError(f"Could not parse IQM file '{tsv_path}': {exc}") from exc

    return df


def flag_outliers(iqms_df, metrics=None, threshold=2.5):
    """Flag outlier subjects using the IQR (interquartile range) method.

    A data point is flagged as an outlier when it lies more than
    ``threshold * IQR`` below Q1 or above Q3.

    Args:
        iqms_df (pandas.DataFrame): IQM table as returned by
            :func:`load_group_iqms`.
        metrics (list[str], optional): Column names to test. If None, all
            numeric columns are used (excluding BIDS entity columns such as
            ``subject``, ``session``, ``task``, ``run``).
        threshold (float, optional): Multiplier applied to the IQR to set the
            outlier fence. Defaults to ``2.5``.

    Returns:
        pandas.DataFrame: Boolean mask DataFrame of the same shape as
        ``iqms_df[metrics]``, where ``True`` indicates an outlier cell.
        An additional column ``any_outlier`` is ``True`` if any metric
        is flagged for that row.

    Raises:
        TypeError: If iqms_df is not a pandas DataFrame.
        ValueError: If none of the requested metrics are present.
    """
    if not isinstance(iqms_df, pd.DataFrame):
        raise TypeError(f"Expected a pandas DataFrame, got {type(iqms_df).__name__}.")

    _meta_cols = {"subject", "session", "task", "run", "bids_name"}
    if metrics is None:
        metrics = [
            c for c in iqms_df.select_dtypes(include=[np.number]).columns
            if c not in _meta_cols
        ]
    else:
        metrics = [m for m in metrics if m in iqms_df.columns]

    if not metrics:
        raise ValueError("No valid numeric metric columns found in the DataFrame.")

    flags = pd.DataFrame(index=iqms_df.index)
    for col in metrics:
        series = iqms_df[col].dropna()
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - threshold * iqr
        upper = q3 + threshold * iqr
        flags[col] = (iqms_df[col] < lower) | (iqms_df[col] > upper)

    flags["any_outlier"] = flags.any(axis=1)
    return flags


def plot_iqm_distributions(iqms_df, metrics=None, save_path=None):
    """Plot histograms of IQM distributions, with outlier boundaries shown.

    Args:
        iqms_df (pandas.DataFrame): IQM table as returned by
            :func:`load_group_iqms`.
        metrics (list[str], optional): Columns to plot. If None, the first 12
            numeric columns are used.
        save_path (str, optional): File path to save the figure. If None the
            figure is displayed interactively.

    Returns:
        matplotlib.figure.Figure: The generated figure.

    Raises:
        ImportError: If matplotlib is not installed.
        TypeError: If iqms_df is not a pandas DataFrame.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "matplotlib is required. Install it with: pip install matplotlib"
        ) from exc

    if not isinstance(iqms_df, pd.DataFrame):
        raise TypeError(f"Expected a pandas DataFrame, got {type(iqms_df).__name__}.")

    _meta_cols = {"subject", "session", "task", "run", "bids_name"}
    if metrics is None:
        metrics = [
            c for c in iqms_df.select_dtypes(include=[np.number]).columns
            if c not in _meta_cols
        ][:12]

    n_cols = 3
    n_rows = int(np.ceil(len(metrics) / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 3 * n_rows))
    axes = np.array(axes).flatten()

    for idx, col in enumerate(metrics):
        ax = axes[idx]
        data = iqms_df[col].dropna()
        ax.hist(data, bins=20, color="steelblue", edgecolor="white", alpha=0.8)

        q1, q3 = data.quantile(0.25), data.quantile(0.75)
        iqr = q3 - q1
        for fence, label in [
            (q1 - 2.5 * iqr, "lower fence"),
            (q3 + 2.5 * iqr, "upper fence"),
        ]:
            ax.axvline(fence, color="red", linestyle="--", linewidth=1, label=label)

        ax.set_title(col, fontsize=9)
        ax.set_xlabel("Value")
        ax.set_ylabel("Count")

    # Hide any unused axes
    for ax in axes[len(metrics):]:
        ax.set_visible(False)

    fig.suptitle("IQM Distributions (red dashed = IQR×2.5 fences)", fontsize=11)
    fig.tight_layout()

    if save_path:
        _ensure_parent(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    else:
        plt.show()

    return fig


def generate_exclusion_report(iqms_df, output_path=None):
    """Generate a human-readable exclusion decision report based on IQM outliers.

    Args:
        iqms_df (pandas.DataFrame): IQM table as returned by
            :func:`load_group_iqms`.
        output_path (str, optional): Path to write the text report. If None,
            the report is printed to stdout only.

    Returns:
        str: The full report as a string.

    Raises:
        TypeError: If iqms_df is not a pandas DataFrame.
    """
    if not isinstance(iqms_df, pd.DataFrame):
        raise TypeError(f"Expected a pandas DataFrame, got {type(iqms_df).__name__}.")

    flags = flag_outliers(iqms_df)
    n_total = len(iqms_df)
    n_flagged = int(flags["any_outlier"].sum())

    lines = [
        "=" * 60,
        "MRIQC Exclusion Report",
        "=" * 60,
        f"Total scans:   {n_total}",
        f"Flagged scans: {n_flagged}",
        f"Clean scans:   {n_total - n_flagged}",
        "",
    ]

    id_col = next((c for c in ("bids_name", "subject") if c in iqms_df.columns), None)
    flagged_rows = flags[flags["any_outlier"]]

    if flagged_rows.empty:
        lines.append("No outliers detected. All scans recommended for inclusion.")
    else:
        lines.append("Flagged scans (recommended for exclusion / review):")
        lines.append("-" * 60)
        for row_idx in flagged_rows.index:
            label = iqms_df.loc[row_idx, id_col] if id_col else f"row {row_idx}"
            bad_metrics = [
                col for col in flagged_rows.columns
                if col != "any_outlier" and flagged_rows.loc[row_idx, col]
            ]
            lines.append(f"  {label}")
            for m in bad_metrics:
                lines.append(f"    - {m}: {iqms_df.loc[row_idx, m]:.4g}")

    lines.append("=" * 60)
    report = "\n".join(lines)

    print(report)

    if output_path:
        _ensure_parent(output_path)
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(report)

    return report


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _ensure_parent(path):
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
