#!/usr/bin/env python3
"""Validate a BIDS events TSV file.

Checks performed
----------------
1. Required columns are present (onset, duration, trial_type).
2. All onsets are non-negative.
3. All durations are positive.
4. No overlapping trials (onset[i+1] < onset[i] + duration[i]).
5. Consistent trial-type labels (warns on very few or very many unique values).
6. If --bold_json is provided:
   - Checks that events finish before the run ends
     (using ``RepetitionTime`` × ``NumberOfVolumes`` if available, or
     ``TaskDuration`` if present).

Example
-------
    python validate_events.py \\
        --events_file sub-01_task-emotionreg_run-1_events.tsv

    python validate_events.py \\
        --events_file sub-01_task-emotionreg_run-1_events.tsv \\
        --bold_json  sub-01_task-emotionreg_run-1_bold.json
"""

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def load_events(events_path: str) -> pd.DataFrame:
    """Load an events TSV file into a DataFrame.

    Args:
        events_path: Absolute path to the TSV file.

    Returns:
        DataFrame with all columns.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be parsed.
    """
    if not os.path.isfile(events_path):
        raise FileNotFoundError(f"Events file not found: {events_path}")
    try:
        df = pd.read_csv(events_path, sep="\t", na_values=["n/a", "N/A", ""])
    except Exception as exc:
        raise ValueError(f"Could not parse events file: {exc}") from exc
    return df


