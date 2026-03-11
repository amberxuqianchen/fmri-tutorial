# fMRI Tutorial Documentation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![BIDS](https://img.shields.io/badge/BIDS-1.8-green.svg)](https://bids.neuroimaging.io/)

## Overview

This tutorial series teaches social neuroscience students how to process fMRI data from raw DICOMs through to first-level GLM-ready statistical maps. Each module is self-contained with a Jupyter notebook, supporting scripts, and a README.

**Pipeline:** Raw DICOM → BIDS → QC → Preprocessing → First-Level GLM Ready

## Quick Navigation

| Module | Topic | Time | Key Tools |
|--------|-------|------|-----------|
| [Module 00](../module_00_environment_setup/README.md) | Environment Setup | ~1h | conda, pip |
| [Module 01](../module_01_fmri_data_and_bids/README.md) | fMRI Data & BIDS | ~2h | PyBIDS |
| [Module 02](../module_02_heudiconv/README.md) | DICOM → BIDS with HeuDiConv | ~2h | HeuDiConv |
| [Module 03](../module_03_bids_validation/README.md) | BIDS Validation | ~1h | bids-validator |
| [Module 04](../module_04_events_files/README.md) | Events Files | ~2h | pandas |
| [Module 05](../module_05_mriqc/README.md) | MRIQC | ~2h | MRIQC |
| [Module 06](../module_06_qc_decisions/README.md) | QC Decisions | ~2h | pandas, matplotlib |
| [Module 07](../module_07_fmriprep/README.md) | Preprocessing with fMRIPrep | ~4–6h | fMRIPrep |
| [Module 08](../module_08_nipype_workflows/README.md) | Custom Nipype Workflows | ~3h | nipype, FSL |
| [Module 09](../module_09_fmriprep_outputs/README.md) | Inspecting fMRIPrep Outputs | ~2h | nibabel, nilearn |
| [Module 10](../module_10_glm_preparation/README.md) | First-Level GLM Preparation | ~3h | nilearn |

## Getting Started

1. Follow **Module 00** to set up your Python environment.
2. Work through modules sequentially — each builds on the previous.
3. All notebooks include fallback synthetic data so you can run them without real fMRI data.

## Repository Structure

```
fmri-tutorial/
├── module_00_environment_setup/
├── module_01_fmri_data_and_bids/
├── module_02_heudiconv/
├── module_03_bids_validation/
├── module_04_events_files/
├── module_05_mriqc/
├── module_06_qc_decisions/
├── module_07_fmriprep/
├── module_08_nipype_workflows/
├── module_09_fmriprep_outputs/
├── module_10_glm_preparation/
├── utils/                  # Shared Python utility functions
├── environments/           # Conda environment files
├── data/                   # Sample data
├── tests/                  # Test suite
└── docs/                   # This documentation
```

## Additional Resources

- [FAQ](faq.md) — Common questions and troubleshooting
- [API Reference](api/utils.md) — Utility function documentation
- [Contributing](../CONTRIBUTING.md) — How to contribute
- [Changelog](../CHANGELOG.md) — Version history
