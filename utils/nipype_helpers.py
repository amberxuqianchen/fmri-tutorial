"""Nipype workflow utilities for fMRI preprocessing and first-level analysis.

Note:
    FSL must be installed and its binaries must be on the system PATH for the
    workflows defined here to execute successfully.  The functions themselves
    only require nipype to be importable; FSL is invoked at *run* time.
"""

import os


def create_minimal_preproc_workflow(name="minimal_preproc"):
    """Create a minimal Nipype preprocessing workflow.

    The workflow chains three FSL nodes:

    1. **BET** – skull stripping (``nipype.interfaces.fsl.BET``)
    2. **MCFLIRT** – motion correction (``nipype.interfaces.fsl.MCFLIRT``)
    3. **IsotropicSmooth** – spatial smoothing
       (``nipype.interfaces.fsl.IsotropicSmooth``)

    Node connections::

        inputnode → bet → mcflirt → smooth → outputnode

    The ``inputnode`` exposes the field ``func`` (path to 4-D BOLD NIfTI).
    The ``outputnode`` exposes ``preprocessed_func`` and ``motion_params``.

    Args:
        name (str, optional): Name for the Nipype workflow. Defaults to
            ``'minimal_preproc'``.

    Returns:
        nipype.pipeline.engine.Workflow: Configured (but not yet run) workflow.

    Raises:
        ImportError: If nipype is not installed.

    Note:
        FSL must be installed and available on the system PATH.
    """
    try:
        import nipype.pipeline.engine as pe
        from nipype.interfaces import fsl
        from nipype.interfaces.utility import IdentityInterface
    except ImportError as exc:
        raise ImportError(
            "nipype is required. Install it with: pip install nipype"
        ) from exc

    wf = pe.Workflow(name=name)

    inputnode = pe.Node(
        IdentityInterface(fields=["func", "fwhm"]),
        name="inputnode",
    )
    inputnode.inputs.fwhm = 6.0  # default smoothing kernel (mm)

    # --- Skull stripping (mean volume first, then BET) ---
    meanvol = pe.Node(fsl.MeanImage(dimension="T"), name="meanvol")
    bet = pe.Node(fsl.BET(mask=True, functional=True), name="bet")

    # --- Motion correction ---
    mcflirt = pe.Node(
        fsl.MCFLIRT(mean_vol=True, save_plots=True, save_rms=True),
        name="mcflirt",
    )

    # --- Spatial smoothing ---
    smooth = pe.Node(fsl.IsotropicSmooth(), name="smooth")

    outputnode = pe.Node(
        IdentityInterface(fields=["preprocessed_func", "motion_params", "brain_mask"]),
        name="outputnode",
    )

    wf.connect([
        (inputnode, meanvol, [("func", "in_file")]),
        (meanvol,   bet,     [("out_file", "in_file")]),
        (inputnode, mcflirt, [("func", "in_file")]),
        (mcflirt,   smooth,  [("out_file", "in_file")]),
        (inputnode, smooth,  [("fwhm", "fwhm")]),
        (smooth,    outputnode, [("out_file", "preprocessed_func")]),
        (mcflirt,   outputnode, [("par_file", "motion_params")]),
        (bet,       outputnode, [("mask_file", "brain_mask")]),
    ])

    return wf


