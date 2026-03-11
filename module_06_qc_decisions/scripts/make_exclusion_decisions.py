#!/usr/bin/env python3
"""Apply QC thresholds to MRIQC IQM files and output an exclusion list."""

import argparse
import sys
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser(
        description="Apply QC thresholds to MRIQC IQMs and produce an exclusion TSV."
    )
    parser.add_argument("--bold_iqms", required=True, help="TSV file with BOLD IQMs from MRIQC")
    parser.add_argument("--t1w_iqms", required=True, help="TSV file with T1w IQMs from MRIQC")
    parser.add_argument("--fd_threshold", type=float, default=0.5,
                        help="Mean framewise-displacement exclusion threshold (default: 0.5)")
    parser.add_argument("--tsnr_threshold", type=float, default=40.0,
                        help="Minimum acceptable tSNR (default: 40)")
    parser.add_argument("--output", required=True, help="Output TSV file path")
    return parser.parse_args()


def main():
    args = parse_args()

    bold = pd.read_csv(args.bold_iqms, sep="\t")
    t1w = pd.read_csv(args.t1w_iqms, sep="\t")

    # Normalise participant id column name
    for df, label in [(bold, "BOLD"), (t1w, "T1w")]:
        if "participant_id" not in df.columns and "subject_id" in df.columns:
            df.rename(columns={"subject_id": "participant_id"}, inplace=True)
        elif "participant_id" not in df.columns:
            sys.exit(f"ERROR: {label} IQM file has neither 'participant_id' nor 'subject_id' column.")

    bold["bold_exclude"] = False
    bold["bold_reason"] = ""

    # MRIQC commonly uses "fd_mean"; older tables may use "mean_fd".
    fd_col = "fd_mean" if "fd_mean" in bold.columns else ("mean_fd" if "mean_fd" in bold.columns else None)
    if fd_col is not None:
        mask = bold[fd_col] > args.fd_threshold
        bold.loc[mask, "bold_exclude"] = True
        bold.loc[mask, "bold_reason"] += f"{fd_col}>{args.fd_threshold};"
    else:
        print("WARNING: No FD mean column found ('fd_mean' or 'mean_fd'); FD threshold will not be applied.")

    if "tsnr" in bold.columns:
        mask = bold["tsnr"] < args.tsnr_threshold
        bold.loc[mask, "bold_exclude"] = True
        bold.loc[mask, "bold_reason"] += f"tsnr<{args.tsnr_threshold};"

    t1w["t1w_exclude"] = False
    t1w["t1w_reason"] = ""

    if "cjv" in t1w.columns:
        mask = t1w["cjv"] > 0.7
        t1w.loc[mask, "t1w_exclude"] = True
        t1w.loc[mask, "t1w_reason"] += "cjv>0.7;"

    merged = bold[["participant_id", "bold_exclude", "bold_reason"]].merge(
        t1w[["participant_id", "t1w_exclude", "t1w_reason"]],
        on="participant_id",
        how="outer",
    )
    merged["exclude_reason"] = (merged["bold_reason"].fillna("") +
                                 merged["t1w_reason"].fillna("")).str.rstrip(";")

    out = merged[["participant_id", "bold_exclude", "t1w_exclude", "exclude_reason"]]
    out.to_csv(args.output, sep="\t", index=False)

    n_bold = int(merged["bold_exclude"].sum())
    n_t1w = int(merged["t1w_exclude"].sum())
    n_total = len(merged)
    print(f"Total participants : {n_total}")
    print(f"BOLD exclusions    : {n_bold}")
    print(f"T1w  exclusions    : {n_t1w}")
    print(f"Output written to  : {args.output}")


if __name__ == "__main__":
    main()
