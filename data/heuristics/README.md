# HeudiConv Heuristic Files

This directory contains [HeudiConv](https://heudiconv.readthedocs.io/) heuristic
files that tell HeudiConv how to map DICOM series to BIDS output paths.

---

## What is a HeudiConv Heuristic?

When HeudiConv converts DICOM data to BIDS format it needs to know which DICOM
series corresponds to which BIDS file.  A **heuristic file** is a plain Python
module that provides this mapping via two required functions:

| Function | Purpose |
|----------|---------|
| `create_key(template, outtype, annotation_classes)` | Returns a BIDS key tuple used as a dictionary key in `infotodict`. |
| `infotodict(seqinfo)` | Receives a list of `SeqInfo` named-tuples (one per DICOM series) and returns a dict mapping BIDS keys → lists of DICOM series IDs. |

---

## Key `SeqInfo` Fields

Each `seqinfo` entry exposes, among others:

| Field | Description |
|-------|-------------|
| `series_id` | Internal series identifier |
| `series_description` | DICOM `(0008,103E) SeriesDescription` |
| `protocol_name` | DICOM `(0018,1030) ProtocolName` |
| `dim4` | Number of volumes (time points) |
| `TR` | Repetition time (seconds) |
| `TE` | Echo time (milliseconds) |
| `patient_id` | Patient / subject ID |
| `dcm_dir_name` | Source DICOM directory |

---

## Files in This Directory

| File | Dataset |
|------|---------|
| `emotion_regulation_heuristic.py` | OpenNeuro **ds000108** – Wager et al. emotion regulation dataset |
| `tom_task_heuristic.py` | OpenNeuro **ds000228** – Richardson et al. Theory of Mind dataset |

---

## Running HeudiConv with a Heuristic

```bash
# Install HeudiConv
pip install heudiconv

# Dry run (inspect what would be created)
heudiconv \
  --dicom_dir_template /path/to/dicoms/{subject}/*/*.dcm \
  --subjects sub-01 \
  --heuristic data/heuristics/emotion_regulation_heuristic.py \
  --outdir data/bids_output/ \
  --bids \
  --overwrite \
  --dry-run

# Full conversion
heudiconv \
  --dicom_dir_template /path/to/dicoms/{subject}/*/*.dcm \
  --subjects sub-01 \
  --heuristic data/heuristics/emotion_regulation_heuristic.py \
  --outdir data/bids_output/ \
  --bids \
  --overwrite
```

---

## Further Reading

- HeudiConv documentation: https://heudiconv.readthedocs.io/
- BIDS specification: https://bids-specification.readthedocs.io/
- Example heuristics gallery: https://github.com/nipy/heudiconv/tree/master/heudiconv/heuristics