def create_first_level_workflow(name="first_level"):
    """Create a first-level GLM workflow using FSL FEAT (film_gls).

    The workflow includes:

    1. **SpecifyModel** – convert events to a design matrix
    2. **Level1Design** – generate FEAT design files
    3. **FEATModel** – create design matrix and contrast files
    4. **FILMGLS** – estimate the GLM

    The ``inputnode`` exposes:

    * ``func`` – preprocessed 4-D BOLD NIfTI
    * ``events`` – events TSV file path
    * ``confounds`` – confounds TSV file path (optional, may be ``None``)
    * ``TR`` – repetition time in seconds

    The ``outputnode`` exposes ``stats_dir`` (FILMGLS output directory).

    Args:
        name (str, optional): Name for the Nipype workflow. Defaults to
            ``'first_level'``.

    Returns:
        nipype.pipeline.engine.Workflow: Configured (but not yet run) workflow.

    Raises:
        ImportError: If nipype is not installed.

    Note:
        FSL must be installed and available on the system PATH.
    """
    try:
        import nipype.pipeline.engine as pe
        from nipype.algorithms.modelgen import SpecifyModel
        from nipype.interfaces import fsl
        from nipype.interfaces.utility import IdentityInterface
    except ImportError as exc:
        raise ImportError(
            "nipype is required. Install it with: pip install nipype"
        ) from exc

    wf = pe.Workflow(name=name)

    inputnode = pe.Node(
        IdentityInterface(fields=["func", "events", "confounds", "TR"]),
        name="inputnode",
    )

    specify_model = pe.Node(
        SpecifyModel(
            input_units="secs",
            high_pass_filter_cutoff=128,
            parameter_source="FSL",
        ),
        name="specify_model",
    )

    level1design = pe.Node(
        fsl.Level1Design(
            bases={"dgamma": {"derivs": True}},
            model_serial_correlations=True,
        ),
        name="level1design",
    )

    feat_model = pe.Node(fsl.FEATModel(), name="feat_model")

    filmgls = pe.Node(
        fsl.FILMGLS(smooth_autocorr=True, mask_size=5),
        name="filmgls",
    )

    outputnode = pe.Node(
        IdentityInterface(fields=["stats_dir", "dof_file"]),
        name="outputnode",
    )

    wf.connect([
        (inputnode,     specify_model,  [("func",    "functional_runs"),
                                         ("events",  "subject_info"),
                                         ("TR",      "time_repetition")]),
        (inputnode,     level1design,   [("TR",      "interscan_interval")]),
        (specify_model, level1design,   [("session_info", "session_info")]),
        (level1design,  feat_model,     [("fsf_files", "fsf_file"),
                                         ("ev_files",  "ev_files")]),
        (inputnode,     filmgls,        [("func",    "in_file")]),
        (feat_model,    filmgls,        [("design_file",   "design_file"),
                                         ("con_file",      "tcon_file")]),
        (filmgls,       outputnode,     [("stats_dir", "stats_dir"),
                                         ("dof_file",  "dof_file")]),
    ])

    return wf


def get_node_info(workflow):
    """Print a summary of all nodes in a Nipype workflow.

    Args:
        workflow (nipype.pipeline.engine.Workflow): A Nipype workflow object.

    Returns:
        list[dict]: One dict per node with keys ``name``, ``interface``, and
        ``inputs``.
    """
    try:
        import nipype.pipeline.engine as pe
    except ImportError as exc:
        raise ImportError(
            "nipype is required. Install it with: pip install nipype"
        ) from exc

    if not isinstance(workflow, pe.Workflow):
        raise TypeError(f"Expected a nipype Workflow, got {type(workflow).__name__}.")

    nodes = list(workflow._graph.nodes())
    info = []
    print(f"Workflow: {workflow.name}")
    print(f"{'=' * 50}")
    print(f"Total nodes: {len(nodes)}")
    print(f"{'-' * 50}")

    for node in nodes:
        interface_name = type(node.interface).__name__
        try:
            inputs = list(node.inputs.visible_traits().keys())
        except AttributeError:
            inputs = []
        entry = {"name": node.name, "interface": interface_name, "inputs": inputs}
        info.append(entry)
        print(f"  Node:      {node.name}")
        print(f"  Interface: {interface_name}")
        print(f"  Inputs:    {inputs}")
        print()

    return info


def run_workflow(workflow, plugin="Linear", n_procs=1):
    """Run a Nipype workflow with basic error handling.

    Args:
        workflow (nipype.pipeline.engine.Workflow): Workflow to execute.
        plugin (str, optional): Nipype execution plugin, e.g. ``'Linear'``,
            ``'MultiProc'``, or ``'SLURM'``. Defaults to ``'Linear'``.
        n_procs (int, optional): Number of parallel processes (only relevant
            for ``'MultiProc'`` plugin). Defaults to ``1``.

    Returns:
        None

    Raises:
        ImportError: If nipype is not installed.
        RuntimeError: If the workflow raises an exception during execution.

    Note:
        FSL must be installed and available on the system PATH.
    """
    try:
        import nipype.pipeline.engine as pe
    except ImportError as exc:
        raise ImportError(
            "nipype is required. Install it with: pip install nipype"
        ) from exc

    if not isinstance(workflow, pe.Workflow):
        raise TypeError(f"Expected a nipype Workflow, got {type(workflow).__name__}.")

    plugin_args = {}
    if plugin == "MultiProc":
        plugin_args["n_procs"] = n_procs

    print(f"Running workflow '{workflow.name}' with plugin='{plugin}' ...")
    try:
        workflow.run(plugin=plugin, plugin_args=plugin_args)
    except Exception as exc:
        raise RuntimeError(
            f"Workflow '{workflow.name}' failed: {exc}"
        ) from exc

    print(f"Workflow '{workflow.name}' completed successfully.")
