#!/usr/bin/env python3
"""Generate a GLM contrast specification JSON file from a BIDS events TSV.

For each unique ``trial_type`` found in the events file the script creates:

* A **simple contrast** (condition vs. implicit baseline).
* **Pairwise comparisons** for the emotion-regulation conditions:
  Reappraise > Look, Reappraise > Suppress, Look > Suppress (and reverses).
* A generic **all-conditions > baseline** F-contrast.

The output JSON follows the structure expected by most Python-based GLM
libraries (e.g., nilearn, nistats) and looks like::

    {
      "conditions": ["Reappraise", "Look", "Suppress"],
      "contrasts": [
          {
              "name": "Reappraise_vs_baseline",
              "type": "t",
              "weights": {"Reappraise": 1, "Look": 0, "Suppress": 0}
          },
          ...
      ]
    }

Example
-------
    python create_condition_contrasts.py \\
        --events_file sub-01_task-emotionreg_run-1_events.tsv \\
        --output contrasts.json
"""

import argparse
import json
import os
import sys

import pandas as pd


# ---------------------------------------------------------------------------
# Contrast builders
# ---------------------------------------------------------------------------


def load_trial_types(events_path: str) -> list[str]:
    """Return sorted list of unique trial_type values from an events TSV.

    Args:
        events_path: Absolute path to the BIDS events TSV file.

    Returns:
        Sorted list of unique trial type strings.

    Raises:
        FileNotFoundError: If the events file does not exist.
        ValueError: If the file cannot be parsed or lacks 'trial_type'.
    """
    if not os.path.isfile(events_path):
        raise FileNotFoundError(f"Events file not found: {events_path}")
    try:
        df = pd.read_csv(events_path, sep="\t", na_values=["n/a", "N/A", ""])
    except Exception as exc:
        raise ValueError(f"Could not parse events file: {exc}") from exc

    if "trial_type" not in df.columns:
        raise ValueError("Events file does not contain a 'trial_type' column.")

    types = sorted(df["trial_type"].dropna().unique().tolist())
    if not types:
        raise ValueError("No trial types found in events file.")
    return types


def zero_weights(conditions: list[str]) -> dict[str, float]:
    """Return a zero-weight dictionary for all conditions.

    Args:
        conditions: List of condition names.

    Returns:
        Dict mapping each condition to 0.0.
    """
    return {c: 0.0 for c in conditions}


def simple_contrasts(conditions: list[str]) -> list[dict]:
    """Create one t-contrast per condition vs. implicit baseline.

    Args:
        conditions: Sorted list of condition names.

    Returns:
        List of contrast specification dicts.
    """
    contrasts = []
    for cond in conditions:
        weights = zero_weights(conditions)
        weights[cond] = 1.0
        contrasts.append(
            {
                "name": f"{cond}_vs_baseline",
                "type": "t",
                "weights": weights,
            }
        )
    return contrasts


def pairwise_contrasts(conditions: list[str]) -> list[dict]:
    """Create t-contrasts for every ordered pair (A > B).

    Args:
        conditions: Sorted list of condition names.

    Returns:
        List of contrast specification dicts.
    """
    contrasts = []
    for i, cond_a in enumerate(conditions):
        for j, cond_b in enumerate(conditions):
            if i == j:
                continue
            weights = zero_weights(conditions)
            weights[cond_a] = 1.0
            weights[cond_b] = -1.0
            contrasts.append(
                {
                    "name": f"{cond_a}_gt_{cond_b}",
                    "type": "t",
                    "weights": weights,
                }
            )
    return contrasts


def f_contrast_all_vs_baseline(conditions: list[str]) -> dict:
    """Create an F-contrast testing all conditions against baseline.

    Each row of the contrast matrix is one condition vs. baseline.

    Args:
        conditions: Sorted list of condition names.

    Returns:
        A single contrast specification dict with ``type`` = ``'F'``.
    """
    matrix = []
    for cond in conditions:
        row = zero_weights(conditions)
        row[cond] = 1.0
        matrix.append(row)

    return {
        "name": "all_conditions_vs_baseline",
        "type": "F",
        "weights": matrix,
    }


def build_contrast_spec(conditions: list[str]) -> dict:
    """Assemble the full contrast specification dictionary.

    Args:
        conditions: Sorted list of condition names.

    Returns:
        Dict with keys ``conditions`` and ``contrasts``.
    """
    contrasts: list[dict] = []
    contrasts.extend(simple_contrasts(conditions))
    contrasts.extend(pairwise_contrasts(conditions))
    contrasts.append(f_contrast_all_vs_baseline(conditions))

    return {
        "conditions": conditions,
        "n_contrasts": len(contrasts),
        "contrasts": contrasts,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a GLM contrast specification JSON from a BIDS events TSV file."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--events_file",
        required=True,
        metavar="EVENTS_TSV",
        help="Absolute path to the BIDS events TSV file.",
    )
    parser.add_argument(
        "--output",
        required=True,
        metavar="OUTPUT_JSON",
        help="Absolute path for the output contrast specification JSON file.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    """Entry point.

    Returns:
        0 on success, 1 on failure.
    """
    args = parse_args(argv)

    try:
        conditions = load_trial_types(args.events_file)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}")
        return 1

    print(f"Found {len(conditions)} condition(s): {conditions}")

    spec = build_contrast_spec(conditions)

    out_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, indent=2)

    print(f"Written {spec['n_contrasts']} contrasts to: {out_path}")
    for c in spec["contrasts"]:
        ctype = c["type"]
        print(f"  [{ctype}] {c['name']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
