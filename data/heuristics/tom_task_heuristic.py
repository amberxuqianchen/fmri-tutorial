"""
tom_task_heuristic.py

HeudiConv heuristic for the Theory of Mind (ToM) fMRI dataset.

Compatible with:
  - OpenNeuro ds000228 (Richardson et al., 2018 – "Development of the social
    brain from age three to twelve years")

Dataset description
-------------------
ds000228 includes children (ages 3–12) and adults performing a Theory of Mind
localiser task (animated shapes: "ToM" and "Random" conditions).

Scans per subject
-----------------
  - T1w anatomical (1 run)
  - BOLD ToM task   (1 run, ~168 volumes at TR = 2 s)

Usage
-----
    heudiconv \\
      --dicom_dir_template /path/to/ds000228_dicoms/{subject}/*/*.dcm \\
      --subjects sub-pixar001 \\
      --heuristic tom_task_heuristic.py \\
      --outdir /path/to/bids_output/ \\
      --bids --overwrite

Series mapping
--------------
  Protocol / description                    → BIDS output
  -------------------------------------------------------
  t1_mprage* / T1w* / *MPRAGE*              → sub-XX/anat/sub-XX_T1w
  *tom* / *theory_of_mind* / *pixar* /      → sub-XX/func/sub-XX_task-ToM_bold
  *bold* (dim4 >= 100)
"""

import re

# Minimum number of volumes to consider a series a full functional run
# (rather than a single-volume fieldmap reference or scout image).
# ds000228 runs are ~168 volumes; set conservatively high to avoid false matches.
MIN_FUNCTIONAL_VOLUMES = 100


# --------------------------------------------------------------------------- #
# create_key
# --------------------------------------------------------------------------- #
def create_key(template, outtype=("nii.gz",), annotation_classes=None):
    """Return a BIDS key tuple.

    Parameters
    ----------
    template : str
        BIDS path template string.
    outtype : tuple of str
        Output file type(s).
    annotation_classes : None
        Reserved; always ``None`` for standard BIDS output.

    Returns
    -------
    tuple
        ``(template, outtype, annotation_classes)``
    """
    if template is None or not template:
        raise ValueError("Template must be a non-empty string.")
    return (template, outtype, annotation_classes)


# --------------------------------------------------------------------------- #
# infotodict
# --------------------------------------------------------------------------- #
def infotodict(seqinfo):
    """Map DICOM series to BIDS file keys for the ds000228 ToM dataset.

    Parameters
    ----------
    seqinfo : list of SeqInfo
        One element per DICOM series.

    Returns
    -------
    dict
        Mapping of BIDS key tuples → lists of series IDs.
    """

    # --- Define BIDS output keys ---
    t1w = create_key("sub-{subject}/anat/sub-{subject}_T1w")
    bold_tom = create_key("sub-{subject}/func/sub-{subject}_task-ToM_bold")

    info = {
        t1w: [],
        bold_tom: [],
    }

    for s in seqinfo:
        protocol = (s.protocol_name or "").lower()
        description = (s.series_description or "").lower()

        # ------------------------------------------------------------------ #
        # T1w anatomical
        # ------------------------------------------------------------------ #
        t1w_patterns = [
            r"t1[_\s]?mprage",
            r"t1w",
            r"mprage",
            r"t1[_\s]?weighted",
        ]
        if any(re.search(p, protocol) or re.search(p, description)
               for p in t1w_patterns):
            if not any(x in description for x in ("scout", "localizer", "loc")):
                info[t1w].append(s.series_id)
            continue

        # ------------------------------------------------------------------ #
        # BOLD – Theory of Mind task
        # Criteria:
        #   - Protocol or description references ToM, theory of mind, pixar,
        #     or the generic bold/epi tag
        #   - dim4 >= 100  (full functional run, not a fieldmap reference)
        # ------------------------------------------------------------------ #
        tom_patterns = [
            r"tom",
            r"theory[_\s]?of[_\s]?mind",
            r"pixar",
            r"social",
            r"animate",
        ]
        is_tom_protocol = any(
            re.search(p, protocol) or re.search(p, description)
            for p in tom_patterns
        )

        # Fallback: any BOLD/EPI series with enough volumes
        if not is_tom_protocol:
            is_tom_protocol = (
                "bold" in protocol or "epi" in protocol
            ) and s.dim4 is not None and s.dim4 >= MIN_FUNCTIONAL_VOLUMES

        if is_tom_protocol and s.dim4 and s.dim4 > 1:
            info[bold_tom].append(s.series_id)

    return info
