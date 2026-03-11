# Module 06: Inspecting MRIQC Reports and Making Exclusion Decisions

## Learning Objectives

By the end of this module, you will be able to:

1. Navigate and interpret MRIQC HTML reports for both T1w and BOLD data
2. Identify key image quality metrics (IQMs) and understand what they measure
3. Apply evidence-based thresholds to define exclusion criteria for T1w structural images
4. Apply evidence-based thresholds to define exclusion criteria for BOLD functional images
5. Document exclusion decisions in a reproducible, structured format
6. Add QC columns to a BIDS `participants.tsv` file
7. Calculate and interpret inter-rater reliability for visual QC

## Prerequisites

- Module 00: Environment Setup
- Module 01: fMRI Data and BIDS
- Module 02: HeuDiConv
- Module 03: BIDS Validation
- Module 04: Events Files
- Module 05: MRIQC

## Time Estimate

**1–2 hours** (depending on dataset size and familiarity with quality metrics)

## Overview

After running MRIQC (Module 05), you have HTML reports and group-level TSV files containing quantitative image quality metrics for every scan in your dataset. This module teaches you how to turn those outputs into concrete, documented exclusion decisions — a critical step before preprocessing.

Poor-quality data can introduce noise, bias statistical results, and reduce replication likelihood. Systematic QC with documented criteria ensures your exclusions are transparent, reproducible, and defensible in peer review.

## Module Contents

| File | Description |
|------|-------------|
| `06_qc_decisions.ipynb` | Main tutorial notebook |
| `scripts/make_exclusion_decisions.py` | Script to apply thresholds and generate exclusion list |
| `scripts/update_participants_qc.py` | Script to merge QC decisions into `participants.tsv` |

## Key Metrics Covered

### T1w Structural
- **CJV** (Coefficient of Joint Variation) — tissue contrast noise
- **CNR** (Contrast-to-Noise Ratio) — gray/white matter contrast
- **FWHM** (Full-Width at Half-Maximum) — spatial smoothness / motion blur
- **WM2MAX** — white matter signal intensity ratio
- **SNR** — signal-to-noise ratio

### BOLD Functional
- **tSNR** (temporal SNR) — signal stability over time
- **Mean FD** (Framewise Displacement) — average head motion
- **DVARS** — frame-to-frame signal change
- **% volumes flagged** — proportion of volumes exceeding motion threshold
- **FD outlier ratio** — fraction of high-motion frames

## Suggested Exclusion Thresholds

These are starting points based on published literature; adjust for your specific study:

| Metric | Exclusion if… | Reference |
|--------|--------------|-----------|
| CJV | > 0.75 | Esteban et al. 2017 |
| CNR | < 1.5 | Esteban et al. 2017 |
| Mean FD | > 0.5 mm | Power et al. 2012 |
| % FD > 0.5 mm | > 20% | Parkes et al. 2018 |
| tSNR | < 50 | Murphy et al. 2007 |

## References

- Esteban O, et al. (2017). MRIQC: Advancing the automatic prediction of image quality in MRI acquisition. *PLOS ONE*. https://doi.org/10.1371/journal.pone.0184661
- Power JD, et al. (2012). Spurious but systematic correlations in functional connectivity MRI networks arise from subject motion. *NeuroImage*. https://doi.org/10.1016/j.neuroimage.2011.10.018
- Parkes L, et al. (2018). An evaluation of the efficacy, reliability, and sensitivity of motion correction strategies for resting-state functional MRI. *NeuroImage*. https://doi.org/10.1016/j.neuroimage.2017.12.073
- Murphy K, et al. (2007). How long to scan? The relationship between fMRI temporal signal to noise ratio and necessary scan duration. *NeuroImage*. https://doi.org/10.1016/j.neuroimage.2006.11.026
