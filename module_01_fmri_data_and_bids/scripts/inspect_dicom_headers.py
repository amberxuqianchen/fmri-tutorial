#!/usr/bin/env python3
"""inspect_dicom_headers.py — Read DICOM files from a directory and print a
table of key header fields.  Optionally saves the table to a CSV file.

Usage
-----
    python inspect_dicom_headers.py --dicom_dir /path/to/dicoms
    python inspect_dicom_headers.py --dicom_dir /path/to/dicoms --output headers.csv
"""

import argparse
import csv
import os
import sys
from pathlib import Path


DICOM_FIELDS = [
    ("PatientID",          "0010|0020"),
    ("PatientName",        "0010|0010"),
    ("PatientAge",         "0010|1010"),
    ("PatientSex",         "0010|0040"),
    ("StudyDate",          "0008|0020"),
    ("StudyTime",          "0008|0030"),
    ("Modality",           "0008|0060"),
    ("SeriesDescription",  "0008|103e"),
    ("SeriesNumber",       "0020|0011"),
    ("InstanceNumber",     "0020|0013"),
    ("Rows",               "0028|0010"),
    ("Columns",            "0028|0011"),
    ("SliceThickness",     "0050|0018"),
    ("PixelSpacing",       "0028|0030"),
    ("RepetitionTime",     "0018|0080"),
    ("EchoTime",           "0018|0081"),
    ("FlipAngle",          "0018|1314"),
    ("MagneticFieldStrength", "0018|0087"),
    ("Manufacturer",       "0008|0070"),
    ("ManufacturerModelName", "0008|1090"),
]

FIELD_NAMES = [f[0] for f in DICOM_FIELDS]


def get_dicom_field(dataset, keyword: str) -> str:
    """Safely retrieve a DICOM field value as a string."""
    try:
        val = getattr(dataset, keyword, None)
        if val is None:
            return ""
        return str(val).strip()
    except Exception:
        return ""


def find_dicom_files(dicom_dir: Path) -> list[Path]:
    """Return all files in *dicom_dir* that appear to be DICOM (recursively)."""
    candidates = []
    for root, _dirs, files in os.walk(dicom_dir):
        for fname in sorted(files):
            fpath = Path(root) / fname
            # Include files with common DICOM extensions or no extension
            if fpath.suffix.lower() in (".dcm", ".ima", "") or "." not in fpath.name:
                candidates.append(fpath)
    return candidates


def read_dicom_headers(dicom_dir: Path, max_files: int = 0) -> list[dict]:
    """Read DICOM headers from all files in *dicom_dir*.

    Parameters
    ----------
    dicom_dir:
        Path to directory containing DICOM files.
    max_files:
        If > 0, stop after reading this many files (useful for large series).

    Returns
    -------
    List of dicts, one per file, with keys from FIELD_NAMES plus 'FilePath'.
    """
    try:
        import pydicom
    except ImportError:
        print("Error: pydicom is not installed.", file=sys.stderr)
        print("  Install it with:  conda install -c conda-forge pydicom", file=sys.stderr)
        sys.exit(1)

    files = find_dicom_files(dicom_dir)
    if not files:
        print(f"No DICOM files found in {dicom_dir}", file=sys.stderr)
        sys.exit(1)

    if max_files > 0:
        files = files[:max_files]

    rows = []
    skipped = 0
    for fpath in files:
        try:
            ds = pydicom.dcmread(str(fpath), stop_before_pixels=True)
        except Exception:
            skipped += 1
            continue

        row = {"FilePath": str(fpath)}
        for keyword, _tag in DICOM_FIELDS:
            row[keyword] = get_dicom_field(ds, keyword)
        rows.append(row)

    if skipped:
        print(f"⚠️   Skipped {skipped} file(s) that could not be read as DICOM.", file=sys.stderr)

    return rows


def print_table(rows: list[dict], fields: list[str] | None = None) -> None:
    """Print rows as a fixed-width table."""
    if not rows:
        print("No rows to display.")
        return

    display_fields = fields or (["FilePath"] + FIELD_NAMES)
    col_widths = {f: max(len(f), max(len(str(r.get(f, ""))) for r in rows)) for f in display_fields}
    col_widths = {f: min(w, 40) for f, w in col_widths.items()}  # cap column width

    header = "  ".join(f.ljust(col_widths[f]) for f in display_fields)
    separator = "  ".join("-" * col_widths[f] for f in display_fields)
    print(header)
    print(separator)
    for row in rows:
        line = "  ".join(str(row.get(f, ""))[:col_widths[f]].ljust(col_widths[f]) for f in display_fields)
        print(line)


def save_csv(rows: list[dict], output_path: Path) -> None:
    """Write rows to a CSV file."""
    if not rows:
        print("No data to save.", file=sys.stderr)
        return

    fieldnames = ["FilePath"] + FIELD_NAMES
    with open(output_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅  Saved {len(rows)} row(s) to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect DICOM header fields from a directory of DICOM files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dicom_dir",
        required=True,
        type=Path,
        metavar="DIR",
        help="Path to directory containing DICOM files (searched recursively).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        metavar="CSV",
        help="Optional path to save the header table as a CSV file.",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=0,
        metavar="N",
        help="Stop after reading N files. 0 (default) means read all files.",
    )
    parser.add_argument(
        "--fields",
        nargs="+",
        default=None,
        choices=FIELD_NAMES,
        metavar="FIELD",
        help="Subset of fields to display. Defaults to all fields.",
    )
    args = parser.parse_args()

    if not args.dicom_dir.is_dir():
        print(f"Error: '{args.dicom_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning: {args.dicom_dir}")
    rows = read_dicom_headers(args.dicom_dir, max_files=args.max_files)
    print(f"Found {len(rows)} readable DICOM file(s).\n")

    display_fields = args.fields or FIELD_NAMES
    print_table(rows, fields=["FilePath"] + display_fields)

    if args.output:
        save_csv(rows, args.output)


if __name__ == "__main__":
    main()
