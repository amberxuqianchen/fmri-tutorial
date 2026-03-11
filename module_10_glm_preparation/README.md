# Module 10: Preparing Data for First-Level GLM Analysis

## Learning Objectives

By the end of this module, you will be able to:

1. Understand the structure of a GLM design matrix and how it encodes experimental conditions over time
2. Build a first-level design matrix using `nilearn.glm.first_level.make_first_level_design_matrix()`
3. Explain how the haemodynamic response function (HRF) is convolved with a boxcar stimulus model to produce BOLD regressors
4. Select and clean confound regressors from fMRIPrep output using minimal, moderate, and aggressive strategies
5. Fit a `FirstLevelModel` to preprocessed BOLD data using nilearn
6. Specify contrasts of interest (e.g., Reappraise vs Look or Look_Neg) as linear combinations of design matrix columns
7. Compute z-statistic and t-statistic contrast maps from a fitted GLM
8. Perform quality checks on the design matrix, including rank assessment, condition coverage, and variance inflation factors (VIF)

## Prerequisites

- Module 00: Environment Setup
- Module 01: fMRI Data and BIDS
- Module 02: HeuDiConv
- Module 03: BIDS Validation
- Module 04: Events Files
- Module 05: MRIQC
- Module 06: QC Decisions
- Module 07: Preprocessing with fMRIPrep
- Module 08: Nipype Workflows
- Module 09: Inspecting fMRIPrep Outputs (confound selection strategies)
- **nilearn** (≥ 0.9)
- **nibabel** (≥ 3.0)
- **pandas** (≥ 1.3)
- **numpy** (≥ 1.21)
- **matplotlib** (≥ 3.5)

## Time Estimate

**~3 hours** — includes notebook walkthroughs, design matrix building, GLM fitting, and contrast computation. No long cluster jobs are required; fitting runs on a single CPU in a few minutes with the synthetic data provided.

## Overview

The General Linear Model (GLM) is the cornerstone of task-based fMRI analysis. At the first level, a separate GLM is fit for each subject, regressing the preprocessed BOLD signal at every voxel onto a design matrix that encodes the timing of experimental conditions, low-frequency drift, and nuisance confounds. The resulting parameter estimates (β-maps) and their contrasts yield the statistical maps (z-maps, t-maps) that are carried forward to group-level analysis.

This module walks through every step of first-level GLM preparation for an emotion regulation task: loading a preprocessed BOLD image, building a design matrix with HRF-convolved condition regressors, selecting confounds, fitting a `FirstLevelModel` with nilearn, and computing contrasts comparing regulatory strategies (Reappraise, Suppress) against a passive-viewing baseline (`Look` or `Look_Neg`, depending on your task labels). You will also learn how to quality-check the design matrix before committing to a full analysis pipeline.

## Module Contents

| File | Description |
|------|-------------|
| `10_glm_preparation.ipynb` | Main tutorial notebook: design matrix, GLM fitting, contrasts, QC |
| `scripts/prepare_glm_regressors.py` | CLI script: build and save design matrix and cleaned confounds TSV |
| `scripts/run_first_level_glm.py` | CLI script: fit GLM, compute contrasts, save z-maps and figures |
| `README.md` | This file |

---

## The First-Level GLM

### Design Matrix

The general linear model for a single voxel's BOLD timeseries **y** is:

```
y = X β + ε
```

where:

- **y** ∈ ℝ^T is the BOLD signal across *T* timepoints
- **X** ∈ ℝ^(T × p) is the **design matrix** with *p* regressors
- **β** ∈ ℝ^p is the vector of **parameter estimates** (effect sizes)
- **ε** ∈ ℝ^T is residual noise, assumed ε ~ N(0, σ²V)

The ordinary least-squares estimator is:

```
β̂ = (X'X)⁻¹ X' y
```

In practice, the model is also prewhitened to account for serial autocorrelation in the BOLD signal (nilearn uses an AR(1) model by default).

### Haemodynamic Response Function (HRF)

Neurons fire in response to a stimulus, but the BOLD signal follows a delayed haemodynamic response. The canonical HRF peaks around 5–6 seconds after stimulus onset and returns to baseline at ~20 seconds. To model the expected BOLD response for each trial type, we convolve the **stimulus boxcar** function (1 during stimulus, 0 otherwise) with the HRF:

```
x_condition(t) = boxcar(t) * hrf(t)
```

nilearn supports several HRF models. The **SPM canonical HRF** (`hrf_model='spm'`) is the standard choice for task fMRI; `'spm + derivative'` adds a temporal derivative regressor to model small latency shifts.

### Confound Regressors

The design matrix also includes:

1. **Experimental regressors** — one HRF-convolved regressor per trial type
2. **Drift regressors** — cosine basis functions modelling low-frequency scanner drift (replacing a high-pass filter)
3. **Nuisance regressors** — motion parameters, tissue signals, and aCompCor components from fMRIPrep (selected via the confound extraction strategy from Module 09)

### Contrasts

A contrast **c** is a vector of weights over the design matrix columns. The contrast estimate is:

```
ĉ = c' β̂
```

and the t-statistic is:

```
t = ĉ / sqrt(c' (X'X)⁻¹ c · σ̂²)
```

For this emotion-regulation task the primary contrasts of interest are:

| Contrast Name | Weights |
|---|---|
| `Reappraise_vs_Look` | Reappraise − Look (or Look_Neg) |
| `Suppress_vs_Look` | Suppress − Look (or Look_Neg) |
| `Reappraise_vs_Suppress` | Reappraise − Suppress |

---

## GLM Workflow

```
fMRIPrep BOLD image
        │
        ▼
┌───────────────────┐
│  Load events TSV  │  onset, duration, trial_type
└────────┬──────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  make_first_level_design_matrix()        │
│  • HRF convolution (spm canonical)       │
│  • Cosine drift regressors               │
│  • Confound regressors (Module 09)       │
└────────┬─────────────────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Quality check DM   │  rank, VIF, condition coverage
└────────┬────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  FirstLevelModel.fit(bold, events) │
└────────┬───────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  compute_contrast(contrast_id)       │
│  → z_map (NIfTI)                     │
└────────┬─────────────────────────────┘
         │
         ▼
┌────────────────────────┐
│  Save z-maps (.nii.gz) │  → Input to your group-level analysis workflow
└────────────────────────┘
```

---

## References

- Friston KJ, et al. (1994). Statistical parametric maps in functional imaging: a general linear approach. *Human Brain Mapping*, 2(4), 189–210. https://doi.org/10.1002/hbm.460020402
- Mumford JA & Nichols TE. (2009). Simple group fMRI modeling and inference. *NeuroImage*, 47(4), 1469–1475. https://doi.org/10.1016/j.neuroimage.2009.05.034
- Poldrack RA, Mumford JA, & Nichols TE. (2011). *Handbook of Functional MRI Data Analysis*. Cambridge University Press.
- nilearn documentation — First-Level Model: https://nilearn.github.io/stable/glm/first_level_model.html
- Pernet CR. (2014). Misconceptions in the use of the General Linear Model applied to functional MRI: a tutorial for junior neuro-imagers. *Frontiers in Neuroscience*, 8, 1. https://doi.org/10.3389/fnins.2014.00001
