# fMRI Analysis Tutorials for Social Neuroscience

[![Tests](https://github.com/amberxuqianchen/fmri-tutorial/actions/workflows/test_scripts.yml/badge.svg)](https://github.com/amberxuqianchen/fmri-tutorial/actions/workflows/test_scripts.yml)
[![Lint Notebooks](https://github.com/amberxuqianchen/fmri-tutorial/actions/workflows/lint_notebooks.yml/badge.svg)](https://github.com/amberxuqianchen/fmri-tutorial/actions/workflows/lint_notebooks.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![BIDS 1.8](https://img.shields.io/badge/BIDS-1.8-green.svg)](https://bids.neuroimaging.io/)

---

A step-by-step, hands-on tutorial series for social neuroscience students learning to process fMRI data from raw DICOM scanner output through to preprocessed, GLM-ready data.

**Pipeline:** Raw DICOM → BIDS → Quality Control → Preprocessing → First-Level GLM Ready

Each module is self-contained with a narrative Jupyter notebook, standalone CLI scripts for batch/HPC use, and a README with learning objectives and expected outputs. The primary example dataset is an **emotion regulation task** (conditions: Reappraise / Look / Suppress) based on [ds000108](https://openneuro.org/datasets/ds000108) on OpenNeuro.

---

## Table of Contents

- [Module Overview](#module-overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Repository Structure](#repository-structure)
- [Running the Tests](#running-the-tests)
- [License](#license)
- [Citation](#citation)
- [Contributing](#contributing)

---

## Module Overview

| # | Folder | Notebook | Description | Time |
|---|--------|----------|-------------|------|
| 00 | `module_00_environment_setup/` | `00_environment_setup.ipynb` | Verify Python environment and all required packages | ~1 h |
| 01 | `module_01_fmri_data_and_bids/` | `01_understanding_fmri_data.ipynb`, `01_bids_overview.ipynb` | DICOM format, NIfTI files, and the BIDS standard | ~2 h |
| 02 | `module_02_heudiconv/` | `02_heudiconv_conversion.ipynb` | DICOM → BIDS conversion with HeuDiConv | ~2 h |
| 03 | `module_03_bids_validation/` | `03_bids_validation.ipynb` | Validate a BIDS dataset with bids-validator and PyBIDS | ~1 h |
| 04 | `module_04_events_files/` | `04_events_files.ipynb` | Create and validate stimuli/events TSV files | ~2 h |
| 05 | `module_05_mriqc/` | `05_mriqc.ipynb` | Run MRIQC and interpret image quality metrics (IQMs) | ~2 h |
| 06 | `module_06_qc_decisions/` | `06_qc_decisions.ipynb` | Inspect MRIQC reports and make participant exclusion decisions | ~2 h |
| 07 | `module_07_fmriprep/` | `07_fmriprep_docker.ipynb`, `07_fmriprep_singularity.ipynb` | Preprocessing with fMRIPrep (Docker and Singularity) | ~4–6 h |
| 08 | `module_08_nipype_workflows/` | `08_nipype_workflows.ipynb` | Build custom preprocessing workflows with Nipype | ~3 h |
| 09 | `module_09_fmriprep_outputs/` | `09_fmriprep_outputs.ipynb` | Inspect fMRIPrep outputs and confound regressors | ~2 h |
| 10 | `module_10_glm_preparation/` | `10_glm_preparation.ipynb` | Build first-level GLM design matrices and compute contrast maps | ~3 h |

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python ≥ 3.9 | Tested on 3.9 – 3.12 |
| JupyterLab ≥ 3.0 | `pip install jupyterlab` |
| Git ≥ 2.30 | For cloning and contributing |
| Docker ≥ 20.10 *(optional)* | Required for MRIQC and fMRIPrep containers (Modules 05–07) |
| Singularity/Apptainer *(optional)* | Alternative to Docker on HPC clusters |
| FreeSurfer licence *(optional)* | Required for full fMRIPrep surface reconstruction |
| ≥ 8 GB RAM | 16 GB recommended for fMRIPrep |
| ≥ 5 GB free disk | For example datasets and working directories |

Basic familiarity with Python and neuroimaging concepts (BOLD signal, HRF) is assumed. No prior experience with BIDS or any specific tool is required.

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/amberxuqianchen/fmri-tutorial.git
cd fmri-tutorial
```

### 2. Create and activate a Conda environment (recommended)

```bash
conda env create -f environments/environment_full.yml
conda activate fmri-tutorial-full
```

Or use a plain virtual environment with pip:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Install the local utils package

```bash
pip install -e .
```

### 4. Register the Jupyter kernel

```bash
python -m ipykernel install --user --name fmri-tutorial --display-name "fMRI Tutorial"
```

### 5. Launch JupyterLab

```bash
jupyter lab
```

Open `module_00_environment_setup/00_environment_setup.ipynb` first to confirm your environment is configured correctly, then work through the modules in order.

---

## Repository Structure

```
fmri-tutorial/
├── module_00_environment_setup/    # Env verification
├── module_01_fmri_data_and_bids/   # DICOM + BIDS overview
├── module_02_heudiconv/            # DICOM → BIDS conversion
├── module_03_bids_validation/      # BIDS validation
├── module_04_events_files/         # Events / stimuli TSVs
├── module_05_mriqc/                # Quality control with MRIQC
├── module_06_qc_decisions/         # QC report inspection
├── module_07_fmriprep/             # fMRIPrep preprocessing
├── module_08_nipype_workflows/     # Custom Nipype workflows
├── module_09_fmriprep_outputs/     # Confounds and derivatives
├── module_10_glm_preparation/      # First-level GLM
├── utils/                          # Shared Python utility library
├── tests/                          # pytest test suite
├── data/                           # Synthetic BIDS example dataset
├── environments/                   # Conda YAMLs, Dockerfile, Singularity
├── docs/                           # Documentation index, FAQ, API reference
├── .github/workflows/              # CI: lint, validate BIDS, run tests
├── requirements.txt                # pip-installable dependencies
├── pyproject.toml                  # Package metadata (pip install -e .)
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md
└── LICENSE
```

---

## Running the Tests

```bash
pip install pytest
pytest tests/ -v
```

The test suite covers `utils/` helpers (BIDS queries, DICOM parsing, events validation, Nipype workflow creation, GLM preparation). Tests that require optional heavy dependencies (nilearn, nipype) are automatically skipped if those packages are not installed.

---

## License

Distributed under the [MIT License](LICENSE). Example datasets used in the notebooks are drawn from [OpenNeuro](https://openneuro.org/) and are governed by their own licences; each notebook documents the relevant source and licence.

---

## Citation

If these tutorials contribute to your research or teaching, please cite:

```bibtex
@software{fmri_tutorial,
  author    = {Amber Chen and Contributors},
  title     = {fMRI Analysis Tutorials for Social Neuroscience},
  year      = {2026},
  url       = {https://github.com/amberxuqianchen/fmri-tutorial}
}
```

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding new modules, the notebook style guide, and the pull request process. All participants are expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

