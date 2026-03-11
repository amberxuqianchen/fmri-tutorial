# Module 09: Inspecting fMRIPrep Outputs

## Learning Objectives

By the end of this module, you will be able to:

1. Navigate the fMRIPrep derivatives directory structure and locate key output files
2. Load and interpret the confounds timeseries TSV produced by fMRIPrep
3. Plot and visually inspect the six rigid-body motion parameters
4. Understand how framewise displacement (FD) is calculated and what it quantifies
5. Identify motion spikes and create a scrubbing mask to censor high-motion volumes
6. Select an appropriate confound regression strategy (minimal / moderate / aggressive) for GLM analysis
7. Interpret the fMRIPrep subject-level HTML quality report

## Prerequisites

- Module 00: Environment Setup
- Module 01: fMRI Data and BIDS
- Module 02: HeuDiConv
- Module 03: BIDS Validation
- Module 04: Events Files
- Module 05: MRIQC
- Module 06: QC Decisions
- Module 07: Preprocessing with fMRIPrep (especially its HTML report and confounds output)
- **nibabel** (≥ 3.0)
- **nilearn** (≥ 0.9)
- **pandas** (≥ 1.3)
- **matplotlib** (≥ 3.5)
- **numpy** (≥ 1.21)

## Time Estimate

**~2 hours** — primarily notebook exploration; no long compute jobs required.

## Overview

After fMRIPrep finishes, you are left with a derivatives directory full of preprocessed images, quality figures, confound tables, and an HTML report for each subject. Knowing how to navigate and interpret these outputs is an essential skill before proceeding to first-level GLM modelling.

This module walks through the fMRIPrep derivatives structure, shows how to load and visualise motion parameters and framewise displacement, explains scrubbing strategies for high-motion volumes, and demonstrates how to extract a confound matrix for downstream denoising. You will also learn what each section of the fMRIPrep HTML report contains so you can quickly flag problematic subjects.

## Module Contents

| File | Description |
|------|-------------|
| `09_fmriprep_outputs.ipynb` | Main tutorial notebook: explore derivatives, motion, confounds, brain masks |
| `scripts/inspect_fmriprep_outputs.py` | CLI script: summarise fMRIPrep outputs and motion statistics for a subject |
| `scripts/extract_confounds.py` | CLI script: extract a confound matrix with a chosen denoising strategy |
| `README.md` | This file |

---

## fMRIPrep Derivatives Structure

After a successful fMRIPrep run the `derivatives/fmriprep/` directory follows a BIDS-Derivatives layout:

```
derivatives/fmriprep/
├── dataset_description.json
├── sub-01.html                          ← subject HTML report
├── sub-01/
│   ├── anat/
│   │   ├── sub-01_desc-brain_mask.nii.gz
│   │   ├── sub-01_desc-preproc_T1w.nii.gz
│   │   ├── sub-01_from-T1w_to-MNI152NLin2009cAsym_mode-image_xfm.h5
│   │   └── sub-01_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5
│   ├── func/
│   │   ├── sub-01_task-rest_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz
│   │   ├── sub-01_task-rest_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz
│   │   ├── sub-01_task-rest_desc-confounds_timeseries.tsv
│   │   ├── sub-01_task-rest_desc-confounds_timeseries.json
│   │   └── sub-01_task-rest_space-MNI152NLin2009cAsym_boldref.nii.gz
│   └── figures/
│       ├── sub-01_task-rest_desc-carpetplot_bold.svg
│       ├── sub-01_task-rest_desc-rois_bold.svg
│       └── ...
└── sub-02/
    └── ...
```

### Key Output Files

| File pattern | Description |
|---|---|
| `*_desc-preproc_bold.nii.gz` | Preprocessed BOLD in the requested output space |
| `*_desc-brain_mask.nii.gz` | Binary brain mask in the same space |
| `*_desc-confounds_timeseries.tsv` | Confound regressors (one row per volume) |
| `sub-XX.html` | Subject-level QC report with figures and carpet plots |

---

## Confound Strategies

fMRIPrep does **not** perform confound regression — it only estimates and outputs the confound columns. You choose which columns to include in your GLM or nuisance regression. Three commonly used strategies are:

### Minimal (6 motion parameters + FD)

Regress only the six rigid-body motion parameters (three translations, three rotations) and framewise displacement. Appropriate as a baseline or for datasets with very little motion.

Columns: `trans_x`, `trans_y`, `trans_z`, `rot_x`, `rot_y`, `rot_z`, `framewise_displacement`

### Moderate (motion + tissue signals + aCompCor)

Adds global signal, white-matter signal, CSF signal, and the first six anatomical CompCor components. This is the most widely used strategy and provides a good balance between noise removal and degrees of freedom.

Columns: all minimal + `global_signal`, `white_matter`, `csf`, `a_comp_cor_00`–`a_comp_cor_05`

### Aggressive (36-parameter or full aCompCor)

Either uses the "36-parameter" strategy (6 motion params + their temporal derivatives + their squares + squares of the derivatives = 24 motion params, plus tissue signals and their derivatives/squares) or retains the full set of aCompCor components. Best for resting-state connectivity analyses where motion artefact control is paramount, but consumes many degrees of freedom.

Columns: all moderate + `trans_x_derivative1`, `trans_x_power2`, `trans_x_derivative1_power2` (and equivalents for each axis) + expanded aCompCor columns

### Scrubbing

Regardless of strategy, volumes with FD > 0.5 mm (or a threshold of your choice) are typically excluded from analysis by either removing them entirely or by adding per-volume indicator regressors. The `extract_confounds.py` script adds a binary `motion_outlier` column when `--scrub` is requested.

---

## References

- Esteban O, et al. (2019). fMRIPrep: a robust preprocessing pipeline for functional MRI. *Nature Methods*, 16(1), 111–116. https://doi.org/10.1038/s41592-018-0235-4
- Ciric R, et al. (2017). Benchmarking of participant-level confound regression strategies for the control of motion artifact in studies of functional connectivity. *NeuroImage*, 154, 174–187. https://doi.org/10.1016/j.neuroimage.2017.03.020
- Power JD, et al. (2012). Spurious but systematic correlations in functional connectivity MRI networks arise from subject motion. *NeuroImage*, 59(3), 2142–2154. https://doi.org/10.1016/j.neuroimage.2011.10.018
- Friston KJ, et al. (1996). Movement-related effects in fMRI time-series. *Magnetic Resonance in Medicine*, 35(3), 346–355. https://doi.org/10.1002/mrm.1910350312
