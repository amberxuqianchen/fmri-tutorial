"""Tests for utils/bids_helpers.py.

Covers :func:`~utils.bids_helpers.load_events` and
:func:`~utils.bids_helpers.check_bids_completeness`.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Make sure the repository root is on the path so utils can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.bids_helpers import load_events


def test_load_events_basic(tmp_bids_dir):
    """Test that load_events() returns a DataFrame when given a valid events file."""
    events_file = (
        tmp_bids_dir
        / "sub-01"
        / "func"
        / "sub-01_task-emotionreg_run-01_events.tsv"
    )
    df = load_events(str(events_file))
    assert isinstance(df, pd.DataFrame), "load_events() should return a DataFrame"
    assert len(df) > 0, "DataFrame should not be empty"


def test_load_events_columns(tmp_bids_dir):
    """Test that the events DataFrame contains the required BIDS columns."""
    events_file = (
        tmp_bids_dir
        / "sub-01"
        / "func"
        / "sub-01_task-emotionreg_run-01_events.tsv"
    )
    df = load_events(str(events_file))
    required_columns = {"onset", "duration"}
    assert required_columns.issubset(
        set(df.columns)
    ), f"DataFrame is missing required columns. Found: {list(df.columns)}"


def test_load_events_file_not_found():
    """Test that load_events() raises FileNotFoundError for a missing file."""
    with pytest.raises(FileNotFoundError):
        load_events("/nonexistent/path/to_events.tsv")


def test_load_events_missing_required_columns(tmp_path):
    """Test that load_events() raises ValueError when required columns are absent."""
    bad_tsv = tmp_path / "bad_events.tsv"
    bad_tsv.write_text("trial_type\tstimulus\nNeutral\timage01.png\n")
    with pytest.raises(ValueError, match="missing required columns"):
        load_events(str(bad_tsv))


@pytest.mark.skip(
    reason=(
        "check_bids_completeness() requires pybids to index the dataset "
        "and expects actual NIfTI files; skipped in lightweight CI."
    )
)
def test_check_bids_completeness_runs(tmp_bids_dir):
    """Test that check_bids_completeness() runs without error on a valid BIDS dir.

    Skipped because pybids validation requires .nii.gz files to be present.
    """
    from utils.bids_helpers import check_bids_completeness

    report = check_bids_completeness(str(tmp_bids_dir))
    assert isinstance(report, dict), "check_bids_completeness() should return a dict"
