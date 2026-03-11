"""Pytest configuration and shared fixtures for the fmri-tutorial test suite."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def tmp_bids_dir(tmp_path):
    """Create a minimal BIDS directory structure for testing.

    Creates the following layout under a temporary directory::

        bids_root/
        ├── dataset_description.json
        ├── participants.tsv
        └── sub-01/
            ├── anat/
            │   └── sub-01_T1w.json
            └── func/
                ├── sub-01_task-emotionreg_run-01_bold.json
                └── sub-01_task-emotionreg_run-01_events.tsv

    Args:
        tmp_path (pathlib.Path): Pytest-provided temporary directory.

    Returns:
        pathlib.Path: Path to the BIDS root directory.
    """
    bids_root = tmp_path / "bids"
    bids_root.mkdir()

    # dataset_description.json (required by BIDS spec)
    dataset_description = {
        "Name": "fMRI Tutorial Test Dataset",
        "BIDSVersion": "1.8.0",
        "DatasetType": "raw",
    }
    (bids_root / "dataset_description.json").write_text(
        json.dumps(dataset_description, indent=2)
    )

    # participants.tsv
    participants_tsv = "participant_id\tage\tsex\n" "sub-01\t25\tF\n"
    (bids_root / "participants.tsv").write_text(participants_tsv)

    # Subject directories
    func_dir = bids_root / "sub-01" / "func"
    anat_dir = bids_root / "sub-01" / "anat"
    func_dir.mkdir(parents=True)
    anat_dir.mkdir(parents=True)

    # sub-01/func/sub-01_task-emotionreg_run-01_events.tsv
    events_tsv = (
        "onset\tduration\ttrial_type\n"
        "0.0\t2.0\tNeutral\n"
        "10.0\t2.0\tNegative\n"
        "20.0\t2.0\tPositive\n"
        "30.0\t2.0\tNeutral\n"
        "40.0\t2.0\tNegative\n"
    )
    (func_dir / "sub-01_task-emotionreg_run-01_events.tsv").write_text(events_tsv)

    # sub-01/func/sub-01_task-emotionreg_run-01_bold.json
    bold_json = {
        "RepetitionTime": 2.0,
        "TaskName": "emotionreg",
        "SliceTiming": [0.0, 0.5, 1.0, 1.5],
        "PhaseEncodingDirection": "j-",
        "EffectiveEchoSpacing": 0.00058,
    }
    (func_dir / "sub-01_task-emotionreg_run-01_bold.json").write_text(
        json.dumps(bold_json, indent=2)
    )

    # sub-01/anat/sub-01_T1w.json
    t1w_json = {
        "Manufacturer": "Siemens",
        "ManufacturersModelName": "Prisma",
        "MagneticFieldStrength": 3,
    }
    (anat_dir / "sub-01_T1w.json").write_text(json.dumps(t1w_json, indent=2))

    return bids_root


@pytest.fixture
def sample_events_df():
    """Return a pandas DataFrame with sample BIDS-formatted events data.

    Returns:
        pandas.DataFrame: Events table with ``onset``, ``duration``, and
        ``trial_type`` columns, sorted by onset.
    """
    data = {
        "onset": [0.0, 10.0, 20.0, 30.0, 40.0, 50.0],
        "duration": [2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
        "trial_type": ["Neutral", "Negative", "Positive", "Neutral", "Negative", "Positive"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_confounds_df():
    """Return a pandas DataFrame with typical fMRIPrep confound columns.

    The DataFrame contains 50 time points of simulated head-motion and
    nuisance-signal confounds as produced by fMRIPrep.

    Returns:
        pandas.DataFrame: Confounds table with columns ``trans_x``,
        ``trans_y``, ``trans_z``, ``rot_x``, ``rot_y``, ``rot_z``,
        ``framewise_displacement``, and ``global_signal``.
    """
    rng = np.random.default_rng(seed=42)
    n_timepoints = 50

    data = {
        "trans_x": rng.normal(0, 0.1, n_timepoints),
        "trans_y": rng.normal(0, 0.1, n_timepoints),
        "trans_z": rng.normal(0, 0.1, n_timepoints),
        "rot_x": rng.normal(0, 0.005, n_timepoints),
        "rot_y": rng.normal(0, 0.005, n_timepoints),
        "rot_z": rng.normal(0, 0.005, n_timepoints),
        "framewise_displacement": np.abs(rng.normal(0, 0.2, n_timepoints)),
        "global_signal": rng.normal(0, 1.0, n_timepoints),
    }
    # fMRIPrep sets the first FD value to NaN
    data["framewise_displacement"][0] = float("nan")

    return pd.DataFrame(data)
