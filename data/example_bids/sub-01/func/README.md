# Functional NIfTI Files

The NIfTI image files (`sub-01_task-emotionreg_run-01_bold.nii.gz` and
`sub-01_task-emotionreg_run-02_bold.nii.gz`) are **not included** in this
repository because binary image files are large and require special generation.

## How to Obtain the NIfTI Files

### Option 1 – Generate from synthetic DICOMs

1. Generate synthetic DICOM files using the provided script:

   ```bash
   pip install pydicom numpy
   python data/example_dicoms/generate_synthetic_dicoms.py \
       --output /tmp/synthetic_dicoms
   ```

2. Convert the BOLD series to NIfTI with `dcm2niix`:

   ```bash
   pip install dcm2niix   # or: conda install -c conda-forge dcm2niix
   dcm2niix -o data/example_bids/sub-01/func/ /tmp/synthetic_dicoms/bold/
   ```

3. Rename outputs to BIDS convention:

   ```bash
   mv data/example_bids/sub-01/func/*.nii.gz \
      data/example_bids/sub-01/func/sub-01_task-emotionreg_run-01_bold.nii.gz
   # Repeat the generation with a different random seed for run-02
   ```

### Option 2 – Download from OpenNeuro

Download the real ds000108 dataset (see `data/download_openneuro.sh`) and copy
the desired subject's BOLD runs here.  Ensure file names match BIDS convention:

```
sub-01_task-emotionreg_run-01_bold.nii.gz
sub-01_task-emotionreg_run-02_bold.nii.gz
```

## Events Files

The timing/events files (`.tsv`) **are** included and ready to use:

- `sub-01_task-emotionreg_run-01_events.tsv`
- `sub-01_task-emotionreg_run-02_events.tsv`

Each file contains 60 trials (20 × Reappraise / Look / Suppress), 10 s each,
with ~15–20 s ITI, starting at 10 s.
