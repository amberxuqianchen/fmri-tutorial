# Module 04: Creating and Managing Stimuli/Events Files

## Overview

Task-based fMRI experiments record when stimuli were presented and what participants
did.  The BIDS standard captures this information in plain-text **events TSV files**
that live alongside each BOLD run.  This module shows you how to understand, create,
validate, and use these files so that your data are ready for first-level GLM
modelling.

---

## Learning Objectives

By the end of this module you will be able to:

1. Describe the BIDS events file format and its required/recommended columns
   (`onset`, `duration`, `trial_type`, `response_time`).
2. Read and explore existing events files with pandas.
3. Convert raw PsychoPy output (CSV) into BIDS-compliant TSV files.
4. Validate events files for timing consistency, overlap, and required columns.
5. Visualise trial structure as a timeline plot with matplotlib.
6. Compute per-condition summary statistics (mean RT, accuracy, trial counts).
7. Generate a contrast-specification JSON file ready for GLM software.

---

## Prerequisites

- **Module 00** completed — Python environment with all packages installed.
- **Module 01** completed — familiarity with BIDS structure and NIfTI files.
- **Module 02** completed — DICOM-to-BIDS conversion with HeuDiConv.
- **Module 03** completed — BIDS dataset passes validation.
- Basic pandas experience (reading CSVs, filtering DataFrames).

---

## Time Estimate

**2 hours** (including exercises).

---

## Contents

| File | Description |
|------|-------------|
| `04_events_files.ipynb` | Main tutorial notebook |
| `scripts/convert_psychopy_to_bids_events.py` | Convert PsychoPy CSV → BIDS TSV |
| `scripts/validate_events.py` | Validate an events TSV file |
| `scripts/create_condition_contrasts.py` | Generate GLM contrast JSON from events |

---

## Background: BIDS Events Files

Each task-fMRI BOLD run requires a companion file named according to the pattern:

```
<BIDS_root>/
  sub-<label>/
    ses-<label>/         (optional)
      func/
        sub-<label>_task-<label>_run-<index>_bold.nii.gz
        sub-<label>_task-<label>_run-<index>_events.tsv   ← this module
        sub-<label>_task-<label>_run-<index>_events.json  ← sidecar (optional)
```

### Required columns

| Column | Type | Description |
|--------|------|-------------|
| `onset` | float (s) | Onset time relative to start of the BOLD run |
| `duration` | float (s) | Duration of the event |
| `trial_type` | string | Label for the experimental condition |

### Recommended columns

| Column | Type | Description |
|--------|------|-------------|
| `response_time` | float (s) | Reaction time (NaN if no response) |
| `stim_file` | string | Stimulus filename shown to participant |
| `HED` | string | Hierarchical Event Descriptor tags |

---

## The Emotion Regulation Paradigm

The sample dataset uses an emotion-regulation task with three conditions:

| Condition | trial_type | Description |
|-----------|-----------|-------------|
| Reappraise | `Reappraise` | Cognitive reappraisal of negative image |
| Look | `Look` | Passive viewing of negative image |
| Suppress | `Suppress` | Expressive suppression during negative image |

Each trial follows: fixation cross → image + instruction → rating period.

---

## Running the Scripts

```bash
# Convert PsychoPy output to BIDS events TSV
python scripts/convert_psychopy_to_bids_events.py \
    --input /path/to/psychopy_output.csv \
    --output /path/to/sub-01_task-emotionreg_run-1_events.tsv \
    --task_name emotionreg \
    --run 1

# Validate an events file
python scripts/validate_events.py \
    --events_file /path/to/sub-01_task-emotionreg_run-1_events.tsv \
    --bold_json  /path/to/sub-01_task-emotionreg_run-1_bold.json

# Create GLM contrast specification
python scripts/create_condition_contrasts.py \
    --events_file /path/to/sub-01_task-emotionreg_run-1_events.tsv \
    --output /path/to/contrasts.json
```

---

## Further Reading

- [BIDS Specification — Task events](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/task-events.html)
- [PsychoPy documentation](https://www.psychopy.org/documentation.html)
- [nilearn GLM first-level models](https://nilearn.github.io/stable/glm/first_level_model.html)
- [HED (Hierarchical Event Descriptors)](https://www.hedtags.org/)
