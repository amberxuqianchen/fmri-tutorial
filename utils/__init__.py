"""fMRI Tutorial utility library.

This package provides helper modules for common neuroimaging workflows:

* :mod:`utils.bids_helpers`  – PyBIDS dataset queries and events loading
* :mod:`utils.dicom_helpers` – DICOM header inspection and protocol extraction
* :mod:`utils.mriqc_helpers` – MRIQC image quality metrics analysis
* :mod:`utils.nipype_helpers` – Nipype preprocessing and GLM workflows
* :mod:`utils.plotting`      – Brain visualisation and timeseries plotting
* :mod:`utils.io_utils`      – General-purpose I/O (TSV, JSON, file discovery)

Quick-start example::

    from utils import get_bids_layout, load_events, load_tsv
    layout = get_bids_layout('/path/to/bids')
    events = load_events('/path/to/sub-01_task-rest_events.tsv')
"""

from utils.bids_helpers import (
    check_bids_completeness,
    get_bids_layout,
    get_bold_files,
    get_confounds_file,
    get_events_files,
    load_events,
)
from utils.dicom_helpers import (
    extract_protocol_info,
    get_series_info,
    print_dicom_summary,
    read_dicom_header,
)
from utils.io_utils import (
    ensure_dir,
    find_files,
    load_json,
    load_tsv,
    save_json,
    save_tsv,
)
from utils.mriqc_helpers import (
    flag_outliers,
    generate_exclusion_report,
    load_group_iqms,
    plot_iqm_distributions,
)
from utils.nipype_helpers import (
    create_first_level_workflow,
    create_minimal_preproc_workflow,
    get_node_info,
    run_workflow,
)
from utils.plotting import (
    plot_bold_timeseries,
    plot_brain_mosaic,
    plot_design_matrix,
    plot_motion_params,
)

__all__ = [
    # bids_helpers
    "get_bids_layout",
    "get_bold_files",
    "get_events_files",
    "get_confounds_file",
    "check_bids_completeness",
    "load_events",
    # dicom_helpers
    "read_dicom_header",
    "get_series_info",
    "print_dicom_summary",
    "extract_protocol_info",
    # io_utils
    "load_tsv",
    "save_tsv",
    "load_json",
    "save_json",
    "ensure_dir",
    "find_files",
    # mriqc_helpers
    "load_group_iqms",
    "flag_outliers",
    "plot_iqm_distributions",
    "generate_exclusion_report",
    # nipype_helpers
    "create_minimal_preproc_workflow",
    "create_first_level_workflow",
    "get_node_info",
    "run_workflow",
    # plotting
    "plot_bold_timeseries",
    "plot_brain_mosaic",
    "plot_design_matrix",
    "plot_motion_params",
]