def load_bold_json(bold_json_path: str) -> dict:
    """Load a BOLD sidecar JSON file.

    Args:
        bold_json_path: Absolute path to the JSON sidecar.

    Returns:
        Parsed dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be parsed as JSON.
    """
    if not os.path.isfile(bold_json_path):
        raise FileNotFoundError(f"BOLD JSON not found: {bold_json_path}")
    try:
        with open(bold_json_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse BOLD JSON: {exc}") from exc


def check_required_columns(df: pd.DataFrame, issues: list[str]) -> None:
    """Check that required BIDS columns are present."""
    for col in ("onset", "duration", "trial_type"):
        if col not in df.columns:
            issues.append(f"[ERROR] Required column missing: '{col}'")


def check_numeric_columns(df: pd.DataFrame, issues: list[str]) -> None:
    """Coerce onset/duration to numeric and report conversion failures."""
    for col in ("onset", "duration"):
        if col not in df.columns:
            return
        numeric = pd.to_numeric(df[col], errors="coerce")
        n_bad = numeric.isna().sum() - df[col].isna().sum()
        if n_bad > 0:
            issues.append(
                f"[ERROR] Column '{col}' has {n_bad} non-numeric value(s)."
            )


def check_non_negative_onsets(df: pd.DataFrame, issues: list[str]) -> None:
    """Check that all onsets are >= 0."""
    if "onset" not in df.columns:
        return
    onsets = pd.to_numeric(df["onset"], errors="coerce")
    bad = (onsets < 0).sum()
    if bad:
        issues.append(f"[ERROR] {bad} negative onset value(s) found.")


def check_positive_durations(df: pd.DataFrame, issues: list[str]) -> None:
    """Check that all durations are > 0."""
    if "duration" not in df.columns:
        return
    durations = pd.to_numeric(df["duration"], errors="coerce")
    bad = (durations <= 0).sum()
    if bad:
        issues.append(f"[ERROR] {bad} non-positive duration value(s) found.")


def check_overlapping_trials(df: pd.DataFrame, issues: list[str]) -> None:
    """Check for overlapping trials (onset[i+1] < onset[i] + duration[i])."""
    if "onset" not in df.columns or "duration" not in df.columns:
        return

    df_sorted = df.copy()
    df_sorted["onset"] = pd.to_numeric(df_sorted["onset"], errors="coerce")
    df_sorted["duration"] = pd.to_numeric(df_sorted["duration"], errors="coerce")
    df_sorted = df_sorted.dropna(subset=["onset", "duration"]).sort_values("onset")

    overlap_count = 0
    ends = df_sorted["onset"].values + df_sorted["duration"].values
    onsets = df_sorted["onset"].values

    for i in range(len(onsets) - 1):
        if ends[i] > onsets[i + 1] + 1e-6:
            overlap_count += 1
            if overlap_count <= 5:
                issues.append(
                    f"[ERROR] Overlap between trial {i} (ends {ends[i]:.3f}s) "
                    f"and trial {i + 1} (starts {onsets[i + 1]:.3f}s)."
                )

    if overlap_count > 5:
        issues.append(
            f"[ERROR] ... and {overlap_count - 5} more overlapping trial pair(s)."
        )


def check_trial_types(df: pd.DataFrame, issues: list[str]) -> None:
    """Warn if trial_type column looks unusual."""
    if "trial_type" not in df.columns:
        return

    n_unique = df["trial_type"].nunique()
    if n_unique == 0:
        issues.append("[ERROR] 'trial_type' column is empty.")
    elif n_unique == 1:
        issues.append(
            "[WARNING] Only one unique trial_type found. "
            "Verify that condition labels are correct."
        )
    elif n_unique > 20:
        issues.append(
            f"[WARNING] {n_unique} unique trial_type values. "
            "Consider whether this is expected (e.g., parametric design)."
        )


def check_response_time(df: pd.DataFrame, issues: list[str]) -> None:
    """Validate response_time column if present."""
    if "response_time" not in df.columns:
        return
    rt = pd.to_numeric(df["response_time"], errors="coerce")
    # Negative RTs (excluding NaN) are suspicious
    bad = (rt < 0).sum()
    if bad:
        issues.append(f"[ERROR] {bad} negative response_time value(s) found.")


def check_timing_against_bold(
    df: pd.DataFrame,
    bold_meta: dict,
    issues: list[str],
) -> None:
    """Check that events finish before the end of the BOLD run.

    Uses ``NumberOfVolumes * RepetitionTime`` as the run duration if both are
    available; falls back to ``TaskDuration`` if present.

    Args:
        df: Events DataFrame.
        bold_meta: Parsed BOLD sidecar JSON dictionary.
        issues: List to append issue strings to.
    """
    if "onset" not in df.columns or "duration" not in df.columns:
        return

    run_duration = None

    n_vols = bold_meta.get("NumberOfVolumes") or bold_meta.get("dcmmeta_shape", [None] * 4)[3]
    tr = bold_meta.get("RepetitionTime")
    if n_vols is not None and tr is not None:
        run_duration = float(n_vols) * float(tr)

    if run_duration is None:
        run_duration = bold_meta.get("TaskDuration")

    if run_duration is None:
        issues.append(
            "[INFO] Cannot determine run duration from BOLD JSON "
            "(need RepetitionTime + NumberOfVolumes or TaskDuration). "
            "Skipping timing check."
        )
        return

    onsets = pd.to_numeric(df["onset"], errors="coerce")
    durations = pd.to_numeric(df["duration"], errors="coerce")
    ends = (onsets + durations).dropna()

    last_end = ends.max()
    if last_end > run_duration + 1.0:
        issues.append(
            f"[ERROR] Last event ends at {last_end:.3f}s but run duration is "
            f"{run_duration:.3f}s (TR={tr}s × {n_vols} volumes)."
        )
    else:
        issues.append(
            f"[INFO] Run duration check passed "
            f"(last event ends at {last_end:.3f}s / {run_duration:.3f}s)."
        )


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def build_report(
    events_path: str,
    df: pd.DataFrame,
    issues: list[str],
) -> str:
    """Format a human-readable validation report.

    Args:
        events_path: Path to the events file (for display).
        df: Events DataFrame.
        issues: List of issue strings collected during validation.

    Returns:
        Multi-line report string.
    """
    errors = [i for i in issues if i.startswith("[ERROR]")]
    warnings = [i for i in issues if i.startswith("[WARNING]")]
    infos = [i for i in issues if i.startswith("[INFO]")]

    lines = [
        "=" * 60,
        "BIDS Events Validation Report",
        "=" * 60,
        f"File: {events_path}",
        f"Rows: {len(df)}",
    ]

    if "trial_type" in df.columns:
        counts = df["trial_type"].value_counts().to_dict()
        lines.append("Trial type counts:")
        for tt, n in sorted(counts.items()):
            lines.append(f"  {tt}: {n}")

    lines.append("")
    lines.append(f"Errors:   {len(errors)}")
    lines.append(f"Warnings: {len(warnings)}")
    lines.append("")

    for item in errors + warnings + infos:
        lines.append(f"  {item}")

    if not errors and not warnings:
        lines.append("  ✓ No issues found.")

    lines.append("=" * 60)
    if errors:
        lines.append("RESULT: FAILED")
    elif warnings:
        lines.append("RESULT: PASSED WITH WARNINGS")
    else:
        lines.append("RESULT: PASSED")
    lines.append("=" * 60)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a BIDS events TSV file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--events_file",
        required=True,
        metavar="EVENTS_TSV",
        help="Absolute path to the BIDS events TSV file to validate.",
    )
    parser.add_argument(
        "--bold_json",
        default=None,
        metavar="BOLD_JSON",
        help=(
            "Optional: absolute path to the companion BOLD JSON sidecar. "
            "When provided, event timing is checked against run duration."
        ),
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    """Entry point.

    Returns:
        0 if validation passed (possibly with warnings), 1 if errors found.
    """
    args = parse_args(argv)

    try:
        df = load_events(args.events_file)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}")
        return 1

    issues: list[str] = []

    check_required_columns(df, issues)
    check_numeric_columns(df, issues)
    check_non_negative_onsets(df, issues)
    check_positive_durations(df, issues)
    check_overlapping_trials(df, issues)
    check_trial_types(df, issues)
    check_response_time(df, issues)

    if args.bold_json:
        try:
            bold_meta = load_bold_json(args.bold_json)
            check_timing_against_bold(df, bold_meta, issues)
        except (FileNotFoundError, ValueError) as exc:
            issues.append(f"[WARNING] Could not load BOLD JSON: {exc}")

    report = build_report(args.events_file, df, issues)
    print(report)

    errors = [i for i in issues if i.startswith("[ERROR]")]
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
