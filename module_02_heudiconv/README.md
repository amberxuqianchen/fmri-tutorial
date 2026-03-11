# Module 02: DICOM-to-BIDS Conversion with HeudiConv

## Overview

This module walks you through converting raw DICOM files from an MRI scanner into
[BIDS-compliant](https://bids-specification.readthedocs.io/) NIfTI datasets using
[HeudiConv](https://heudiconv.readthedocs.io/). By the end of the module you will
be able to run a reproducible, scriptable conversion pipeline on single subjects and
entire study cohorts.

---

## Learning Objectives

By completing this module you will be able to:

1. Explain the role HeudiConv plays in a BIDS data-management pipeline and how it
   differs from a simple DICOM-to-NIfTI converter.
2. Inspect a DICOM directory and use HeudiConv's **dry-run** mode to discover all
   series without converting any data.
3. Write and customise a **heuristic file** that maps DICOM series descriptions to
   BIDS filenames and data types.
4. Execute a full HeudiConv conversion for a single subject and verify the resulting
   BIDS structure.
5. Scale the conversion to a full cohort using the provided batch scripts and
   optional parallel execution.

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Module 00 – Environment Setup | Conda environment `fmri-tutorial` must be active |
| Module 01 – fMRI Data and BIDS | Familiarity with BIDS directory layout |
| HeudiConv ≥ 0.13 | `pip install heudiconv[all]` or see `environments/` |
| dcm2niix | Bundled with HeudiConv; installed automatically |
| Python ≥ 3.9 | Available inside the tutorial conda environment |

---

## Estimated Time

**2–3 hours** (including exercises)

---

## Contents

```
module_02_heudiconv/
├── README.md                              ← this file
├── 02_heudiconv_conversion.ipynb          ← main tutorial notebook
└── scripts/
    ├── run_heudiconv_single_subject.sh    ← convert one subject
    ├── run_heudiconv_batch.sh             ← convert a full cohort
    └── check_heudiconv_output.py          ← validate conversion output
```

### Notebook: `02_heudiconv_conversion.ipynb`

| Section | Description |
|---------|-------------|
| 1. Introduction | What HeudiConv does and why |
| 2. DICOM Directory Structure | Typical scanner output layout |
| 3. Dry-run Mode | Discovering series without converting |
| 4. The Heuristic File | Mapping series to BIDS names |
| 5. Full Conversion | Running HeudiConv end-to-end |
| 6. Verifying BIDS Output | Checking files and metadata |

### Scripts

| Script | Purpose |
|--------|---------|
| `run_heudiconv_single_subject.sh` | Wrapper for a single subject; validates inputs and logs timing |
| `run_heudiconv_batch.sh` | Iterates over a subject list; supports `--parallel` flag |
| `check_heudiconv_output.py` | Reports missing or unexpected BIDS files after conversion |

---

## Expected Outputs

After successfully completing this module, your BIDS dataset directory should
contain the following for each converted subject (using `sub-01` as an example):

```
bids_dataset/
├── dataset_description.json
├── participants.tsv
├── participants.json
├── .bidsignore
├── sub-01/
│   ├── anat/
│   │   ├── sub-01_T1w.nii.gz
│   │   └── sub-01_T1w.json
│   ├── func/
│   │   ├── sub-01_task-rest_bold.nii.gz
│   │   ├── sub-01_task-rest_bold.json
│   │   └── sub-01_task-rest_events.tsv   ← add manually if needed
│   └── fmap/
│       ├── sub-01_magnitude1.nii.gz
│       ├── sub-01_magnitude2.nii.gz
│       ├── sub-01_phasediff.nii.gz
│       └── sub-01_phasediff.json
└── sourcedata/
    └── sub-01/
        └── <original DICOM files>
```

> **Note:** Exact output depends on the sequences acquired. Use
> `check_heudiconv_output.py` to validate your conversion against an expected
> file list.

---

## Quick Start

```bash
# 1. Activate environment
conda activate fmri-tutorial

# 2. Dry run — discover series
heudiconv \
  --dicom_dir_template "dicoms/{subject}/*/*.dcm" \
  --subjects sub-01 \
  --heuristic convertall \
  --outdir /tmp/heudiconv_test \
  --bids \
  --datalad \
  --dry_run

# 3. Convert a single subject with the helper script
bash scripts/run_heudiconv_single_subject.sh \
  sub-01 \
  /path/to/dicoms/sub-01 \
  /path/to/bids_output \
  ../data/heuristics/emotion_regulation_heuristic.py

# 4. Validate output
python scripts/check_heudiconv_output.py \
  --bids_dir /path/to/bids_output \
  --expected_subjects sub-01 sub-02
```

---

## Further Reading

- [HeudiConv documentation](https://heudiconv.readthedocs.io/)
- [BIDS specification](https://bids-specification.readthedocs.io/)
- [dcm2niix](https://github.com/rordenlab/dcm2niix)
- [ReproIn heuristic](https://github.com/ReproNim/reproin) — a community-maintained
  heuristic for common scanner protocols
