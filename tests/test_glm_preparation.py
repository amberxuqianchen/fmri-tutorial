"""Tests for GLM preparation utilities.

Uses nilearn's ``make_first_level_design_matrix`` to build a design matrix
and validates its structure.  The entire module is skipped if nilearn is not
installed.

Fixtures used: ``sample_events_df``, ``sample_confounds_df`` (from conftest.py).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

nilearn = pytest.importorskip(
    "nilearn", reason="nilearn is not installed; skipping GLM preparation tests"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CONFOUND_COLUMNS = [
    "trans_x",
    "trans_y",
    "trans_z",
    "rot_x",
    "rot_y",
    "rot_z",
    "framewise_displacement",
    "global_signal",
]

TR = 2.0  # seconds
N_SCANS = 50


def _build_design_matrix(events_df, confounds_df=None, hrf_model="spm"):
    """Helper that wraps nilearn's make_first_level_design_matrix."""
    from nilearn.glm.first_level import make_first_level_design_matrix

    frame_times = np.arange(N_SCANS) * TR

    add_regs = None
    add_reg_names = None
    if confounds_df is not None:
        # Drop rows with NaN (e.g. first FD value) for nilearn compatibility
        clean = confounds_df.fillna(0)
        add_regs = clean.values
        add_reg_names = list(clean.columns)

    dm = make_first_level_design_matrix(
        frame_times=frame_times,
        events=events_df,
        hrf_model=hrf_model,
        add_regs=add_regs,
        add_reg_names=add_reg_names,
    )
    return dm


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_design_matrix_columns(sample_events_df):
    """Test that the design matrix contains columns for each trial type and a constant."""
    dm = _build_design_matrix(sample_events_df)

    assert isinstance(dm, pd.DataFrame), "Design matrix should be a DataFrame"

    trial_types = sample_events_df["trial_type"].unique().tolist()
    for tt in trial_types:
        assert any(tt in col for col in dm.columns), (
            f"Design matrix should contain a column for trial type '{tt}'. "
            f"Columns found: {list(dm.columns)}"
        )

    # nilearn always appends a constant/drift column
    assert any("constant" in col.lower() or "drift" in col.lower() for col in dm.columns), (
        "Design matrix should contain a constant or drift column. "
        f"Columns found: {list(dm.columns)}"
    )


def test_design_matrix_shape(sample_events_df):
    """Test that the design matrix has the expected number of rows (== n_scans)."""
    dm = _build_design_matrix(sample_events_df)
    assert dm.shape[0] == N_SCANS, (
        f"Design matrix should have {N_SCANS} rows (one per scan), got {dm.shape[0]}"
    )


def test_confounds_selection(sample_confounds_df):
    """Test selecting a subset of confound columns from the fMRIPrep confounds table."""
    motion_cols = ["trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z"]

    selected = sample_confounds_df[motion_cols]

    assert list(selected.columns) == motion_cols, (
        "Selected confounds DataFrame should only contain the requested columns"
    )
    assert selected.shape == (len(sample_confounds_df), len(motion_cols))
    assert not selected.isnull().any().any(), (
        "Motion parameter columns should not contain NaN values"
    )


def test_confounds_have_expected_columns(sample_confounds_df):
    """Test that the confounds fixture contains all expected fMRIPrep column names."""
    for col in CONFOUND_COLUMNS:
        assert col in sample_confounds_df.columns, (
            f"Expected confound column '{col}' not found in sample_confounds_df"
        )


def test_design_matrix_with_confounds(sample_events_df, sample_confounds_df):
    """Test that adding confounds to the design matrix increases the column count."""
    dm_no_confounds = _build_design_matrix(sample_events_df)
    dm_with_confounds = _build_design_matrix(sample_events_df, confounds_df=sample_confounds_df)

    assert dm_with_confounds.shape[1] > dm_no_confounds.shape[1], (
        "Design matrix with confounds should have more columns than one without"
    )


def test_design_matrix_no_nan(sample_events_df, sample_confounds_df):
    """Test that the final design matrix contains no NaN values."""
    dm = _build_design_matrix(sample_events_df, confounds_df=sample_confounds_df)
    assert not dm.isnull().any().any(), (
        "Design matrix should not contain NaN values after confounds are added"
    )


def test_framewise_displacement_first_value_nan(sample_confounds_df):
    """Test that the first framewise_displacement value is NaN (fMRIPrep convention)."""
    fd = sample_confounds_df["framewise_displacement"]
    assert pd.isna(fd.iloc[0]), (
        "The first framewise_displacement value should be NaN (fMRIPrep convention)"
    )
    assert fd.iloc[1:].notna().all(), (
        "All framewise_displacement values after the first should be non-NaN"
    )
