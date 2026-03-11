#!/usr/bin/env python3
"""Convert PsychoPy output CSV to a BIDS-compliant events TSV file.

PsychoPy saves trial information in a CSV where column names are experiment-
specific.  This script maps those columns to the BIDS required columns
(onset, duration, trial_type) and optionally response_time, then writes a
tab-separated TSV file.

Example
-------
    python convert_psychopy_to_bids_events.py \\
        --input  psychopy_output.csv \\
        --output sub-01_task-emotionreg_run-1_events.tsv \\
        --task_name emotionreg \\
        --run 1
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Column-name mapping: PsychoPy → BIDS
# Adjust this dictionary to match the actual column names in your CSV.
# ---------------------------------------------------------------------------
_DEFAULT_COLUMN_MAP = {
    "onset": "onset",           # seconds since run start
    "duration": "duration",     # seconds
    "trial_type": "trial_type", # condition label
    "rt": "response_time",      # reaction time (seconds); may be absent
}

# Columns that are always written to the TSV (in this order)
_BIDS_REQUIRED = ["onset", "duration", "trial_type"]
_BIDS_RECOMMENDED = ["response_time"]


def load_psychopy_csv(input_path: str) -> pd.DataFrame:
    """Load a PsychoPy CSV output file.

    Args:
        input_path: Absolute path to the PsychoPy CSV.

    Returns:
        Raw DataFrame with all PsychoPy columns.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be parsed as CSV.
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as exc:
        raise ValueError(f"Could not parse '{input_path}' as CSV: {exc}") from exc
    return df


def map_columns(
    df: pd.DataFrame,
    column_map: dict[str, str],
) -> pd.DataFrame:
    """Rename and select columns according to *column_map*.

    The keys of *column_map* are source column names (as they appear in the
    PsychoPy CSV); the values are the target BIDS column names.

    Args:
        df: Raw PsychoPy DataFrame.
        column_map: Mapping from PsychoPy column names to BIDS column names.

    Returns:
        DataFrame containing only the mapped columns under their BIDS names.

    Raises:
        KeyError: If a required source column is missing from *df*.
    """
    rename = {}
    for src, tgt in column_map.items():
        if tgt in _BIDS_REQUIRED:
            if src not in df.columns:
                raise KeyError(
                    f"Required column '{src}' not found in input CSV. "
                    f"Available columns: {list(df.columns)}"
                )
            rename[src] = tgt
        elif src in df.columns:
            # Optional column — include only if present
            rename[src] = tgt

    events = df.rename(columns=rename)[list(rename.values())].copy()
    return events


def handle_missing_response_times(events: pd.DataFrame) -> pd.DataFrame:
    """Replace missing/invalid response times with NaN.

    PsychoPy records 'None', empty strings, or 0 when no response was made.
    BIDS convention is to use NaN for absent responses.

    Args:
        events: Events DataFrame (may contain 'response_time' column).

    Returns:
        DataFrame with cleaned response_time column.
    """
    if "response_time" not in events.columns:
        return events

    rt = events["response_time"].copy()
    rt = pd.to_numeric(rt, errors="coerce")
    rt = rt.where(rt > 0, other=np.nan)
    events["response_time"] = rt
    return events


def sort_and_clean(events: pd.DataFrame) -> pd.DataFrame:
    """Sort by onset, ensure numeric types, and reset index.

    Args:
        events: Mapped events DataFrame.

    Returns:
        Cleaned and sorted DataFrame.
    """
    events["onset"] = pd.to_numeric(events["onset"], errors="coerce")
    events["duration"] = pd.to_numeric(events["duration"], errors="coerce")
    events = events.dropna(subset=["onset", "duration"])
    events = events.sort_values("onset").reset_index(drop=True)
    return events


def build_output_columns(events: pd.DataFrame) -> pd.DataFrame:
    """Order output columns: required first, then recommended, then rest.

    Args:
        events: Cleaned events DataFrame.

    Returns:
        DataFrame with columns in BIDS-preferred order.
    """
    ordered = _BIDS_REQUIRED.copy()
    for col in _BIDS_RECOMMENDED:
        if col in events.columns:
            ordered.append(col)
    extras = [c for c in events.columns if c not in ordered]
    ordered.extend(extras)
    return events[ordered]


