# Tests

This directory contains the pytest test suite for the `fmri-tutorial` repository.

## Running the tests

### Prerequisites

Install the core test dependencies:

```bash
pip install pytest pandas numpy
```

Install optional dependencies to unlock additional test coverage:

```bash
# BIDS dataset querying
pip install pybids

# DICOM reading
pip install pydicom

# Neuroimaging pipeline
pip install nipype

# GLM / first-level analysis
pip install nilearn
```

### Run all tests

```bash
# From the repository root
pytest tests/

# With verbose output
pytest tests/ -v

# Stop on first failure
pytest tests/ -x
```

### Run a single test file

```bash
pytest tests/test_bids_helpers.py -v
pytest tests/test_events_conversion.py -v
```

### Run with coverage (requires pytest-cov)

```bash
pip install pytest-cov
pytest tests/ --cov=utils --cov-report=term-missing
```

---

## Test files

| File | What it covers |
|---|---|
| `conftest.py` | Shared pytest fixtures: `tmp_bids_dir`, `sample_events_df`, `sample_confounds_df` |
| `test_bids_helpers.py` | `utils/bids_helpers.py` — `load_events()`, `check_bids_completeness()` |
| `test_dicom_helpers.py` | `utils/dicom_helpers.py` — module import, error handling for missing paths (requires pydicom) |
| `test_events_conversion.py` | BIDS events TSV structure: required columns, positive onsets/durations, valid trial types, sort order |
| `test_nipype_workflow.py` | `utils/nipype_helpers.py` — workflow creation, node names/count (requires nipype; FSL not needed) |
| `test_glm_preparation.py` | First-level design matrix construction with nilearn: columns, shape, confound selection, NaN handling (requires nilearn) |

---

## Notes on optional dependencies

Tests that require a library not present in the current environment are
**automatically skipped** — they will not fail.  You will see output like:

```
SKIPPED [1] tests/test_nipype_workflow.py: nipype is not installed; skipping nipype workflow tests
```

The `test_bids_helpers.py::test_check_bids_completeness_runs` test is
explicitly skipped because pybids validation requires actual NIfTI (`.nii.gz`)
files to be present on disk, which are not included in the lightweight fixture
directory.
