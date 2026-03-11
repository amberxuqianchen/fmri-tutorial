"""BIDS helper utilities for querying datasets via PyBIDS."""

import os

import pandas as pd


def get_bids_layout(bids_dir):
    """Return a PyBIDS :class:`~bids.BIDSLayout` object for the given dataset.

    Args:
        bids_dir (str): Path to the root of a BIDS dataset.

    Returns:
        bids.BIDSLayout: Indexed BIDS layout.

    Raises:
        FileNotFoundError: If bids_dir does not exist.
        ImportError: If pybids is not installed.
    """
    try:
        from bids import BIDSLayout
    except ImportError as exc:
        raise ImportError(
            "pybids is required. Install it with: pip install pybids"
        ) from exc

    abs_dir = os.path.abspath(bids_dir)
    if not os.path.isdir(abs_dir):
        raise FileNotFoundError(f"BIDS directory not found: {abs_dir}")

    return BIDSLayout(abs_dir, validate=True)


def get_bold_files(layout, subject, task, run=None):
    """Get BOLD NIfTI files for a subject and task.

    Args:
        layout (bids.BIDSLayout): Indexed BIDS layout.
        subject (str): Subject label (without the ``sub-`` prefix).
        task (str): Task label.
        run (str or int, optional): Run label. If None, all runs are returned.

    Returns:
        list[str]: Absolute paths to matching BOLD files.

    Raises:
        ValueError: If no BOLD files are found for the given query.
    """
    query = dict(subject=subject, task=task, suffix="bold", extension=".nii.gz")
    if run is not None:
        query["run"] = run

    files = layout.get(return_type="file", **query)
    if not files:
        raise ValueError(
            f"No BOLD files found for subject='{subject}', task='{task}'"
            + (f", run='{run}'" if run is not None else "")
        )
    return sorted(files)


def get_events_files(layout, subject, task, run=None):
    """Get events TSV files for a subject and task.

    Args:
        layout (bids.BIDSLayout): Indexed BIDS layout.
        subject (str): Subject label (without the ``sub-`` prefix).
        task (str): Task label.
        run (str or int, optional): Run label. If None, all runs are returned.

    Returns:
        list[str]: Absolute paths to matching events files.

    Raises:
        ValueError: If no events files are found for the given query.
    """
    query = dict(subject=subject, task=task, suffix="events", extension=".tsv")
    if run is not None:
        query["run"] = run

    files = layout.get(return_type="file", **query)
    if not files:
        raise ValueError(
            f"No events files found for subject='{subject}', task='{task}'"
            + (f", run='{run}'" if run is not None else "")
        )
    return sorted(files)


def get_confounds_file(layout, subject, task, run, space="MNI152NLin2009cAsym"):
    """Get the fMRIPrep confounds TSV file for a subject, task, and run.

    This function queries the fMRIPrep derivatives directory that was passed
    to :func:`get_bids_layout` (or a layout that includes derivatives).

    Args:
        layout (bids.BIDSLayout): Indexed BIDS layout (should include derivatives).
        subject (str): Subject label (without the ``sub-`` prefix).
        task (str): Task label.
        run (str or int): Run label.
        space (str, optional): Template space. Defaults to ``'MNI152NLin2009cAsym'``.

    Returns:
        str: Absolute path to the confounds TSV file.

    Raises:
        ValueError: If the confounds file cannot be found.
    """
    files = layout.get(
        return_type="file",
        subject=subject,
        task=task,
        run=run,
        desc="confounds",
        suffix="timeseries",
        extension=".tsv",
    )
    if not files:
        # Fallback: search without space constraint
        files = layout.get(
            return_type="file",
            subject=subject,
            task=task,
            run=run,
            suffix="regressors",
            extension=".tsv",
        )
    if not files:
        raise ValueError(
            f"No confounds file found for subject='{subject}', task='{task}', run='{run}'"
        )
    return files[0]


def check_bids_completeness(bids_dir):
    """Check a BIDS dataset for common missing files and print a report.

    Checks that every subject with at least one BOLD file also has a
    corresponding events file.

    Args:
        bids_dir (str): Path to the root of a BIDS dataset.

    Returns:
        dict: Mapping of subject label to list of issues found (empty list = no issues).
    """
    layout = get_bids_layout(bids_dir)
    subjects = layout.get_subjects()
    report = {}

    print(f"BIDS Completeness Report — {os.path.abspath(bids_dir)}")
    print(f"{'=' * 60}")
    print(f"Total subjects: {len(subjects)}")

    for sub in sorted(subjects):
        issues = []
        bold_files = layout.get(subject=sub, suffix="bold", extension=".nii.gz")
        events_files = layout.get(subject=sub, suffix="events", extension=".tsv")

        if not bold_files:
            issues.append("No BOLD files found")
        else:
            bold_tasks = {f.get_entities().get("task") for f in bold_files}
            events_tasks = {f.get_entities().get("task") for f in events_files}
            missing_events = bold_tasks - events_tasks
            if missing_events:
                issues.append(f"Missing events for tasks: {missing_events}")

        # Check for anatomical T1w
        t1w = layout.get(subject=sub, suffix="T1w", extension=".nii.gz")
        if not t1w:
            issues.append("No T1w anatomical found")

        report[sub] = issues
        status = "OK" if not issues else "ISSUES"
        print(f"  sub-{sub}: {status}" + (f" — {'; '.join(issues)}" if issues else ""))

    print(f"{'=' * 60}")
    n_ok = sum(1 for v in report.values() if not v)
    print(f"Subjects without issues: {n_ok}/{len(subjects)}")
    return report


def load_events(events_file):
    """Load a BIDS events TSV file as a pandas DataFrame.

    Args:
        events_file (str): Path to a ``*_events.tsv`` file.

    Returns:
        pandas.DataFrame: Events table with at minimum ``onset``, ``duration``,
        and ``trial_type`` columns.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is missing required columns.
    """
    if not os.path.isfile(events_file):
        raise FileNotFoundError(f"Events file not found: {events_file}")

    df = pd.read_csv(events_file, sep="\t")

    required_cols = {"onset", "duration"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"Events file '{events_file}' is missing required columns: {missing}"
        )
    return df
