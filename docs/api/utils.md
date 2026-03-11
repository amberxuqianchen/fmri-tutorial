# API Reference: `utils/`

This page documents all public functions in the `utils/` package.

---

## `utils.bids_helpers`

Utilities for querying BIDS datasets via PyBIDS.

### `get_bids_layout(bids_dir)`

Return a PyBIDS `BIDSLayout` object for the given dataset.

**Parameters:**
- `bids_dir` *(str)* — Path to the root of a BIDS dataset.

**Returns:** `bids.BIDSLayout`

**Raises:** `FileNotFoundError` if directory does not exist; `ImportError` if pybids is not installed.

---

### `get_bold_files(layout, subject, task, run=None)`

Get BOLD NIfTI files for a subject and task.

**Parameters:**
- `layout` *(BIDSLayout)* — Indexed BIDS layout.
- `subject` *(str)* — Subject label (without `sub-` prefix).
- `task` *(str)* — Task label.
- `run` *(str or int, optional)* — Run label. If `None`, all runs are returned.

**Returns:** `list[str]` — Sorted absolute paths to matching BOLD files.

**Raises:** `ValueError` if no BOLD files are found.

---

## `utils.dicom_helpers`

Utilities for inspecting DICOM files before conversion.

### `get_dicom_info(dicom_path)`

Extract key header fields from a DICOM file.

**Parameters:**
- `dicom_path` *(str)* — Path to a DICOM file.

**Returns:** `dict` — Dictionary with keys such as `PatientID`, `SeriesDescription`, `RepetitionTime`, `EchoTime`, `SliceThickness`, `Manufacturer`.

---

### `list_series(dicom_dir)`

List all unique series found in a DICOM directory.

**Parameters:**
- `dicom_dir` *(str)* — Path to a directory containing DICOM files.

**Returns:** `list[dict]` — One dict per series with `SeriesNumber`, `SeriesDescription`, `NumFiles`.

---

## `utils.mriqc_helpers`

Utilities for loading and summarising MRIQC outputs.

### `load_mriqc_group_report(mriqc_dir, modality="bold")`

Load the MRIQC group-level IQMs TSV for a given modality.

**Parameters:**
- `mriqc_dir` *(str)* — Path to the MRIQC derivatives directory.
- `modality` *(str)* — `"bold"` or `"T1w"`. Defaults to `"bold"`.

**Returns:** `pandas.DataFrame` — Group IQM table with one row per scan.

**Raises:** `FileNotFoundError` if the group TSV is not found.

---

### `flag_outliers(df, metrics=None, z_threshold=2.5)`

Flag scans with IQM values that are statistical outliers.

**Parameters:**
- `df` *(pd.DataFrame)* — IQM DataFrame as returned by `load_mriqc_group_report`.
- `metrics` *(list[str], optional)* — Columns to check. Defaults to a standard set (tSNR, DVARS, FD, etc.).
- `z_threshold` *(float)* — Z-score threshold for outlier flagging. Defaults to 2.5.

**Returns:** `pandas.DataFrame` — Copy of `df` with an added boolean `outlier` column.

---

### `plot_iqm_distributions(df, metrics=None, save_path=None)`

Plot histograms of selected IQMs across the group.

**Parameters:**
- `df` *(pd.DataFrame)* — IQM DataFrame.
- `metrics` *(list[str], optional)* — Columns to plot.
- `save_path` *(str, optional)* — File path to save figure. If `None`, displays interactively.

**Returns:** `matplotlib.figure.Figure`

---

## `utils.nipype_helpers`

Utilities for building and running Nipype workflows.

### `create_minimal_preproc_workflow(name="minimal_preproc")`

Create a minimal Nipype preprocessing workflow: BET → MCFLIRT → IsotropicSmooth.

**Parameters:**
- `name` *(str)* — Workflow name. Defaults to `"minimal_preproc"`.

**Returns:** `nipype.pipeline.engine.Workflow`

**inputnode fields:** `func` (4-D BOLD NIfTI path), `fwhm` (smoothing kernel in mm, default 6.0)

**outputnode fields:** `preprocessed_func`, `motion_params`, `brain_mask`

**Raises:** `ImportError` if nipype is not installed.

---

### `create_first_level_workflow(name="first_level")`

Create a first-level GLM workflow: SpecifyModel → Level1Design → FEATModel → FILMGLS.

**Parameters:**
- `name` *(str)* — Workflow name. Defaults to `"first_level"`.

**Returns:** `nipype.pipeline.engine.Workflow`

**inputnode fields:** `func`, `events`, `confounds`, `TR`

**outputnode fields:** `stats_dir`, `dof_file`

**Raises:** `ImportError` if nipype is not installed.

---

### `get_node_info(workflow)`

Print and return a summary of all nodes in a Nipype workflow.

**Parameters:**
- `workflow` *(nipype.pipeline.engine.Workflow)* — A configured workflow.

