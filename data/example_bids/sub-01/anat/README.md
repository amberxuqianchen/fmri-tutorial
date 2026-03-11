# Anatomical NIfTI Files

The NIfTI image file `sub-01_T1w.nii.gz` is **not included** in this
repository because binary image files are large and require special generation.

## How to Obtain the NIfTI File

### Option 1 – Generate from synthetic DICOMs

1. Generate synthetic DICOM files using the provided script:

   ```bash
   pip install pydicom numpy
   python data/example_dicoms/generate_synthetic_dicoms.py \
       --output /tmp/synthetic_dicoms
   ```

2. Convert the T1w series to NIfTI with `dcm2niix`:

   ```bash
   pip install dcm2niix   # or: conda install -c conda-forge dcm2niix
   dcm2niix -o data/example_bids/sub-01/anat/ /tmp/synthetic_dicoms/T1w/
   ```

3. Rename the output to match BIDS convention if needed:

   ```bash
   mv data/example_bids/sub-01/anat/*.nii.gz \
      data/example_bids/sub-01/anat/sub-01_T1w.nii.gz
   ```

### Option 2 – Download from OpenNeuro

Download the real ds000108 dataset (see `data/download_openneuro.sh`) and copy
the desired subject's T1w image here.
