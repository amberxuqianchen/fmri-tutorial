# Data Directory

This directory contains example datasets, BIDS-formatted data, DICOM examples,
and HeudiConv heuristic files used throughout the fMRI tutorial.

---

## Directory Structure

```
data/
├── README.md                          # This file
├── download_openneuro.sh              # Script to download real OpenNeuro datasets
├── example_bids/                      # Synthetic BIDS-formatted dataset
│   ├── dataset_description.json
│   ├── participants.tsv
│   ├── participants.json
│   ├── task-emotionreg_bold.json
│   └── sub-01/
│       ├── anat/
│       │   ├── README.md
│       │   └── sub-01_T1w.json
│       └── func/
│           ├── README.md
│           ├── sub-01_task-emotionreg_run-01_bold.json
│           ├── sub-01_task-emotionreg_run-01_events.tsv
│           └── sub-01_task-emotionreg_run-02_events.tsv
├── example_dicoms/                    # Synthetic DICOM files and generator script
│   ├── README.md
│   └── generate_synthetic_dicoms.py
└── heuristics/                        # HeudiConv heuristic files
    ├── README.md
    ├── emotion_regulation_heuristic.py
    └── tom_task_heuristic.py
```

---

## Synthetic Emotion Regulation Dataset

The `example_bids/` subdirectory contains a minimal synthetic dataset modelled
after a standard blocked emotion-regulation fMRI paradigm (see Ochsner et al.,
2002 and related designs).

**Participants:** Two synthetic participants (`sub-01`, `sub-02`).

**Task (`task-emotionreg`):** Participants view negative images and are cued to
*Reappraise* (cognitively reframe), *Suppress* (inhibit expression), or simply
*Look* at the images. Each trial lasts 10 s with a ~15–20 s inter-trial
interval (ITI).

**Scans:** T1w structural and 2 BOLD functional runs per participant.
NIfTI image files are **not** included; see the placeholder READMEs in the
`anat/` and `func/` subdirectories for how to generate or obtain them.

---

## Downloading Real OpenNeuro Datasets

Use the provided `download_openneuro.sh` script to download publicly available
datasets from [OpenNeuro](https://openneuro.org) via the AWS CLI:

```bash
# Download both recommended datasets to ./openneuro_data/
bash data/download_openneuro.sh -o data/openneuro_data

# Download only ds000108 (Emotion Regulation)
bash data/download_openneuro.sh -d ds000108 -o data/openneuro_data

# Show help
bash data/download_openneuro.sh -h
```

### Recommended datasets

| Accession | Name | Reference |
|-----------|------|-----------|
| [ds000108](https://openneuro.org/datasets/ds000108) | Emotion Regulation | Wager et al. (2008) |
| [ds000228](https://openneuro.org/datasets/ds000228) | Theory of Mind (children & adults) | Richardson et al. (2018) |

**Requirements:** [AWS CLI](https://aws.amazon.com/cli/) must be installed
(`pip install awscli` or your OS package manager). No AWS account is needed;
the S3 bucket is public and anonymous access is used automatically.

---

## Licensing Notes

| Resource | License |
|----------|---------|
| Synthetic tutorial data in `example_bids/` and `example_dicoms/` | [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) – no restrictions |
| OpenNeuro ds000108 | [PPDL](https://opendatacommons.org/licenses/pddl/1-0/) – see dataset page |
| OpenNeuro ds000228 | [CC0](https://creativecommons.org/publicdomain/zero/1.0/) – see dataset page |

When using real OpenNeuro datasets in publications, please cite the original
study and acknowledge OpenNeuro (Markiewicz et al., 2021,
*eLife* 10:e71774, https://doi.org/10.7554/eLife.71774).
