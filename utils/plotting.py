"""Visualisation utilities for fMRI data, design matrices, and motion parameters."""

import os

import numpy as np


def plot_bold_timeseries(nii_path, mask_path=None, n_voxels=100, save_path=None):
    """Plot the BOLD timeseries of randomly sampled voxels.

    Args:
        nii_path (str): Path to a 4-D BOLD NIfTI file.
        mask_path (str, optional): Path to a binary brain-mask NIfTI.  Only
            voxels inside the mask are sampled.  If None, all non-zero voxels
            in the mean volume are candidates.
        n_voxels (int, optional): Number of voxels to plot. Defaults to 100.
        save_path (str, optional): File path to save the figure.  If None,
            the figure is displayed interactively.

    Returns:
        matplotlib.figure.Figure: The generated figure.

    Raises:
        FileNotFoundError: If nii_path or mask_path does not exist.
        ImportError: If nibabel or matplotlib is not installed.
        ValueError: If the image is not 4-D.
    """
    try:
        import nibabel as nib
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "nibabel and matplotlib are required. "
            "Install them with: pip install nibabel matplotlib"
        ) from exc

    abs_nii = os.path.abspath(nii_path)
    if not os.path.isfile(abs_nii):
        raise FileNotFoundError(f"NIfTI file not found: {abs_nii}")

    img = nib.load(abs_nii)
    data = img.get_fdata()
    if data.ndim != 4:
        raise ValueError(f"Expected a 4-D NIfTI, got shape {data.shape}.")

    n_timepoints = data.shape[3]

    if mask_path is not None:
        abs_mask = os.path.abspath(mask_path)
        if not os.path.isfile(abs_mask):
            raise FileNotFoundError(f"Mask file not found: {abs_mask}")
        mask = nib.load(abs_mask).get_fdata().astype(bool)
    else:
        mask = np.mean(data, axis=3) > 0

    voxel_coords = np.array(np.where(mask)).T
    rng = np.random.default_rng(seed=42)
    chosen = rng.choice(
        len(voxel_coords),
        size=min(n_voxels, len(voxel_coords)),
        replace=False,
    )
    selected_coords = voxel_coords[chosen]

    timeseries = np.array([
        data[x, y, z, :] for x, y, z in selected_coords
    ])

    # Percent-signal-change normalisation
    means = timeseries.mean(axis=1, keepdims=True)
    means[means == 0] = 1
    timeseries_psc = (timeseries / means - 1) * 100

    fig, ax = plt.subplots(figsize=(14, 4))
    t = np.arange(n_timepoints) * img.header.get_zooms()[3]
    for ts in timeseries_psc:
        ax.plot(t, ts, lw=0.4, alpha=0.4, color="steelblue")

    mean_ts = timeseries_psc.mean(axis=0)
    ax.plot(t, mean_ts, color="black", lw=1.5, label="Mean")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Signal change (%)")
    ax.set_title(f"BOLD timeseries — {n_voxels} voxels (blue = individual, black = mean)")
    ax.legend(loc="upper right")
    fig.tight_layout()

    if save_path:
        _ensure_parent(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    else:
        plt.show()

    return fig


def plot_brain_mosaic(nii_path, cut_coords=None, display_mode="ortho", save_path=None):
    """Plot brain slices using nilearn's glass brain / stat map viewer.

    Args:
        nii_path (str): Path to a 3-D or 4-D NIfTI file.  For 4-D images the
            mean volume is computed and displayed.
        cut_coords (int or tuple, optional): Number of cuts or explicit MNI
            coordinates.  Passed directly to
            :func:`nilearn.plotting.plot_anat`.  If None, nilearn chooses
            automatically.
        display_mode (str, optional): Slice display mode, e.g. ``'ortho'``,
            ``'x'``, ``'y'``, ``'z'``, ``'mosaic'``.  Defaults to
            ``'ortho'``.
        save_path (str, optional): File path to save the figure.  If None,
            the figure is displayed interactively.

    Returns:
        nilearn.plotting.displays.BaseAxes: The nilearn display object.

    Raises:
        FileNotFoundError: If nii_path does not exist.
        ImportError: If nibabel or nilearn is not installed.
    """
    try:
        import nibabel as nib
        from nilearn import image, plotting
    except ImportError as exc:
        raise ImportError(
            "nibabel and nilearn are required. "
            "Install them with: pip install nibabel nilearn"
        ) from exc

    abs_nii = os.path.abspath(nii_path)
    if not os.path.isfile(abs_nii):
        raise FileNotFoundError(f"NIfTI file not found: {abs_nii}")

    img = nib.load(abs_nii)
    if img.ndim == 4:
        img = image.mean_img(img)

    display = plotting.plot_anat(
        img,
        cut_coords=cut_coords,
        display_mode=display_mode,
        title=os.path.basename(nii_path),
    )

    if save_path:
        _ensure_parent(save_path)
        display.savefig(save_path, dpi=150)
    else:
        plotting.show()

    return display


def plot_design_matrix(design_matrix_df, save_path=None):
    """Plot a GLM design matrix as a colour-coded heatmap.

    Args:
        design_matrix_df (pandas.DataFrame): Design matrix with timepoints as
            rows and regressors as columns, as returned by
            :func:`nilearn.glm.first_level.make_first_level_design_matrix`.
        save_path (str, optional): File path to save the figure.  If None,
            the figure is displayed interactively.

    Returns:
        matplotlib.figure.Figure: The generated figure.

    Raises:
        ImportError: If nilearn or matplotlib is not installed.
        TypeError: If design_matrix_df is not a pandas DataFrame.
    """
    try:
        import matplotlib.pyplot as plt
        import pandas as pd
        from nilearn.plotting import plot_design_matrix as _nilearn_pdm
    except ImportError as exc:
        raise ImportError(
            "nilearn and matplotlib are required. "
            "Install them with: pip install nilearn matplotlib"
        ) from exc

    if not isinstance(design_matrix_df, pd.DataFrame):
        raise TypeError(
            f"Expected a pandas DataFrame, got {type(design_matrix_df).__name__}."
        )

    fig, ax = plt.subplots(figsize=(10, 6))
    _nilearn_pdm(design_matrix_df, ax=ax)
    ax.set_title("GLM Design Matrix")
    fig.tight_layout()

    if save_path:
        _ensure_parent(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    else:
        plt.show()

    return fig


def plot_motion_params(motion_file, save_path=None):
    """Plot the six rigid-body motion parameters over time.

    Accepts FSL MCFLIRT ``.par`` files (space-separated, 6 columns: rotations
    in radians then translations in mm) and fMRIPrep confounds TSV files
    (columns named ``trans_x``, ``trans_y``, ``trans_z``, ``rot_x``,
    ``rot_y``, ``rot_z``).

    Args:
        motion_file (str): Path to a motion-parameter file (``.par`` or
            confounds ``.tsv``).
        save_path (str, optional): File path to save the figure.  If None,
            the figure is displayed interactively.

    Returns:
        matplotlib.figure.Figure: The generated figure.

    Raises:
        FileNotFoundError: If the motion file does not exist.
        ImportError: If matplotlib or pandas is not installed.
        ValueError: If the file format is not recognised.
    """
    try:
        import matplotlib.pyplot as plt
        import pandas as pd
    except ImportError as exc:
        raise ImportError(
            "matplotlib and pandas are required. "
            "Install them with: pip install matplotlib pandas"
        ) from exc

    abs_path = os.path.abspath(motion_file)
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"Motion file not found: {abs_path}")

    ext = os.path.splitext(abs_path)[1].lower()

    if ext == ".par":
        df = pd.read_csv(abs_path, sep=r"\s+", header=None)
        if df.shape[1] != 6:
            raise ValueError(
                f"Expected 6 columns in .par file, found {df.shape[1]}."
            )
        rot_cols = [0, 1, 2]
        trans_cols = [3, 4, 5]
        rot_labels = ["rot_x (rad)", "rot_y (rad)", "rot_z (rad)"]
        trans_labels = ["trans_x (mm)", "trans_y (mm)", "trans_z (mm)"]
        rot_data = df.iloc[:, rot_cols]
        trans_data = df.iloc[:, trans_cols]
    elif ext == ".tsv":
        df = pd.read_csv(abs_path, sep="\t")
        rot_cols = ["rot_x", "rot_y", "rot_z"]
        trans_cols = ["trans_x", "trans_y", "trans_z"]
        missing = [c for c in rot_cols + trans_cols if c not in df.columns]
        if missing:
            raise ValueError(
                f"Motion TSV is missing columns: {missing}"
            )
        rot_data = df[rot_cols]
        trans_data = df[trans_cols]
        rot_labels = rot_cols
        trans_labels = trans_cols
    else:
        raise ValueError(
            f"Unrecognised motion file extension '{ext}'. "
            "Supported: .par (FSL MCFLIRT) and .tsv (fMRIPrep confounds)."
        )

    fig, (ax_rot, ax_trans) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)

    colors = ["#e41a1c", "#377eb8", "#4daf4a"]
    for col, label, color in zip(rot_data.columns, rot_labels, colors):
        ax_rot.plot(rot_data[col].values, label=label, color=color, lw=1)
    ax_rot.set_ylabel("Rotation (rad)")
    ax_rot.legend(loc="upper right", fontsize=8)
    ax_rot.set_title("Head Motion Parameters")

    for col, label, color in zip(trans_data.columns, trans_labels, colors):
        ax_trans.plot(trans_data[col].values, label=label, color=color, lw=1)
    ax_trans.set_ylabel("Translation (mm)")
    ax_trans.set_xlabel("Volume")
    ax_trans.legend(loc="upper right", fontsize=8)

    fig.tight_layout()

    if save_path:
        _ensure_parent(save_path)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    else:
        plt.show()

    return fig


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _ensure_parent(path):
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
