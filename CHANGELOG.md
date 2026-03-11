# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

#### Repository scaffolding
- `README.md` — comprehensive overview with accurate module table, quick-start (conda + pip), repository structure, and citation
- `CONTRIBUTING.md` — development environment setup, notebook style guide, and PR process
- `CODE_OF_CONDUCT.md` — Contributor Covenant v2.1 adapted for academic neuroscience
- `CHANGELOG.md` — this file
- `requirements.txt` — pip-installable dependency list
- `pyproject.toml` — package metadata enabling `pip install -e .` for the `utils/` library
- `.github/workflows/lint_notebooks.yml` — nbval + flake8 + black CI check
- `.github/workflows/validate_bids.yml` — bids-validator on example data
- `.github/workflows/test_scripts.yml` — pytest on utility scripts
- `.github/ISSUE_TEMPLATE/bug_report.md` and `content_request.md`

#### Environments
- `environments/environment_full.yml` — full conda environment (all tools except fMRIPrep)
- `environments/environment_minimal.yml` — minimal environment (HeuDiConv + BIDS only)
- `environments/environment_nipype.yml` — Nipype + FSL/ANTs wrappers
- `environments/Dockerfile` — multi-stage, non-root user, JupyterLab entry point
- `environments/docker-compose.yml` — Jupyter + fMRIPrep + MRIQC services
- `environments/singularity/fmriprep.def` and `mriqc.def` — Singularity definition files
- `environments/setup_environment.sh` — interactive local setup walkthrough

#### Data
- `data/example_bids/` — synthetic BIDS dataset (emotion-regulation task, 1 subject, 2 runs, Reappraise/Look/Suppress conditions)
- `data/heuristics/` — HeuDiConv heuristics for ds000108 (emotion regulation) and ds000228 (ToM)
- `data/example_dicoms/generate_synthetic_dicoms.py` — pydicom-based T1w + BOLD DICOM generator
- `data/download_openneuro.sh` — AWS CLI sync for OpenNeuro datasets

#### `utils/` library
- `utils/bids_helpers.py` — PyBIDS dataset queries and events loading
- `utils/dicom_helpers.py` — DICOM header inspection and protocol extraction
- `utils/mriqc_helpers.py` — MRIQC image quality metrics analysis
- `utils/nipype_helpers.py` — Nipype preprocessing and first-level GLM workflows
- `utils/plotting.py` — brain visualization and timeseries plotting
- `utils/io_utils.py` — general-purpose I/O (TSV, JSON, file discovery)

#### `tests/` suite
- `tests/conftest.py` — shared fixtures (synthetic BIDS dir, events DataFrame, confounds DataFrame)
- `tests/test_bids_helpers.py` — BIDS layout queries and events loading
- `tests/test_dicom_helpers.py` — DICOM header parsing
- `tests/test_events_conversion.py` — events TSV validation
- `tests/test_nipype_workflow.py` — Nipype workflow creation (skipped without nipype)
- `tests/test_glm_preparation.py` — design matrix construction with nilearn (skipped without nilearn)

#### Tutorial Modules 00–10
- **Module 00** — Environment setup and installation verification
- **Module 01** — fMRI data (DICOM/NIfTI) and the BIDS standard
- **Module 02** — DICOM → BIDS conversion with HeuDiConv
- **Module 03** — BIDS validation with bids-validator and PyBIDS
- **Module 04** — Creating and managing stimuli/events TSV files
- **Module 05** — Quality control with MRIQC
- **Module 06** — Inspecting MRIQC reports and making exclusion decisions
- **Module 07** — Preprocessing with fMRIPrep (Docker and Singularity)
- **Module 08** — Building custom Nipype preprocessing workflows
- **Module 09** — Inspecting fMRIPrep outputs and confound regressors
- **Module 10** — Preparing data for first-level GLM analysis

#### `docs/`
- `docs/index.md` — documentation home page with module navigation table
- `docs/faq.md` — frequently asked questions and troubleshooting guide
- `docs/api/utils.md` — API reference for the `utils/` library

---

## [0.1.0] — 2026-03-11

### Added
- Initial repository setup
- `.gitignore` configured for Python, Jupyter notebooks, and common neuroimaging data formats
- `LICENSE` (MIT)
- `README.md` stub

---

[Unreleased]: https://github.com/amberxuqianchen/fmri-tutorial/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/amberxuqianchen/fmri-tutorial/releases/tag/v0.1.0
