#!/usr/bin/env python3
"""
generate_synthetic_dicoms.py

Generate minimal synthetic DICOM files for fMRI tutorial purposes.

Creates two series:
  - T1w structural scan  (configurable number of slices)
  - BOLD functional scan (configurable volumes × slices)

The files are structurally valid DICOM objects with proper UIDs and tags but
contain no real patient data and no diagnostically meaningful image content.

Usage
-----
    python generate_synthetic_dicoms.py [--output OUTPUT_DIR]
                                        [--t1-slices N]
                                        [--bold-slices N]
                                        [--bold-volumes N]
                                        [--matrix-size N]

Requirements
------------
    pip install pydicom numpy
"""

import argparse
import datetime
import os
import sys

import numpy as np

try:
    import pydicom
    from pydicom.dataset import Dataset, FileDataset, FileMetaDataset
    from pydicom.uid import (
        ExplicitVRLittleEndian,
        generate_uid,
        MRImageStorage,
    )
    from pydicom.sequence import Sequence
except ImportError:
    sys.exit(
        "pydicom is required.  Install it with:  pip install pydicom numpy"
    )


# --------------------------------------------------------------------------- #
# Constants / shared tag values
# --------------------------------------------------------------------------- #
PATIENT_NAME = "Synthetic^Tutorial"
PATIENT_ID = "SYN001"
STUDY_DATE = datetime.date.today().strftime("%Y%m%d")
STUDY_TIME = "120000.000000"
INSTITUTION_NAME = "Tutorial Institute"
MANUFACTURER = "Siemens"
MAGNETIC_FIELD_STRENGTH = "3"
PIXEL_SPACING = [1.0, 1.0]
SLICE_THICKNESS = 1.0


# --------------------------------------------------------------------------- #
# Low-level helpers
# --------------------------------------------------------------------------- #
def _base_dataset(
    sop_instance_uid: str,
    series_instance_uid: str,
    study_instance_uid: str,
    series_number: int,
    instance_number: int,
    rows: int,
    cols: int,
    image_type: str,
    series_description: str,
    protocol_name: str,
) -> FileDataset:
    """Return a FileDataset with required DICOM tags populated."""

    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = MRImageStorage
    file_meta.MediaStorageSOPInstanceUID = sop_instance_uid
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = FileDataset(
        filename_or_obj=None,
        dataset={},
        file_meta=file_meta,
        is_implicit_VR=False,
        is_little_endian=True,
    )
    ds.is_implicit_VR = False
    ds.is_little_endian = True

    # --- SOP common ---
    ds.SOPClassUID = MRImageStorage
    ds.SOPInstanceUID = sop_instance_uid

    # --- Patient ---
    ds.PatientName = PATIENT_NAME
    ds.PatientID = PATIENT_ID
    ds.PatientBirthDate = ""
    ds.PatientSex = "O"

    # --- Study ---
    ds.StudyInstanceUID = study_instance_uid
    ds.StudyDate = STUDY_DATE
    ds.StudyTime = STUDY_TIME
    ds.StudyDescription = "fMRI Tutorial Synthetic Study"
    ds.AccessionNumber = ""

    # --- Series ---
    ds.SeriesInstanceUID = series_instance_uid
    ds.SeriesNumber = series_number
    ds.SeriesDescription = series_description
    ds.ProtocolName = protocol_name
    ds.Modality = "MR"

    # --- Equipment ---
    ds.Manufacturer = MANUFACTURER
    ds.InstitutionName = INSTITUTION_NAME
    ds.MagneticFieldStrength = MAGNETIC_FIELD_STRENGTH
    ds.MRAcquisitionType = "3D" if "T1" in protocol_name else "2D"

    # --- Image ---
    ds.ImageType = image_type
    ds.InstanceNumber = instance_number
    ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
    ds.PixelSpacing = PIXEL_SPACING
    ds.SliceThickness = SLICE_THICKNESS
    ds.Rows = rows
    ds.Columns = cols
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 12
    ds.HighBit = 11
    ds.PixelRepresentation = 0  # unsigned

    return ds


def _add_pixel_data(ds: FileDataset, rows: int, cols: int, seed: int) -> None:
    """Add random 16-bit pixel data to *ds*."""
    rng = np.random.default_rng(seed)
    pixels = rng.integers(0, 2**12, size=(rows, cols), dtype=np.uint16)
    ds.PixelData = pixels.tobytes()


