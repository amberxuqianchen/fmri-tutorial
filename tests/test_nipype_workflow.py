"""Tests for Nipype preprocessing workflow utilities (utils/nipype_helpers.py).

The entire module is gated behind ``pytest.importorskip("nipype")`` so it is
skipped cleanly in environments where nipype is not installed.  FSL binaries
are *not* required because the tests only inspect the workflow graph; they
never call ``workflow.run()``.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

pytest.importorskip("nipype", reason="nipype is not installed; skipping nipype workflow tests")


def test_minimal_preproc_workflow_creation():
    """Test that create_minimal_preproc_workflow() returns a Nipype Workflow object."""
    import nipype.pipeline.engine as pe

    from utils.nipype_helpers import create_minimal_preproc_workflow

    wf = create_minimal_preproc_workflow(name="test_preproc")
    assert isinstance(wf, pe.Workflow), (
        "create_minimal_preproc_workflow() should return a nipype Workflow"
    )
    assert wf.name == "test_preproc"


def test_workflow_has_required_nodes():
    """Test that the preprocessing workflow contains BET and MCFLIRT nodes."""
    from utils.nipype_helpers import create_minimal_preproc_workflow

    wf = create_minimal_preproc_workflow()
    node_names = [node.name for node in wf._graph.nodes()]

    assert "bet" in node_names, (
        f"Workflow should contain a 'bet' node. Found nodes: {node_names}"
    )
    assert "mcflirt" in node_names, (
        f"Workflow should contain an 'mcflirt' node. Found nodes: {node_names}"
    )


def test_workflow_has_inputnode_and_outputnode():
    """Test that the workflow has inputnode and outputnode utility nodes."""
    from utils.nipype_helpers import create_minimal_preproc_workflow

    wf = create_minimal_preproc_workflow()
    node_names = [node.name for node in wf._graph.nodes()]

    assert "inputnode" in node_names, "Workflow should have an 'inputnode'"
    assert "outputnode" in node_names, "Workflow should have an 'outputnode'"


def test_workflow_node_count():
    """Test that the preprocessing workflow has the expected number of nodes."""
    from utils.nipype_helpers import create_minimal_preproc_workflow

    wf = create_minimal_preproc_workflow()
    n_nodes = len(list(wf._graph.nodes()))
    # Expect: inputnode, meanvol, bet, mcflirt, smooth, outputnode = 6
    assert n_nodes == 6, (
        f"Expected 6 nodes in the preprocessing workflow, found {n_nodes}"
    )


def test_first_level_workflow_creation():
    """Test that create_first_level_workflow() returns a valid Nipype Workflow."""
    import nipype.pipeline.engine as pe

    from utils.nipype_helpers import create_first_level_workflow

    wf = create_first_level_workflow(name="test_first_level")
    assert isinstance(wf, pe.Workflow)
    assert wf.name == "test_first_level"


def test_get_node_info_returns_list():
    """Test that get_node_info() returns a list of dicts for a valid workflow."""
    from utils.nipype_helpers import create_minimal_preproc_workflow, get_node_info

    wf = create_minimal_preproc_workflow()
    info = get_node_info(wf)

    assert isinstance(info, list), "get_node_info() should return a list"
    assert len(info) > 0, "Node info list should not be empty"
    for entry in info:
        assert "name" in entry
        assert "interface" in entry
        assert "inputs" in entry


def test_get_node_info_raises_for_non_workflow():
    """Test that get_node_info() raises TypeError for a non-Workflow argument."""
    from utils.nipype_helpers import get_node_info

    with pytest.raises(TypeError):
        get_node_info("not_a_workflow")
