"""Tests for utils/dicom_helpers.py.

All tests that perform real DICOM I/O are gated behind
``pytest.importorskip("pydicom")`` so the test suite stays runnable in
environments where pydicom is not installed.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_import_dicom_helpers():
    """Test that the dicom_helpers module imports successfully."""
    import utils.dicom_helpers as dh  # noqa: F401

    assert hasattr(dh, "read_dicom_header"), "read_dicom_header should be defined"
    assert hasattr(dh, "get_series_info"), "get_series_info should be defined"
    assert hasattr(dh, "print_dicom_summary"), "print_dicom_summary should be defined"
    assert hasattr(dh, "extract_protocol_info"), "extract_protocol_info should be defined"


def test_print_dicom_summary_nonexistent():
    """Test that print_dicom_summary() raises an error for a nonexistent directory.

    The function calls get_series_info() internally, which raises
    FileNotFoundError when the directory does not exist.  pydicom is required
    to reach that code path, so we skip gracefully if it is absent.
    """
    pydicom = pytest.importorskip("pydicom")  # noqa: F841

    from utils.dicom_helpers import print_dicom_summary

    with pytest.raises((FileNotFoundError, OSError)):
        print_dicom_summary("/nonexistent/dicom/directory")


def test_get_series_info_nonexistent():
    """Test that get_series_info() raises FileNotFoundError for a missing directory."""
    pytest.importorskip("pydicom")

    from utils.dicom_helpers import get_series_info

    with pytest.raises(FileNotFoundError):
        get_series_info("/nonexistent/dicom/directory")


def test_read_dicom_header_nonexistent():
    """Test that read_dicom_header() raises FileNotFoundError for a missing file."""
    pytest.importorskip("pydicom")

    from utils.dicom_helpers import read_dicom_header

    with pytest.raises(FileNotFoundError):
        read_dicom_header("/nonexistent/file.dcm")


def test_get_series_info_empty_directory(tmp_path):
    """Test that get_series_info() returns an empty list for a directory with no DICOMs."""
    pytest.importorskip("pydicom")

    from utils.dicom_helpers import get_series_info

    result = get_series_info(str(tmp_path))
    assert result == [], "Empty directory should yield an empty series list"


def test_extract_protocol_info_nonexistent():
    """Test that extract_protocol_info() raises FileNotFoundError for missing dir."""
    pytest.importorskip("pydicom")

    from utils.dicom_helpers import extract_protocol_info

    with pytest.raises(FileNotFoundError):
        extract_protocol_info("/nonexistent/dicom/directory")