# --------------------------------------------------------------------------- #
# Series generators
# --------------------------------------------------------------------------- #
def generate_t1w(
    output_dir: str,
    study_uid: str,
    n_slices: int = 8,
    matrix_size: int = 32,
) -> None:
    """Generate a minimal T1w structural DICOM series."""

    series_dir = os.path.join(output_dir, "T1w")
    os.makedirs(series_dir, exist_ok=True)

    series_uid = generate_uid()

    print(f"  [T1w]  Generating {n_slices} slice(s) → {series_dir}")

    for sl in range(1, n_slices + 1):
        sop_uid = generate_uid()
        ds = _base_dataset(
            sop_instance_uid=sop_uid,
            series_instance_uid=series_uid,
            study_instance_uid=study_uid,
            series_number=1,
            instance_number=sl,
            rows=matrix_size,
            cols=matrix_size,
            image_type=r"ORIGINAL\PRIMARY\M\ND",
            series_description="T1w_MPRAGE",
            protocol_name="t1_mprage_sag_p2",
        )

        ds.SliceLocation = float(sl) * SLICE_THICKNESS
        ds.ImagePositionPatient = [0.0, 0.0, float(sl) * SLICE_THICKNESS]

        # T1-like contrast parameters
        ds.RepetitionTime = 2300.0   # ms
        ds.EchoTime = 2.98           # ms
        ds.InversionTime = 900.0     # ms
        ds.FlipAngle = "9"

        _add_pixel_data(ds, matrix_size, matrix_size, seed=sl)

        fname = os.path.join(series_dir, f"{sl:04d}.dcm")
        pydicom.dcmwrite(fname, ds)

    print(f"  [T1w]  Done – {n_slices} file(s) written.")


def generate_bold(
    output_dir: str,
    study_uid: str,
    n_volumes: int = 5,
    n_slices: int = 8,
    matrix_size: int = 32,
    tr_ms: float = 2000.0,
) -> None:
    """Generate a minimal BOLD fMRI DICOM series."""

    series_dir = os.path.join(output_dir, "bold")
    os.makedirs(series_dir, exist_ok=True)

    series_uid = generate_uid()
    total_instances = n_volumes * n_slices

    print(
        f"  [BOLD] Generating {n_volumes} volume(s) × {n_slices} slice(s) "
        f"= {total_instances} file(s) → {series_dir}"
    )

    instance = 1
    for vol in range(1, n_volumes + 1):
        for sl in range(1, n_slices + 1):
            sop_uid = generate_uid()
            ds = _base_dataset(
                sop_instance_uid=sop_uid,
                series_instance_uid=series_uid,
                study_instance_uid=study_uid,
                series_number=2,
                instance_number=instance,
                rows=matrix_size,
                cols=matrix_size,
                image_type=r"ORIGINAL\PRIMARY\EPI\M\ND",
                series_description="task-emotionreg_bold",
                protocol_name="bold_emotionreg",
            )

            ds.SliceLocation = float(sl) * SLICE_THICKNESS
            ds.ImagePositionPatient = [0.0, 0.0, float(sl) * SLICE_THICKNESS]

            # EPI / BOLD parameters
            ds.RepetitionTime = tr_ms
            ds.EchoTime = 30.0            # ms  (typical EPI TE ~30 ms)
            ds.FlipAngle = "90"
            ds.NumberOfTemporalPositions = str(n_volumes)
            ds.TemporalPositionIdentifier = str(vol)

            _add_pixel_data(ds, matrix_size, matrix_size, seed=instance)

            fname = os.path.join(series_dir, f"{instance:04d}.dcm")
            pydicom.dcmwrite(fname, ds)
            instance += 1

    print(f"  [BOLD] Done – {total_instances} file(s) written.")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate minimal synthetic DICOM files for fMRI tutorial use.\n"
            "Creates a T1w structural series and a BOLD functional series."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output",
        default="./synthetic_dicoms",
        metavar="DIR",
        help="Root output directory (default: ./synthetic_dicoms)",
    )
    parser.add_argument(
        "--t1-slices",
        type=int,
        default=8,
        metavar="N",
        help="Number of T1w slices to generate (default: 8)",
    )
    parser.add_argument(
        "--bold-slices",
        type=int,
        default=8,
        metavar="N",
        help="Number of BOLD slices per volume (default: 8)",
    )
    parser.add_argument(
        "--bold-volumes",
        type=int,
        default=5,
        metavar="N",
        help="Number of BOLD volumes (TRs) to generate (default: 5)",
    )
    parser.add_argument(
        "--matrix-size",
        type=int,
        default=32,
        metavar="N",
        help="In-plane matrix size in pixels (default: 32)",
    )
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    study_uid = generate_uid()

    print(f"Synthetic DICOM generator")
    print(f"  Output  : {os.path.abspath(args.output)}")
    print(f"  Study UID: {study_uid}")
    print()

    generate_t1w(
        output_dir=args.output,
        study_uid=study_uid,
        n_slices=args.t1_slices,
        matrix_size=args.matrix_size,
    )
    print()
    generate_bold(
        output_dir=args.output,
        study_uid=study_uid,
        n_volumes=args.bold_volumes,
        n_slices=args.bold_slices,
        matrix_size=args.matrix_size,
    )

    print()
    print("Generation complete.")
    print(
        "Convert to NIfTI with:  "
        f"dcm2niix -o ./nifti_out/ {os.path.abspath(args.output)}"
    )


if __name__ == "__main__":
    main()
