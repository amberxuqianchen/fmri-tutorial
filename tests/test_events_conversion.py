"""Tests for BIDS events file structure and content.

These tests validate that events data (loaded via the ``sample_events_df``
fixture or read directly from the BIDS fixture directory) conforms to the
BIDS specification and the conventions used in this tutorial.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.bids_helpers import load_events

# Expected trial types for the emotion-regulation paradigm used in this tutorial
EXPECTED_TRIAL_TYPES = {"Neutral", "Negative", "Positive"}


def test_events_tsv_columns(sample_events_df):
    """Test that the events DataFrame has all required BIDS columns."""
    required = {"onset", "duration", "trial_type"}
    missing = required - set(sample_events_df.columns)
    assert not missing, f"Events DataFrame is missing BIDS-required columns: {missing}"


def test_events_onsets_positive(sample_events_df):
    """Test that all onset values are greater than or equal to zero."""
    assert (
        sample_events_df["onset"] >= 0
    ).all(), "All onset values must be non-negative (>= 0)"


def test_events_durations_positive(sample_events_df):
    """Test that all duration values are strictly positive (> 0)."""
    assert (
        sample_events_df["duration"] > 0
    ).all(), "All duration values must be strictly positive (> 0)"


def test_trial_types_valid(sample_events_df):
    """Test that trial_type only contains expected paradigm-specific values."""
    observed = set(sample_events_df["trial_type"].unique())
    unexpected = observed - EXPECTED_TRIAL_TYPES
    assert not unexpected, (
        f"Unexpected trial_type values found: {unexpected}. "
        f"Expected a subset of {EXPECTED_TRIAL_TYPES}."
    )


def test_events_sorted_by_onset(sample_events_df):
    """Test that events are sorted in ascending order by onset time."""
    onsets = sample_events_df["onset"].tolist()
    assert onsets == sorted(onsets), (
        "Events should be sorted by onset time in ascending order. "
        f"Got: {onsets}"
    )


def test_events_no_overlapping_trials(sample_events_df):
    """Test that no two trials overlap in time (onset + duration <= next onset)."""
    df = sample_events_df.sort_values("onset").reset_index(drop=True)
    for i in range(len(df) - 1):
        end_current = df.loc[i, "onset"] + df.loc[i, "duration"]
        start_next = df.loc[i + 1, "onset"]
        assert end_current <= start_next, (
            f"Trial {i} (onset={df.loc[i, 'onset']}, "
            f"duration={df.loc[i, 'duration']}) overlaps with "
            f"trial {i + 1} (onset={start_next})"
        )


def test_events_file_loads_from_bids_fixture(tmp_bids_dir):
    """Test that the events TSV written by the BIDS fixture loads correctly."""
    events_file = (
        tmp_bids_dir
        / "sub-01"
        / "func"
        / "sub-01_task-emotionreg_run-01_events.tsv"
    )
    df = load_events(str(events_file))

    assert isinstance(df, pd.DataFrame)
    assert set(df.columns) >= {"onset", "duration", "trial_type"}
    assert len(df) == 5, f"Expected 5 events in fixture file, got {len(df)}"
    assert (df["onset"] >= 0).all()
    assert (df["duration"] > 0).all()
