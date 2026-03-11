# Frequently Asked Questions

## Environment & Setup

### Which environment should I use?

Use the provided conda environment from `environments/`. Run:
```bash
conda env create -f environments/environment_full.yml
conda activate fmri-tutorial-full
```
This installs all required packages (nibabel, nilearn, nipype, pybids, pandas, matplotlib, etc.) at tested versions. Using a different environment may cause compatibility issues.

### What are the minimum system requirements?

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 8 GB | 16–32 GB |
| CPU cores | 4 | 8+ |
| Disk space | 50 GB | 200+ GB |
| Python | 3.9 | 3.10+ |

fMRIPrep (Module 07) is the most resource-intensive step and benefits greatly from more RAM and CPU cores.

### Do I need a GPU?

No. All tools in this tutorial run on CPU. Some steps (e.g., HD-BET brain extraction in newer fMRIPrep versions) can optionally use a GPU, but this is not required.

---

## BIDS & Data Organization

### Can I use this tutorial with non-emotion regulation tasks?

Yes. The BIDS conversion (Modules 01–03), QC (Modules 05–06), and preprocessing (Module 07) steps are fully task-agnostic. For the GLM modules (08–10), you will need to update the trial types and contrast definitions to match your task design. The `CONTRASTS` dictionary in `scripts/run_first_level_glm.py` is the main place to edit.

### How do I handle missing slice timing information?

If your BOLD JSON sidecar is missing `SliceTiming`, fMRIPrep will skip slice timing correction (STC). You have two options:
1. **Add SliceTiming manually** — edit the BOLD JSON sidecar with the correct values from your scanner protocol (e.g., ascending order for a typical EPI sequence).
2. **Skip STC** — pass `--ignore slicetiming` to fMRIPrep. This is acceptable for TR ≥ 2s; for shorter TRs (< 1.5s), STC matters more.

Slice order information is typically found in the DICOM headers or scanner documentation. HeuDiConv (Module 02) extracts this automatically when available.

### My BIDS dataset fails validation — what should I check?

Common causes:
- Missing `dataset_description.json` at the root
- Incorrect filename format (check sub-/ses-/task-/run- entities)
- Events TSV missing `onset` or `duration` columns
- JSON sidecar `TaskName` not matching the `task-` BIDS entity

Run `bids-validator /path/to/bids --verbose` and read each error carefully. The [BIDS Validator documentation](https://bids-standard.github.io/bids-validator/) lists all error codes.

---

## fMRIPrep

### My fMRIPrep run failed — what do I do?

1. **Check the log file** — look for lines starting with `[ERROR]` or `Traceback`.
2. **Check the work directory** — crash files are in `work/nipype/crash-*.txt` and contain the full Python traceback.
3. **Common issues:**
   - Out of memory → reduce `--mem-mb` and close other applications
   - FreeSurfer license missing → verify `-v /path/to/license.txt:/opt/freesurfer/license.txt:ro`
   - Docker storage → run `docker system prune` to free space
   - Corrupt NIfTI → re-run HeuDiConv on that subject
4. **Rerun safely** — fMRIPrep uses Nipype's caching. Re-running after fixing the issue resumes from the last successful node.

### How long does preprocessing take?

Typical times per subject on a modern laptop (8 cores, 16 GB RAM):

| Dataset type | Time |
|--------------|------|
| Single session, 1 run, no FreeSurfer surfaces | 30–60 min |
| Single session, 1 run, with FreeSurfer surfaces | 2–4 hours |
| Multiple runs or sessions | Add ~20 min per extra run |

On an HPC cluster with 16+ cores and fast storage, times can be cut by 50–70%.

### Can I run fMRIPrep without FreeSurfer surface reconstruction?

Yes. Add `--fs-no-reconall` to your fMRIPrep command. This skips cortical surface reconstruction and greatly reduces runtime. You lose surface-based outputs, but volumetric preprocessing (motion correction, MNI registration, confound estimation) is unaffected.

### What output spaces should I use?

For group-level volumetric analysis: `--output-spaces MNI152NLin2009cAsym:res-2`
For subject-native space: add `T1w`
For surface analysis: add `fsaverage5` or `fsnative`

For most social neuroscience analyses, `MNI152NLin2009cAsym:res-2` is standard.

---

## Quality Control

### How do I decide whether to exclude a subject's run?

Use these thresholds as a starting point (adjust for your field's norms):

| Metric | Exclude if |
|--------|-----------|
| Mean framewise displacement | > 0.5 mm |
| % volumes with FD > 0.5 mm | > 20% |
| MRIQC tSNR | < 40 (for 3T data) |
| MRIQC DVARS | > 1.5× group median |

Document all exclusions and report them in your methods section.

### What confound strategy should I use?

- **Minimal** (6 motion + FD): good baseline, least aggressive
- **Moderate** (+ global signal, WM, CSF, 6 aCompCor): recommended for most analyses
- **Aggressive** (+ 36-parameter expansion or full aCompCor): use for functional connectivity or when motion is a concern

See `module_09_fmriprep_outputs/scripts/extract_confounds.py` for implementation.

---

## GLM & Analysis

### What HRF model should I use?

For most analyses, use `hrf_model="spm"` (the canonical HRF commonly used in task fMRI). If you have reason to believe HRF timing varies across regions or subjects, consider `"spm + derivative"` which adds a temporal derivative regressor. Nilearn also supports `"glover"`; it is similar in practice but not identical to SPM's HRF.

### My design matrix has a rank deficiency warning — what does that mean?

This means one or more regressors are collinear (linearly dependent). Common causes:
- Conditions that never occur in this run
- Confound regressors that are constant (e.g., all zeros)
- Too many aCompCor components relative to the number of volumes

Fix by: removing empty conditions, checking for constant confound columns, or reducing the number of aCompCor components.
