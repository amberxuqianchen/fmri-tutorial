"""DICOM utility functions for reading headers and summarising scan series."""

import os


def read_dicom_header(dicom_path):
    """Read a single DICOM file and return its header as a pydicom Dataset.

    Args:
        dicom_path (str): Absolute or relative path to a DICOM file.

    Returns:
        pydicom.dataset.FileDataset: Parsed DICOM dataset.

    Raises:
        FileNotFoundError: If the file does not exist.
        ImportError: If pydicom is not installed.
        ValueError: If the file cannot be read as a DICOM file.
    """
    try:
        import pydicom
    except ImportError as exc:
        raise ImportError(
            "pydicom is required. Install it with: pip install pydicom"
        ) from exc

    abs_path = os.path.abspath(dicom_path)
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"DICOM file not found: {abs_path}")

    try:
        ds = pydicom.dcmread(abs_path)
    except Exception as exc:
        raise ValueError(f"Could not read DICOM file '{abs_path}': {exc}") from exc

    return ds


def get_series_info(dicom_dir):
    """Collect unique series information from all DICOM files in a directory.

    The function reads the first file per unique SeriesInstanceUID to minimise
    I/O overhead.

    Args:
        dicom_dir (str): Path to a directory containing DICOM files.

    Returns:
        list[dict]: One dict per unique series, each containing keys:
            ``SeriesNumber``, ``SeriesDescription``, ``ProtocolName``,
            ``Modality``, ``SeriesInstanceUID``, and ``FileCount``.

    Raises:
        FileNotFoundError: If dicom_dir does not exist.
        ImportError: If pydicom is not installed.
    """
    try:
        import pydicom
    except ImportError as exc:
        raise ImportError(
            "pydicom is required. Install it with: pip install pydicom"
        ) from exc

    abs_dir = os.path.abspath(dicom_dir)
    if not os.path.isdir(abs_dir):
        raise FileNotFoundError(f"DICOM directory not found: {abs_dir}")

    series_map = {}  # UID -> dict
    series_counts = {}

    for fname in sorted(os.listdir(abs_dir)):
        fpath = os.path.join(abs_dir, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            ds = pydicom.dcmread(fpath, stop_before_pixels=True)
        except Exception:
            continue

        uid = getattr(ds, "SeriesInstanceUID", "unknown")
        series_counts[uid] = series_counts.get(uid, 0) + 1

        if uid not in series_map:
            series_map[uid] = {
                "SeriesNumber": getattr(ds, "SeriesNumber", None),
                "SeriesDescription": getattr(ds, "SeriesDescription", "N/A"),
                "ProtocolName": getattr(ds, "ProtocolName", "N/A"),
                "Modality": getattr(ds, "Modality", "N/A"),
                "SeriesInstanceUID": uid,
            }

    result = []
    for uid, info in series_map.items():
        info["FileCount"] = series_counts.get(uid, 0)
        result.append(info)

    result.sort(key=lambda x: (x["SeriesNumber"] if x["SeriesNumber"] is not None else 9999))
    return result


def print_dicom_summary(dicom_dir):
    """Print a human-readable summary of all DICOM series in a directory.

    Args:
        dicom_dir (str): Path to a directory containing DICOM files.

    Returns:
        None
    """
    series_list = get_series_info(dicom_dir)

    print(f"DICOM Summary — {os.path.abspath(dicom_dir)}")
    print(f"{'=' * 70}")
    print(f"{'Series#':<10} {'Description':<30} {'Protocol':<20} {'Files':<6} {'Modality'}")
    print(f"{'-' * 70}")

    for s in series_list:
        print(
            f"{str(s['SeriesNumber']):<10} "
            f"{str(s['SeriesDescription']):<30} "
            f"{str(s['ProtocolName']):<20} "
            f"{s['FileCount']:<6} "
            f"{s['Modality']}"
        )

    print(f"{'=' * 70}")
    print(f"Total unique series: {len(series_list)}")


def extract_protocol_info(dicom_dir):
    """Extract key MRI protocol parameters from DICOM files in a directory.

    Reads the first DICOM file found in each unique series and extracts
    commonly needed acquisition parameters.

    Args:
        dicom_dir (str): Path to a directory containing DICOM files.

    Returns:
        dict: Mapping of SeriesDescription -> dict of protocol parameters,
            including ``TR``, ``TE``, ``FlipAngle``, ``SliceThickness``,
            ``PixelSpacing``, ``MatrixSize``, ``NumberOfSlices``, and
            ``Manufacturer``.

    Raises:
        FileNotFoundError: If dicom_dir does not exist.
        ImportError: If pydicom is not installed.
    """
    try:
        import pydicom
    except ImportError as exc:
        raise ImportError(
            "pydicom is required. Install it with: pip install pydicom"
        ) from exc

    abs_dir = os.path.abspath(dicom_dir)
    if not os.path.isdir(abs_dir):
        raise FileNotFoundError(f"DICOM directory not found: {abs_dir}")

    seen_uids = set()
    protocol_info = {}

    for fname in sorted(os.listdir(abs_dir)):
        fpath = os.path.join(abs_dir, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            ds = pydicom.dcmread(fpath, stop_before_pixels=True)
        except Exception:
            continue

        uid = getattr(ds, "SeriesInstanceUID", "unknown")
        if uid in seen_uids:
            continue
        seen_uids.add(uid)

        desc = getattr(ds, "SeriesDescription", uid)

        pixel_spacing = None
        if hasattr(ds, "PixelSpacing"):
            pixel_spacing = [float(v) for v in ds.PixelSpacing]

        matrix = None
        if hasattr(ds, "Rows") and hasattr(ds, "Columns"):
            matrix = [int(ds.Rows), int(ds.Columns)]

        protocol_info[desc] = {
            "TR": float(getattr(ds, "RepetitionTime", None) or 0) or None,
            "TE": float(getattr(ds, "EchoTime", None) or 0) or None,
            "FlipAngle": float(getattr(ds, "FlipAngle", None) or 0) or None,
            "SliceThickness": float(getattr(ds, "SliceThickness", None) or 0) or None,
            "PixelSpacing": pixel_spacing,
            "MatrixSize": matrix,
            "NumberOfSlices": int(getattr(ds, "ImagesInAcquisition", 0)) or None,
            "Manufacturer": getattr(ds, "Manufacturer", "N/A"),
        }

    return protocol_info
