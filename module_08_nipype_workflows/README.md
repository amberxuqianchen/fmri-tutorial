# Module 08: Building Custom Nipype Workflows

## Learning Objectives

By the end of this module, you will be able to:

1. Explain Nipype's node/workflow model and how it differs from scripting pipelines
2. Create `Node` and `Workflow` objects and configure interface inputs
3. Connect nodes using `wf.connect()` to build directed acyclic processing graphs
4. Build a minimal preprocessing workflow chaining BET → MCFLIRT → IsotropicSmooth
5. Use `get_node_info()` to introspect workflow nodes and their interfaces
6. Visualize workflow graphs with `workflow.write_graph()` and interpret the output
7. Run workflows with the `Linear` (serial) and `MultiProc` (parallel) plugins

## Prerequisites

- Module 00: Environment Setup
- Module 01: fMRI Data and BIDS
- Module 02: HeuDiConv
- Module 03: BIDS Validation
- Module 04: Events Files
- Module 05: MRIQC
- Module 06: QC Decisions
- Module 07: Preprocessing with fMRIPrep
- **nipype** (≥ 1.8): `pip install nipype`
- **FSL** (≥ 6.0) installed and on `$PATH` (required at run time)
- **graphviz** (optional, for workflow visualization): `conda install graphviz`

## Time Estimate

**~3 hours** — 1 hour reading and running the notebook, 1 hour building and running the preprocessing workflow, 1 hour adapting scripts to your own data.

## Overview

Nipype (Neuroimaging in Python — Pipelines and Interfaces) is a Python framework that wraps command-line neuroimaging tools (FSL, FreeSurfer, SPM, AFNI, ANTs) in a common interface and chains them into reproducible, parallelisable workflows. Rather than writing `subprocess.run(...)` calls manually, you define **nodes** (one tool each) and **connections** (data flow between tools). Nipype then tracks which outputs exist, skips up-to-date nodes, and can distribute work across cores or HPC clusters.

This module introduces Nipype's core abstractions, walks through building and running a minimal FSL-based preprocessing workflow, and shows how the same pattern extends to a first-level GLM workflow. The helper functions in `utils/nipype_helpers.py` encapsulate the workflow definitions so you can focus on understanding the structure rather than boilerplate.

## Module Contents

| File | Description |
|------|-------------|
| `08_nipype_workflows.ipynb` | Interactive notebook: concepts, workflow construction, visualization, and running |
| `scripts/run_nipype_preproc.py` | CLI script: run the minimal preprocessing workflow on one BIDS subject |
| `scripts/run_nipype_batch.sh` | Shell script: batch preprocessing across multiple subjects |
| `README.md` | This file |

## Nipype Core Concepts

### Node

A `Node` wraps a single neuroimaging interface (e.g., `fsl.BET`) and represents one processing step. You specify required and optional inputs as Python attributes before connecting the node into a workflow.

```python
import nipype.pipeline.engine as pe
from nipype.interfaces import fsl

bet = pe.Node(fsl.BET(frac=0.5, mask=True), name="bet")
bet.inputs.in_file = "/path/to/T1w.nii.gz"
```

### MapNode

A `MapNode` is like `Node` but applies the same interface to a **list** of inputs in parallel — one job per input. Useful for running BET on every subject's structural scan simultaneously.

```python
bet_many = pe.MapNode(fsl.BET(mask=True), iterfield=["in_file"], name="bet_many")
bet_many.inputs.in_file = ["/sub-01/T1w.nii.gz", "/sub-02/T1w.nii.gz"]
```

### Workflow

A `Workflow` is a directed acyclic graph (DAG) of nodes. It manages execution order, working directories, and output caching.

```python
wf = pe.Workflow(name="my_pipeline")
wf.base_dir = "/tmp/nipype_work"
```

### connect()

`wf.connect()` wires an output field of one node to an input field of another. Nipype infers execution order from these connections.

```python
wf.connect([
    (node_a, node_b, [("out_file", "in_file")]),
    (node_b, node_c, [("out_file", "in_file")]),
])
```

### IdentityInterface

`IdentityInterface` is a pass-through node used as `inputnode` and `outputnode` to give workflows clean, named entry and exit points. It does no computation — it simply holds named fields.

```python
from nipype.interfaces.utility import IdentityInterface

inputnode = pe.Node(
    IdentityInterface(fields=["func", "fwhm"]),
    name="inputnode",
)
```

### Execution Plugins

| Plugin | Use case |
|--------|----------|
| `Linear` | Serial execution on a single CPU (good for debugging) |
| `MultiProc` | Parallel execution across local CPU cores |
| `SLURM` | Distribute jobs to a SLURM HPC scheduler |
| `SGE` | Sun Grid Engine cluster |
| `PBS` | PBS/Torque cluster |

```python
wf.run(plugin="MultiProc", plugin_args={"n_procs": 8})
```

### Working Directories and Crash Files

Nipype stores all intermediate files under `workflow.base_dir/<workflow_name>/`. If a node fails, a crash file (`.pklz`) is saved in the working directory. You can re-run the workflow after fixing the problem and Nipype will skip already-completed nodes (hash-based caching).

```
<base_dir>/
└── <workflow_name>/
    ├── bet/
    │   └── _report/
    ├── mcflirt/
    └── smooth/
```

## References

- Gorgolewski K, et al. (2011). Nipype: a flexible, lightweight and extensible neuroimaging data processing framework in Python. *Frontiers in Neuroinformatics*, 5, 13. https://doi.org/10.3389/fninf.2011.00013
- Esteban O, et al. (2019). fMRIPrep: a robust preprocessing pipeline for functional MRI. *Nature Methods*, 16, 111–116. https://doi.org/10.1038/s41592-018-0235-4
- Nipype documentation: https://nipype.readthedocs.io
- FSL documentation: https://fsl.fmrib.ox.ac.uk/fsl/fslwiki
