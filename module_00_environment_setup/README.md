# Module 00: Environment Setup

## Overview

This module walks you through setting up a Python environment suitable for fMRI data analysis. You will verify that all required packages are installed, run basic sanity checks, and familiarise yourself with the key libraries used throughout this tutorial series.

---

## Learning Objectives

By the end of this module you will be able to:

1. Create and activate a conda environment containing all packages needed for fMRI analysis.
2. Verify that core libraries (nibabel, nilearn, pybids, nipype) are correctly installed and importable.
3. Create and inspect a synthetic NIfTI image using nibabel.
4. Load and display a standard-space brain mask using nilearn.

---

## Prerequisites

- Basic familiarity with Python (variables, imports, functions).
- Basic command-line / terminal usage (navigating directories, running scripts).
- [Conda](https://docs.conda.io/en/latest/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) installed.

---

## Time Estimate

**30 – 60 minutes** (depending on download speed for conda packages).

---

## Contents

| File | Description |
|------|-------------|
| `README.md` | This file — module overview, objectives, and instructions. |
| `00_environment_setup.ipynb` | Interactive Jupyter notebook guiding you through environment verification, package checks, and basic library tests. |
| `verify_installation.py` | Standalone Python script that checks all required and optional packages and exits with a status code suitable for automated testing. |

---

## Setup Instructions

### 1. Create the conda environment

An `environment.yml` file is provided in the repository root under `environments/`. To create the environment run:

```bash
conda env create -f environments/environment.yml
conda activate fmri-tutorial
```

### 2. Launch JupyterLab

```bash
jupyter lab
```

Open `00_environment_setup.ipynb` and run all cells from top to bottom.

### 3. Quick command-line check

```bash
python verify_installation.py
```

A return code of `0` means all **required** packages were found. A return code of `1` means one or more required packages are missing.

---

## Expected Outputs

After completing this module you should see:

- ✅ Python version ≥ 3.8 printed to the notebook.
- ✅ All required packages (`numpy`, `pandas`, `nibabel`, `matplotlib`) reported as **available**.
- ✅ A synthetic NIfTI image created, saved, and reloaded without errors.
- ✅ A nilearn brain-mask figure rendered inside the notebook.
- ✅ `verify_installation.py` exits with code `0`.

---

## Next Steps

Proceed to **Module 01: Understanding fMRI Data and the BIDS Standard** once all checks pass.