def write_bids_tsv(events: pd.DataFrame, output_path: str) -> None:
    """Write events DataFrame to a BIDS TSV file.

    Args:
        events: Processed events DataFrame.
        output_path: Absolute path for the output TSV.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    events.to_csv(output_path, sep="\t", index=False, na_rep="n/a")
    print(f"Written: {output_path}")


def validate_output(events: pd.DataFrame) -> bool:
    """Perform basic validation on the output events DataFrame.

    Checks:
    - Required columns are present.
    - Onsets are non-negative.
    - Durations are positive.
    - No fully overlapping trials.

    Args:
        events: Processed events DataFrame.

    Returns:
        True if validation passes; False if any check fails (warnings printed).
    """
    passed = True

    for col in _BIDS_REQUIRED:
        if col not in events.columns:
            print(f"[VALIDATION ERROR] Missing required column: '{col}'")
            passed = False

    if "onset" in events.columns and (events["onset"] < 0).any():
        print("[VALIDATION WARNING] Negative onset values detected.")
        passed = False

    if "duration" in events.columns and (events["duration"] <= 0).any():
        print("[VALIDATION WARNING] Non-positive duration values detected.")
        passed = False

    if "onset" in events.columns and "duration" in events.columns:
        ends = events["onset"] + events["duration"]
        for i in range(len(events) - 1):
            if ends.iloc[i] > events["onset"].iloc[i + 1]:
                print(
                    f"[VALIDATION WARNING] Trials {i} and {i + 1} overlap: "
                    f"trial {i} ends at {ends.iloc[i]:.3f}s, "
                    f"trial {i + 1} starts at {events['onset'].iloc[i + 1]:.3f}s"
                )
                passed = False

    if passed:
        print("[VALIDATION] All checks passed.")
    return passed


def parse_args(argv=None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert PsychoPy CSV output to a BIDS events TSV file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input",
        required=True,
        metavar="PSYCHOPY_CSV",
        help="Absolute path to the PsychoPy output CSV file.",
    )
    parser.add_argument(
        "--output",
        required=True,
        metavar="BIDS_TSV",
        help="Absolute path for the output BIDS events TSV file.",
    )
    parser.add_argument(
        "--task_name",
        default=None,
        metavar="TASK",
        help="Task label (informational; used to verify filename convention).",
    )
    parser.add_argument(
        "--run",
        type=int,
        default=None,
        metavar="RUN",
        help="Run index (informational; used to verify filename convention).",
    )
    parser.add_argument(
        "--onset_col",
        default="onset",
        help="PsychoPy column name for trial onset (seconds).",
    )
    parser.add_argument(
        "--duration_col",
        default="duration",
        help="PsychoPy column name for trial duration (seconds).",
    )
    parser.add_argument(
        "--trial_type_col",
        default="trial_type",
        help="PsychoPy column name for condition / trial type.",
    )
    parser.add_argument(
        "--rt_col",
        default="rt",
        help="PsychoPy column name for response time (optional).",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    """Entry point for the converter.

    Returns:
        0 on success, 1 on failure.
    """
    args = parse_args(argv)

    column_map = {
        args.onset_col: "onset",
        args.duration_col: "duration",
        args.trial_type_col: "trial_type",
        args.rt_col: "response_time",
    }

    print(f"Loading PsychoPy CSV: {args.input}")
    try:
        raw = load_psychopy_csv(args.input)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}")
        return 1

    print(f"  Found {len(raw)} rows, {len(raw.columns)} columns.")

    try:
        events = map_columns(raw, column_map)
    except KeyError as exc:
        print(f"[ERROR] {exc}")
        return 1

    events = handle_missing_response_times(events)
    events = sort_and_clean(events)
    events = build_output_columns(events)

    print(f"\nFirst 5 events:\n{events.head()}\n")
    print(f"Unique trial types: {sorted(events['trial_type'].unique())}")

    write_bids_tsv(events, args.output)

    valid = validate_output(events)
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
