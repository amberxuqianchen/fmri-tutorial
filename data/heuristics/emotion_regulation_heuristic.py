"""
emotion_regulation_heuristic.py

HeudiConv heuristic for the emotion regulation fMRI dataset.

Compatible with:
  - The synthetic tutorial data in data/example_bids/
  - OpenNeuro ds000108 (Wager et al., 2008 – "Prefrontal-subcortical pathways
    mediating successful emotion regulation")

Usage
-----
    heudiconv \\
      --dicom_dir_template /path/to/dicoms/{subject}/*/*.dcm \\
      --subjects sub-01 \\
      --heuristic emotion_regulation_heuristic.py \\
      --outdir /path/to/bids_output/ \\
      --bids --overwrite

Series mapping
--------------
  Protocol name / series description        → BIDS output
  ------------------------------------------------------ 
  t1_mprage* / T1w* / *MPRAGE*              → sub-XX/anat/sub-XX_T1w
  bold_emotionreg* / task-emotionreg*       → sub-XX/func/sub-XX_task-emotionreg_run-{run}_bold
  (run index is inferred from series order)
"""

import re

# Minimum number of volumes to consider a series a full functional run
# (rather than a single-volume fieldmap reference or scout image).
MIN_FUNCTIONAL_VOLUMES = 10


# --------------------------------------------------------------------------- #
# create_key
# --------------------------------------------------------------------------- #
def create_key(template, outtype=("nii.gz",), annotation_classes=None):
    """Return a BIDS key tuple.

    Parameters
    ----------
    template : str
        BIDS path template, e.g.
        ``'sub-{subject}/anat/sub-{subject}_T1w'``.
    outtype : tuple of str
        Output file type(s).  Default ``('nii.gz',)``.
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
    """Map DICOM series to BIDS file keys.

    Parameters
    ----------
    seqinfo : list of SeqInfo
        Each element is a named-tuple with fields describing one DICOM series
        (series_description, protocol_name, dim4, TR, TE, …).

    Returns
    -------
    dict
        Keys are BIDS key tuples (from :func:`create_key`); values are lists
        of ``series_id`` strings that should be converted to that key.
    """

    # --- Define BIDS output keys ---
    t1w = create_key("sub-{subject}/anat/sub-{subject}_T1w")

    # Two runs of emotion-regulation BOLD; {item} is auto-incremented per run
    bold_emotionreg = create_key(
        "sub-{subject}/func/sub-{subject}_task-emotionreg_run-{item:02d}_bold"
    )

    info = {
        t1w: [],
        bold_emotionreg: [],
    }

    for s in seqinfo:
        protocol = (s.protocol_name or "").lower()
        description = (s.series_description or "").lower()

        # ------------------------------------------------------------------ #
        # T1w anatomical – match MPRAGE or T1w acquisitions
        # ------------------------------------------------------------------ #
        t1w_patterns = [
            r"t1[_\s]?mprage",
            r"t1w",
            r"mprage",
            r"t1[_\s]?weighted",
        ]
        if any(re.search(p, protocol) or re.search(p, description)
               for p in t1w_patterns):
            # Exclude localiser / scout series
            if not any(x in description for x in ("scout", "localizer", "loc")):
                info[t1w].append(s.series_id)
            continue

        # ------------------------------------------------------------------ #
        # BOLD – emotion regulation task
        # Criteria:
        #   - Protocol or description contains "emotionreg" or "emotion_reg"
        #     or "bold"
        #   - dim4 > 1  (multiple volumes → functional run, not a single ref)
        # ------------------------------------------------------------------ #
        bold_patterns = [
            r"emotion[_\s]?reg",
            r"bold[_\s]?emotion",
            r"task[_\s-]?emotionreg",
        ]
        is_bold_protocol = any(
            re.search(p, protocol) or re.search(p, description)
            for p in bold_patterns
        )

        # Fallback: any BOLD series with sufficient volumes
        if not is_bold_protocol:
            is_bold_protocol = (
                "bold" in protocol or "epi" in protocol
            ) and s.dim4 >= MIN_FUNCTIONAL_VOLUMES

        if is_bold_protocol and s.dim4 and s.dim4 > 1:
            info[bold_emotionreg].append(s.series_id)

    return info