**Returns:** `list[dict]` — One dict per node with keys `name`, `interface`, `inputs`.

---

### `run_workflow(workflow, plugin="Linear", n_procs=1)`

Run a Nipype workflow with basic error handling.

**Parameters:**
- `workflow` *(nipype.pipeline.engine.Workflow)* — Workflow to execute.
- `plugin` *(str)* — Nipype plugin: `"Linear"`, `"MultiProc"`, or `"SLURM"`. Defaults to `"Linear"`.
- `n_procs` *(int)* — Parallel processes for `MultiProc`. Defaults to 1.

**Returns:** `None`

**Raises:** `RuntimeError` if the workflow fails.

---

## `utils.plotting`

Visualisation utilities for fMRI data, design matrices, and motion parameters.

### `plot_bold_timeseries(nii_path, mask_path=None, n_voxels=100, save_path=None)`

Plot the BOLD timeseries of randomly sampled voxels as percent signal change.

**Parameters:**
- `nii_path` *(str)* — Path to a 4-D BOLD NIfTI.
- `mask_path` *(str, optional)* — Brain mask NIfTI. If `None`, all non-zero voxels are candidates.
- `n_voxels` *(int)* — Number of voxels to sample. Defaults to 100.
- `save_path` *(str, optional)* — Save path. If `None`, displays interactively.

**Returns:** `matplotlib.figure.Figure`

---

### `plot_brain_mosaic(nii_path, cut_coords=None, display_mode="ortho", save_path=None)`

Plot brain slices using nilearn. For 4-D images, the mean volume is displayed.

**Parameters:**
- `nii_path` *(str)* — Path to a 3-D or 4-D NIfTI.
- `cut_coords` *(int or tuple, optional)* — Number of cuts or MNI coordinates.
- `display_mode` *(str)* — Slice mode: `"ortho"`, `"x"`, `"y"`, `"z"`, `"mosaic"`. Defaults to `"ortho"`.
- `save_path` *(str, optional)* — Save path.

**Returns:** `nilearn.plotting.displays.BaseAxes`

---

### `plot_design_matrix(design_matrix_df, save_path=None)`

Plot a GLM design matrix as a colour-coded heatmap.

**Parameters:**
- `design_matrix_df` *(pd.DataFrame)* — Design matrix with timepoints as rows and regressors as columns, as returned by `nilearn.glm.first_level.make_first_level_design_matrix`.
- `save_path` *(str, optional)* — Save path.

**Returns:** `matplotlib.figure.Figure`

---

### `plot_motion_params(motion_file, save_path=None)`

Plot the six rigid-body motion parameters over time.

Accepts FSL MCFLIRT `.par` files (6 columns: rotations in radians, then translations in mm) and fMRIPrep confounds `.tsv` files (columns `trans_x/y/z`, `rot_x/y/z`).

**Parameters:**
- `motion_file` *(str)* — Path to a `.par` or confounds `.tsv` file.
- `save_path` *(str, optional)* — Save path.

**Returns:** `matplotlib.figure.Figure`

---

## `utils.io_utils`

I/O utilities for common neuroimaging data formats.

### `load_tsv(tsv_path, **kwargs)`

Load a TSV file as a pandas DataFrame.

**Parameters:**
- `tsv_path` *(str)* — Path to the TSV file.
- `**kwargs` — Passed to `pandas.read_csv`.

**Returns:** `pandas.DataFrame`

**Raises:** `FileNotFoundError`; `ValueError` if the file cannot be parsed.

---

### `save_tsv(df, tsv_path)`

Save a pandas DataFrame as a TSV file (no index).

**Parameters:**
- `df` *(pd.DataFrame)* — DataFrame to save.
- `tsv_path` *(str)* — Destination path.

**Returns:** `str` — Absolute path to the saved file.

---

### `load_json(json_path)`

Load a JSON file and return its contents.

**Parameters:**
- `json_path` *(str)* — Path to the JSON file.

**Returns:** `dict` or `list`

---

### `save_json(data, json_path, indent=2)`

Save a Python object as a JSON file.

**Parameters:**
- `data` *(dict or list)* — Data to serialise.
- `json_path` *(str)* — Destination path.
- `indent` *(int)* — Indentation spaces. Defaults to 2.

**Returns:** `str` — Absolute path to the saved file.

---

### `ensure_dir(path)`

Create a directory and all intermediate parents if it does not exist.

**Parameters:**
- `path` *(str)* — Directory path to create.

**Returns:** `str` — Absolute path to the directory.

---

### `find_files(root_dir, pattern)`

Find files matching a glob pattern recursively under `root_dir`.

**Parameters:**
- `root_dir` *(str)* — Root directory to search.
- `pattern` *(str)* — Glob pattern, e.g. `"**/*.nii.gz"`.

**Returns:** `list[str]` — Sorted absolute paths.
