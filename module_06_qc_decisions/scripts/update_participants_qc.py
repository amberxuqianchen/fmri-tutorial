"""Update participants.tsv with QC exclusion decisions."""

import argparse
import sys
import pandas as pd
from pathlib import Path


def update_participants_qc(participants_tsv, exclusion_list, output):
    """Merge exclusion decisions into participants.tsv.

    Args:
        participants_tsv: Path to participants.tsv
        exclusion_list: Path to exclusion TSV from make_exclusion_decisions.py
        output: Path to write updated participants.tsv
    """
    participants = pd.read_csv(participants_tsv, sep="\t")
    exclusions = pd.read_csv(exclusion_list, sep="\t")

    # Normalize participant_id column name
    id_col = "participant_id"
    if id_col not in exclusions.columns and "subject_id" in exclusions.columns:
        exclusions = exclusions.rename(columns={"subject_id": id_col})

    merged = participants.merge(exclusions, on=id_col, how="left")

    # Add QC pass/fail columns
    if "bold_exclude" in merged.columns:
        merged["qc_bold_pass"] = ~merged["bold_exclude"].fillna(False).astype(bool)
    if "t1w_exclude" in merged.columns:
        merged["qc_t1w_pass"] = ~merged["t1w_exclude"].fillna(False).astype(bool)
    if "exclude_reason" in merged.columns:
        merged["qc_exclude_reason"] = merged["exclude_reason"].fillna("")

    merged.to_csv(output, sep="\t", index=False)
    print(f"Updated participants TSV written to: {output}")
    n_excluded = int(merged.get("qc_bold_pass", pd.Series(dtype=bool)).eq(False).sum())
    print(f"Subjects excluded: {n_excluded}/{len(merged)}")


def main():
    parser = argparse.ArgumentParser(
        description="Add QC columns to participants.tsv"
    )
    parser.add_argument("--participants_tsv", required=True,
                        help="Path to participants.tsv")
    parser.add_argument("--exclusion_list", required=True,
                        help="Path to exclusion TSV from make_exclusion_decisions.py")
    parser.add_argument("--output", required=True,
                        help="Path to write updated participants.tsv")
    args = parser.parse_args()

    for path in [args.participants_tsv, args.exclusion_list]:
        if not Path(path).exists():
            print(f"Error: File not found: {path}", file=sys.stderr)
            sys.exit(1)

    update_participants_qc(args.participants_tsv, args.exclusion_list, args.output)


if __name__ == "__main__":
    main()
