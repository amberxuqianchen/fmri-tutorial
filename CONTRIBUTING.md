# Contributing to fMRI Analysis Tutorials for Social Neuroscience

Thank you for your interest in contributing! This project thrives on community input from researchers, educators, and students in neuroimaging and social neuroscience. Every contribution — from fixing a typo to adding a full tutorial module — is valued.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Setting Up the Development Environment](#setting-up-the-development-environment)
- [Adding New Modules](#adding-new-modules)
- [Style Guide for Notebooks](#style-guide-for-notebooks)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs and Issues](#reporting-bugs-and-issues)
- [Contribution Types](#contribution-types)

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this standard. Please report unacceptable behaviour to the contact address listed in that document.

---

## How to Contribute

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/fmri-tutorial.git
   cd fmri-tutorial
   ```
3. **Create a branch** for your work:
   ```bash
   git checkout -b feature/my-new-module
   ```
4. Make your changes following the guidelines below.
5. **Commit** with a clear message:
   ```bash
   git commit -m "Add Module 11: ROI analysis with nilearn"
   ```
6. **Push** to your fork and open a **Pull Request** against `main`.

For small fixes (typos, broken links) you may also use GitHub's in-browser editor directly.

---

## Setting Up the Development Environment

### Requirements

| Tool | Recommended version |
|------|---------------------|
| Python | ≥ 3.9 |
| JupyterLab / Jupyter Notebook | latest stable |
| Git | ≥ 2.30 |

### Steps

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Register the kernel (optional but recommended)
python -m ipykernel install --user --name fmri-tutorial --display-name "fMRI Tutorial"

# 4. Launch JupyterLab
jupyter lab
```

If a `requirements.txt` is not yet present in the repository, install the core stack manually:

```bash
pip install numpy scipy matplotlib nibabel nilearn \
            mne pandas seaborn jupyterlab ipykernel \
            dcm2bids bids-validator
```

### Verifying the Setup

Run the helper notebook `00_setup_check.ipynb` (if present) to confirm all imports resolve correctly.

---

## Adding New Modules

Modules are self-contained Jupyter notebooks numbered `XX_short_title.ipynb` placed in the repository root or an appropriate sub-directory.

### Checklist for a New Module

- [ ] Follow the sequential numbering scheme (`00`–`NN`).
- [ ] Begin with a **Module Overview** Markdown cell (see template below).
- [ ] Keep cells short and focused — one concept per cell where possible.
- [ ] Include a **Summary** cell at the end recapping key takeaways.
- [ ] Provide a **Next Steps** cell pointing to the following module.
- [ ] Ensure the notebook runs end-to-end with `Kernel > Restart & Run All` before submitting.
- [ ] Add the module to the table in `README.md`.
- [ ] If the module introduces new dependencies, update `requirements.txt`.

### Module Overview Cell Template

```markdown
## Module XX — Title

**Goal:** One-sentence description of what the learner will achieve.

**Prerequisites:** List the modules or concepts required before this one.

**Estimated time:** ~30 min

**Key concepts:** concept1, concept2, concept3
```

---

## Style Guide for Notebooks

### Narrative and Documentation

- Write in clear, accessible English aimed at early-career researchers.
- Explain the **neuroscientific motivation** before introducing code — readers should understand *why* before *how*.
- Use second-person ("you will…") to maintain an active, tutorial tone.
- Avoid jargon without definition; hyperlink to relevant papers or documentation where appropriate.
- Every Markdown heading should follow a logical hierarchy (`##` for sections, `###` for subsections).

### Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code.
- Use descriptive variable names (`bold_img` over `b`, `confounds_df` over `df`).
- Add a **comment above each logical block** explaining its purpose:
  ```python
  # Load the preprocessed BOLD image and extract the brain mask
  bold_img = nib.load(bold_path)
  mask_img = masking.compute_epi_mask(bold_img)
  ```
- Avoid deeply nested logic inside notebook cells; define helper functions at the top of the notebook or in a companion `.py` module.
- Pin random seeds where stochastic processes are used (`random_state=42`).

### Figures

- All figures must have axis labels, a title, and (where applicable) a colorbar with units.
- Use `matplotlib` or `nilearn` plotting utilities; avoid inline HTML.
- Save figures to an `figures/` subdirectory with `fig.savefig(...)` so they render in static viewers.

### Data

- Use only openly licensed example datasets (e.g., `nilearn.datasets`, OpenNeuro).
- Document the dataset source, accession number, and licence in the notebook.
- Do **not** commit large data files (> 1 MB) to the repository; use download helpers instead.

---

## Pull Request Process

1. Ensure your branch is up to date with `main` before opening a PR:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```
2. Fill in the PR template completely, including a description of changes and a testing checklist.
3. All notebooks must pass the **"Restart & Run All"** test locally.
4. At least **one maintainer review** is required before merging.
5. Maintainers may request changes; please address them within 14 days or the PR may be closed.
6. Once approved, a maintainer will squash-merge into `main`.

### Commit Message Convention

Use the imperative mood and prefix with a type:

| Prefix | Use for |
|--------|---------|
| `feat:` | New tutorial module or major feature |
| `fix:` | Bug fix in code or content error |
| `docs:` | Documentation-only changes |
| `style:` | Formatting, whitespace (no logic change) |
| `refactor:` | Code restructuring without feature/fix |
| `data:` | Adding or updating example data helpers |
| `ci:` | CI/CD configuration changes |

---

## Reporting Bugs and Issues

Found a broken notebook, incorrect analysis step, or missing dependency? Please [open an issue](../../issues/new) and include:

- **Module number and title** affected.
- **Operating system** and **Python version**.
- **Full error traceback** (paste into a fenced code block).
- **Steps to reproduce** the problem.
- Any relevant environment information (`pip freeze` output or `conda list`).

For content questions or discussions, prefer [GitHub Discussions](../../discussions) over issues.

---

## Contribution Types

We welcome contributions of all kinds:

### 🧑‍💻 Code
- New tutorial modules
- Bug fixes in existing notebooks
- Utility functions or helper scripts
- CI/CD improvements

### 📖 Documentation
- Clarifying explanations in existing notebooks
- Improving this `CONTRIBUTING.md` or `README.md`
- Adding docstrings to helper functions
- Translating content to other languages

### 🗂️ Data Examples
- Pointing to new openly licensed fMRI datasets
- Adding download helper scripts for publicly available data
- Improving existing data loading cells for robustness

### 🐛 Bug Reports & Suggestions
- Detailed issue reports (see above)
- Feature requests via GitHub Discussions
- Peer review of open pull requests

---

*Thank you for helping make neuroimaging education more accessible!*
