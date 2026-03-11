# Example DICOM Files

This directory contains **synthetic DICOM files** generated for tutorial
purposes. They are structurally valid DICOM objects (correct tag layout,
proper UIDs) but contain no real patient data and no meaningful image content.

---

## Purpose

Real DICOM data from scanner archives cannot be redistributed freely due to
privacy concerns. These synthetic files let you practise the DICOM → NIfTI
conversion steps (e.g. with `dcm2niix` or `heudiconv`) without needing access
to a real scanner.

---

## Generated Structure

Running `generate_synthetic_dicoms.py` (see below) produces:

```
<output_dir>/
├── T1w/
│   ├── 0001.dcm   # slice 1
│   ├── 0002.dcm   # slice 2
│   └── ...        # configurable number of slices
└── bold/
    ├── 0001.dcm   # volume 1, slice 1
    ├── 0002.dcm   # volume 1, slice 2
    └── ...        # (n_volumes × n_slices) files
```

Each DICOM file carries minimal but valid tags:
- **Patient / Study / Series UIDs** – generated with `pydicom.uid.generate_uid()`
- **Modality** – `MR`
- **Image type** – `ORIGINAL\PRIMARY\M` for T1w; `ORIGINAL\PRIMARY\EPI` for BOLD
- **Protocol / Series description** – human-readable names
- **Slice / Instance numbers** – correctly incremented
- **Pixel data** – small random array (no diagnostic value)

---

## Generating the Files

```bash
# Install dependency
pip install pydicom numpy

# Generate to the default output directory (./synthetic_dicoms/)
python data/example_dicoms/generate_synthetic_dicoms.py

# Specify a custom output directory
python data/example_dicoms/generate_synthetic_dicoms.py --output /tmp/my_dicoms

# Show all options
python data/example_dicoms/generate_synthetic_dicoms.py --help
```

---

## Converting to NIfTI

After generating the DICOMs you can convert them with `dcm2niix`:

```bash
# Install dcm2niix (conda example)
conda install -c conda-forge dcm2niix

# Convert T1w
dcm2niix -o ./nifti_out/ ./synthetic_dicoms/T1w/

# Convert BOLD
dcm2niix -o ./nifti_out/ ./synthetic_dicoms/bold/
```

---

## Licensing

These synthetic files are released under **CC0 1.0 Universal** – they are
placed in the public domain and may be used without restriction.
