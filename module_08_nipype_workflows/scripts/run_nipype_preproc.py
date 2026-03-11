"""Run the minimal Nipype preprocessing workflow for a single BIDS subject.

This script locates a subject's BOLD NIfTI file in a BIDS dataset, configures
the minimal preprocessing workflow (BET → MCFLIRT → IsotropicSmooth), and
executes it using the specified Nipype plugin.

The workflow is defined in ``utils/nipype_helpers.py`` and chains:

1. ``fsl.MeanImage``   — compute mean volume for skull stripping
2. ``fsl.BET``         — brain extraction (produces brain mask)
3. ``fsl.MCFLIRT``     — rigid-body motion correction
4. ``fsl.IsotropicSmooth`` — spatial smoothing with specified FWHM

Outputs are written to ``<output_dir>/nipype_work/<workflow_name>/``.

Requirements:
    - nipype >= 1.8
    - FSL >= 6.0 on $PATH
    - pybids (for BIDS layout)

Example usage::

    python run_nipype_preproc.py \\
        --bids_dir /data/bids \\
        --subject 01 \\
        --output_dir /data/nipype_output \\
        --fwhm 6.0 \\
        --plugin MultiProc \\
        --n_procs 4

    python run_nipype_preproc.py \\
        --bids_dir /data/bids \\
        --subject 01 \\
        --task rest \\
        --output_dir /data/nipype_output
"""

import argparse
import os
import sys


def parse_args():
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed argument values.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Run the minimal Nipype preprocessing workflow (BET → MCFLIRT → smooth) "
            "for one BIDS subject."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--bids_dir",
        required=True,
        metavar="PATH",
        help="Path to the root of the BIDS dataset.",
    )
    parser.add_argument(
        "--subject",
        required=True,
        metavar="LABEL",
        help="Subject label without the 'sub-' prefix (e.g. '01').",
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        metavar="PATH",
        help=(
            "Directory for workflow outputs. Nipype working files are written "
            "to <output_dir>/nipype_work/."
        ),
    )
    parser.add_argument(
        "--task",
        default=None,
        metavar="LABEL",
        help=(
            "Task label for BOLD file selection (e.g. 'rest'). "
            "If omitted, all tasks are considered and the first file found is used."
        ),
    )
    parser.add_argument(
        "--run",
        default=None,
        metavar="LABEL",
        help=(
            "Run label for BOLD file selection (e.g. '01'). "
            "If omitted, all runs are considered."
        ),
    )
    parser.add_argument(
        "--fwhm",
        type=float,
        default=6.0,
        metavar="MM",
        help="Full-width at half-maximum of the isotropic smoothing kernel (mm).",
    )
    parser.add_argument(
        "--plugin",
        default="Linear",
        choices=["Linear", "MultiProc", "SLURM", "SGE", "PBS"],
        help="Nipype execution plugin.",
    )
    parser.add_argument(
        "--n_procs",
        type=int,
        default=1,
        metavar="N",
        help="Number of parallel processes (MultiProc plugin only).",
    )
    parser.add_argument(
        "--workflow_name",
        default="minimal_preproc",
        metavar="NAME",
        help="Name for the Nipype workflow (used as the working subdirectory name).",
    )
    return parser.parse_args()


def find_bold_file(bids_dir, subject, task=None, run=None):
    """Locate the BOLD NIfTI for a subject using PyBIDS.

    Args:
        bids_dir (str): Root of the BIDS dataset.
        subject (str): Subject label (without 'sub-' prefix).
        task (str or None): Task label filter. If None, all tasks are searched.
        run (str or None): Run label filter. If None, all runs are searched.

    Returns:
        str: Absolute path to the first matching BOLD NIfTI file.

    Raises:
        ImportError: If pybids is not installed.
        FileNotFoundError: If no matching BOLD files are found.
        RuntimeError: If multiple BOLD files are found and no task/run is specified.
    """
    # Add repo root to sys.path so utils/ is importable when called from any cwd
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    from utils.bids_helpers import get_bids_layout, get_bold_files

    print(f"Indexing BIDS layout: {bids_dir}")
    layout = get_bids_layout(bids_dir)

    # If task is not provided, discover all tasks for this subject
    if task is None:
        tasks = layout.get_tasks(subject=subject)
        if not tasks:
            raise FileNotFoundError(
                f"No tasks found for subject '{subject}' in {bids_dir}"
            )
        if len(tasks) > 1:
            print(
                f"Multiple tasks found for sub-{subject}: {tasks}. "
                f"Using task='{tasks[0]}'. Specify --task to override."
            )
        task = tasks[0]

    bold_files = get_bold_files(layout, subject=subject, task=task, run=run)

    if len(bold_files) > 1:
        print(
            f"Multiple BOLD files found for sub-{subject}, task={task}: "
            f"{len(bold_files)} file(s). Using the first. "
            "Specify --run to select a specific run."
        )

    selected = bold_files[0]
    print(f"Selected BOLD file: {selected}")
    return selected


def main():
    """Entry point: parse arguments, find BOLD file, configure and run workflow."""
    args = parse_args()

    # Resolve absolute paths
    bids_dir = os.path.abspath(args.bids_dir)
    output_dir = os.path.abspath(args.output_dir)
    work_dir = os.path.join(output_dir, "nipype_work")
    os.makedirs(work_dir, exist_ok=True)

    print("=" * 60)
    print("Nipype Minimal Preprocessing Workflow")
    print("=" * 60)
    print(f"BIDS directory : {bids_dir}")
    print(f"Subject        : sub-{args.subject}")
    print(f"Task           : {args.task or '(auto-detect)'}")
    print(f"Run            : {args.run or '(all)'}")
    print(f"Output dir     : {output_dir}")
    print(f"Working dir    : {work_dir}")
    print(f"FWHM           : {args.fwhm} mm")
    print(f"Plugin         : {args.plugin}")
    if args.plugin == "MultiProc":
        print(f"n_procs        : {args.n_procs}")
    print("=" * 60)

    # Locate the BOLD file
    bold_file = find_bold_file(
        bids_dir=bids_dir,
        subject=args.subject,
        task=args.task,
        run=args.run,
    )

    # Import workflow utilities (after sys.path is set by find_bold_file)
    try:
        from utils.nipype_helpers import (
            create_minimal_preproc_workflow,
            run_workflow,
        )
    except ImportError as exc:
        print(f"ERROR: Could not import nipype_helpers: {exc}")
        print("Ensure nipype is installed: pip install nipype")
        sys.exit(1)

    # Build and configure the workflow
    wf = create_minimal_preproc_workflow(name=args.workflow_name)
    wf.base_dir = work_dir

    inputnode = wf.get_node("inputnode")
    inputnode.inputs.func = bold_file
    inputnode.inputs.fwhm = args.fwhm

    print(f"\nWorkflow '{wf.name}' configured.")
    print(f"Nodes: {[n.name for n in wf._graph.nodes()]}")

    # Run
    run_workflow(wf, plugin=args.plugin, n_procs=args.n_procs)

    print("\nDone.")
    print(f"Outputs in: {os.path.join(work_dir, args.workflow_name)}")


if __name__ == "__main__":
    main()
