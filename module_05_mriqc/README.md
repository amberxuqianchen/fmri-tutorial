# Module 05: Quality Control with MRIQC

## Overview

Garbage in, garbage out.  Before spending hours running a full fMRI preprocessing
pipeline you should check whether your raw data are fit for analysis.  **MRIQC**
(MRI Quality Control) is a BIDS App that automatically extracts dozens of
**Image Quality Metrics (IQMs)** from both T1-weighted structural and BOLD
functional scans and produces visual HTML reports that make problems easy to spot.

---

## Learning Objectives

By the end of this module you will be able to:

1. Explain what MRIQC does and why quality control is essential before
   preprocessing.
2. Describe the key structural IQMs: CNR, SNR, CJV, EFC, FBER, WM2MAX.
3. Describe the key functional IQMs: tSNR, DVARS, FD, AOR, AQI, GSR.
4. Run MRIQC at the **participant level** using Docker or Singularity.
5. Run MRIQC at the **group level** to aggregate IQMs across subjects.
6. Navigate MRIQC HTML reports and identify common artefacts.
7. Load the group IQM TSV with pandas and flag statistical outliers.
8. Visualise IQM distributions and produce an exclusion candidate list.

---

## Prerequisites

- **Module 00** completed — Python environment installed.
- **Module 01** completed — familiarity with BIDS and NIfTI files.
- **Module 02** completed — BIDS dataset created with HeuDiConv.
- **Module 03** completed — dataset passes BIDS Validator.
- **Module 04** completed — events files are in place.
- **Docker** (≥ 20.10) *or* **Singularity / Apptainer** (≥ 3.7) installed.
- At least **8 GB RAM** and **4 CPU cores** available for MRIQC.

> **Cloud / HPC note:**  On shared HPC systems Docker is often unavailable.
> Use the Singularity scripts provided in `scripts/`.

---

## Time Estimate

**2 – 4 hours** depending on data size and hardware.

| Step | Typical time |
|------|-------------|
| MRIQC participant-level (1 subject, 1 session) | 20 – 40 min |
| MRIQC group-level aggregation | < 2 min |
| Reviewing HTML reports | 15 – 30 min |
| Notebook analysis | 30 – 45 min |

---

## Contents

| File | Description |
|------|-------------|
| `05_mriqc.ipynb` | Main tutorial notebook |
| `scripts/run_mriqc_single_subject.sh` | Run participant-level MRIQC (Docker or Singularity) |
| `scripts/run_mriqc_group.sh` | Run group-level MRIQC aggregation |
| `scripts/analyze_mriqc_output.py` | Load IQMs, flag outliers, create plots |

---

## Quick Start

```bash
# Participant-level (Docker)
bash scripts/run_mriqc_single_subject.sh \
    --docker \
    /data/bids_dataset \
    /data/mriqc_output \
    01

# Group-level (after all participants are done)
bash scripts/run_mriqc_group.sh \
    /data/bids_dataset \
    /data/mriqc_output

# Analyze outputs in Python
python scripts/analyze_mriqc_output.py \
    --mriqc_dir /data/mriqc_output \
    --output_dir /data/mriqc_output/qc_figures
```

---

## MRIQC Output Structure

```
mriqc_output/
  sub-01/
    anat/
      sub-01_T1w.html          ← individual report
    func/
      sub-01_task-emotionreg_run-1_bold.html
  group_T1w.tsv                ← all T1w IQMs (one row per subject)
  group_bold.tsv               ← all BOLD IQMs (one row per run)
  group_T1w.html               ← group visual report
  group_bold.html
  logs/
```

---

## Key Image Quality Metrics

### Structural (T1w)

| IQM | Full name | Good value |
|-----|-----------|------------|
| `cnr` | Contrast-to-Noise Ratio | Higher is better |
| `snr_wm` | SNR in white matter | Higher is better |
| `cjv` | Coefficient of Joint Variation | Lower is better |
| `efc` | Entropy Focus Criterion | Lower is better |
| `fber` | Foreground-Background Energy Ratio | Higher is better |

### Functional (BOLD)

| IQM | Full name | Good value |
|-----|-----------|------------|
| `tsnr` | Temporal SNR | Higher is better (≥ 40) |
| `dvars_nstd` | DVARS (normalised) | Lower is better |
| `fd_mean` | Mean Framewise Displacement | < 0.5 mm |
| `aor` | AFNI Outlier Ratio | Lower is better |
| `aqi` | AFNI Quality Index | Lower is better |
| `gsr_x` / `gsr_y` | Ghost-to-Signal Ratio | Lower is better |

---

## Further Reading

- [MRIQC documentation](https://mriqc.readthedocs.io/)
- [MRIQC paper (Esteban et al., 2017)](https://doi.org/10.1371/journal.pone.0184661)
- [BIDS Apps](https://bids-apps.neuroimaging.io/)
- [fMRIPrep documentation](https://fmriprep.org/) — the next preprocessing step
- [The IQM reference](https://mriqc.readthedocs.io/en/latest/measures.html)
