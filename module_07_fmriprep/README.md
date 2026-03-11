# Module 07: Preprocessing with fMRIPrep

## Learning Objectives

By the end of this module, you will be able to:

1. Describe the major preprocessing steps performed by fMRIPrep and why each matters
2. Obtain and configure a FreeSurfer license for use with fMRIPrep
3. Run fMRIPrep using Docker on a local workstation
4. Run fMRIPrep using Singularity/Apptainer on an HPC cluster
5. Specify output spaces (MNI, T1w, native) appropriate for your analysis
6. Interpret fMRIPrep's visual HTML reports and confound regressors TSV
7. Troubleshoot common fMRIPrep errors and understand log output

## Prerequisites

- Module 00: Environment Setup
- Module 01: fMRI Data and BIDS
- Module 02: HeuDiConv
- Module 03: BIDS Validation
- Module 04: Events Files
- Module 05: MRIQC
- Module 06: QC Decisions
- **Docker** (≥ 20.10) or **Singularity/Apptainer** (≥ 3.x)
- **FreeSurfer license** (free from https://surfer.nmr.mgh.harvard.edu/registration.html)
- ≥ 16 GB RAM recommended; ≥ 8 CPU cores recommended

## Time Estimate

**4–6 hours** — mostly compute time. Per-subject preprocessing typically takes 1–4 hours depending on data length and hardware.

## Overview

fMRIPrep is a robust, minimally opinionated preprocessing pipeline for fMRI data. It automatically adapts to your dataset's structure (detected from BIDS), performs state-of-the-art preprocessing steps, and produces comprehensive quality reports.

Using a containerized version (Docker or Singularity) ensures reproducibility across computing environments and avoids complex dependency installation.

## Module Contents

| File | Description |
|------|-------------|
| `07_fmriprep_docker.ipynb` | fMRIPrep with Docker (local workstation) |
| `07_fmriprep_singularity.ipynb` | fMRIPrep with Singularity/Apptainer (HPC) |
| `scripts/run_fmriprep_docker.sh` | Shell script: single-subject Docker run |
| `scripts/run_fmriprep_singularity.sh` | Shell script: single-subject Singularity run |
| `scripts/run_fmriprep_batch.sh` | Shell script: batch multi-subject processing |

## Key fMRIPrep Preprocessing Steps

| Step | Tool Used | Output |
|------|-----------|--------|
| Brain extraction | ANTs / HD-BET | Brain mask |
| Tissue segmentation | FastSurfer / FreeSurfer | Tissue probability maps |
| Surface reconstruction | FreeSurfer | Cortical surfaces |
| T1w–MNI registration | ANTs | Warp fields |
| Susceptibility distortion correction | fieldmap / SyN | Unwarped EPI |
| Head motion estimation | MCFLIRT | Rigid body parameters |
| Slice timing correction | AFNI | Time-shifted BOLD |
| Confound estimation | Multiple | confounds TSV |
| ICA-AROMA (optional) | ICA-AROMA | Noise-classified components |

## Output Spaces

fMRIPrep can output preprocessed BOLD in multiple spaces. Commonly used:

- `MNI152NLin2009cAsym` — standard MNI space (good for group analysis)
- `T1w` — subject's native structural space
- `fsnative` — FreeSurfer native surface
- `fsaverage5` — downsampled FreeSurfer average surface

## References

- Esteban O, et al. (2019). fMRIPrep: a robust preprocessing pipeline for functional MRI. *Nature Methods*. https://doi.org/10.1038/s41592-018-0235-4
- Ciric R, et al. (2017). Benchmarking of participant-level confound regression strategies for the control of motion artifact in studies of functional connectivity. *NeuroImage*. https://doi.org/10.1016/j.neuroimage.2017.03.020
- Gorgolewski KJ, et al. (2016). The brain imaging data structure, a format for organizing and describing outputs of neuroimaging experiments. *Scientific Data*. https://doi.org/10.1038/sdata.2016.44
