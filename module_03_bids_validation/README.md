# Module 03: BIDS Validation with bids-validator and PyBIDS

## Overview

A BIDS dataset is only useful if it actually conforms to the specification.
This module covers two complementary validation approaches:

1. **bids-validator** – the official Node.js command-line tool that checks
   structural and metadata compliance against the full BIDS specification.
2. **PyBIDS** – a Python library that provides programmatic access to BIDS
   datasets, enabling custom completeness checks and flexible queries.

---

## Learning Objectives

By completing this module you will be able to:

1. Describe why validation is a critical step before sharing or analysing a
   BIDS dataset.
2. Run `bids-validator` from the command line, interpret its error and warning
   output, and distinguish fixable issues from acceptable deviations.
3. Use PyBIDS to load a dataset and run programmatic queries (e.g. list all
   BOLD files, filter by task or subject, check event file completeness).
4. Generate a machine-readable validation report (JSON) and parse it with Python.
5. Identify and resolve the most common BIDS validation errors produced during
   a HeudiConv conversion.

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Module 00 – Environment Setup | Conda environment `fmri-tutorial` must be active |
| Module 01 – fMRI Data and BIDS | Familiarity with BIDS directory layout |
| Module 02 – HeudiConv | A converted BIDS dataset to validate |
| Node.js ≥ 14 + npm | Required for bids-validator; see install note below |
| bids-validator ≥ 1.14 | `npm install -g bids-validator` |
| PyBIDS ≥ 0.16 | `pip install pybids` (included in tutorial environment) |

> **Install bids-validator:**
> ```bash
> # macOS / Linux — requires Node.js
> npm install -g bids-validator
> # or via Docker (no Node.js needed)
> docker run -ti --rm -v /path/to/bids:/data:ro bids/validator /data
> ```

---

## Estimated Time

**1–2 hours**

---

## Contents

```
module_03_bids_validation/
├── README.md                          ← this file
├── 03_bids_validation.ipynb           ← main tutorial notebook
└── scripts/
    ├── validate_dataset.sh            ← run bids-validator on a directory
    └── query_bids_pybids.py           ← demonstrate PyBIDS queries
```

### Notebook: `03_bids_validation.ipynb`

| Section | Description |
|---------|-------------|
| 1. Why Validate? | Consequences of non-compliant datasets |
| 2. bids-validator CLI | Running and interpreting the validator |
| 3. Validator Output | Errors vs. warnings; common fixes |
| 4. PyBIDS Basics | Loading a dataset, BIDSLayout object |
| 5. Querying BOLD Files | `layout.get()` with filters |
| 6. Checking Completeness | Detecting missing files across subjects |

### Scripts

| Script | Purpose |
|--------|---------|
| `validate_dataset.sh` | Shell wrapper; checks for `bids-validator`, saves report |
| `query_bids_pybids.py` | Dataset summary and example PyBIDS queries |

---

## Expected Outputs

Running `validate_dataset.sh` produces:

```
bids_validation_report/
├── bids_validator_output.txt    ← human-readable console output
└── bids_validator_report.json  ← machine-readable report (with --json flag)
```

Running `query_bids_pybids.py` prints to stdout:

```
Dataset summary
===============
  Path            : /path/to/bids
  Subjects (n=20) : sub-01, sub-02, …
  Sessions        : n/a
  Tasks           : rest, nback
  BOLD runs       : 60
  T1w scans       : 20
  Field maps      : 40
```

---

## Quick Start

```bash
# 1. Activate environment
conda activate fmri-tutorial

# 2. Validate with bids-validator
bash scripts/validate_dataset.sh /path/to/bids_dataset

# 3. Validate with JSON report
bash scripts/validate_dataset.sh /path/to/bids_dataset --json

# 4. Query dataset with PyBIDS
python scripts/query_bids_pybids.py --bids_dir /path/to/bids_dataset

# 5. Filter by subject and task
python scripts/query_bids_pybids.py \
  --bids_dir /path/to/bids_dataset \
  --subject sub-01 \
  --task rest
```

---

## Common Validation Errors and Fixes

| Error code | Cause | Fix |
|------------|-------|-----|
| `NOT_INCLUDED` | File not recognised by BIDS | Add to `.bidsignore` or rename |
| `MISSING_SESSION` | Some subjects have session dirs, some don't | Use sessions consistently |
| `EVENTS_TSV_MISSING` | `_events.tsv` absent for a task run | Create events file or add task to `.bidsignore` |
| `BOLD_NOT_4D` | NIfTI has wrong dimensionality | Re-run dcm2niix / HeudiConv |
| `INCONSISTENT_PARAMETERS` | TR/TE differs across runs | Check DICOM metadata; add `IntendedFor` if field map |
| `INVALID_JSON` | Malformed sidecar `.json` | Validate JSON syntax with `python -m json.tool` |

---

## Further Reading

- [bids-validator GitHub](https://github.com/bids-standard/bids-validator)
- [PyBIDS documentation](https://bids-standard.github.io/pybids/)
- [BIDS specification](https://bids-specification.readthedocs.io/)
- [OpenNeuro validator web app](https://bids-standard.github.io/bids-validator/)
