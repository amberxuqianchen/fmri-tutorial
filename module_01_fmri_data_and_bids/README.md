# Module 01: Understanding fMRI Data and the BIDS Standard

## Overview

This module introduces the fundamentals of functional MRI (fMRI) data and the Brain Imaging Data
Structure (BIDS) standard. You will learn how fMRI images are stored, how to read and visualise
them in Python, and how to organise neuroimaging datasets in a way that is reproducible and
interoperable with community tools.

---

## Learning Objectives

By the end of this module you will be able to:

1. Describe the basic principles of the BOLD fMRI signal and why 4-D NIfTI files are used.
2. Load and inspect NIfTI images (shape, affine, header metadata) using nibabel.
3. Visualise brain volumes and time-series with nilearn.
4. Explain the BIDS directory structure and file-naming conventions.
5. Use pybids to query a BIDS dataset for specific files and metadata.
6. Read and interpret BIDS events TSV files for task-based fMRI.

---

## Prerequisites

- **Module 00 completed** — all required packages installed and verified.
- Basic familiarity with NumPy arrays.
- Optional: familiarity with pandas DataFrames.

---

## Time Estimate

**2 – 3 hours** (including exercises).

---

## Contents

| File | Description |
|------|-------------|
| `README.md` | This file — module overview, objectives, and instructions. |
| `01_understanding_fmri_data.ipynb` | Notebook covering NIfTI format, image dimensions, header metadata, and nilearn visualisation. |
| `01_bids_overview.ipynb` | Notebook covering the BIDS standard, directory layout, sidecar JSON/TSV files, and pybids querying. |
| `scripts/inspect_dicom_headers.py` | Command-line script that reads DICOM files and prints (or saves) a table of key header fields. |

---

## Data

The notebooks use:

- **Synthetic NIfTI data** generated on-the-fly with nibabel — no download required.
- **nilearn's built-in datasets** (`fetch_*` functions) — small files downloaded automatically on
  first use (~10–50 MB, cached in `~/nilearn_data/`).
- **`data/example_bids/`** in this repository — a minimal BIDS dataset for demonstration.

---

## Next Steps

After completing this module, continue to **Module 02: fMRI Preprocessing** to learn about
motion correction, slice-timing correction, and spatial normalisation.
